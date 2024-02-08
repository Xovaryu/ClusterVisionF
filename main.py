"""
main.py
This is the main entry point of the program and contains mostly the code related to building the Kivy UI, which means an App class
As such the list here gives details on the functions in that App class
When the program is started via this file, first it runs initialization.py needed for the GlobalState and the exception handling
After that finished successfully the ClusterVisionF Kivy app is run (with a check for __main__) which starts the GUI

01.	update_preview
			Runs periodically to refresh the image preview (should be exchanged)
02.	on_steps_value_change_min/on_steps_value_change_max
			Functions that adjusts values for the steps sliders
03.	build
			The main build function called by Kivy to build the UI
04.	check_settings
			Small function that checks a built settings dict and makes sure that no critical settings are left empty
05.	generate_single_image
			Generates a settings dict and fills in variables with 0 and attempts to generate a single image
06.	on_queue_button_press
			Generates a settings dict for a full task and queues it
07.	on_process_button_press
			Locks the according parts of the UI and starts to process all tasks in order
08.	on_process_complete
			Wraps up a processing run
09.	switch_processing_state
			Used to switch the processing state and in turn which parts of the UI are locked
"""
import os
import sys
if sys.platform == 'win32' or sys.platform == 'cygwin':
	# Overwrite the ctypes clipboard for windows since it bugs out when trying to copy special symbols like 💠
	os.environ['KIVY_CLIPBOARD'] = 'sdl2'
	OS = 'Win'
	# This block is specifically needed to address Windows DPI issues
	import ctypes
	# Query DPI Awareness (Windows 10 and 8)
	awareness = ctypes.c_int()
	errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
	# Set DPI Awareness  (Windows 10 and 8)
	errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)
	# Set DPI Awareness  (Windows 7 and Vista)
	success = ctypes.windll.user32.SetProcessDPIAware()
elif sys.platform.startswith('linux'):
	OS = 'Linux'
elif sys.platform == 'darwin':
	OS = 'Mac'



from initialization import handle_exceptions, GlobalState
GS = GlobalState()
import image_generator as IM_G
import text_manipulation as TM
import file_loading as FL
import kivy_widgets as KW
from kivy_widgets import TextInput
from kivy_widgets import Button
from kivy_widgets import Label

from transformers import AutoTokenizer
class CLIPCostCalculator:
	def __init__(self, model_name_or_path="openai/clip-vit-base-patch32"):
		self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
	
	def calculate_token_cost(self, text):
		tokens = self.tokenizer.encode(text, add_special_tokens=True)
		return len(tokens)
clip_calculator = CLIPCostCalculator()

import math
import kivy
import time
import re
import traceback
import copy
import io
from PIL import Image as PILImage
import kivy
from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.image import Image as CoreImage
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.effects.dampedscroll import ScrollEffect
from kivy.graphics import Color, Rectangle, Line
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.image import Image, AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.config import Config
Config.set('input', 'mouse', 'mouse, disable_multitouch')
from kivy.metrics import Metrics
Metrics.density = 1

MAX_TOKEN_COUNT = 225 ###To be set in context later
PROMPT_CHUNKS = GS.NAI_PROMPT_CHUNKS + GS.USER_PROMPT_CHUNKS
UC_CHUNKS = GS.NAI_UCS + GS.USER_UCS
MODELS=GS.NAI_MODELS

### Configuration ###
field_height=30
font_hyper=20
font_large=19
font_small=15

l_row_size1={'size_hint':(None, None),'size':(120, field_height)}
l_row_size2={'size_hint':(None, 1),'size':(120, field_height)}
imp_row_size1={'size_hint':(None, None),'size':(field_height, field_height)}
imp_row_size2={'size_hint':(None, 1),'size':(field_height, field_height)}

# The main app
class ClusterVisionF(App):
	# Checks the attached list for newly generated image paths
	# No @handle_exceptions since it has its own exception handling
	def update_preview(self, time):
		try:
			new_image = GS.PREVIEW_QUEUE.pop()
			self.preview.load_image(new_image)
		except:
			pass

	# Functions needed for the steps slider
	@handle_exceptions
	def on_steps_value_change_min(self, instance, value):
		self.steps_counter_min.text = str(int(value))
	@handle_exceptions
	def on_steps_value_change_max(self, instance, value):
		self.steps_counter_max.text = str(int(value))

	# build() is the main function which creates the main window of the app
	# No @handle_exceptions for build() because it's part of the main thread, so crashes get reported, and this function is all or nothing for the GUI anyway
	def build(self):
		self.icon = 'ClusterVisionF.ico'
		# Binding the file dropping function
		Window.bind(on_drop_file=FL.on_file_drop)
		Window.size = (1000, 1000)
		Window.clearcolor = GS.THEME["ProgBg"]['value']
		self.config_window = KW.ConfigWindow(title='Configure Settings')
		self.file_handling_window = KW.FileHandlingWindow(title='File Handling (the f-strings here determine how the folder structure for created files look)')
		layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

		# Mode Switcher and config window buttons
		mode_label = Label(text='Mode:', **l_row_size1)
		settings_button = Button(text='⚙️', font_size=font_large, on_release=self.config_window.open, **imp_row_size1)
		settings_button.font_name = 'NotoEmoji'
		file_handling_button = Button(text='📁', font_size=font_large, on_release=self.file_handling_window.open, **imp_row_size1)
		file_handling_button.font_name = 'NotoEmoji'
		self.mode_switcher = KW.ModeSwitcher(app=self, size_hint=(1, None), size=(100, field_height))
		mode_switcher_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		#mode_switcher_layout.add_widget(file_handling_button)
		mode_switcher_layout.add_widget(self.mode_switcher)
	
		# Name
		name_label = Label(text='Name:', **l_row_size1)
		self.name_import = KW.ImportButton(**imp_row_size1)
		self.name_input = KW.ScrollInput(min_value=-100000, max_value=100000, fi_mode=None, increment=1, multiline=False, size_hint=(1, None), size=(100, field_height))

		# Folder Name
		folder_name_label = Label(text='Folder Name:', **l_row_size1)
		self.folder_name_import = KW.ImportButton(**imp_row_size1)
		self.folder_name_input = KW.ScrollInput(min_value=-100000, max_value=100000, fi_mode=None, increment=1, multiline=False, allow_empty=True, size_hint=(1, None), size=(100, field_height))

		# Model
		self.model_label = Label(text='Model:', **l_row_size1)
		self.model_import = KW.ImportButton(**imp_row_size1)
		
		self.model_dropdown = DropDown()
		self.model_button = KW.ScrollDropDownButton(self.model_dropdown, text='nai-diffusion-3', size_hint=(1, None), size=(100, field_height))

		for model_name in MODELS.values():
			btn = KW.DropDownButton(text=model_name, size_hint_y=None, height=field_height)
			btn.bind(on_release=handle_exceptions(lambda btn: self.model_dropdown.select(btn.text)))
			self.model_dropdown.add_widget(btn)
		self.model_dropdown.bind(on_select=handle_exceptions(lambda instance, x: setattr(self.model_button, 'text', x)))

		# Seed - Cluster Collage
		cc_seed_label = Label(text='Seed:', **l_row_size2)
		self.cc_seed_import = KW.ImportButton(**imp_row_size2)
		self.cc_seed_grid=KW.SeedGrid(size_hint=(1, 1))

		# Seed - Image Sequence
		is_seed_label = Label(text='Seed:', **l_row_size1)
		self.is_seed_import = KW.ImportButton(**imp_row_size1)
		is_seed_randomize = Button(text='Randomize', size_hint=(None, None), size=(100, field_height))
		is_seed_clear = Button(text='Clear', size_hint=(None, None), size=(60, field_height))
		self.is_seed_input = KW.SeedScrollInput(min_value=0, max_value=4294967295, increment=1000, text='', multiline=False, size_hint=(1, None), size=(100, field_height), allow_empty=True)
		is_seed_randomize.bind(on_release=handle_exceptions(lambda btn: setattr(self.is_seed_input, 'text', str(IM_G.generate_seed()))))
		is_seed_clear.bind(on_release=handle_exceptions(lambda btn: setattr(self.is_seed_input, 'text', '')))
		is_seed_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		is_seed_layout.add_widget(is_seed_randomize)
		is_seed_layout.add_widget(is_seed_clear)
		is_seed_layout.add_widget(self.is_seed_input)

		# Steps
		steps_label = Label(text='Steps:', **l_row_size1)
		self.steps_import = KW.ImportButton(**imp_row_size1)
		steps_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		self.steps_slider_min = Slider(min=1, max=100, value=28, step=1)
		self.steps_counter_min = Label(text=str(28), size_hint=(None, None), size=(50, field_height))
		self.steps_slider_max = Slider(min=1, max=100, value=28, step=1)
		self.steps_counter_max = Label(text=str(28), size_hint=(None, None), size=(50, field_height))
		self.steps_slider_min.bind(value=self.on_steps_value_change_min)
		self.steps_slider_max.bind(value=self.on_steps_value_change_max)
		steps_layout.add_widget(self.steps_slider_min)
		steps_layout.add_widget(self.steps_counter_min)
		steps_layout.add_widget(self.steps_slider_max)
		steps_layout.add_widget(self.steps_counter_max)
		# Create the f-string variant
		self.steps_input_f = KW.FScrollInput(min_value=1, max_value=50, fi_mode=None, increment=1, text='⁅(c+1)⁆', multiline=False, size_hint=(1, None), size=(100, field_height), font_size=font_small,font_name='Unifont')
		self.steps_f = KW.StateFButton(self.mode_switcher, steps_layout, self.steps_input_f, None, [steps_layout], [self.steps_input_f], size_hint=(None, None), size=(field_height, field_height))
		steps_super_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		steps_super_layout.add_widget(self.steps_f)
		steps_super_layout.add_widget(steps_layout)
		steps_super_layout.add_widget(self.steps_input_f)

		# Guidance
		guidance_label = Label(text='Guidance:', **l_row_size1)
		self.guidance_import = KW.ImportButton(**imp_row_size1)
		guidance_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		#The API actually accepts much, much higher guidance values, though there really seems no point in going higher than 100 at all
		self.guidance_input_min = KW.ScrollInput(min_value=1.1, max_value=1000, fi_mode=float, increment=0.1, text='10', multiline=False, size_hint=(1, None), size=(100, field_height), font_size=font_small)
		self.guidance_input_max = KW.ScrollInput(min_value=1.1, max_value=1000, fi_mode=float, increment=0.1, text='10', multiline=False, size_hint=(1, None), size=(100, field_height), font_size=font_small)
		guidance_layout.add_widget(self.guidance_input_min)
		guidance_layout.add_widget(self.guidance_input_max)
		# Create the f-string variant
		self.guidance_input_f = KW.FScrollInput(min_value=1.1, max_value=1000, fi_mode=None, increment=0.1, text='5', multiline=False, size_hint=(1, None), size=(100, field_height), font_size=font_small,font_name='Unifont')
		guidance_rescale_label = Label(text='G. Rescale:', **l_row_size1)
		self.guidance_rescale_input_f = KW.FScrollInput(min_value=0, max_value=1000, fi_mode=None, increment=0.1, text='0', multiline=False, size_hint=(1, None), size=(100, field_height), font_size=font_small,font_name='Unifont')
		guidance_layout_f = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		
		guidance_layout_f.add_widget(self.guidance_input_f)
		guidance_layout_f.add_widget(guidance_rescale_label)
		guidance_layout_f.add_widget(self.guidance_rescale_input_f)
		self.guidance_f = KW.StateFButton(self.mode_switcher, guidance_layout, guidance_layout_f, None, [guidance_layout], [self.guidance_input_f], size_hint=(None, None), size=(field_height, field_height))
		
		guidance_super_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		guidance_super_layout.add_widget(self.guidance_f)
		guidance_super_layout.add_widget(guidance_layout)
		guidance_super_layout.add_widget(guidance_layout_f)
		

		# Sampler - Cluster Collage
		cc_sampler_label = Label(text='Sampler:', **l_row_size1)	
		self.cc_sampler_import = KW.ImportButton(size_hint = (None, None), size = (field_height, field_height*2))
		self.cc_sampler_input = TextInput(multiline=True, size_hint=(1, 1), height=field_height*2)
		cc_clear_button = Button(text='Clear', size_hint=(None, 1), size=(60, field_height*2))
		cc_clear_button.bind(on_release=handle_exceptions(lambda button: setattr(self.cc_sampler_input, 'text', '')))
		cc_sampler_button = Button(text='Add Sampler', size_hint=(None, 1), size=(150, field_height*2))

		cc_sampler_injector = KW.ConditionalInjectorDropDown(size_hint=(None, 1), width=field_height, dropdown_list=GS.NAI_SAMPLERS, button_text='+', target=self.cc_sampler_input, inject_identifier='S')
		cc_sampler_dropdown = DropDown()

		cc_sampler_layout = BoxLayout(orientation='horizontal',size_hint=(1, None), height=field_height*2)
		cc_sampler_layout.add_widget(self.cc_sampler_input)
		cc_sampler_layout.add_widget(cc_clear_button)
		cc_sampler_layout.add_widget(cc_sampler_injector)

		# Sampler - Image Sequence
		is_sampler_label = Label(text='Sampler:', **l_row_size1)		
		self.is_sampler_import = KW.ImportButton(**imp_row_size1)
		is_sampler_dropdown = DropDown()
		self.is_sampler_button = KW.ScrollDropDownButton(is_sampler_dropdown, text='k_dpmpp_2m', size_hint=(1, None), size=(100, field_height))
		for sampler_name in GS.NAI_SAMPLERS_RAW:
			btn = KW.DropDownButton(text=sampler_name, size_hint_y=None, height=field_height)
			btn.bind(on_release=handle_exceptions(lambda btn: is_sampler_dropdown.select(btn.text)))
			is_sampler_dropdown.add_widget(btn)
		is_sampler_dropdown.bind(on_select=handle_exceptions(lambda instance, x: setattr(self.is_sampler_button, 'text', x)))
		
		is_sampler_layout = BoxLayout(orientation='horizontal',size_hint=(1, None), height=field_height)
		self.is_sampler_smea = KW.StateShiftButton(text='SMEA', size_hint=(None, 1), size=(80,field_height))
		self.is_sampler_dyn = KW.StateShiftButton(text='Dyn', size_hint=(None, 1), size=(80,field_height))

		self.is_sampler_smea.bind(enabled=handle_exceptions(lambda instance, value: KW.on_smea_disabled(value, self.is_sampler_dyn)))
		self.is_sampler_dyn.bind(enabled=handle_exceptions(lambda instance, value: KW.on_dyn_enabled(value, self.is_sampler_smea)))
		is_sampler_layout.add_widget(self.is_sampler_button)
		is_sampler_layout.add_widget(self.is_sampler_smea)
		is_sampler_layout.add_widget(self.is_sampler_dyn)

		# Decrisper
		decrisp_label = Label(text='Decrisper:', **l_row_size1)
		self.decrisp_import = KW.ImportButton(**imp_row_size1)
		self.decrisp_button = KW.StateShiftButton(text='Decrisper', size_hint=(None, None), size=(90,field_height))
		decrisp_scale = Label(text='Mimic Scale:', size_hint=(None, None), size=(100, field_height))
		self.decrisp_guidance_input = KW.FScrollInput(min_value=-10000, max_value=10000, fi_mode=None, increment=0.1, text='10', multiline=False, size_hint=(1, None), size=(100, field_height), font_size=font_small,font_name='Unifont')
		decrisp_percentile = Label(text='Percentile:', size_hint=(None, None), size=(90, field_height))
		self.decrisp_percentile_input = KW.FScrollInput(min_value=0.000001, max_value=1, fi_mode=None, increment=0.001, text='0.999', multiline=False, size_hint=(1, None), size=(100, field_height), round_value=6, font_size=font_small,font_name='Unifont')
		decrisp_layout = BoxLayout(orientation='horizontal',size_hint=(1, None), height=field_height)
		decrisp_layout.add_widget(self.decrisp_button)
		decrisp_layout.add_widget(decrisp_scale)
		decrisp_layout.add_widget(self.decrisp_guidance_input)
		decrisp_layout.add_widget(decrisp_percentile)
		decrisp_layout.add_widget(self.decrisp_percentile_input)
		
		# Resolution
		resolution_label = Label(text='Resolution:', **l_row_size1)
		self.resolution_import = KW.ImportButton(**imp_row_size1)
		self.resolution_selector = KW.ResolutionSelector()

		# Prompt
		prompt_label = Label(text='Prompt:', **l_row_size2)
		prompt_buttons_layout = BoxLayout(orientation='vertical', **imp_row_size2)
		self.prompt_import = KW.ImportButton()
		self.prompt_input = TextInput(multiline=True, size_hint=(1, 1), size=(100, field_height*4))
		self.prompt_input.font_size = 23
		self.prompt_input.font_name = 'Unifont'
		prompt_injector = KW.InjectorDropDown(dropdown_list=PROMPT_CHUNKS, button_text='+', target=self.prompt_input)
		
		prompt_buttons_layout.add_widget(prompt_injector)
		prompt_buttons_layout.add_widget(self.prompt_import)
		
		prompt_layout = BoxLayout(orientation='horizontal')
		prompt_token_counter=KW.TokenCostBar(clip_calculator, MAX_TOKEN_COUNT, size_hint=(None, 1), width=20)
		prompt_layout.add_widget(self.prompt_input)
		prompt_layout.add_widget(prompt_token_counter)
		self.prompt_input.bind(text=prompt_token_counter.calculate_token_cost)
		# Create the f-string variant
		self.prompt_f_input = KW.PromptGrid(size_hint=(1, 1), size=(100, field_height*4))
		prompt_layout.add_widget(self.prompt_f_input)
		self.prompt_f = KW.StateFButton(self.mode_switcher, self.prompt_input, self.prompt_f_input.prompt_inputs[0], prompt_injector, prompt_layout.children[1:], [prompt_layout.children[0]], enabled=False)
		prompt_buttons_layout.add_widget(self.prompt_f)

		# UC
		uc_label = Label(text='Neg. Prompt:', **l_row_size2)
		uc_buttons_layout = BoxLayout(orientation='vertical', **imp_row_size2)
		self.uc_import = KW.ImportButton()
		self.uc_input = TextInput(multiline=True, size_hint=(1, 1), size=(100, field_height*4))
		self.uc_input.font_size = 23
		self.uc_input.font_name = 'Unifont'
		uc_injector = KW.InjectorDropDown(dropdown_list=UC_CHUNKS, button_text='+', target=self.uc_input, inject_identifier='UC')
		
		uc_buttons_layout.add_widget(uc_injector)
		uc_buttons_layout.add_widget(self.uc_import)
		
		uc_layout = BoxLayout(orientation='horizontal')
		uc_token_counter=KW.TokenCostBar(clip_calculator, MAX_TOKEN_COUNT, size_hint=(None, 1), width=20)
		uc_layout.add_widget(self.uc_input)
		uc_layout.add_widget(uc_token_counter)
		self.uc_input.bind(text=uc_token_counter.calculate_token_cost)
		# Create the f-string variant
		self.uc_f_input = KW.PromptGrid(size_hint=(1, 1), size=(100, field_height*4))
		uc_layout.add_widget(self.uc_f_input)
		self.uc_f = KW.StateFButton(self.mode_switcher, self.uc_input, self.uc_f_input.prompt_inputs[0], uc_injector, uc_layout.children[1:], [uc_layout.children[0]], enabled=False)
		uc_buttons_layout.add_widget(self.uc_f)

		# UC Content Strength
		ucs_label = Label(text='NP Strength:', **l_row_size1)
		self.ucs_import = KW.ImportButton(**imp_row_size1)
		ucs_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)

		ucs_slider = Slider(min=0, max=500, value=100, size_hint=(1, None), height=field_height)
		self.ucs_input = KW.FScrollInput(min_value=0, max_value=1000, fi_mode=None, text='100', size_hint=(None, None), width=200, height=field_height, font_name='Unifont')
		ucs_percent_label = Label(text='%', size_hint=(None, None), width=40, height=field_height)
		ucs_slider.bind(value=handle_exceptions(lambda instance, value: setattr(self.ucs_input, 'text', str(value))))

		ucs_layout.add_widget(ucs_slider)
		ucs_layout.add_widget(self.ucs_input)
		ucs_layout.add_widget(ucs_percent_label)

		# Collage Dimensions
		cc_dim_label = Label(text='Collage Dim.:', **l_row_size1)
		self.cc_dim_import = KW.ImportButton(**imp_row_size1)
		cc_dim_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		cc_dim_width_label = Label(text='Columns:', size_hint=(None, None), width=80, height=field_height)
		self.cc_dim_width = KW.ScrollInput(text='3', size_hint=(1, None), width=60, height=field_height)
		cc_dim_height_label = Label(text='Rows:', size_hint=(None, None), width=80, height=field_height)
		self.cc_dim_height = KW.ScrollInput(text='3', size_hint=(1, None), width=60, height=field_height)
		cc_dim_layout.add_widget(cc_dim_width_label)
		cc_dim_layout.add_widget(self.cc_dim_width)
		cc_dim_layout.add_widget(cc_dim_height_label)
		cc_dim_layout.add_widget(self.cc_dim_height)

		# Image Sequence Quantity
		is_range_label = Label(text='Quantity/FPS:', **l_row_size1)
		self.is_range_import = KW.ImportButton(**imp_row_size1)
		is_range_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.is_quantity = KW.ScrollInput(text='28', min_value=1, max_value=100000, size_hint=(1, None), width=60, height=field_height)
		self.is_video = KW.StateShiftButton(text='🎬',font_name='NotoEmoji')
		is_range_layout.add_widget(self.is_quantity)
		is_range_layout.add_widget(self.is_video)
		is_fps_label = Label(text='FPS:', size_hint=(None, None), size=(60,field_height))
		self.is_fps = KW.ScrollInput(text=str(GS.BASE_FPS), min_value=1, max_value=144, size_hint=(1, None), width=60, height=field_height)
		is_range_layout.add_widget(is_fps_label)
		is_range_layout.add_widget(self.is_fps)

		# Action buttons
		action_buttons_label = Label(text='Create images:', **l_row_size1)
		action_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.single_img_button = Button(text='Generate Image', size_hint=(1, None), height=field_height)
		self.single_img_button.bind(on_release=self.generate_single_image)
		self.queue_button = Button(text='Queue Task', size_hint=(1, None), height=field_height)
		self.queue_button.bind(on_release=self.on_queue_button_press)
		self.process_button = Button(text='Process Tasks', size_hint=(1, None), height=field_height)
		self.process_button.bind(on_release=self.on_process_button_press)
		action_buttons_layout.add_widget(self.single_img_button)
		action_buttons_layout.add_widget(self.queue_button)
		action_buttons_layout.add_widget(self.process_button)

		# Add all elements to input_layout, which is the primary block for interactions on the left, split into the label/button/input columns

		input_layout = GridLayout(cols=3)
		input_layout.add_widget(mode_label)
		input_layout.add_widget(settings_button)
		input_layout.add_widget(mode_switcher_layout)

		input_layout.add_widget(name_label)
		input_layout.add_widget(self.name_import)
		input_layout.add_widget(self.name_input)

		input_layout.add_widget(folder_name_label)
		input_layout.add_widget(self.folder_name_import)
		input_layout.add_widget(self.folder_name_input)

		input_layout.add_widget(self.model_label)
		input_layout.add_widget(self.model_import)
		input_layout.add_widget(self.model_button)

		input_layout.add_widget(cc_seed_label)
		input_layout.add_widget(self.cc_seed_import)
		input_layout.add_widget(self.cc_seed_grid)

		input_layout.add_widget(is_seed_label)
		input_layout.add_widget(self.is_seed_import)
		input_layout.add_widget(is_seed_layout)		

		input_layout.add_widget(steps_label)
		input_layout.add_widget(self.steps_import)
		input_layout.add_widget(steps_super_layout)	

		input_layout.add_widget(guidance_label)
		input_layout.add_widget(self.guidance_import)
		input_layout.add_widget(guidance_super_layout)

		input_layout.add_widget(cc_sampler_label)
		input_layout.add_widget(self.cc_sampler_import)
		input_layout.add_widget(cc_sampler_layout)

		input_layout.add_widget(is_sampler_label)
		input_layout.add_widget(self.is_sampler_import)
		input_layout.add_widget(is_sampler_layout)		

		input_layout.add_widget(decrisp_label)
		input_layout.add_widget(self.decrisp_import)
		input_layout.add_widget(decrisp_layout)

		input_layout.add_widget(resolution_label)
		input_layout.add_widget(self.resolution_import)
		input_layout.add_widget(self.resolution_selector)

		input_layout.add_widget(prompt_label)
		input_layout.add_widget(prompt_buttons_layout)
		input_layout.add_widget(prompt_layout)

		input_layout.add_widget(uc_label)
		input_layout.add_widget(uc_buttons_layout)
		input_layout.add_widget(uc_layout)

		input_layout.add_widget(ucs_label)
		input_layout.add_widget(self.ucs_import)
		input_layout.add_widget(ucs_layout)

		input_layout.add_widget(cc_dim_label)
		input_layout.add_widget(self.cc_dim_import)
		input_layout.add_widget(cc_dim_layout)

		input_layout.add_widget(is_range_label)
		input_layout.add_widget(self.is_range_import)
		input_layout.add_widget(is_range_layout)

		input_layout.add_widget(action_buttons_label)
		input_layout.add_widget(Label(text='',size_hint=(None, None),size=(0,0)))
		input_layout.add_widget(action_buttons_layout)

		# In the middle is the meta_layout with the console and a some more relevant buttons
		task_state_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.cancel_button = Button(text='⬛', font_name='Unifont',size_hint=(None, None), size=(field_height,field_height))
		self.cancel_button.bind(on_release=handle_exceptions(lambda instance: setattr(GS, 'PAUSE_REQUEST', False)))
		self.cancel_button.bind(on_release=handle_exceptions(lambda instance: setattr(GS, 'CANCEL_REQUEST', True)))

		self.pause_button = KW.PauseButton(**imp_row_size1)
		self.pause_button.bind(on_release=handle_exceptions(lambda instance: setattr(GS, 'PAUSE_REQUEST', not GS.PAUSE_REQUEST)))
		overwrite_button = KW.StateShiftButton(text='Overwrite Images', size_hint=(1, None), size=(70,field_height), font_size=font_small)
		overwrite_button.bind(on_release=handle_exceptions(lambda instance: setattr(GS, 'OVERWRITE_IMAGES', not GS.OVERWRITE_IMAGES)))
		self.wipe_queue_button = Button(text='Wipe Queue', size_hint=(1, None), size=(60,field_height))
		self.wipe_queue_button.bind(on_release=IM_G.wipe_queue)
		task_state_layout.add_widget(self.pause_button)
		task_state_layout.add_widget(self.cancel_button)
		task_state_layout.add_widget(overwrite_button)
		task_state_layout.add_widget(self.wipe_queue_button)

		meta_layout = BoxLayout(orientation='vertical', size_hint=(0.5, 1))
		meta_layout.add_widget(KW.Console())
		meta_layout.add_widget(task_state_layout)

		# The KW.ImagePreview goes currently alone on the right
		self.preview = KW.ImagePreview()

		# The super_layout is highest layout in the hierarchy and is also the one that is returned for Kivy to display
		# It has the user interaction section left, the console/metadata section in the middle, and the image preview on the right		
		self.super_layout = BoxLayout(orientation='horizontal')
		self.super_layout.add_widget(input_layout)
		self.super_layout.add_widget(meta_layout)
		self.super_layout.add_widget(self.preview)

		self.cc_exclusive_widgets = [cc_seed_label, self.cc_seed_import, self.cc_seed_grid,
			cc_sampler_label, self.cc_sampler_import, cc_sampler_layout,
			cc_dim_label, self.cc_dim_import, cc_dim_layout]
		self.is_exclusive_widgets = [is_sampler_label, self.is_sampler_import, is_sampler_layout,
			is_seed_label, self.is_seed_import, is_seed_layout,
			is_range_label, self.is_range_import, is_range_layout]
		self.non_cs_widgets = [is_sampler_label, self.is_sampler_import, is_sampler_layout, is_seed_label, self.is_seed_import, is_seed_layout]
		self.import_buttons = [self.name_import, self.folder_name_import, self.model_import, self.cc_seed_import, self.is_seed_import,
			self.steps_import, self.guidance_import, self.cc_sampler_import, self.is_sampler_import, self.resolution_import, self.prompt_import, self.uc_import,
			self.cc_dim_import, self.is_range_import]

		self.mode_switcher.hide_widgets(self.is_exclusive_widgets)
		Clock.schedule_interval(self.update_preview, 0.2)
		self.pause_button.disabled = True
		self.cancel_button.disabled = True

		return self.super_layout

	# This function checks the validity of passed settings
	@handle_exceptions
	def check_settings(self, instance, settings):
		empty_field = False
		if settings['name'] == '':
			print("Name field can't be empty!")
			empty_field = True
		if settings['sampler'] == '':
			print("Sampler field can't be empty!")
			empty_field = True
		if settings['prompt'] == '':
			print("Prompt field can't be empty!")
			empty_field = True
		if empty_field: print('\n')
		return empty_field

	# This function generates a single image like any other UI would do, just that it has to be aware of which fields are active and which to use
	@handle_exceptions
	def generate_single_image(self, instance):
		GS.CANCEL_REQUEST = False
		blank_eval_dict = {'n':0,'c':0,'r':0,'cc':0,'s':0}
		if self.mode_switcher.cc_active:
			if not self.cc_seed_grid.seed_inputs[0].text == '':
				seed = self.cc_seed_grid.seed_inputs[0].text
			else:
				seed = str(IM_G.generate_seed())
			if self.cc_sampler_input.text.__contains__(','):
				sampler = self.cc_sampler_input.text.split(", ")[0]
			else:
				sampler = self.cc_sampler_input.text
		else:
			if not self.is_seed_input.text == '':
				seed = self.is_seed_input.text
			else:
				seed = str(IM_G.generate_seed())
			sampler = self.is_sampler_button.text
			if self.is_sampler_dyn.enabled:
				sampler+='_dyn'
			elif self.is_sampler_smea.enabled:
					sampler+='_smea'
		settings = {'name': self.name_input.text,
		'folder_name': self.folder_name_input.text,
		'folder_name_extra': '',
		'model': self.model_button.text,
		'seed': int(seed),
		'sampler': sampler,
		'scale': float(TM.f_string_processor([['f"""'+self.guidance_input_f.text+'"""']],self.config_window.eval_guard_button.enabled,blank_eval_dict)) if self.guidance_f.enabled else
		float(self.guidance_input_min.text),
		'guidance_rescale': float(TM.f_string_processor([['f"""'+self.guidance_rescale_input_f.text+'"""']],self.config_window.eval_guard_button.enabled,blank_eval_dict)),
		'steps': int(TM.f_string_processor([['f"""'+self.steps_input_f.text+'"""']],self.config_window.eval_guard_button.enabled,blank_eval_dict)) if self.steps_f.enabled else
		int(self.steps_slider_min.value),
		'img_mode': {'width': int(self.resolution_selector.resolution_width.text),
								'height': int(self.resolution_selector.resolution_height.text)},
		'prompt': TM.f_string_processor([['f"""' + self.prompt_f_input.prompt_inputs[i].text + '"""'] for i in range(self.prompt_f_input.prompt_rows)],self.config_window.eval_guard_button.enabled,blank_eval_dict) if self.prompt_f.enabled else
		self.prompt_input.text,
		'negative_prompt': TM.f_string_processor([['f"""' + self.uc_f_input.prompt_inputs[i].text + '"""'] for i in range(self.uc_f_input.prompt_rows)],self.config_window.eval_guard_button.enabled,blank_eval_dict)if self.uc_f.enabled else
		self.uc_input.text,
		'negative_prompt_strength': self.ucs_input.text,
		'dynamic_thresholding': self.decrisp_button.enabled,
		'dynamic_thresholding_mimic_scale': float(TM.f_string_processor([['f"""'+self.decrisp_guidance_input.text+'"""']],self.config_window.eval_guard_button.enabled,blank_eval_dict)) if self.decrisp_button.enabled else 10,
		'dynamic_thresholding_percentile': float(TM.f_string_processor([['f"""'+self.decrisp_percentile_input.text+'"""']],self.config_window.eval_guard_button.enabled,blank_eval_dict)) if self.decrisp_button.enabled else 0.999,}
		if self.check_settings(None, settings):
			return
		print(settings)
		self.single_img_button.disabled = True
		#self.queue_button.disabled = True
		self.process_button.disabled = True
		self.cancel_button.disabled = False
		self.wipe_queue_button.disabled = True
		future = GS.EXECUTOR.submit(IM_G.generate_as_is,settings,'')
		future.add_done_callback(self.on_process_complete)

	# This function is responsible for taking all of the settings in the UI and queueing the desired task
	@handle_exceptions
	def on_queue_button_press(self, instance):
		# Get shared settings from text inputs and sliders
		name = self.name_input.text
		folder_name = self.folder_name_input.text
		model = self.model_button.text
		if self.steps_f.enabled:
			steps = self.steps_input_f.text
		else:
			steps = [int(self.steps_slider_min.value),(self.steps_slider_max.value)]
			if steps[0] == steps[1]:
				steps=steps[0]
		guidance_rescale = self.guidance_rescale_input_f.text
		if self.guidance_f.enabled:
			scale = self.guidance_input_f.text
		else:
			scale = [float(self.guidance_input_min.text), float(self.guidance_input_max.text)]
			if scale[0] == scale[1]:
				scale=scale[0]
		img_mode = {'width': int(self.resolution_selector.resolution_width.text),
								'height': int(self.resolution_selector.resolution_height.text)}
		if self.prompt_f.enabled:
			prompt = [['f"""' + self.prompt_f_input.prompt_inputs[i].text + '"""'] for i in range(self.prompt_f_input.prompt_rows)]
		else:
			prompt = self.prompt_input.text
		if self.uc_f.enabled:
			uc = [['f"""' + self.uc_f_input.prompt_inputs[i].text + '"""'] for i in range(self.uc_f_input.prompt_rows)]
		else:
			uc = self.uc_input.text
		settings = {'name': name, 'folder_name': folder_name, 'model': model, 'scale': scale, 'guidance_rescale': guidance_rescale, 'steps': steps, 'img_mode': img_mode,
		'prompt': prompt, 'negative_prompt': uc, 'dynamic_thresholding': self.decrisp_button.enabled, 'negative_prompt_strength': self.ucs_input.text,
		'dynamic_thresholding_mimic_scale': self.decrisp_guidance_input.text if self.decrisp_button.enabled else 10,
		'dynamic_thresholding_percentile': self.decrisp_percentile_input.text if self.decrisp_button.enabled else 0.999,}

		if self.mode_switcher.cc_active or self.mode_switcher.cs_active: # Cluster collage specific settings
			seeds = [[self.cc_seed_grid.seed_inputs[j+i*int(self.cc_seed_grid.seed_cols_input.text)].text for j in range(int(self.cc_seed_grid.seed_cols_input.text))] for i in range(int(self.cc_seed_grid.seed_rows_input.text))]
			seed = [[str(IM_G.generate_seed()) if value == '' else value for value in inner_list] for inner_list in seeds]
			if self.cc_sampler_input.text.__contains__(','):
				sampler = [list(filter(None, self.cc_sampler_input.text.split(", "))),'']
			else:
				sampler = self.cc_sampler_input.text
			collage_dimensions = [int(self.cc_dim_width.text), int(self.cc_dim_height.text)]
			settings.update({'seed': seed, 'sampler': sampler, 'collage_dimensions': collage_dimensions})
			if self.mode_switcher.cs_active:
				settings.update({'quantity': int(self.is_quantity.text), 'video': 'standard' if self.is_video.enabled else '', 'FPS': int(self.is_fps.text)})
			IM_G.cluster_collage(settings,self.config_window.eval_guard_button.enabled) if self.mode_switcher.cc_active else IM_G.cluster_sequence(settings,self.config_window.eval_guard_button.enabled)
		else: # Image sequence specific settings
			if not self.is_seed_input.text == '':
				seed = self.is_seed_input.text
			else:
				seed = str(IM_G.generate_seed())
			sampler = self.is_sampler_button.text
			if self.is_sampler_dyn.enabled:
				sampler+='_dyn'
			elif self.is_sampler_smea.enabled:
				sampler+='_smea'
			settings.update({'seed': int(seed), 'sampler': sampler, 'quantity': int(self.is_quantity.text), 'video': 'standard' if self.is_video.enabled else '', 'FPS': int(self.is_fps.text)})
			if self.check_settings(None, settings):
				return
			IM_G.image_sequence(settings,self.config_window.eval_guard_button.enabled)
		print(settings)

	# This function locks part of the UI and then processes the queued tasks one after the other in a separate thread
	# No @handle_exceptions due to custom treatment of exceptions in the function
	def on_process_button_press(self, instance):	
		try:
			self.switch_processing_state(True)
			future = GS.EXECUTOR.submit(IM_G.process_queue)
			future.add_done_callback(self.on_process_complete)
		except:
			traceback.print_exc()
			self.on_process_complete(None,immediate_preview=False)
			GS.PREVIEW_QUEUE= []
			print('Task queue has been wiped due to an exception')

	# Ends a processing run
	@handle_exceptions
	def on_process_complete(self, future, immediate_preview = True):
		self.switch_processing_state(False)

	# Locks/unlocks elements according to the current processing state
	@handle_exceptions
	def switch_processing_state(self, processing):
		self.single_img_button.disabled = processing
		#self.queue_button.disabled = processing
		self.process_button.disabled = processing 
		self.wipe_queue_button.disabled = processing
		self.cancel_button.disabled = not processing
		self.pause_button.disabled = not processing

if __name__ == '__main__':
	GS.main_app = ClusterVisionF()
	GS.main_app.run()
