"""
main.py
This is the main entry point of the program and contains mostly the code related to building the Kivy UI, which means an App class
As such the list here gives details on the functions in that App class
When the program is started via this file, first it runs initialization.py needed for the GlobalState and the exception handling
After that finished successfully the ClusterVisionF Kivy app is run (with a check for __main__) which starts the GUI

01.	on_steps_value_change_min + on_steps_value_change_max + format_sampler_text
			Functions that adjusts values for the steps sliders, and keep sampler text formatted neatly
02.	build
			The main build function called by Kivy to build the UI
03.	check_settings
			Small function that checks a built settings dict and makes sure that no critical settings are left empty
04.	generate_single_image
			Generates a settings dict and fills in variables with 0 and attempts to generate a single image
05.	on_queue_button_press
			Generates a settings dict for a full task and queues it
06.	get_image_entries
			This function processes all loaded image intries into a functional dict to be used when processing the task independent of later states of the loaded images
07.	get_sampler_setting
			Processes the current state of sampler UI elements into a workable string or list
08.	on_process_button_press
			Locks the according parts of the UI and starts to process all tasks in order
09.	on_process_complete
			Wraps up a processing run
10.	switch_processing_state
			Used to switch the processing state and in turn which parts of the UI are locked
"""
import sys
if sys.platform == 'win32' or sys.platform == 'cygwin':
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


import logging
logging.getLogger('PIL').setLevel(logging.WARNING) # If we don't do this then PIL will by default drop debug messages, polluting the python console (not CVF's console but still)
from initialization import handle_exceptions, GlobalState
GS = GlobalState()
import image_generator as IM_G
import text_manipulation as TM
import file_loading as FL
import kivy_widgets as KW
from kivy_widgets import TextInput
from kivy_widgets import Button
from kivy_widgets import Label


import math
import kivy
import time
import re
import traceback
import copy
import os
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

### Configuration ###
font_hyper=20
font_large=19
font_small=15

class ClusterVisionF(App):
	# 01. Function needed for the steps slider
	@handle_exceptions
	def format_sampler_text(self, current_text):
		current_text = current_text.rstrip()
		if current_text and not current_text.endswith(','):
			if current_text[-1].isalnum():
				current_text += ','
		if current_text:
			current_text += ' '
		return current_text + self.get_sampler_setting(comma_check=False) + ', '

	# 02. build() is the main function which creates the main window of the app
	@handle_exceptions
	def build(self):
		self.icon = 'ClusterVisionF.ico'
		Window.exit_on_escape = False
		# Binding the file dropping function
		Window.dropped_files = []
		Window.bind(on_drop_file=FL.on_drop_file)
		Window.bind(on_drop_end=FL.on_drop_end)
		
		# These are the main 3 layouts containing the primary inputs on the left, console and additional inputs, as well as image handling on the right
		self.top_input_layout = BoxLayout(orientation='vertical')
		self.meta_layout = BoxLayout(orientation='vertical', size_hint=(0.5, 1))
		self.image_organization_layout = BoxLayout(orientation='vertical')
		
		self.input_scrollview = KW.PermissiveScrollView(effect_cls=ScrollEffect)
		self.input_layout = KW.FlexibleBoxLayout(orientation='vertical', size_hint_y=None)
		#self.input_layout.bind(minimum_height=self.input_layout.setter('height'))
		self.input_scrollview.add_widget(self.input_layout)
		Window.clearcolor = GS.theme["ProgBg"]['value']
		self.config_window = KW.ConfigWindow(title=f'Configure Settings (Version: {GS.VERSION})')
		self.theme_window = KW.ThemeWindow(title='Configure Theme')
		self.file_handling_window = KW.FileHandlingWindow(title='File Handling (the f-strings here determine how the folder structure for created files look)')
		self.drop_overlay = KW.DropOverlay() # This overlay uses the size_hints of the main layouts, so they need to be initialized first

		# Mode Switcher and config window buttons
		mode_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		mode_label = Label(text='Mode:', **GS.l_row_size)
		settings_button = Button(text='⚙️', font_size=font_large, font_name = 'NotoEmoji', on_release=self.config_window.open, **GS.imp_row_size, tooltip_types=['Settings'])
		theme_button = Button(text='🎨', font_size=font_large, font_name = 'NotoEmoji', on_release=self.theme_window.open, **GS.imp_row_size, tooltip_types=['Themes'])
		file_handling_button = Button(text='📁', font_size=font_large, font_name = 'NotoEmoji', on_release=self.file_handling_window.open, **GS.imp_row_size)
		drop_overlay_button = Button(text='Help', font_size=font_large, size_hint = (None, None), on_release=self.drop_overlay.open, size = (65, GS.UI_field_height))
		self.mode_switcher = KW.ModeSwitcher(app=self, size_hint=(1, None), size=(100, GS.UI_field_height))
		mode_switcher_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, GS.UI_field_height))
		mode_switcher_layout.add_widget(theme_button)
		#mode_switcher_layout.add_widget(file_handling_button)
		mode_switcher_layout.add_widget(drop_overlay_button)
		mode_switcher_layout.add_widget(self.mode_switcher)
		
		mode_row.add_widget(mode_label)
		mode_row.add_widget(settings_button)
		mode_row.add_widget(mode_switcher_layout)
		self.top_input_layout.add_widget(mode_row)
		self.top_input_layout.add_widget(self.input_scrollview)
		
		# Generation Providers
		generation_provider_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		generation_provider_label = Label(text='Gen. Provider:', **GS.l_row_size)
		self.generation_provider_import = KW.ImportButton(**GS.imp_row_size)
		self.generation_provider_dropdown = DropDown()
		self.generation_provider_button = KW.ScrollDropDownButton(self.generation_provider_dropdown, text='NO GENERATION PROVIDER INITIALIZED', size_hint=(1, None), tooltip_types=['Generation Provider'],
			size=(100, GS.UI_field_height), set_state_func = (handle_exceptions(lambda index: [
				setattr(self.generation_provider_button, 'text', self.generation_provider_button.children[index].text),
				GS.MODULE_FACTORY.providers[self.generation_provider_button.children[index].text].switch_to()
			])))
		self.generation_provider_dropdown.bind(on_select=handle_exceptions(lambda instance, btn: [
			setattr(self.generation_provider_button, 'text', btn.text),
			GS.MODULE_FACTORY.providers[btn.text].switch_to()
			]))

		for provider_name in list(GS.MODULE_FACTORY.providers.keys()):
			btn = KW.DropDownEntryButton(text=provider_name, size_hint_y=None, height=GS.UI_field_height)
			btn.bind(on_release=handle_exceptions(lambda btn: self.generation_provider_dropdown.select(btn)))
			self.generation_provider_dropdown.add_widget(btn)

		generation_provider_row.add_widget(generation_provider_label)
		generation_provider_row.add_widget(self.generation_provider_import)
		generation_provider_row.add_widget(self.generation_provider_button)
		self.input_layout.add_widget(generation_provider_row)

		# Model
		model_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		self.model_label = Label(text='Model:', **GS.l_row_size)
		self.model_import = KW.ImportButton(**GS.imp_row_size)
		
		self.model_dropdown = DropDown()
		self.model_dropdown.bind(on_select=handle_exceptions(lambda instance, btn: setattr(GS.MAIN_APP.model_button, 'text', btn.text)))
		self.model_button = KW.ScrollDropDownButton(self.model_dropdown, text='NO MODEL INITIALIZED', size_hint=(1, None), size=(100, GS.UI_field_height), tooltip_types=['Model'])

		model_row.add_widget(self.model_label)
		model_row.add_widget(self.model_import)
		model_row.add_widget(self.model_button)
		self.input_layout.add_widget(model_row)

		# Name
		name_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		name_label = Label(text='Name:', **GS.l_row_size)
		self.name_import = KW.ImportButton(**GS.imp_row_size)
		self.name_input = KW.ScrollInput(min_value=-100000, max_value=100000, fi_mode='hybrid_int', increment=1, multiline=False, size_hint=(1, None), size=(100, GS.UI_field_height), tooltip_types=['Name'])
	
		name_row.add_widget(name_label)
		name_row.add_widget(self.name_import)
		name_row.add_widget(self.name_input)
		self.input_layout.add_widget(name_row)
		
		# Folder Name
		folder_name_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		folder_name_label = Label(text='Folder Name:', **GS.l_row_size)
		self.folder_name_import = KW.ImportButton(**GS.imp_row_size)
		folder_name_layout = BoxLayout(orientation='horizontal')
		self.folder_name_input = KW.ScrollInput(min_value=-100000, max_value=100000, fi_mode='hybrid_int', increment=1, multiline=False, allow_empty=True, size_hint=(1, None), size=(100, GS.UI_field_height),
			tooltip_types=['Folder Name'])
		open_folder_button = Button(text='📁', font_size=19,
			on_release=handle_exceptions(lambda btn: [
				os.makedirs(f'{GS.FULL_DIR}/__0utput__/{self.folder_name_input.text}', exist_ok=True),
				os.startfile(f'{GS.FULL_DIR}/__0utput__/{self.folder_name_input.text}/')]),
			font_name = 'NotoEmoji', size_hint = (None, None), size = (GS.UI_field_height, GS.UI_field_height), tooltip_types=['Open Generation Folder'])
		folder_name_layout.add_widget(open_folder_button)
		folder_name_layout.add_widget(self.folder_name_input)

		folder_name_row.add_widget(folder_name_label)
		folder_name_row.add_widget(self.folder_name_import)
		folder_name_row.add_widget(folder_name_layout)
		self.input_layout.add_widget(folder_name_row)

		# Seed - Cluster Collage
		cc_seed_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height*4)
		cc_seed_label = Label(text='Seed:', **GS.l_row_size)
		self.cc_seed_import = KW.ImportButton(**GS.imp_row_size)
		self.cc_seed_grid=KW.SeedGrid(size_hint=(1, None), height=GS.UI_field_height*4, layout=cc_seed_row)

		cc_seed_row.add_widget(cc_seed_label)
		cc_seed_row.add_widget(self.cc_seed_import)
		cc_seed_row.add_widget(self.cc_seed_grid)
		self.input_layout.add_widget(cc_seed_row)

		# Seed - Image Sequence
		is_seed_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		is_seed_label = Label(text='Seed:', **GS.l_row_size)
		self.is_seed_import = KW.ImportButton(**GS.imp_row_size)
		is_seed_randomize = Button(text='Randomize', size_hint=(None, None), size=(100, GS.UI_field_height))
		is_seed_clear = Button(text='Clear', size_hint=(None, None), size=(60, GS.UI_field_height))
		self.is_seed_input = KW.SeedScrollInput(min_value=0, max_value=4294967295, increment=1000, text='', multiline=False, size_hint=(1, None), size=(100, GS.UI_field_height), allow_empty=True)
		is_seed_randomize.bind(on_release=handle_exceptions(lambda btn: setattr(self.is_seed_input, 'text', str(IM_G.generate_seed()))))
		is_seed_clear.bind(on_release=handle_exceptions(lambda btn: setattr(self.is_seed_input, 'text', '')))
		is_seed_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, GS.UI_field_height))
		is_seed_layout.add_widget(is_seed_randomize)
		is_seed_layout.add_widget(is_seed_clear)
		is_seed_layout.add_widget(self.is_seed_input)

		is_seed_row.add_widget(is_seed_label)
		is_seed_row.add_widget(self.is_seed_import)
		is_seed_row.add_widget(is_seed_layout)
		self.input_layout.add_widget(is_seed_row)

		# Collage Dimensions
		cc_dim_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		cc_dim_label = Label(text='Collage Dim.:', **GS.l_row_size)
		self.cc_dim_import = KW.ImportButton(**GS.imp_row_size)
		cc_dim_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		cc_dim_width_label = Label(text='Columns:', size_hint=(None, None), width=80, height=GS.UI_field_height)
		self.cc_dim_width = KW.ScrollInput(text='3', size_hint=(1, None), width=60, height=GS.UI_field_height, tooltip_types=['Cluster Columns'])
		cc_dim_height_label = Label(text='Rows:', size_hint=(None, None), width=80, height=GS.UI_field_height)
		self.cc_dim_height = KW.ScrollInput(text='3', size_hint=(1, None), width=60, height=GS.UI_field_height, tooltip_types=['Cluster Rows'])
		cc_dim_layout.add_widget(cc_dim_width_label)
		cc_dim_layout.add_widget(self.cc_dim_width)
		cc_dim_layout.add_widget(cc_dim_height_label)
		cc_dim_layout.add_widget(self.cc_dim_height)

		cc_dim_row.add_widget(cc_dim_label)
		cc_dim_row.add_widget(self.cc_dim_import)
		cc_dim_row.add_widget(cc_dim_layout)
		self.input_layout.add_widget(cc_dim_row)

		# Image Sequence Quantity
		is_range_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		is_range_label = Label(text='Quantity/FPS:', **GS.l_row_size)
		self.is_range_import = KW.ImportButton(**GS.imp_row_size)
		is_range_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		self.is_quantity = KW.ScrollInput(text='28', min_value=1, max_value=100000, size_hint=(1, None), width=60, height=GS.UI_field_height, tooltip_types=['Image Quantity'])
		self.is_video = KW.StateShiftButton(text='🎬',font_name='NotoEmoji')
		is_range_layout.add_widget(self.is_quantity)
		is_range_layout.add_widget(self.is_video)
		is_fps_label = Label(text='FPS:', size_hint=(None, None), size=(60,GS.UI_field_height))
		self.is_fps = KW.ScrollInput(text=str(GS.BASE_FPS), min_value=1, max_value=144, size_hint=(1, None), width=60, height=GS.UI_field_height)
		is_range_layout.add_widget(is_fps_label)
		is_range_layout.add_widget(self.is_fps)

		is_range_row.add_widget(is_range_label)
		is_range_row.add_widget(self.is_range_import)
		is_range_row.add_widget(is_range_layout)
		self.input_layout.add_widget(is_range_row)

		# Steps
		steps_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		steps_label = Label(text='Steps:', **GS.l_row_size)
		self.steps_import = KW.ImportButton(**GS.imp_row_size)
		steps_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, GS.UI_field_height))
		self.steps_input = KW.FScrollInput(min_value=1, max_value=50, fi_mode='hybrid_int', increment=1, text='28', multiline=False, size_hint=(1, None), size=(100, GS.UI_field_height), font_size=font_small,font_name='Unifont', tooltip_types=['Steps'])
		steps_layout.add_widget(self.steps_input)

		steps_row.add_widget(steps_label)
		steps_row.add_widget(self.steps_import)
		steps_row.add_widget(steps_layout)
		self.input_layout.add_widget(steps_row)

		# Guidance
		guidance_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		guidance_label = Label(text='Guidance:', **GS.l_row_size)
		self.guidance_import = KW.ImportButton(**GS.imp_row_size)
		guidance_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, GS.UI_field_height))
		self.guidance_input = KW.FScrollInput(min_value=-1000, max_value=1000, fi_mode='hybrid_float', increment=0.1, text='5', multiline=False, size_hint=(1, None), size=(100, GS.UI_field_height), font_size=font_small,font_name='Unifont', tooltip_types=['CFG Scale/Scale/Guidance'])
		guidance_rescale_label = Label(text='G. Rescale:', **GS.l_row_size)
		self.guidance_rescale_input_f = KW.FScrollInput(min_value=-1000, max_value=1000, fi_mode='hybrid_float', increment=0.1, text='0', multiline=False, size_hint=(1, None), size=(100, GS.UI_field_height), font_size=font_small,font_name='Unifont')
		
		guidance_layout.add_widget(self.guidance_input)
		guidance_layout.add_widget(guidance_rescale_label)
		guidance_layout.add_widget(self.guidance_rescale_input_f)
		
		guidance_row.add_widget(guidance_label)
		guidance_row.add_widget(self.guidance_import)
		guidance_row.add_widget(guidance_layout)
		self.input_layout.add_widget(guidance_row)

		# Sampler
		sampler_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height*2)
		sampler_label = Label(text='Sampler:', **GS.l_row_size)
		self.sampler_import = KW.ImportButton(**GS.imp_row_size)

		self.sampler_input = TextInput(multiline=True, size_hint=(1, 1), height=GS.UI_field_height*2, tooltip_types=['Sampler'])
		add_sampler_button = Button(text='<', size_hint=(None, 1), width=GS.UI_field_height, tooltip_types=['Add Sampler String From Scroll Dropdowns'])
		add_sampler_button.bind(on_release=handle_exceptions(
			lambda btn: setattr(self.sampler_input, 'text', self.format_sampler_text(self.sampler_input.text))
		))
		sampler_clear_button = Button(text='Clear', size_hint=(None, 1), size=(60, GS.UI_field_height), tooltip_types=['Clear Sampler String'])
		sampler_clear_button.bind(on_release=handle_exceptions(lambda btn: setattr(self.sampler_input, 'text', '')))

		self.sampler_injector_dropdown = KW.PermissiveDropDown(auto_width=False,size_hint=(1, None))
		self.sampler_injector_dropdown.children[0].bind(
			children=lambda instance, children: [
				child.mod_values.update({'NOISE_SCHEDULE': lambda: '_' + self.noise_schedule_button.text})
				for child in children if hasattr(child, 'mod_values')
			]
		)
		self.sampler_injector_button = Button(text='+', size_hint=(None, 1), width=GS.UI_field_height, height=GS.UI_field_height, tooltip_types=['Open Sampler Injector Dropdown'])
		self.sampler_injector_button.bind(
		on_release=handle_exceptions(lambda *args: [_move_noise_button(self, self.sampler_injector_dropdown),
		self.sampler_injector_dropdown.open(self.sampler_injector_button)])
		)

		self.sampler_dropdown = DropDown()
		self.sampler_dropdown.bind(on_select=handle_exceptions(lambda instance, btn: setattr(self.sampler_button, 'text', btn.text)))
		self.sampler_dropdown.bind(on_select=handle_exceptions(lambda instance, btn: setattr(self.sampler_button, 'gen_value', btn.gen_value)))
		self.sampler_button = KW.ScrollDropDownButton(self.sampler_dropdown, text='NOT INITIALIZED', size_hint=(1, None), size=(100, GS.UI_field_height), tooltip_types=['Sampler'],
			set_state_func = (lambda index: [
				setattr(self.sampler_button, 'text', self.sampler_button.children[index].text),
				setattr(self.sampler_button, 'gen_value', self.sampler_button.children[index].gen_value)
			]))
		self.sampler_button.gen_value = 'NI'

		self.sampler_cutoff = KW.ScrollInput(text='0', min_value=0, size_hint=(None, None), width=28, height=GS.UI_field_height, tooltip_types=['Sampler Cutoff'])
		self.noise_schedule_dropdown = DropDown()
		self.noise_schedule_button = KW.ScrollDropDownButton(self.noise_schedule_dropdown, text='default', size_hint=(1, None), size=(100, GS.UI_field_height), tooltip_types=['Noise Schedule'])
		self.noise_schedule_dropdown.bind(on_select=handle_exceptions(lambda instance, btn: setattr(self.noise_schedule_button, 'text', btn.text)))

		self.sampler_injector_dropdown.bind(on_dismiss=handle_exceptions(lambda *args: _move_noise_button(self, sampler_sublayout_bottom)))
		self.noise_schedule_button.target_index = 0
		self.noise_schedule_button.mod_values = {}
		def _move_noise_button(self, target_layout):
			if target_layout == self.sampler_injector_dropdown:
				self.noise_schedule_button.target_index = sampler_sublayout_bottom.children.index(self.noise_schedule_button)
				self.noise_schedule_button.parent.remove_widget(self.noise_schedule_button)
				self.sampler_injector_dropdown.add_widget(self.noise_schedule_button, index=len(self.sampler_injector_dropdown.children[0].children))
			else:
				self.noise_schedule_button.parent.remove_widget(self.noise_schedule_button)
				sampler_sublayout_bottom.add_widget(self.noise_schedule_button, index=0)

		self.sampler_smea = KW.StateShiftButton(text='SMEA', size_hint=(None, 1), size=(60,GS.UI_field_height))
		self.sampler_dyn = KW.StateShiftButton(text='Dyn', size_hint=(None, 1), size=(46,GS.UI_field_height))
		self.sampler_smea.bind(enabled=handle_exceptions(lambda instance, value: KW.on_smea_disabled(value, self.sampler_dyn)))
		self.sampler_dyn.bind(enabled=handle_exceptions(lambda instance, value: KW.on_dyn_enabled(value, self.sampler_smea)))
		
		sampler_layout = BoxLayout(orientation='horizontal')
		sampler_sublayout_top = BoxLayout(orientation='horizontal',size_hint=(1, None), height=GS.UI_field_height*1)
		sampler_sublayout_bottom = BoxLayout(orientation='horizontal',size_hint=(1, None), height=GS.UI_field_height*1)
		sampler_sublayout = BoxLayout(orientation='vertical',size_hint=(None, None), size=(285, GS.UI_field_height*2))
		
		sampler_sublayout_top.add_widget(add_sampler_button)
		sampler_sublayout_top.add_widget(sampler_clear_button)
		sampler_sublayout_top.add_widget(self.sampler_button)
		sampler_sublayout_bottom.add_widget(self.sampler_injector_button)
		sampler_sublayout_bottom.add_widget(self.sampler_cutoff)
		sampler_sublayout_bottom.add_widget(self.sampler_smea)
		sampler_sublayout_bottom.add_widget(self.sampler_dyn)
		sampler_sublayout_bottom.add_widget(self.noise_schedule_button)
		
		sampler_sublayout.add_widget(sampler_sublayout_top)
		sampler_sublayout.add_widget(sampler_sublayout_bottom)
		
		sampler_layout.add_widget(self.sampler_input)
		sampler_layout.add_widget(sampler_sublayout)

		sampler_row.add_widget(sampler_label)
		sampler_row.add_widget(self.sampler_import)
		sampler_row.add_widget(sampler_layout)
		self.input_layout.add_widget(sampler_row)
		
		# Resolution
		resolution_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		resolution_label = Label(text='Resolution:', **GS.l_row_size)
		self.resolution_import = KW.ImportButton(**GS.imp_row_size)
		self.resolution_selector = KW.ResolutionSelector()

		resolution_row.add_widget(resolution_label)
		resolution_row.add_widget(self.resolution_import)
		resolution_row.add_widget(self.resolution_selector)
		self.input_layout.add_widget(resolution_row)

		# Prompt
		prompt_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height*4)
		prompt_row.flex_min_height = GS.UI_field_height*4
		prompt_label = Label(text='Prompt:', **GS.l_row_size)
		prompt_buttons_layout = BoxLayout(orientation='vertical', **GS.imp_row_size)
		self.prompt_import = KW.ImportButton()
		self.prompt = KW.FPrompt(size_hint=(1, 1), size=(100, GS.UI_field_height*4))
		self.prompt.input.font_size = 23
		self.prompt.input.font_name = 'Unifont'
		
		self.prompt_dropdown = DropDown(auto_width=False,size_hint=(1, None))
		self.prompt_injector_button = Button(text='+', size_hint=(None, 1), width=GS.UI_field_height, height=GS.UI_field_height*2)
		self.prompt_injector_button.bind(on_release=handle_exceptions(lambda *args: self.prompt_dropdown.open(self.prompt_injector_button)))
		
		prompt_buttons_layout.add_widget(self.prompt_injector_button)
		prompt_buttons_layout.add_widget(self.prompt_import)
		
		prompt_layout = BoxLayout(orientation='horizontal')
		self.prompt_token_counter=KW.TokenCostBar(self.prompt.input, size_hint=(None, 1), width=20)
		prompt_layout.add_widget(self.prompt)
		prompt_layout.add_widget(self.prompt_token_counter)
		self.prompt.input.bind(text=self.prompt_token_counter.update_rect)

		prompt_row.add_widget(prompt_label)
		prompt_row.add_widget(prompt_buttons_layout)
		prompt_row.add_widget(prompt_layout)
		self.input_layout.add_widget(prompt_row)

		# UC
		uc_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height*4)
		uc_row.flex_min_height = GS.UI_field_height*4
		uc_label = Label(text='Neg. Prompt:', **GS.l_row_size)
		uc_buttons_layout = BoxLayout(orientation='vertical', **GS.imp_row_size)
		self.uc_import = KW.ImportButton()
		self.uc = KW.FPrompt(size_hint=(1, 1), size=(100, GS.UI_field_height*4), tooltip_types=['Negative Prompt/Undesired Content'])
		self.uc.input.font_size = 23
		self.uc.input.font_name = 'Unifont'

		self.uc_dropdown = DropDown(auto_width=False,size_hint=(1, None))
		self.uc_injector_button = Button(text='+', size_hint=(None, 1), width=GS.UI_field_height, height=GS.UI_field_height*2)
		self.uc_injector_button.bind(on_release=handle_exceptions(lambda *args: self.uc_dropdown.open(self.uc_injector_button)))

		uc_buttons_layout.add_widget(self.uc_injector_button)
		uc_buttons_layout.add_widget(self.uc_import)
		
		uc_layout = BoxLayout(orientation='horizontal')
		self.uc_token_counter=KW.TokenCostBar(self.uc.input, size_hint=(None, 1), width=20)
		uc_layout.add_widget(self.uc)
		uc_layout.add_widget(self.uc_token_counter)
		self.uc.input.bind(text=self.uc_token_counter.update_rect)

		uc_row.add_widget(uc_label)
		uc_row.add_widget(uc_buttons_layout)
		uc_row.add_widget(uc_layout)
		self.input_layout.add_widget(uc_row)

		# Decrisper/Dynamic Thresholding
		decrisp_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		decrisp_label = Label(text='Dyn. Thresh.:', **GS.l_row_size)
		self.decrisp_import = KW.ImportButton(**GS.imp_row_size)
		self.decrisp_button = KW.StateShiftButton(text='Decrisper', size_hint=(None, None), size=(90,GS.UI_field_height), tooltip_types=['Decrisper/Dynamic Thresholding'])
		decrisp_scale = Label(text='Mimic Scale:', size_hint=(None, None), size=(100, GS.UI_field_height))
		self.decrisp_guidance_input = KW.FScrollInput(min_value=-10000, max_value=10000, fi_mode='hybrid_float', increment=0.1, text='10', multiline=False, size_hint=(1, None), size=(100, GS.UI_field_height),
		tooltip_types=['Decrisper/Dynamic Thresholding'], font_size=font_small,font_name='Unifont')
		decrisp_percentile = Label(text='Percentile:', size_hint=(None, None), size=(90, GS.UI_field_height))
		self.decrisp_percentile_input = KW.FScrollInput(min_value=0.000001, max_value=1, fi_mode='hybrid_float', increment=0.001, text='0.999', multiline=False, size_hint=(1, None), size=(100, GS.UI_field_height),
		tooltip_types=['Decrisper/Dynamic Thresholding'], round_value=6, font_size=font_small,font_name='Unifont')
		decrisp_layout = BoxLayout(orientation='horizontal',size_hint=(1, None), height=GS.UI_field_height)
		decrisp_layout.add_widget(self.decrisp_button)
		decrisp_layout.add_widget(decrisp_scale)
		decrisp_layout.add_widget(self.decrisp_guidance_input)
		decrisp_layout.add_widget(decrisp_percentile)
		decrisp_layout.add_widget(self.decrisp_percentile_input)

		decrisp_row.add_widget(decrisp_label)
		decrisp_row.add_widget(self.decrisp_import)
		decrisp_row.add_widget(decrisp_layout)
		self.input_layout.add_widget(decrisp_row)

		# Action buttons
		action_buttons_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		action_buttons_label = Label(text='Create images:', **GS.l_row_size)
		action_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		self.single_img_button = Button(text='Generate Image', size_hint=(1, None), height=GS.UI_field_height, tooltip_types=['Generate Image'])
		self.single_img_button.bind(on_release=self.generate_single_image)
		self.queue_button = Button(text='Queue Task', size_hint=(1, None), height=GS.UI_field_height, tooltip_types=['Queue Task'])
		self.queue_button.bind(on_release=self.on_queue_button_press)
		self.process_button = Button(text='Process Tasks', size_hint=(1, None), height=GS.UI_field_height, tooltip_types=['Process Tasks'])
		self.process_button.bind(on_release=self.on_process_button_press)
		action_buttons_layout.add_widget(self.single_img_button)
		action_buttons_layout.add_widget(self.queue_button)
		action_buttons_layout.add_widget(self.process_button)
		
		action_buttons_row.add_widget(action_buttons_label)
		action_buttons_row.add_widget(Label(text='', size_hint=(None, None), size=(0,0)))
		action_buttons_row.add_widget(action_buttons_layout)
		self.top_input_layout.add_widget(action_buttons_row)

		# In the middle is the self.meta_layout with the console, task tracker and some more relevant buttons
		task_state_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=GS.UI_field_height*5)
		
		self.import_buttons = [self.generation_provider_import, self.name_import, self.folder_name_import, self.model_import, self.cc_seed_import, self.is_seed_import,
			self.steps_import, self.guidance_import, self.sampler_import, self.resolution_import, self.prompt_import, self.uc_import,
			self.cc_dim_import, self.is_range_import, self.decrisp_import]

		activate_all_imports_button = KW.Button(text='Import All', text_color_dict = GS.theme["SBtnText"], bg_color_dict=GS.theme["SBtnBgOn"])
		activate_all_imports_button.bind(on_release=handle_exceptions(lambda *args: [setattr(button, 'enabled', True) for button in self.import_buttons[:]]))
		deactivate_all_imports_button = KW.Button(text='Import None', text_color_dict = GS.theme["SBtnText"], bg_color_dict=GS.theme["SBtnBgOff"])
		deactivate_all_imports_button.bind(on_release=handle_exceptions(lambda *args: [setattr(button, 'enabled', False) for button in self.import_buttons[:]]))

		import_adjust_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		import_adjust_layout.add_widget(activate_all_imports_button)
		import_adjust_layout.add_widget(deactivate_all_imports_button)

		task_state_counters_queued_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		queued_tasks_label = Label(text='Queued tasks: 0', halign = 'left', **GS.l_row_size, size_hint_x=0.5)
		GS.bind(queued_tasks=lambda instance, value: setattr(queued_tasks_label, 'text', "Queued tasks: " + str(value)))
		queued_images_label = Label(text='Queued images: 0', **GS.l_row_size, size_hint_x=0.5, halign = 'right')
		GS.bind(queued_images=lambda instance, value: setattr(queued_images_label, 'text', "Queued images: " + str(value)))
		task_state_counters_queued_layout.add_widget(queued_tasks_label)
		task_state_counters_queued_layout.add_widget(queued_images_label)
		
		task_state_counters_done_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		finished_tasks_label = Label(text='Finished tasks: 0', halign = 'left', **GS.l_row_size, size_hint_x=0.5)
		GS.bind(finished_tasks=lambda instance, value: setattr(finished_tasks_label, 'text', "Finished tasks: " + str(value)))
		produced_images_label = Label(text='Produced images: 0', **GS.l_row_size, size_hint_x=0.5)
		GS.bind(produced_images=lambda instance, value: setattr(produced_images_label, 'text', "Produced images: " + str(value)))
		task_state_counters_done_layout.add_widget(finished_tasks_label)
		task_state_counters_done_layout.add_widget(produced_images_label)
		
		task_state_counters_skipped_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		skipped_tasks_label = Label(text='Skipped tasks: 0', halign = 'left', **GS.l_row_size, size_hint_x=0.5)
		GS.bind(skipped_tasks=lambda instance, value: setattr(skipped_tasks_label, 'text', "Skipped tasks: " + str(value)))
		skipped_images_label = Label(text='Skipped images: 0', **GS.l_row_size, size_hint_x=0.5)
		GS.bind(skipped_images=lambda instance, value: setattr(skipped_images_label, 'text', "Skipped images: " + str(value)))
		task_state_counters_skipped_layout.add_widget(skipped_tasks_label)
		task_state_counters_skipped_layout.add_widget(skipped_images_label)

		wait_time_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		wait_time_label = Label(text='Wait time:', halign = 'left', **GS.l_row_size, size_hint_x=None)
		self.wait_time_input = KW.ScrollInput(text='1', fi_mode=float, min_value=0, size_hint=(1, None), width=60, height=GS.UI_field_height, tooltip_types=['Wait Time'])
		wait_time_layout.add_widget(wait_time_label)
		wait_time_layout.add_widget(self.wait_time_input)
		
		task_state_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=GS.UI_field_height)
		self.cancel_button = Button(text='⬛', font_name='Unifont',size_hint=(None, None), size=(GS.UI_field_height,GS.UI_field_height))
		self.cancel_button.bind(on_release=handle_exceptions(lambda instance: setattr(GS.MAIN_APP.pause_button, 'enabled', True)))
		self.cancel_button.bind(on_release=handle_exceptions(lambda instance: setattr(GS, 'cancel_request', True)))
		self.pause_button = KW.PauseButton(**GS.imp_row_size)
		overwrite_button = KW.StateShiftButton(text='Overwrite Images', size_hint=(0.6, None), height=GS.UI_field_height, font_size=font_small, tooltip_types=['Overwrite Images'])
		overwrite_button.bind(on_release=handle_exceptions(lambda instance: setattr(GS, 'overwrite_images', not GS.overwrite_images)))
		self.wipe_queue_button = Button(text='Wipe Queue', size_hint=(0.4, None), height=GS.UI_field_height, tooltip_types=['Wipe Queue'])
		self.wipe_queue_button.bind(on_release=IM_G.wipe_queue)
		task_state_buttons_layout.add_widget(self.pause_button)
		task_state_buttons_layout.add_widget(self.cancel_button)
		task_state_buttons_layout.add_widget(overwrite_button)
		task_state_buttons_layout.add_widget(self.wipe_queue_button)
		
		task_state_layout.add_widget(task_state_counters_queued_layout)
		task_state_layout.add_widget(task_state_counters_done_layout)
		task_state_layout.add_widget(task_state_counters_skipped_layout)
		task_state_layout.add_widget(wait_time_layout)
		task_state_layout.add_widget(task_state_buttons_layout)

		self.console = KW.Console()
		self.meta_layout.add_widget(self.console)
		self.meta_layout.add_widget(import_adjust_layout)
		self.meta_layout.add_widget(task_state_layout)

		self.preview = KW.ImagePreview()
		self.image_organization_layout.add_widget(self.preview)
		self.metadata_viewer = KW.MetadataViewer()
		self.image_organization_layout.add_widget(self.metadata_viewer)

		image_lists_layout = BoxLayout(orientation='horizontal', size_hint_y = None, height = GS.UI_field_height*1)

		self.loaded_images_dropdown = KW.PermissiveDropDown(auto_width=False,size_hint=(1, None))
		self.loaded_images_button = KW.Button(text = 'Loaded Images', tooltip_types=['Loaded images'])
		self.loaded_images_button.bind(on_release=handle_exceptions(lambda *args: self.loaded_images_dropdown.open(self.loaded_images_button)))
		image_lists_layout.add_widget(self.loaded_images_button)

		self.generated_images_dropdown = KW.PermissiveDropDown(auto_width=False,size_hint=(1, None))
		self.generated_images_dropdown.children[0].bind(children=handle_exceptions(lambda instance, value: value[-1].self_destruct() if len(value) > int(self.config_window.history_length_input.text) else None))
		self.generated_images_button = KW.Button(text = 'Generation History', tooltip_types=['History'])
		self.generated_images_button.bind(on_release=handle_exceptions(lambda *args: self.generated_images_dropdown.open(self.generated_images_button)))
		image_lists_layout.add_widget(self.generated_images_button)

		self.show_last_generation_button = KW.StateShiftButton(text='Show Last Generation', enabled=True, tooltip_types=['Show Last Generation'])
		image_lists_layout.add_widget(self.show_last_generation_button)

		purge_and_switch_layout = BoxLayout(orientation='horizontal', size_hint_y = None, height = GS.UI_field_height*1)
		self.purge_loaded_images_button = KW.ConfirmButton(
			lambda: [child.self_destruct() for child in self.loaded_images_dropdown.children[0].children[:]] or None,
			text='Purge Loaded Images', tooltip_types=['Purge'])
		purge_and_switch_layout.add_widget(self.purge_loaded_images_button)
		self.purge_history_button = KW.ConfirmButton(
			lambda: [child.self_destruct() for child in self.generated_images_dropdown.children[0].children[:]] or None,
			text='Purge History', tooltip_types=['Purge'])
		purge_and_switch_layout.add_widget(self.purge_history_button)
		self.switch_preview_metadata_button = KW.Button(text = 'Switch Preview/Metadata', tooltip_types=['Metadata Viewer'])
		self.switch_preview_metadata_button.bind(on_release=handle_exceptions(lambda *args: self.metadata_viewer.switch_display('invert')))
		purge_and_switch_layout.add_widget(self.switch_preview_metadata_button)
		
		self.image_organization_layout.add_widget(purge_and_switch_layout)
		self.image_organization_layout.add_widget(image_lists_layout)

		# The super_layout is the highest layout in the hierarchy and is also the one that is returned for Kivy to display
		# It has the user interaction section left, the console/task data section in the middle, and the image organization on the right		
		self.super_layout = BoxLayout(orientation='horizontal')
		self.super_layout.add_widget(self.top_input_layout)
		self.super_layout.add_widget(self.meta_layout)
		self.super_layout.add_widget(self.image_organization_layout)

		self.cc_exclusive_widgets = [cc_seed_row, cc_dim_row]
		self.is_exclusive_widgets = [is_seed_row, is_range_row]
		self.non_cs_widgets = [is_seed_row]

		GS.hide_widgets([*self.is_exclusive_widgets, self.metadata_viewer])
		self.pause_button.disabled = True
		self.cancel_button.disabled = True

		for provider_name, provider in GS.MODULE_FACTORY.providers.items():
			provider.initialize_ui()
		#self.generation_provider_dropdown.bind(on_select=handle_exceptions(lambda instance, btn: GS.MODULE_FACTORY.providers[btn.text].switch_to()))

		#Window.size = [1916, 2003] # These are test values I would use when making the application able to remember it's last window size/pos
		#Window.left = 854 # Unfortunately right now, and for the better part of a decade kivy (or SDL downstream) quietly applies the system scaling when using Window.size
		#Window.top = 29 # Due to this rather abnormal design I will wait for Kivy 3 here
		return self.super_layout

	# 03. This function checks the validity of passed settings
	@handle_exceptions
	def check_settings(self, instance, settings):
		empty_field = False
		if settings["name"] == '':
			print("[Warning] Name field can't be empty!")
			empty_field = True
		if settings["prompt"] == '':
			print("[Warning] Prompt field can't be empty!")
			empty_field = True
		if settings["scale"] == 0:
			print("[Warning] Scale can't be 0!")
			empty_field = True
		return empty_field

	# 04. This function generates a single image like any other UI would do, just that it has to be aware of which fields are active and which to use
	@handle_exceptions
	def generate_single_image(self, instance):
		GS.cancel_request = False
		blank_eval_dict = {'n':0,'c':0,'r':0,'cc':0,'s':0}

		if self.mode_switcher.cc_active:
			if not self.cc_seed_grid.seed_inputs[0].text == '':
				seed = self.cc_seed_grid.seed_inputs[0].text
			else:
				seed = str(IM_G.generate_seed())
		else:
			if not self.is_seed_input.text == '':
				seed = self.is_seed_input.text
			else:
				seed = str(IM_G.generate_seed())

		settings = {
			'name': self.name_input.text,
			'folder_name': self.folder_name_input.text,
			'folder_name_extra': '',
			'provider': GS.MODULE_FACTORY.selected_provider,
			'model': self.model_button.gen_value,
			'seed': int(seed),
			'sampler': self.get_sampler_setting(),
			'scale': self.guidance_input.text,
			'guidance_rescale': self.guidance_rescale_input_f.text,
			'steps': self.steps_input.text,
			'img_mode': {'width': int(self.resolution_selector.resolution_width.text),
								'height': int(self.resolution_selector.resolution_height.text)},
			'prompt': self.prompt.input.text,
			'negative_prompt': self.uc.input.text,
			'dynamic_thresholding': self.decrisp_button.enabled,
			'dynamic_thresholding_mimic_scale': self.decrisp_guidance_input.text if self.decrisp_button.enabled else 10,
			'dynamic_thresholding_percentile': self.decrisp_percentile_input.text if self.decrisp_button.enabled else 0.999,
			'meta': {
				'eval_guard': self.config_window.eval_guard_button.enabled
			}
		}
		settings.update(GS.MODULE_FACTORY.selected_provider.update_settings())
		self.get_image_entries(settings, False)
		if IM_G.f_variables_processor(settings, settings, blank_eval_dict) == 'Error':
			return
		if self.check_settings(None, settings):
			return
		settings.update(IM_G.decode_sampler_string(settings["sampler"], settings["provider"]))
		self.single_img_button.disabled = True
		self.process_button.disabled = True
		self.cancel_button.disabled = False
		self.wipe_queue_button.disabled = True
		future = GS.EXECUTOR.submit(IM_G.generate_as_is,settings,'')
		future.add_done_callback(self.on_process_complete)

	# 05. This function is responsible for taking all of the settings in the UI and queueing the desired task
	@handle_exceptions
	def on_queue_button_press(self, instance):
		# Get shared settings from text inputs and sliders
		steps = self.steps_input.text
		scale = self.guidance_input.text
		guidance_rescale = self.guidance_rescale_input_f.text
		img_mode = {'width': int(self.resolution_selector.resolution_width.text),
								'height': int(self.resolution_selector.resolution_height.text)}
		prompt = self.prompt.input.text
		uc = self.uc.input.text
		settings = {'name': self.name_input.text, 'folder_name': self.folder_name_input.text, 'provider': GS.MODULE_FACTORY.selected_provider,
		'model': self.model_button.gen_value, 'scale': scale, 'guidance_rescale': guidance_rescale, 'steps': steps, 'img_mode': img_mode, 'prompt': prompt,
		'negative_prompt': uc, 'dynamic_thresholding': self.decrisp_button.enabled,
		'dynamic_thresholding_mimic_scale': self.decrisp_guidance_input.text if self.decrisp_button.enabled else 10,
		'dynamic_thresholding_percentile': self.decrisp_percentile_input.text if self.decrisp_button.enabled else 0.999,}
		settings.update(GS.MODULE_FACTORY.selected_provider.update_settings())

		self.get_image_entries(settings, True)

		if self.mode_switcher.cc_active or self.mode_switcher.cs_active: # Cluster collage specific settings
			seeds = [[self.cc_seed_grid.seed_inputs[j+i*int(self.cc_seed_grid.seed_cols_input.text)].text for j in range(int(self.cc_seed_grid.seed_cols_input.text))] for i in range(int(self.cc_seed_grid.seed_rows_input.text))]
			seed = [[str(IM_G.generate_seed()) if value == '' else value for value in inner_list] for inner_list in seeds]
			if self.sampler_input.text != '':
				sampler = [list(filter(None, self.sampler_input.text.replace(" ", "").split(","))), 0 if self.sampler_cutoff.text == '' else int(self.sampler_cutoff.text)]
			else:
				sampler = self.get_sampler_setting()
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
			sampler = self.get_sampler_setting()
			settings.update({'seed': int(seed), 'sampler': sampler, 'quantity': int(self.is_quantity.text), 'video': 'standard' if self.is_video.enabled else '', 'FPS': int(self.is_fps.text)})
			if self.check_settings(None, settings):
				return
			IM_G.image_sequence(settings,self.config_window.eval_guard_button.enabled)
		GS.queued_tasks = len(GS.processing_queue)

	# 06. Processing the loaded images for image2image or vibe transfer happens in this function
	@handle_exceptions
	def get_image_entries(self, settings, lock_entries):
		images_to_be_processed = [
			entry for entry in GS.MAIN_APP.loaded_images_dropdown.children[0].children
			if entry.i2i_button.enabled or entry.vt_button.enabled or
			   entry.i2i_condition_input.text.strip() or entry.vt_condition_input.text.strip()
		]
				
		settings["image_entries"] = []
		for entry in images_to_be_processed:
			entry_data = {"entry_reference": entry}

			# Process I2I
			if entry.i2i_condition_input.text.strip():
				entry_data["i2i"] = {
					"condition": entry.i2i_condition_input.text,
					"strength": entry.i2i_strength_input.text,
					"noise": entry.i2i_noise_input.text
				}
			elif entry.i2i_button.enabled:
				entry_data["i2i"] = {
					"condition": "True",
					"strength": entry.i2i_strength_input.text,
					"noise": entry.i2i_noise_input.text
				}

			# Process VT
			if entry.vt_condition_input.text.strip():
				entry_data["vt"] = {
					"condition": entry.vt_condition_input.text,
					"strength": entry.vt_strength_input.text,
					"information": entry.vt_information_input.text
				}
			elif entry.vt_button.enabled:
				entry_data["vt"] = {
					"condition": "True",
					"strength": entry.vt_strength_input.text,
					"information": entry.vt_information_input.text
				}
			settings["image_entries"].append(entry_data)
			
			# We really really do not want any entries that are queued for processing to get deleted during processing, so we temporarily mark them as not destructible
			entry.destructible = lock_entries

	# 07. Processes the current state of sampler UI elements into a workable string or list
	@handle_exceptions
	def get_sampler_setting(self, comma_check = True):
		if self.sampler_input.text != '' and comma_check == True:
			if self.sampler_input.text.__contains__(','):
				sampler = self.sampler_input.text.replace(" ", "").split(",")[0]
			else:
				sampler = self.sampler_input.text.replace(" ", "")
		else:
			sampler = self.sampler_button.gen_value + '_' + self.noise_schedule_button.text
			if self.sampler_dyn.enabled:
				sampler+='_dyn'
			elif self.sampler_smea.enabled:
					sampler+='_smea'
		return sampler

	# 08. This function locks part of the UI and then processes the queued tasks one after the other in a separate thread
	# No @handle_exceptions due to custom treatment of exceptions in the function
	def on_process_button_press(self, instance):	
		try:
			self.switch_processing_state(True)
			future = GS.EXECUTOR.submit(IM_G.process_queue)
			future.add_done_callback(self.on_process_complete)
		except:
			traceback.print_exc()
			self.on_process_complete(None)
			GS.preview_queue= []
			print('Task queue has been wiped due to an exception')

	# 09. Ends a processing run and resets all relevant variables and states
	@handle_exceptions
	def on_process_complete(self, future):
		self.switch_processing_state(False)
		GS.produced_images=0
		GS.skipped_images=0
		for entry in GS.MAIN_APP.loaded_images_dropdown.children[0].children:
			entry.destructible = True

	# 10. Locks/unlocks elements according to the current processing state
	@handle_exceptions
	def switch_processing_state(self, processing):
		self.single_img_button.disabled = processing
		self.queue_button.disabled = processing
		self.process_button.disabled = processing
		self.wipe_queue_button.disabled = processing
		self.cancel_button.disabled = not processing
		self.pause_button.disabled = not processing

if __name__ == '__main__':
	GS.MAIN_APP = ClusterVisionF()
	GS.MAIN_APP.run()
	for provider_name, provider in GS.MODULE_FACTORY.providers.items():
		if hasattr(provider, 'exit_cleanup'):
			provider.exit_cleanup()
