"""
file_loading.py
This module contains all the big functions to handle loading various files, most importantly images dropped into the program for their metadata

01.	LSBExtractor
			This is a class for NAI's alpha channel metadata and has been copied over verbatim (thanks to the MIT license)
02.	on_file_drop
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

# Functions to enable file dropping. on_file_drop() is called from main when a file is dropped in the window, which is handled here
# 02. This function is the entry point for this module and is called from the main_app whenever dropped files trigger the bound on_drop_file Kivy function
@handle_exceptions
def on_file_drop(window, file_path, x, y):
	# Check if file is a python file or image
	file_path=file_path.decode('utf_8')
	print(f'Attempting to load file: {file_path}')
	if file_path.endswith('.py'):
		load_settings_from_py(file_path)
	elif file_path.endswith('.jpg') or file_path.endswith('.png'):
		load_settings_from_image(file_path)

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
			GS.main_app.config_window.theme_layout.apply_theme(None)
			return
		print(f'Loading generation settings from .py file')
		settings = ast.literal_eval(file_text[9:])

	# Load the settings using the try_to_load function
	try_to_load('name', GS.main_app.name_input, settings, 'name', GS.main_app.name_import.enabled, 'text')
	try_to_load('folder_name', GS.main_app.folder_name_input, settings, 'folder_name', GS.main_app.folder_name_import.enabled, 'text')
	try_to_load('model', GS.main_app.model_button, settings, 'model', GS.main_app.model_import.enabled, 'text')
	if GS.main_app.steps_import.enabled: 
		if type(settings["steps"]) == str:
			GS.main_app.steps_f.enabled = True
			try_to_load('steps', GS.main_app.steps_input_f, settings, 'steps', True, 'text')
		elif type(settings["steps"]) == list:
			GS.main_app.steps_f.enabled = False
			try_to_load('steps', GS.main_app.steps_slider_min, settings, ['steps', 0], True, 'value')
			try_to_load('steps', GS.main_app.steps_slider_max, settings, ['steps', 1], True, 'value')
		else:
			GS.main_app.steps_f.enabled = False
			try_to_load('steps', GS.main_app.steps_slider_min, settings, 'steps', True, 'value')
			try_to_load('steps', GS.main_app.steps_slider_max, settings, 'steps', True, 'value')
	if GS.main_app.guidance_import.enabled:
		if type(settings["scale"]) == str:
			GS.main_app.guidance_f.enabled = True
			try_to_load('scale', GS.main_app.guidance_input_f, settings, 'scale', True, 'text')
			try_to_load('guidance_rescale', GS.main_app.guidance_rescale_input_f, settings, 'guidance_rescale', True, 'text')
		elif type(settings["scale"]) == list:
			GS.main_app.guidance_f.enabled = False
			try_to_load('scale', GS.main_app.guidance_input_min, settings, ['scale', 0], True, 'text')
			try_to_load('scale', GS.main_app.guidance_input_max, settings, ['scale', 1], True, 'text')
		else:
			GS.main_app.guidance_f.enabled = False
			try_to_load('scale', GS.main_app.guidance_input_min, settings, 'scale', True, 'text')
			try_to_load('scale', GS.main_app.guidance_input_max, settings, 'scale', True, 'text')
	try_to_load('dynamic_thresholding', GS.main_app.decrisp_button, settings, 'dynamic_thresholding', GS.main_app.decrisp_import.enabled, 'enabled', False)
	try_to_load('dynamic_thresholding_mimic_scale', GS.main_app.decrisp_guidance_input, settings, 'dynamic_thresholding_mimic_scale', GS.main_app.decrisp_import.enabled, 'text')
	try_to_load('dynamic_thresholding_percentile', GS.main_app.decrisp_percentile_input, settings, 'dynamic_thresholding_percentile', GS.main_app.decrisp_import.enabled, 'text')
	try_to_load('img_mode_width', GS.main_app.resolution_selector.resolution_width, settings, ['img_mode', 'width'], GS.main_app.resolution_import.enabled, 'text')
	try_to_load('img_mode_height', GS.main_app.resolution_selector.resolution_height, settings, ['img_mode', 'height'], GS.main_app.resolution_import.enabled, 'text')
	if GS.main_app.prompt_import.enabled:
		if type(settings["prompt"])!=str:
			GS.main_app.prompt_f.enabled = True
			GS.main_app.prompt_f_input.load_prompts(settings["prompt"])
		else:
			GS.main_app.prompt_f.enabled = False
			try_to_load('prompt', GS.main_app.prompt_input, settings, 'prompt', True, 'text')
	if GS.main_app.uc_import.enabled:
		if settings.get('negative_prompt'):
			uc_label='negative_prompt'
		else:
			uc_label='UC'
		if type(settings[uc_label])!=str:
			GS.main_app.uc_f.enabled = True
			GS.main_app.uc_f_input.load_prompts(settings[uc_label])
		else:
			GS.main_app.uc_f.enabled = False
			try_to_load('negative_prompt', GS.main_app.uc_input, settings, uc_label, True, 'text')
	try_to_load('negative_prompt_strength', GS.main_app.ucs_input, settings, 'negative_prompt_strength', GS.main_app.ucs_import.enabled, 'text', 100)
	if settings.get('collage_dimensions'):
		try_to_load('collage_dimensions', GS.main_app.cc_dim_width, settings, ['collage_dimensions', 0], GS.main_app.cc_dim_import.enabled, 'text')
		try_to_load('collage_dimensions', GS.main_app.cc_dim_height, settings, ['collage_dimensions', 1], GS.main_app.cc_dim_import.enabled, 'text')
		if GS.main_app.cc_seed_import.enabled: GS.main_app.cc_seed_grid.load_seeds(settings["seed"])
		if type(settings["sampler"]) == list and GS.main_app.cc_sampler_import.enabled:
			try:
				GS.main_app.cc_sampler_input.text = ', '.join(settings["sampler"][0])
			except:
				traceback.print_exc()
		elif GS.main_app.cc_sampler_import.enabled:
			try_to_load('sampler', GS.main_app.cc_sampler_input, settings, 'sampler', True, 'text')
		if settings.get('quantity'):
			if GS.main_app.is_range_import.enabled:
				try_to_load('image sequence quantity', GS.main_app.is_quantity, settings, 'quantity', True, 'text')
				if settings["video"] == 'standard':
					GS.main_app.is_video.enabled = True
				else:
					GS.main_app.is_video.enabled = False
				try_to_load('FPS', GS.main_app.is_fps, settings, 'FPS', True, 'text')
			GS.main_app.mode_switcher.switch_cs('')
		else:
			GS.main_app.mode_switcher.switch_cc('')
	else:
		GS.main_app.mode_switcher.switch_is('')
		if GS.main_app.is_sampler_import.enabled: 
			try:
				sampler = settings["sampler"]
				if sampler.endswith('_dyn'):
					GS.main_app.is_sampler_smea.enabled = True
					GS.main_app.is_sampler_dyn.enabled = True
					sampler = sampler[:-4]
				elif sampler.endswith('_smea'):
					GS.main_app.is_sampler_smea.enabled = True
					GS.main_app.is_sampler_dyn.enabled = False
					sampler = sampler[:-5]
				else:
					GS.main_app.is_sampler_smea.enabled = False
					GS.main_app.is_sampler_dyn.enabled = False
				GS.main_app.is_sampler_button.text = str(sampler)
			except:
				traceback.print_exc()
		try_to_load('seed', GS.main_app.is_seed_input, settings, 'seed', GS.main_app.is_seed_import.enabled, 'text')
		if GS.main_app.is_range_import.enabled:
			try_to_load('image sequence quantity', GS.main_app.is_quantity, settings, 'quantity', True, 'text')
			if settings["video"] == 'standard':
				GS.main_app.is_video.enabled = True
			else:
				GS.main_app.is_video.enabled = False
			try_to_load('FPS', GS.main_app.is_fps, settings, 'FPS', True, 'text')
	print(f'Loading from .py settings file successful')

@handle_exceptions
def load_settings_from_image(file_path):
	print(f'Loading settings from picture')
	GS.main_app.mode_switcher.switch_is('')
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
		except Exception as e:
			print("Failed to get metadata from alpha channel, searching EXIF")
			comment_dict = json.loads(metadata["info"]["Comment"])
			exif_metadata = True
	if GS.main_app.name_import.enabled: GS.main_app.name_input.text = os.path.splitext(os.path.basename(file_path))[0]
	if GS.main_app.model_import.enabled:
		if metadata["info"].get('Source'):
			if metadata["info"]["Source"] == 'Stable Diffusion 1D09D794' or metadata["info"]["Source"] == 'Stable Diffusion F64BA557': # Furry: V1.2/1.3 
				GS.main_app.model_button.text = 'nai-diffusion-furry'
			elif metadata["info"]["Source"] == 'Stable Diffusion 81274D13' or metadata["info"]["Source"] == 'Stable Diffusion 3B3287AF': # Anime Full V1: Initial release/silent update with ControlNet
				GS.main_app.model_button.text = 'nai-diffusion'
			elif metadata["info"]["Source"] == 'Stable Diffusion 1D44365E' or metadata["info"]["Source"] == 'Stable Diffusion F4D50568': # Anime Safe V1: Initial release/silent update with ControlNet
				GS.main_app.model_button.text = 'safe-diffusion'
			elif metadata["info"]["Source"] == 'Stable Diffusion F1022D28': # Anime Full V2
				GS.main_app.model_button.text = 'nai-diffusion-2'
			elif metadata["info"]["Source"] == 'Stable Diffusion XL C1E1DE52' or metadata["info"]["Source"] == 'Stable Diffusion XL 8BA2AF87': # Anime Full V3/Inpaint V3
				GS.main_app.model_button.text = 'nai-diffusion-3'
			elif metadata["info"]["Source"] == 'Stable Diffusion': # This should normally not be encountered but some images in the past were generated like this due to a bug on NAI's side
				print(f"[Warning] The loaded picture doesn't have the model specified. Defaulting to NAID Full V3, but be aware the original model for this picture might have been different")
				GS.main_app.model_button.text = 'nai-diffusion-3'
			else:
				print(f'[Warning] Error while determining model, defaulting to NAID Full V3')
				GS.main_app.model_button.text = 'nai-diffusion-3'
	GS.main_app.steps_f.enabled = False
	GS.main_app.guidance_f.enabled = False
	try_to_load('steps', GS.main_app.steps_slider_min, comment_dict, 'steps', GS.main_app.steps_import.enabled, 'value')
	try_to_load('scale', GS.main_app.guidance_input_min, comment_dict, 'scale', GS.main_app.guidance_import.enabled, 'text')
	try_to_load('guidance_rescale', GS.main_app.guidance_rescale_input_f, comment_dict, 'cfg_rescale', GS.main_app.guidance_import.enabled, 'text')
	print(comment_dict)
	if GS.main_app.resolution_import.enabled:
		GS.main_app.resolution_selector.resolution_width.text = str(metadata["size"][0])
		GS.main_app.resolution_selector.resolution_height.text = str(metadata["size"][1])
	try_to_load('seed', GS.main_app.is_seed_input, comment_dict, 'seed', GS.main_app.is_seed_import.enabled, 'text')

	if GS.main_app.is_sampler_import.enabled:
		try:
			sampler_string = str(comment_dict["sampler"])
		except:
			traceback.print_exc()
		if sampler_string == 'nai_smea_dyn':
			GS.main_app.is_sampler_button.text = 'k_euler_ancestral'
			GS.main_app.is_sampler_smea.enabled = True
			GS.main_app.is_sampler_dyn.enabled = True
		elif sampler_string == 'nai_smea':
			GS.main_app.is_sampler_button.text = 'k_euler_ancestral'
			GS.main_app.is_sampler_smea.enabled = True
			GS.main_app.is_sampler_dyn.enabled = False
		else:
			GS.main_app.is_sampler_button.text = sampler_string
			if comment_dict.get('sm_dyn'):
				if comment_dict["sm_dyn"]:
					GS.main_app.is_sampler_smea.enabled = True
					GS.main_app.is_sampler_dyn.enabled = True
			elif comment_dict.get('sm'):
				if comment_dict["sm"]:
					GS.main_app.is_sampler_smea.enabled = True
					GS.main_app.is_sampler_dyn.enabled = False
			else:
				GS.main_app.is_sampler_smea.enabled = False
				GS.main_app.is_sampler_dyn.enabled = False
	if GS.main_app.decrisp_import.enabled:
		try_to_load('dynamic_thresholding', GS.main_app.decrisp_button, comment_dict, 'dynamic_thresholding', True, 'enabled', False)
		try_to_load('dynamic_thresholding_mimic_scale', GS.main_app.decrisp_guidance_input, comment_dict, 'dynamic_thresholding_mimic_scale', True, 'text')
		try_to_load('dynamic_thresholding_percentile', GS.main_app.decrisp_percentile_input, comment_dict, 'dynamic_thresholding_percentile', True, 'text')
	if GS.main_app.prompt_import.enabled:
		GS.main_app.prompt_f.enabled = False
		if exif_metadata:
			try_to_load('prompt', GS.main_app.prompt_input, metadata,["info", "Description"], True, 'text')
		else:
			try_to_load('prompt', GS.main_app.prompt_input, comment_dict,'prompt', True, 'text')
	if GS.main_app.uc_import.enabled:
		GS.main_app.uc_f.enabled = False
		if comment_dict.get('uc'):
			GS.main_app.uc_input.text = comment_dict["uc"]
		else:
			try_to_load('negative_prompt', GS.main_app.uc_input, comment_dict,'negative_prompt', True, 'text')
	if try_to_load('negative_prompt_strength', GS.main_app.ucs_input, comment_dict, 'uncond_scale', GS.main_app.ucs_import.enabled, 'text', 100):
		GS.main_app.ucs_input.text = str(float(GS.main_app.ucs_input.text)*100)
	print(f'Loading from picture successful')
