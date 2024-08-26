"""
file_loading.py
This module contains all the big functions to handle loading various files, most importantly images dropped into the program for their metadata

01.	LSBExtractor
			This is a class for NAI's alpha channel metadata and has been copied over verbatim (thanks to the MIT license)
02.	parse_nested_json+load_metadata_dicts
			These functions are responsible for properly loading in and generating Python dicts from metadata in images
03.	on_drop_file+on_drop_end+dropped_file_processor+bulk_queue
			Each dropped file, even in a bulk, calls on_drop_file separately, so those get appeneded to a list and then on_drop_end triggers the processing
04.	try_to_load
			This function is used when trying to load settings from images or settings files, once per setting so it can report unfound settings
05.	load_settings_from_py/load_settings_from_cvfimgs/load_settings_from_image
			These functions are responsible for attempting to load all the possible settings according to file type
"""
from initialization import handle_exceptions, GlobalState, CH
GS = GlobalState()
import numpy as np
import gzip
import zlib
import base64
import json
import os
import io
import sys
import ast
from PIL import Image as PILImage
import image_generator as IM_G
import kivy_widgets as KW
from kivy.clock import Clock

# 01. Image metadata class and function from https://github.com/NovelAI/novelai-image-metadata
def byteize(alpha):
    alpha = alpha.T.reshape((-1,))
    alpha = alpha[:(alpha.shape[0] // 8) * 8]
    alpha = np.bitwise_and(alpha, 1)
    alpha = alpha.reshape((-1, 8))
    alpha = np.packbits(alpha, axis=1)
    return alpha

class LSBExtractor:
    def __init__(self, data):
        self.data = byteize(data[..., -1])
        self.pos = 0

    def get_one_byte(self):
        byte = self.data[self.pos]
        self.pos += 1
        return byte

    def get_next_n_bytes(self, n):
        n_bytes = self.data[self.pos:self.pos + n]
        self.pos += n
        return bytearray(n_bytes)

    def read_32bit_integer(self):
        bytes_list = self.get_next_n_bytes(4)
        if len(bytes_list) == 4:
            integer_value = int.from_bytes(bytes_list, byteorder='big')
            return integer_value
        else:
            return None

# 02. This function makes sure that if nested parsable dicts are present as strings they get decoded properly
@handle_exceptions
def parse_nested_json(data):
	if isinstance(data, dict):
		return {key: parse_nested_json(value) for key, value in data.items()}
	elif isinstance(data, list):
		return [parse_nested_json(item) for item in data]
	elif isinstance(data, str):
		try:
			return parse_nested_json(json.loads(data))
		except json.JSONDecodeError:
			return data
	else:
		return data

# This function will attempt to get metadata both from the alpha channel as well as EXIF, and also provides an image size readout if needed
@handle_exceptions
def load_metadata_dicts(image):
	alpha_dict = {}
	exif_dict = {}
	if isinstance(image, str): # When we get a string that means we have a file path we need to read in
		with open(image, 'rb') as f:
			raw_image_data = f.read()
	else: # This is for when we get raw data already
		raw_image_data = image
	try:
		img = PILImage.open(io.BytesIO(raw_image_data))
		size_fallback = img.size
		metadata = img.info# {"size": img.size,"info": img.info}
		img = np.array(img)
		assert img.shape[-1] == 4 and len(img.shape) == 3, "image format"
		reader = LSBExtractor(img)
		magic = "stealth_pngcomp"
		read_magic = reader.get_next_n_bytes(len(magic)).decode("utf-8")
		assert magic == read_magic, "magic number"
		read_len = reader.read_32bit_integer() // 8
		json_data = reader.get_next_n_bytes(read_len)
		json_data = json.loads(gzip.decompress(json_data).decode("utf-8"))
		alpha_dict = parse_nested_json(json_data)
	except:
		print("[Warning] Failed to get metadata from alpha channel")
		if GS.verbose:
			traceback.print_exc()
	try:
		exif_dict = parse_nested_json(metadata)
	except:
		print("[Warning] Failed to get metadata from EXIF, no metadata loaded")
		if GS.verbose:
			traceback.print_exc()
	return alpha_dict, exif_dict, size_fallback

# Functions to enable file dropping. on_drop_file() is called from main when a file is dropped in the window, which is handled here
# 03. This function is the entry point for this module and is called from the MAIN_APP whenever dropped files trigger the bound on_drop_file Kivy function
@handle_exceptions
def on_drop_file(window, file_path, x, y):
	window.dropped_files.append(file_path)

# Each drop will then trigger this function once it's done, with one on_drop_file call per file
@handle_exceptions
def on_drop_end(window, x, y):
	# Because DPI and real pixel position handling in Kivy (and far beyond it) is an unholy mess, we immediately need to fix the bad x, y values
	x, y = window.mouse_pos
	
	# Get the size hints and calculate the relative width
	left_size_hint_x = GS.MAIN_APP.drop_overlay.left_layout.size_hint_x
	right_size_hint_x = GS.MAIN_APP.drop_overlay.right_layout.size_hint_x
	total_size_hint = left_size_hint_x + right_size_hint_x
	left_width = (left_size_hint_x / total_size_hint) * window.width
	
	# Check if the drop is left (image metadata) or right
	if x < left_width:
		location = 'left'
	else:
		location = 'right'
	
	# Check if file is a python file or image
	if len(window.dropped_files) > 1:
		single = False
	else:
		single = True
	for file_path in window.dropped_files:
		dropped_file_processor(window, file_path, single, location)
	window.dropped_files = []

# This function will then be called once per file from on_drop_end
@handle_exceptions
def dropped_file_processor(window, file_path, single, location):
	# Check if file is a python file or image
	file_path=file_path.decode('utf_8')
	print(f'Attempting to load file: {file_path}')
	if file_path.endswith('.cvfimgs'):
		load_settings_from_cvfimgs(file_path)
	elif single:
		if file_path.endswith('.py'):
			load_settings_from_py(file_path)
		elif file_path.endswith('.jpg') or file_path.endswith('.png'):
			if location == 'left':
				load_settings_from_image(file_path)
			else:
				GS.MAIN_APP.loaded_images_dropdown.add_widget(KW.ImageGenerationEntry(file_path))
	else: # Multi
		if file_path.endswith('.py'):
			bulk_queue(file_path)
		if file_path.endswith('.jpg') or file_path.endswith('.png'):
			GS.MAIN_APP.loaded_images_dropdown.add_widget(KW.ImageGenerationEntry(file_path))

# When importing multiple CVF settings files this function handles putting them immediately into the queue, for instance for test cases
def bulk_queue(file_path):
	if GS.MAIN_APP.process_button.disabled:
		print(f'[Warning] Tasks not queued, finish the current queue first')
	else:
		with open(file_path, "rb") as f:
			file_text = f.read().decode('utf_16')
			lines = file_text.splitlines()
			print(f'Loading and queueing generation settings from .py file')
			settings = ast.literal_eval(file_text[9:])
		# These values need fallbacks to avoid generation failures
		if not settings.get('guidance_rescale'):
			settings["guidance_rescale"] = '0'
			print(f'[Warning] Failed to load guidance_rescale from file, falling back to 0')
		if not settings.get('dynamic_thresholding'):
			settings["dynamic_thresholding"] = False
			print(f'[Warning] Failed to load dynamic_thresholding from file, falling back to False')
		if not settings.get('negative_prompt_strength'):
			settings["negative_prompt_strength"] = '100'
			print(f'[Warning] Failed to load negative_prompt_strength from file, falling back to 100')
		if not settings.get('negative_prompt'):
			settings["negative_prompt"] = settings["UC"]
		# Support for legacy file format that still put the F wrapping into the files
		
		for prompt_type in ["negative_prompt", "prompt"]:
			if isinstance(settings[prompt_type], list):
				# Check if it's a list of lists (legacy format)
				if isinstance(settings[prompt_type][0], list):
					settings[prompt_type] = [
						string[4:-3] if string.startswith('f"""') and string.endswith('"""') else string
						for string in settings[prompt_type][0]
					]
				else:
					# Handle the new format (regular list)
					settings[prompt_type] = [
						string[4:-3] if string.startswith('f"""') and string.endswith('"""') else string
						for string in settings[prompt_type]
					]
		if settings.get('collage_dimensions'):
			if settings.get('quantity'):
				IM_G.cluster_sequence(settings,GS.MAIN_APP.config_window.eval_guard_button.enabled)
			else:
				IM_G.cluster_collage(settings,GS.MAIN_APP.config_window.eval_guard_button.enabled)
		else:
			IM_G.image_sequence(settings,GS.MAIN_APP.config_window.eval_guard_button.enabled)
		GS.queued_tasks = len(GS.processing_queue)

# 04. In order to handle files robustly even when data in them doesn't have the expected format every setting should be loaded with a try statement
# No @handle_exceptions for try_to_load() because it is expected to fail when encountering incomplete data and will report accordingly
def try_to_load(identifier, target, settings, keys, enabled, setattr_id = None, fallback = None):
	try:
		if enabled:
			if type(keys) == list:
				value = settings
				for key in keys:
					value = value[key]
			else:
				value = settings[keys]
			if setattr_id is None:
				target = settings[key]
			else:
				if setattr_id == 'text':
					setattr(target, setattr_id, str(value))
				else:
					setattr(target, setattr_id, value)
			return True
	except:
		if fallback != None:
			if setattr_id is None:
				target = settings[key]
			else:
				if setattr_id == 'text':
					setattr(target, setattr_id, str(fallback))
				else:
					setattr(target, setattr_id, fallback)
			print(f'[Warning] Failed to load {identifier} from file, falling back to {fallback}')
		else:
			print(f'[Warning] Failed to load {identifier} from file')

# 05. These three functions do what the title says, they are called depending on file ending and will attempt to load image settings
# load_settings_from_py() also checks if the dropped .py file is a theme file, and if it is will load and apply it instead
@handle_exceptions
def load_settings_from_py(file_path):
	with open(file_path, "rb") as f:
		file_text = f.read().decode('utf_16')
		lines = file_text.splitlines()
		if len(lines) > 1 and lines[1].startswith("THEME"):
			print(f'Loading theme from .py file')
			CH.load_config(file_path)
			GS.MAIN_APP.config_window.theme_layout.apply_theme(None)
			return
		elif len(lines) > 1 and lines[0].startswith("settings"):
			print(f'Loading generation settings from .py file')
			settings = ast.literal_eval(file_text[9:])

			# Load the settings using the try_to_load function
			try_to_load('name', GS.MAIN_APP.name_input, settings, 'name', GS.MAIN_APP.name_import.enabled, 'text')
			try_to_load('folder_name', GS.MAIN_APP.folder_name_input, settings, 'folder_name', GS.MAIN_APP.folder_name_import.enabled, 'text')
			try_to_load('model', GS.MAIN_APP.model_button, settings, 'model', GS.MAIN_APP.model_import.enabled, 'text')
			if GS.MAIN_APP.steps_import.enabled: 
				if type(settings["steps"]) == str:
					GS.MAIN_APP.steps_f.enabled = True
					try_to_load('steps', GS.MAIN_APP.steps_input_f, settings, 'steps', True, 'text')
				elif type(settings["steps"]) == list:
					GS.MAIN_APP.steps_f.enabled = False
					try_to_load('steps', GS.MAIN_APP.steps_slider_min, settings, ['steps', 0], True, 'value')
					try_to_load('steps', GS.MAIN_APP.steps_slider_max, settings, ['steps', 1], True, 'value')
				else:
					GS.MAIN_APP.steps_f.enabled = False
					try_to_load('steps', GS.MAIN_APP.steps_slider_min, settings, 'steps', True, 'value')
					try_to_load('steps', GS.MAIN_APP.steps_slider_max, settings, 'steps', True, 'value')
			if GS.MAIN_APP.guidance_import.enabled:
				if type(settings["scale"]) == str:
					GS.MAIN_APP.guidance_f.enabled = True
					try_to_load('scale', GS.MAIN_APP.guidance_input_f, settings, 'scale', True, 'text')
				elif type(settings["scale"]) == list:
					GS.MAIN_APP.guidance_f.enabled = False
					try_to_load('scale', GS.MAIN_APP.guidance_input_min, settings, ['scale', 0], True, 'text')
					try_to_load('scale', GS.MAIN_APP.guidance_input_max, settings, ['scale', 1], True, 'text')
				else:
					GS.MAIN_APP.guidance_f.enabled = False
					try_to_load('scale', GS.MAIN_APP.guidance_input_min, settings, 'scale', True, 'text')
					try_to_load('scale', GS.MAIN_APP.guidance_input_max, settings, 'scale', True, 'text')
				try_to_load('guidance_rescale', GS.MAIN_APP.guidance_rescale_input_f, settings, 'guidance_rescale', True, 'text', 0)
			try_to_load('dynamic_thresholding', GS.MAIN_APP.decrisp_button, settings, 'dynamic_thresholding', GS.MAIN_APP.decrisp_import.enabled, 'enabled', False)
			try_to_load('dynamic_thresholding_mimic_scale', GS.MAIN_APP.decrisp_guidance_input, settings, 'dynamic_thresholding_mimic_scale', GS.MAIN_APP.decrisp_import.enabled, 'text')
			try_to_load('dynamic_thresholding_percentile', GS.MAIN_APP.decrisp_percentile_input, settings, 'dynamic_thresholding_percentile', GS.MAIN_APP.decrisp_import.enabled, 'text')
			try_to_load('img_mode_width', GS.MAIN_APP.resolution_selector.resolution_width, settings, ['img_mode', 'width'], GS.MAIN_APP.resolution_import.enabled, 'text')
			try_to_load('img_mode_height', GS.MAIN_APP.resolution_selector.resolution_height, settings, ['img_mode', 'height'], GS.MAIN_APP.resolution_import.enabled, 'text')
			if GS.MAIN_APP.prompt_import.enabled:
				if type(settings["prompt"])!=str:
					GS.MAIN_APP.prompt_f.enabled = True
					GS.MAIN_APP.prompt_f_input.load_prompts(settings["prompt"])
				else:
					GS.MAIN_APP.prompt_f.enabled = False
					try_to_load('prompt', GS.MAIN_APP.prompt_input, settings, 'prompt', True, 'text')
			if GS.MAIN_APP.uc_import.enabled:
				if settings.get('negative_prompt'):
					uc_label='negative_prompt'
				elif settings.get('UC'):
					uc_label='UC'
				else:
					uc_label=None
				if uc_label==None:
					GS.MAIN_APP.uc_f.enabled = False
					GS.MAIN_APP.uc_input.text = ''
				else:
					if type(settings[uc_label])!=str:
						GS.MAIN_APP.uc_f.enabled = True
						GS.MAIN_APP.uc_f_input.load_prompts(settings[uc_label])
					else:
						GS.MAIN_APP.uc_f.enabled = False
						try_to_load('negative_prompt', GS.MAIN_APP.uc_input, settings, uc_label, True, 'text')
			try_to_load('negative_prompt_strength', GS.MAIN_APP.ucs_input, settings, 'negative_prompt_strength', GS.MAIN_APP.ucs_import.enabled, 'text', 100)
			try_to_load('noise_schedule', GS.MAIN_APP.noise_schedule_button, settings, 'noise_schedule', GS.MAIN_APP.sampler_import.enabled, 'text', 'default')
			if settings.get('collage_dimensions'):
				try_to_load('collage_dimensions', GS.MAIN_APP.cc_dim_width, settings, ['collage_dimensions', 0], GS.MAIN_APP.cc_dim_import.enabled, 'text')
				try_to_load('collage_dimensions', GS.MAIN_APP.cc_dim_height, settings, ['collage_dimensions', 1], GS.MAIN_APP.cc_dim_import.enabled, 'text')
				if GS.MAIN_APP.cc_seed_import.enabled: GS.MAIN_APP.cc_seed_grid.load_seeds(settings["seed"])
				if type(settings["sampler"]) == list and GS.MAIN_APP.sampler_import.enabled:
					try:
						GS.MAIN_APP.sampler_input.text = ', '.join(settings["sampler"][0]) # This is a string of samplers as used for clusters
						GS.MAIN_APP.sampler_cutoff.text = str(settings["sampler"][1]) # This is the sampler cutoff, determining how sampler clusters are placed
					except:
						traceback.print_exc()
				elif GS.MAIN_APP.sampler_import.enabled:
					try_to_load('sampler', GS.MAIN_APP.sampler_input, settings, 'sampler', True, 'text')
				if settings.get('quantity'):
					if GS.MAIN_APP.is_range_import.enabled:
						try_to_load('image sequence quantity', GS.MAIN_APP.is_quantity, settings, 'quantity', True, 'text')
						if settings["video"] == 'standard':
							GS.MAIN_APP.is_video.enabled = True
						else:
							GS.MAIN_APP.is_video.enabled = False
						try_to_load('FPS', GS.MAIN_APP.is_fps, settings, 'FPS', True, 'text')
					GS.MAIN_APP.mode_switcher.switch_cs('')
				else:
					GS.MAIN_APP.mode_switcher.switch_cc('')
			else:
				GS.MAIN_APP.mode_switcher.switch_is('')
				if GS.MAIN_APP.sampler_import.enabled: 
					try:
						sampler = settings["sampler"]
						if sampler.endswith('_dyn'):
							GS.MAIN_APP.sampler_smea.enabled = True
							GS.MAIN_APP.sampler_dyn.enabled = True
							sampler = sampler[:-4]
						elif sampler.endswith('_smea'):
							GS.MAIN_APP.sampler_smea.enabled = True
							GS.MAIN_APP.sampler_dyn.enabled = False
							sampler = sampler[:-5]
						else:
							GS.MAIN_APP.sampler_smea.enabled = False
							GS.MAIN_APP.sampler_dyn.enabled = False
						GS.MAIN_APP.sampler_button.text = str(sampler)
					except:
						traceback.print_exc()
				try_to_load('seed', GS.MAIN_APP.is_seed_input, settings, 'seed', GS.MAIN_APP.is_seed_import.enabled, 'text')
				if GS.MAIN_APP.is_range_import.enabled:
					try_to_load('image sequence quantity', GS.MAIN_APP.is_quantity, settings, 'quantity', True, 'text')
					if settings["video"] == 'standard':
						GS.MAIN_APP.is_video.enabled = True
					else:
						GS.MAIN_APP.is_video.enabled = False
					try_to_load('FPS', GS.MAIN_APP.is_fps, settings, 'FPS', True, 'text')
			print(f'Loading settings from .py settings file successful')
		else:
			print(f'[Warning] Unidentified .py file type, no action taken')

# This function handles reading in the CVF specific cvfimgs file format which consists of compressed dicts and image data
@handle_exceptions
def load_settings_from_cvfimgs(file_path):
	print(f'Loading image entries from .cvfimgs file')
	with open(file_path, 'rb') as file:
		compressed_data = file.read()
	
	# Decompress the data
	json_data = zlib.decompress(compressed_data).decode('utf-8')
	
	# Parse the JSON
	image_entries = json.loads(json_data)
	
	for entry in image_entries:
		# Decode and decompress the image data
		compressed_image = base64.b64decode(entry["entry_reference"])
		raw_image_data = zlib.decompress(compressed_image)
		
		i2i = entry.get('i2i')
		vt = entry.get('vt')
		
		initial_settings = [
			i2i["condition"][3:-3].replace("\\'","'") if i2i else '',
			i2i["strength"][3:-3].replace("\\'","'") if i2i else '0.7',
			i2i["noise"][3:-3].replace("\\'","'") if i2i else '0',
			vt["condition"][3:-3].replace("\\'","'") if vt else '',
			vt["strength"][3:-3].replace("\\'","'") if vt else '0.7',
			vt["information"][3:-3].replace("\\'","'") if vt else '1',
		]
		
		# Schedule the widget addition
		Clock.schedule_once(lambda dt, raw_data=raw_image_data, settings=initial_settings: 
			GS.MAIN_APP.loaded_images_dropdown.add_widget(KW.ImageGenerationEntry(raw_data, False, False, settings)))
	
	print(f'Loading image entries from .cvfimgs settings file successful')

# For normal images this function will attempt to get metadata from them unless loaded for processing
@handle_exceptions
def load_settings_from_image(file_path):
	print(f'Loading settings from picture')
	GS.MAIN_APP.mode_switcher.switch_is('')
	
	alpha_dict, exif_dict, size_fallback = load_metadata_dicts(file_path)
	
	if alpha_dict != {}:
		metadata = alpha_dict
	elif exif_dict != {}:
		metadata = exif_dict
	else:
		print("[Warning] Couldn't get usable metadata")
		return
	comment_dict = metadata["Comment"]
	
	if GS.MAIN_APP.name_import.enabled:
		try:
			GS.MAIN_APP.name_input.text = os.path.splitext(os.path.basename(file_path))[0]
		except:
			print(f'[Warning] Failed to set file name')
	if GS.MAIN_APP.model_import.enabled:
		if metadata.get('Source'):
			if metadata["Source"] == 'Stable Diffusion 1D09D794' or metadata["Source"] == 'Stable Diffusion F64BA557': # Furry: V1.2/1.3 
				GS.MAIN_APP.model_button.text = 'nai-diffusion-furry'
			elif metadata["Source"] == 'Stable Diffusion 81274D13' or metadata["Source"] == 'Stable Diffusion 3B3287AF': # Anime Full V1: Initial release/silent update with ControlNet
				GS.MAIN_APP.model_button.text = 'nai-diffusion'
			elif metadata["Source"] == 'Stable Diffusion 1D44365E' or metadata["Source"] == 'Stable Diffusion F4D50568': # Anime Safe V1: Initial release/silent update with ControlNet
				GS.MAIN_APP.model_button.text = 'safe-diffusion'
			elif metadata["Source"] == 'Stable Diffusion F1022D28': # Anime Full V2
				GS.MAIN_APP.model_button.text = 'nai-diffusion-2'
			elif metadata["Source"] == 'Stable Diffusion XL C1E1DE52' or metadata["Source"] == 'Stable Diffusion XL 8BA2AF87': # Anime Full V3/Inpaint V3
				GS.MAIN_APP.model_button.text = 'nai-diffusion-3'
			elif metadata["Source"] == 'Stable Diffusion XL 9CC2F394' or metadata["Source"] == 'Stable Diffusion XL C8704949': # Furry Full V3/Inpaint V3
				GS.MAIN_APP.model_button.text = 'nai-diffusion-furry-3'
			elif metadata["Source"] == 'Stable Diffusion': # This should normally not be encountered but some images in the past were generated like this due to a bug on NAI's side
				print(f"[Warning] The loaded picture doesn't have the model specified. Defaulting to NAID Full V3, but be aware the original model for this picture might have been different")
				GS.MAIN_APP.model_button.text = 'nai-diffusion-3'
			else:
				print(f'[Warning] Error while determining model, defaulting to NAID Full V3')
				GS.MAIN_APP.model_button.text = 'nai-diffusion-3'
	GS.MAIN_APP.steps_f.enabled = False
	GS.MAIN_APP.guidance_f.enabled = False
	try_to_load('steps', GS.MAIN_APP.steps_slider_min, comment_dict, 'steps', GS.MAIN_APP.steps_import.enabled, 'value')
	try_to_load('scale', GS.MAIN_APP.guidance_input_min, comment_dict, 'scale', GS.MAIN_APP.guidance_import.enabled, 'text')
	try_to_load('guidance_rescale', GS.MAIN_APP.guidance_rescale_input_f, comment_dict, 'cfg_rescale', GS.MAIN_APP.guidance_import.enabled, 'text', 0)
	if GS.MAIN_APP.resolution_import.enabled:
		if comment_dict.get('width'):
			GS.MAIN_APP.resolution_selector.resolution_width.text = str(comment_dict["width"])
			GS.MAIN_APP.resolution_selector.resolution_height.text = str(comment_dict["height"])
		else:
			GS.MAIN_APP.resolution_selector.resolution_width.text = str(size_fallback[0])
			GS.MAIN_APP.resolution_selector.resolution_height.text = str(size_fallback[1])
	try_to_load('seed', GS.MAIN_APP.is_seed_input, comment_dict, 'seed', GS.MAIN_APP.is_seed_import.enabled, 'text')

	if GS.MAIN_APP.sampler_import.enabled:
		try_to_load('noise_schedule', GS.MAIN_APP.noise_schedule_button, comment_dict, 'noise_schedule', True, 'text', 'default')
		try:
			sampler_string = str(comment_dict["sampler"])
		except:
			traceback.print_exc()
		if sampler_string == 'nai_smea_dyn':
			GS.MAIN_APP.sampler_button.text = 'k_euler_ancestral'
			GS.MAIN_APP.sampler_smea.enabled = True
			GS.MAIN_APP.sampler_dyn.enabled = True
		elif sampler_string == 'nai_smea':
			GS.MAIN_APP.sampler_button.text = 'k_euler_ancestral'
			GS.MAIN_APP.sampler_smea.enabled = True
			GS.MAIN_APP.sampler_dyn.enabled = False
		else:
			GS.MAIN_APP.sampler_button.text = sampler_string
			if comment_dict.get('sm_dyn'):
				if comment_dict["sm_dyn"]:
					GS.MAIN_APP.sampler_smea.enabled = True
					GS.MAIN_APP.sampler_dyn.enabled = True
			elif comment_dict.get('sm'):
				if comment_dict["sm"]:
					GS.MAIN_APP.sampler_smea.enabled = True
					GS.MAIN_APP.sampler_dyn.enabled = False
			else:
				GS.MAIN_APP.sampler_smea.enabled = False
				GS.MAIN_APP.sampler_dyn.enabled = False
	if GS.MAIN_APP.decrisp_import.enabled:
		try_to_load('dynamic_thresholding', GS.MAIN_APP.decrisp_button, comment_dict, 'dynamic_thresholding', True, 'enabled', False)
		try_to_load('dynamic_thresholding_mimic_scale', GS.MAIN_APP.decrisp_guidance_input, comment_dict, 'dynamic_thresholding_mimic_scale', True, 'text')
		try_to_load('dynamic_thresholding_percentile', GS.MAIN_APP.decrisp_percentile_input, comment_dict, 'dynamic_thresholding_percentile', True, 'text')
	if GS.MAIN_APP.prompt_import.enabled:
		GS.MAIN_APP.prompt_f.enabled = False
		if comment_dict.get('prompt'):
			GS.MAIN_APP.prompt_input.text = comment_dict["prompt"]
		else:
			try_to_load('prompt', GS.MAIN_APP.prompt_input, metadata,'Description', True, 'text')
	if GS.MAIN_APP.uc_import.enabled:
		GS.MAIN_APP.uc_f.enabled = False
		if comment_dict.get('uc'):
			GS.MAIN_APP.uc_input.text = comment_dict["uc"]
		else:
			try_to_load('negative_prompt', GS.MAIN_APP.uc_input, comment_dict,'negative_prompt', True, 'text')
	if try_to_load('negative_prompt_strength', GS.MAIN_APP.ucs_input, comment_dict, 'uncond_scale', GS.MAIN_APP.ucs_import.enabled, 'text', 100):
		GS.MAIN_APP.ucs_input.text = str(float(GS.MAIN_APP.ucs_input.text)*100)
	print(f'Loading from picture successful')
