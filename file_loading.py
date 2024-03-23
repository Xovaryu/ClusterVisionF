"""
file_loading.py
This module contains all the big functions to handle loading various files, most importantly images dropped into the program for their metadata

01.	LSBExtractor
			This is a class for NAI's alpha channel metadata and has been copied over verbatim (thanks to the MIT license)
02.	on_drop_file
			Just checks the file ending and calls the according function
03.	try_to_load
			This function is used when trying to load settings from images or settings files, once per setting so it can report unfound settings
04.	load_settings_from_py/load_settings_from_image
			These functions are responsible for attempting to load all the possible settings according to file type
"""
from initialization import handle_exceptions, GlobalState, CH
GS = GlobalState()
import numpy as np
import gzip
import json
import os
import sys
import ast
from PIL import Image as PILImage
import image_generator as IM_G

# 01. Image metadata class from https://github.com/NovelAI/novelai-image-metadata
class LSBExtractor:
    def __init__(self, data):
        self.data = data
        self.rows, self.cols, self.dim = data.shape
        self.bits = 0
        self.byte = 0
        self.row = 0
        self.col = 0

    def _extract_next_bit(self):
        if self.row < self.rows and self.col < self.cols:
            bit = self.data[self.row, self.col, self.dim - 1] & 1
            self.bits += 1
            self.byte <<= 1
            self.byte |= bit
            self.row += 1
            if self.row == self.rows:
                self.row = 0
                self.col += 1

    def get_one_byte(self):
        while self.bits < 8:
            self._extract_next_bit()
        byte = bytearray([self.byte])
        self.bits = 0
        self.byte = 0
        return byte

    def get_next_n_bytes(self, n):
        bytes_list = bytearray()
        for _ in range(n):
            byte = self.get_one_byte()
            if not byte:
                break
            bytes_list.extend(byte)
        return bytes_list

    def read_32bit_integer(self):
        bytes_list = self.get_next_n_bytes(4)
        if len(bytes_list) == 4:
            integer_value = int.from_bytes(bytes_list, byteorder='big')
            return integer_value
        else:
            return None

# Functions to enable file dropping. on_drop_file() is called from main when a file is dropped in the window, which is handled here
# 02. This function is the entry point for this module and is called from the MAIN_APP whenever dropped files trigger the bound on_drop_file Kivy function
@handle_exceptions
def on_drop_file(window, file_path, x, y):
	window.dropped_files.append(file_path)
		
@handle_exceptions
def on_drop_end(window, x, y):
	# Check if file is a python file or image
	if len(window.dropped_files) > 1:
		single = False
	else:
		single = True
	for file_path in window.dropped_files:
		dropped_file_processor(window, file_path, single)
	window.dropped_files = []
		
@handle_exceptions
def dropped_file_processor(window, file_path, single):
	# Check if file is a python file or image
	file_path=file_path.decode('utf_8')
	print(f'Attempting to load file: {file_path}')
	if single:
		if file_path.endswith('.py'):
			load_settings_from_py(file_path)
		elif file_path.endswith('.jpg') or file_path.endswith('.png'):
			load_settings_from_image(file_path)
	elif file_path.endswith('.py'):
		bulk_queue(file_path)

def bulk_queue(file_path):
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
	if settings.get('collage_dimensions'):
		if settings.get('quantity'):
			IM_G.cluster_sequence(settings,GS.MAIN_APP.config_window.eval_guard_button.enabled)
		else:
			IM_G.cluster_collage(settings,GS.MAIN_APP.config_window.eval_guard_button.enabled)
	else:
		IM_G.image_sequence(settings,GS.MAIN_APP.config_window.eval_guard_button.enabled)
	GS.queued_tasks = len(GS.processing_queue)

# 03. In order to handle files robustly even when data in them doesn't have the expected format every setting should be loaded with a try statement
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

# 04. These two functions do what the title says, they are called depending on file ending and will attempt to load image settings
# load_settings_from_py() also briefly checks if the dropped .py file is a theme file, and if it is will load and apply it instead
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
		else:
			uc_label='UC'
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
	print(f'Loading from .py settings file successful')

@handle_exceptions
def load_settings_from_image(file_path):
	print(f'Loading settings from picture')
	GS.MAIN_APP.mode_switcher.switch_is('')
	exif_metadata = False
	if file_path.endswith('.png'):
		try:
			img = PILImage.open(file_path)
			metadata = {"size": img.size,"info": img.info}
			img = np.array(img)
			assert img.shape[-1] == 4 and len(img.shape) == 3, "image format"
			reader = LSBExtractor(img)
			magic = "stealth_pngcomp"
			read_magic = reader.get_next_n_bytes(len(magic)).decode("utf-8")
			assert magic == read_magic, "magic number"
			read_len = reader.read_32bit_integer() // 8
			json_data = reader.get_next_n_bytes(read_len)
			json_data = json.loads(gzip.decompress(json_data).decode("utf-8"))
			comment_dict = json.loads(json_data["Comment"])
		except:
			print("[Warning] Failed to get metadata from alpha channel, searching EXIF")
			try:
				comment_dict = json.loads(metadata["info"]["Comment"])
			except:
				print("[Warning] Failed to get metadata from EXIF, no metadata loaded")
				return
			exif_metadata = True
	if GS.MAIN_APP.name_import.enabled: GS.MAIN_APP.name_input.text = os.path.splitext(os.path.basename(file_path))[0]
	if GS.MAIN_APP.model_import.enabled:
		if metadata["info"].get('Source'):
			if metadata["info"]["Source"] == 'Stable Diffusion 1D09D794' or metadata["info"]["Source"] == 'Stable Diffusion F64BA557': # Furry: V1.2/1.3 
				GS.MAIN_APP.model_button.text = 'nai-diffusion-furry'
			elif metadata["info"]["Source"] == 'Stable Diffusion 81274D13' or metadata["info"]["Source"] == 'Stable Diffusion 3B3287AF': # Anime Full V1: Initial release/silent update with ControlNet
				GS.MAIN_APP.model_button.text = 'nai-diffusion'
			elif metadata["info"]["Source"] == 'Stable Diffusion 1D44365E' or metadata["info"]["Source"] == 'Stable Diffusion F4D50568': # Anime Safe V1: Initial release/silent update with ControlNet
				GS.MAIN_APP.model_button.text = 'safe-diffusion'
			elif metadata["info"]["Source"] == 'Stable Diffusion F1022D28': # Anime Full V2
				GS.MAIN_APP.model_button.text = 'nai-diffusion-2'
			elif metadata["info"]["Source"] == 'Stable Diffusion XL C1E1DE52' or metadata["info"]["Source"] == 'Stable Diffusion XL 8BA2AF87': # Anime Full V3/Inpaint V3
				GS.MAIN_APP.model_button.text = 'nai-diffusion-3'
			elif metadata["info"]["Source"] == 'Stable Diffusion': # This should normally not be encountered but some images in the past were generated like this due to a bug on NAI's side
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
		GS.MAIN_APP.resolution_selector.resolution_width.text = str(metadata["size"][0])
		GS.MAIN_APP.resolution_selector.resolution_height.text = str(metadata["size"][1])
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
		if exif_metadata:
			try_to_load('prompt', GS.MAIN_APP.prompt_input, metadata,["info", "Description"], True, 'text')
		else:
			try_to_load('prompt', GS.MAIN_APP.prompt_input, comment_dict,'prompt', True, 'text')
	if GS.MAIN_APP.uc_import.enabled:
		GS.MAIN_APP.uc_f.enabled = False
		if comment_dict.get('uc'):
			GS.MAIN_APP.uc_input.text = comment_dict["uc"]
		else:
			try_to_load('negative_prompt', GS.MAIN_APP.uc_input, comment_dict,'negative_prompt', True, 'text')
	if try_to_load('negative_prompt_strength', GS.MAIN_APP.ucs_input, comment_dict, 'uncond_scale', GS.MAIN_APP.ucs_import.enabled, 'text', 100):
		GS.MAIN_APP.ucs_input.text = str(float(GS.MAIN_APP.ucs_input.text)*100)
	print(f'Loading from picture successful')
