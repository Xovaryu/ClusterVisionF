from ConfigHandler import *
from ImageGenerator import *

from transformers import AutoTokenizer
class CLIPCostCalculator:
	def __init__(self, model_name_or_path="openai/clip-vit-base-patch32"):
		self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
	
	def calculate_token_cost(self, text):
		tokens = self.tokenizer.encode(text, add_special_tokens=True)
		return len(tokens)
clip_calculator = CLIPCostCalculator()

from sys import platform
if platform == 'win32' or platform == 'cygwin':
	OS = 'Win'
	# This block is specifically needed to address Windows DPI issues
	import ctypes
	# Query DPI Awareness (Windows 10 and 8)
	awareness = ctypes.c_int()
	errorCode = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
	#print(awareness.value)
	# Set DPI Awareness  (Windows 10 and 8)
	errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)
	# the argument is the awareness level, which can be 0, 1 or 2:
	# for 1-to-1 pixel control I seem to need it to be non-zero (I'm using level 2)
	# Set DPI Awareness  (Windows 7 and Vista)
	success = ctypes.windll.user32.SetProcessDPIAware()
elif sys.platform.startswith('linux'):
	OS = 'Linux'
elif platform == 'darwin':
	OS = 'Mac'




from kivy.metrics import Metrics
Metrics.density = 1

# Imports and variables for threading so that the main GUI keeps running and updating while tasks are being processed
from concurrent.futures import ThreadPoolExecutor
EXECUTOR = ThreadPoolExecutor()
FUTURES = []

# Other imports
import math
import sys
import kivy
import json
import ast
import time
import re
import itertools
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider
from kivy.properties import BooleanProperty
from kivy.graphics import Color, Rectangle, Line
from kivy.core.text import LabelBase
from kivy.uix.scrollview import ScrollView
from kivy.core.clipboard import Clipboard
from kivy.uix.image import Image
from PIL import Image as PILImage
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.colorpicker import ColorPicker

MAX_TOKEN_COUNT = 225
RESOLUTIONS = copy.deepcopy(NAI_RESOLUTIONS)
RESOLUTIONS.update(USER_RESOLUTIONS)
PROMPT_CHUNKS = NAI_PROMPT_CHUNKS + USER_PROMPT_CHUNKS
UC_CHUNKS = NAI_UCS + USER_UCS
MODELS=NAI_MODELS
PREVIEW_QUEUE = []
FUTURE = None

### Configuration ###
field_height=30
font_hyper=20
font_large=19
font_small=15
input_colors={'foreground_color': THEME[0]["value"], 'background_color': THEME[1]["value"]}
label_color={'color': THEME[2]["value"]}
bg_label_colors={'color': THEME[6]["value"], 'background_color': THEME[7]["value"]}
button_colors={'color': THEME[8]["value"], 'background_color': THEME[9]["value"]}
dp_button_colors={'color': THEME[10]["value"], 'background_color': THEME[11]["value"]}

l_row_size1={'size_hint':(None, None),'size':(170, field_height)}
l_row_size2={'size_hint':(None, 1),'size':(170, field_height)}
imp_row_size1={'size_hint':(None, None),'size':(field_height, field_height)}
imp_row_size2={'size_hint':(None, 1),'size':(field_height, field_height)}
#Load in fonts
LabelBase.register(name='Roboto', fn_regular=FULL_DIR + 'Fonts/Roboto-Regular.ttf')
#LabelBase.register(name='Symbola', fn_regular=FULL_DIR + 'Fonts/Symbola.ttf')
LabelBase.register(name='Unifont', fn_regular=FULL_DIR + 'Fonts/unifont_jp-15.0.01.ttf')
#LabelBase.register(name='NotoSansJP', fn_regular=FULL_DIR + 'Fonts/NotoSansJP-VF.ttf')
LabelBase.register(name='NotoEmoji', fn_regular=FULL_DIR + 'Fonts/NotoEmoji-VariableFont_wght.ttf')

def rgba_to_string(color):
	return '[color={}{}'.format(''.join(hex(int(c * 255))[2:].zfill(2) for c in color), ']')

def on_smea_disabled(value, linked_button):
	if not value:
		linked_button.enabled = False

def on_dyn_enabled(value, linked_button):
	if value:
		linked_button.enabled = True

class TokenCostBar(BoxLayout):
    def __init__(self, clip_calculator, max_token_count, **kwargs):
        super(TokenCostBar, self).__init__(**kwargs)
        self.clip_calculator = clip_calculator#CLIPCostCalculator()
        self.max_token_count = max_token_count
        self.color_threshold = self.max_token_count / 2
        self.token_cost = 0
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw a colored bar based on the token cost
            if self.token_cost <= self.color_threshold:
                color_value = self.token_cost / self.color_threshold
                Color(0, 1, 0, 1)
            else:
                color_value = (self.token_cost - self.color_threshold) / self.color_threshold
                Color(color_value, 1.0 - color_value, 0.0)
            bar_height = min(1,self.token_cost / self.max_token_count) * self.height
            Rectangle(pos=self.pos, size=(self.width, bar_height))

    def calculate_token_cost(self, instance, text):
        self.token_cost = self.clip_calculator.calculate_token_cost(text)
        self.update_rect()

class ImagePreview(BoxLayout):
	def __init__(self, **kwargs):
		super(ImagePreview, self).__init__(**kwargs)
		self.loaded=False

	def load_image(self, path):
		time.sleep(0.5) # Hacky work around to give the system time to refresh the file
		try:
			if os.path.isfile(path):
				if not self.loaded:
					self.image = Image(allow_stretch=True)
					self.add_widget(self.image)
					self.loaded = True
				if self.image.source == path:
					self.image.reload()
				else:
					self.image.source = path
		except:
			print('Image loading failed')
		
class ImagePreviewFAIL(BoxLayout):
	from kivy.core.image import Image as CoreImage
	import io
	def __init__(self, **kwargs):
		super(ImagePreview, self).__init__(**kwargs)
		self.loaded = False

	def load_image(self, img):
		if not self.loaded:
			self.image = Image(allow_stretch=True)
			self.add_widget(self.image)
			self.loaded = True
			buf = io.BytesIO(img)
			cim = CoreImage(buf, ext='jpg')
			self.image = Image(allow_stretch=True, texture=cim.texture)

class DoubleEmojiButton(Button):
	enabled = BooleanProperty(True)
	font_size=23
	font_name='NotoEmoji'

	def __init__(self, symbol1='', symbol2='', **kwargs):
		super().__init__(**kwargs)
		self.bind(enabled=self.on_state_changed)
		self.on_state_changed()
		self.symbol1 = symbol1
		self.symbol2 = symbol2

	def on_state_changed(self, *args):
		if self.enabled:
			self.background_color = (0, 1, 0, 1)  # Green
			self.text = '📥'
		else:
			self.background_color = (1, 0, 0, 1)  # Red
			self.text = '🚫'
			
	def on_release(self):
		self.enabled = not self.enabled
class ImportButton(DoubleEmojiButton):
	def __init__(self, **kwargs):
		super().__init__(symbol1='📥', symbol2='🚫', **kwargs)

class StateShiftButton(Button):
	enabled = BooleanProperty(False)
	font_size=font_large

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.bind(enabled=self.on_state_changed)
		self.on_state_changed()

	def on_state_changed(self, *args):
		if self.enabled:
			self.background_color = (0, 1, 0, 1)  # Green
		else:
			self.background_color = (1, 0, 0, 1)  # Red
			
	def on_release(self):
		self.enabled = not self.enabled
class StateFButton(StateShiftButton):
	def __init__(self, mode_switcher, standard_target, f_target, injector, standard_widgets = [], f_widgets =[], **kwargs):
		self.text = 'f'
		self.mode_switcher = mode_switcher
		self.standard_target = standard_target
		self.f_target = f_target
		self.injector = injector
		self.standard_widgets = standard_widgets
		self.f_widgets = f_widgets
		super().__init__(**kwargs)
	def on_state_changed(self, *args):
		super(StateFButton, self).on_state_changed(*args)
		if self.enabled:
			self.mode_switcher.hide_widgets(self.standard_widgets)
			self.mode_switcher.unhide_widgets(self.f_widgets)
			self.injector.target = self.f_target
		else:
			self.mode_switcher.unhide_widgets(self.standard_widgets)
			self.mode_switcher.hide_widgets(self.f_widgets)
			self.injector.target = self.standard_target

class InjectorDropdown(BoxLayout):
	def __init__(self, dropdown_list=[], button_text='', target=None, inject_identifier='P', **kwargs):
		super().__init__(**kwargs)
		self.orientation='vertical'
		self.target=target
		self.inject_identifier=inject_identifier
		self.dropdown = DropDown(auto_width=False,size_hint=(1, None))
		dropdown_button = Button(text=button_text, size_hint=(None, 1), width=field_height, height=field_height*2, **button_colors)
		#dropdown_button.bind(on_release=dropdown.open) # This should work but is unreliable
		dropdown_button.bind(on_release=lambda *args: self.dropdown.open(dropdown_button))
		# Update the dropdown button text when an item is selected
		self.dropdown.bind(on_select=lambda instance, x: setattr(dropdown_button, 'text', x))
		self.add_widget(dropdown_button)

		# Create a button for each item in the list
		for item in dropdown_list:
			self.add_button(item)

	def add_button(self, item):
		item_string = item['string']  # Store the string in a local variable
		# Create a label for the name and string
		item_label = BGLabel(text=f'[u]{item["name"]}[/u]\n{item_string}',markup=True,size_hint=(1, 1), **bg_label_colors)
		item_label.bind(
			width=lambda *args, item_label=item_label: item_label.setter('text_size')(item_label, (item_label.width, None)),
			texture_size=lambda *args, item_label=item_label: item_label.setter('height')(item_label, item_label.texture_size[1])
		)
		# Create a box layout for the item
		item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height*2)
		# Create a button to copy the string to the clipboard
		copy_button = Button(text='Copy', font_size=font_large, size_hint=(None, None), width=50, height=field_height*2, **button_colors)
		copy_button.bind(on_release=lambda *args, item_string=item_string, item_layout=item_layout: self.copy_to_clipboard(item_string, item_layout))
		# Create a button to prepend the string to the text box
		prepend_button = Button(text='>' + self.inject_identifier, font_size=font_large, size_hint=(None, None), width=50, height=field_height*2, **button_colors)
		prepend_button.bind(on_release=lambda *args, item_string=item_string, item_layout=item_layout: self.prepend_to_text_box(item_string, item_layout))
		# Create a button to append the string to the text box
		append_button = Button(text=self.inject_identifier + '<', font_size=font_large, size_hint=(None, None), width=50, height=field_height*2, **button_colors)
		append_button.bind(on_release=lambda *args, item_string=item_string, item_layout=item_layout: self.append_to_text_box(item_string, item_layout))
		item_layout.add_widget(copy_button)
		item_layout.add_widget(prepend_button)
		item_layout.add_widget(append_button)
		item_layout.add_widget(item_label)
		# Add the item layout to the dropdown
		self.dropdown.add_widget(item_layout)
		return item_layout, item_string

	def copy_to_clipboard(self, string, item_layout):
		Clipboard.copy(string)

	def prepend_to_text_box(self, string, item_layout):
		self.target.text = string + self.target.text

	def append_to_text_box(self, string, item_layout):
		self.target.text += string
class ConditionalInjectorDropdown(InjectorDropdown):
	def __init__(self, dropdown_list=[], button_text='', target=None, **kwargs):
		super().__init__(dropdown_list=dropdown_list, button_text=button_text, target=target, **kwargs)
	
	def add_button(self, item, *args):
		item_layout, item_string = super(ConditionalInjectorDropdown, self).add_button(item, *args)
		if not (item_string == 'ddim, ' or item_string == 'plms, '):
			sampler_smea = StateShiftButton(text='SMEA', size_hint=(None, 1), size=(70,field_height))
			sampler_dyn = StateShiftButton(text='Dyn', size_hint=(None, 1), size=(70,field_height))

			sampler_smea.bind(enabled=lambda instance, value: on_smea_disabled(value, sampler_dyn))
			sampler_dyn.bind(enabled=lambda instance, value: on_dyn_enabled(value, sampler_smea))
			item_layout.add_widget(sampler_smea, index=1)
			item_layout.add_widget(sampler_dyn, index=1)
		

	def copy_to_clipboard(self, string, item_layout):
		string = self.attach_smea_dyn(string, item_layout)
		Clipboard.copy(string)

	def prepend_to_text_box(self, string, item_layout):
		string = self.attach_smea_dyn(string, item_layout)
		self.target.text = string + self.target.text

	def append_to_text_box(self, string, item_layout):
		string = self.attach_smea_dyn(string, item_layout)
		self.target.text += string
	
	def attach_smea_dyn(self, string, item_layout):
		if item_layout.children[1].enabled: #Dyn
			string = string[:-2] + '_dyn' + string[-2:]
		elif item_layout.children[2].enabled: #SMEA
			string = string[:-2] + '_smea' + string[-2:]
		return string

class ScrollDropDownButton(Button):
	def __init__(self, associated_dropdown, **kwargs):
		self.associated_dropdown = associated_dropdown
		super().__init__(**kwargs)
		
	def on_touch_down(self, touch):
		if touch.is_mouse_scrolling and self.collide_point(*touch.pos):
			if touch.button == 'scrolldown':
				# Set text to next entry in dropdown list
				children = self.associated_dropdown.children[0].children
				current_index = 0
				for i, child in enumerate(children):
					if child.text == self.text:
						current_index = i
						break
				next_index = (current_index + 1) % len(children)
				self.text = children[next_index].text
			elif touch.button == 'scrollup':
				# Set text to previous entry in dropdown list
				children = self.associated_dropdown.children[0].children
				current_index = 0
				for i, child in enumerate(children):
					if child.text == self.text:
						current_index = i
						break
				prev_index = (current_index - 1) % len(children)
				self.text = children[prev_index].text
		return super(ScrollDropDownButton, self).on_touch_down(touch)

class ModeSwitcher(BoxLayout):
	def __init__(self, app='', **kwargs):
		super(ModeSwitcher, self).__init__(**kwargs)
		self.app=app
		self.cc_active = True
		self.is_active = False
		self.cc_button = Button(text='Cluster Collage', on_press=self.switch_cc)
		self.im_button = Button(text='Image Sequence', on_press=self.switch_is)
		self.add_widget(self.cc_button)
		self.add_widget(self.im_button)
		self.cc_button.background_color = (0, 1, 0, 1)
		self.im_button.background_color = (1, 0, 0, 1)
	
	# These functions are responsible for switching between the cluster collage and image sequence layouts
	def switch_cc(self, f):
		if self.cc_active == True:
			return
		self.cc_active = True
		self.is_active = False
		self.cc_button.background_color = (0, 1, 0, 1)
		self.im_button.background_color = (1, 0, 0, 1)
		self.hide_widgets(self.app.is_exclusive_widgets)
		self.unhide_widgets(self.app.cc_exclusive_widgets)

	def switch_is(self, f):
		if self.is_active == True:
			return
		self.cc_active = False
		self.is_active = True
		self.cc_button.background_color = (1, 0, 0, 1)
		self.im_button.background_color = (0, 1, 0, 1)
		self.hide_widgets(self.app.cc_exclusive_widgets)
		self.unhide_widgets(self.app.is_exclusive_widgets)
	
	# These functions hide and unhide widgets (little warning, calling hide_widgets twice on a widget will hide those widgets for the rest of the run time, so don't)
	def hide_widgets(self, widgets):
		for widget in widgets:
			widget.ori_opacity = widget.opacity
			widget.ori_height = widget.height
			widget.ori_width = widget.width
			widget.ori_size_hint_y = widget.size_hint_y
			widget.ori_size_hint_x = widget.size_hint_x
			widget.opacity = 0
			widget.height = 0
			widget.width = 0
			widget.size_hint_y = None
			widget.size_hint_x = None
		
	def unhide_widgets(self, widgets):
		try:
			for widget in widgets:
				widget.opacity = widget.ori_opacity
				widget.height = widget.ori_height
				widget.width = widget.ori_width
				widget.size_hint_y = widget.ori_size_hint_y
				widget.size_hint_x = widget.ori_size_hint_x
		except:
			pass

# SeedGrid class for seed grids when making cluster collages
class SeedGrid(GridLayout):
	def __init__(self, **kwargs):
		super(SeedGrid, self).__init__(**kwargs)
		self.cols=2
		self.seed_inputs = []
		self.cc_seed_grid = GridLayout(cols=3, size_hint=(1, 1), size=(100, field_height*4))
		
		self.seed_cols_input = ScrollInput(text='3', size_hint=(1, None), width=60, height=field_height, **input_colors)
		self.seed_rows_input = ScrollInput(text='3', size_hint=(1, None), width=60, height=field_height, **input_colors)
		self.seed_mult_label = Label(text='×', size_hint=(None, None), width=20, height=field_height)
		self.dim_input_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.dim_input_layout.add_widget(self.seed_cols_input)
		self.dim_input_layout.add_widget(self.seed_mult_label)
		self.dim_input_layout.add_widget(self.seed_rows_input)
		self.seed_cols_input.bind(text=self.adjust_grid_size)
		self.seed_rows_input.bind(text=self.adjust_grid_size)

		self.btn1 = Button(text='Randomize', size_hint=(None, None), size=(100, field_height), **button_colors)
		self.btn1.bind(on_release=lambda btn: self.randomize())
		self.btn2 = Button(text='Clear', size_hint=(None, None), size=(100, field_height), **button_colors)
		self.btn2.bind(on_release=lambda btn: self.clear())
		self.btn3 = Button(text='Load List', size_hint=(None, None), size=(100, field_height), **button_colors)

		# create label for the multiplication sign between width and height
		self.seed_list_dropdown = DropDown()
		self.btn3.bind(on_release=self.seed_list_dropdown.open)
		for seed_list in SEED_LISTS:
			btn = Button(text=seed_list["name"], size_hint_y=None, height=field_height, **dp_button_colors)
			btn.bind(on_release=lambda btn, seed_list=seed_list: (self.load_seeds(seed_list["seeds"]), self.seed_list_dropdown.dismiss()))
			self.seed_list_dropdown.add_widget(btn)
		
		self.btn_grid = GridLayout(cols=1, size_hint=(None, 1))
		self.btn_grid.add_widget(self.dim_input_layout)
		self.btn_grid.add_widget(self.btn1)
		self.btn_grid.add_widget(self.btn2)
		self.btn_grid.add_widget(self.btn3)

		self.add_widget(self.btn_grid)
		self.add_widget(self.cc_seed_grid)
		
		self.adjust_grid_size()
		
	def adjust_grid_size(self, instance=None, text=None):
		if self.seed_rows_input.text == '' or self.seed_cols_input.text == '':
			return
		# calculate the number of rows and columns needed to fit all the inputs
		num_inputs = int(self.seed_rows_input.text) * int(self.seed_cols_input.text)

		# adjust the size of the grid
		self.cc_seed_grid.cols = int(self.seed_cols_input.text)

		# remove any excess input widgets
		while len(self.seed_inputs) > num_inputs:
			self.cc_seed_grid.remove_widget(self.seed_inputs.pop())

		# add any missing input widgets
		while len(self.seed_inputs) < num_inputs:
			seed_input = ScrollInput(text='', min_value=0, max_value=4294967295, multiline=False, **input_colors, font_size=font_small, allow_empty=True)
			self.seed_inputs.append(seed_input)
			self.cc_seed_grid.add_widget(seed_input)

	def load_seeds(self, seeds):
		self.seed_rows_input.text, self.seed_cols_input.text = str(len(seeds)), str(len(seeds[0]))
		self.adjust_grid_size()
		for seed_input, value in zip(self.seed_inputs, itertools.chain(*seeds)):
			seed_input.text = str(value)

	def randomize(self):
		for widget in self.cc_seed_grid.children:
			if isinstance(widget, TextInput):
				widget.text = str(generate_seed())

	def clear(self):
		for widget in self.cc_seed_grid.children:
			if isinstance(widget, TextInput):
				widget.text = ''

# PromptGrid class for the use of f-strings in prompting
class PromptGrid(GridLayout):
	def __init__(self, **kwargs):
		super(PromptGrid, self).__init__(**kwargs)
		self.rows = 1
		self.prompt_rows = 1
		self.prompt_inputs = []
		self.prompt_eval_list = BoxLayout(orientation='vertical', size_hint=(1, 1), size=(100, field_height*4))
		self.btn1 = Button(text='Row+', size_hint=(None, None), size=(100, field_height), **button_colors)
		self.btn1.bind(on_release=lambda btn: self.on_increase_rows())
		self.btn2 = Button(text='Row-', size_hint=(None, None), size=(100, field_height), **button_colors)
		self.btn2.bind(on_release=lambda btn: self.on_decrease_rows())
		self.btn3 = Button(text='Copy ⁅⁆', size_hint=(None, None), size=(100, field_height), **button_colors)
		self.btn3.bind(on_release=lambda btn: Clipboard.copy('⁅⁆'))
		self.btn3.font_name = 'Unifont'
		self.btn4 = Button(text='Inject ⁅⁆', size_hint=(None, None), size=(100, field_height), **button_colors)
		self.btn4.bind(on_release=lambda btn: setattr(self.prompt_inputs[0], 'text', self.prompt_inputs[0].text+'⁅⁆'))
		self.btn4.font_name = 'Unifont'
		self.btn_grid = GridLayout(cols=1, size_hint=(None, 1))
		self.btn_grid.add_widget(self.btn1)
		self.btn_grid.add_widget(self.btn2)
		self.btn_grid.add_widget(self.btn3)
		self.btn_grid.add_widget(self.btn4)
		self.add_widget(self.btn_grid)
		self.add_widget(self.prompt_eval_list)
		
		self.adjust_grid_size(1)

	def adjust_grid_size(self, rows):
		self.prompt_rows = rows
		# retain the text of the existing inputs
		prompt_input_texts = [input.text for input in self.prompt_inputs]
		self.prompt_inputs.clear()
		self.prompt_eval_list.clear_widgets()
		for i in range(rows):
			prompt_input = TextInput(multiline=True, **input_colors)
			prompt_input.font_size = 23
			prompt_input.font_name = 'Unifont'
			if i < len(prompt_input_texts):
				prompt_input.text = prompt_input_texts[i]
			self.prompt_inputs.append(prompt_input)
			self.prompt_eval_list.add_widget(prompt_input)

	def load_prompts(self, prompts):
		self.adjust_grid_size(len(prompts))
		for i in range(len(prompts)):
			self.prompt_inputs[i].text = str(prompts[i])[6:-5].replace("\\'","'")

	def on_increase_rows(self):
		rows = min(self.prompt_rows + 1, 5)
		self.adjust_grid_size(rows)

	def on_decrease_rows(self):
		rows = max(self.prompt_rows - 1, 1)
		self.adjust_grid_size(rows)

# In order to use the previous generation metadata, this class replicates a functional read-only console
class Console(BoxLayout):
	#A proper passing function is needed to prevent program breaking recursion
	class TerminalPass():
		def __init__(self, type='', parent=None, **kwargs):
			self.type = type
			self.parent = parent
		def write(self, message):
			self.parent.process_message(message, self.type)
		def flush(self):
			pass

	def __init__(self, max_lines=200, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'vertical'
		self.max_lines = max_lines

		self.output_text = Label(text='', font_size=12, size_hint=(1,None), valign='top', markup=True)
		self.output_text.bind(
			width=lambda *x: self.output_text.setter('text_size')(self.output_text, (self.output_text.width, None)),
			texture_size=lambda *x: self.output_text.setter('height')(self.output_text, self.output_text.texture_size[1]))
		self.output_scroll = ScrollView(size_hint=(1, 1))
		self.output_scroll.add_widget(self.output_text)
		self.add_widget(self.output_scroll)
		self._stdout = sys.stdout
		self._stderr = sys.stderr
		sys.stdout = self.pass_out = self.TerminalPass(type='out', parent=self)
		sys.stderr = self.pass_err = self.TerminalPass(type='err', parent=self)

	def process_message(self, message, type):
		if type == 'out':
			self._stdout.write(message)
			self.output_text.text += f'{rgba_to_string(THEME[4]["value"])}{message}[/color]'
		elif type == 'err':
			self._stderr.write(message)
			self.output_text.text += f'{rgba_to_string(THEME[5]["value"])}{message}[/color]'

		# Split the text into lines
		lines = self.output_text.text.splitlines()

		# Remove the oldest lines if the maximum number of lines is reached, otherwise the element will eventually fail
		if len(lines) > self.max_lines:
			self.output_text.text = '\n'.join(lines[-self.max_lines:])
			
	def flush(self):
		pass

# A special label with a convenient integrated background, used for stuff like categories in dropdown lists
class BGLabel(Label):
	def __init__(self, background_color=[0, 0, 0.3, 1],**kwargs):
		super(BGLabel, self).__init__(**kwargs)
		with self.canvas.before:
			Color(*background_color)  # set the background color here
			self.rect = Rectangle(size=self.size, pos=self.pos)
		self.bind(size=self._update_rect, pos=self._update_rect)

	def _update_rect(self, instance, value):
		self.rect.pos = instance.pos
		self.rect.size = instance.size
	
	def _update_color(self, instance, color):
		self.canvas.before.clear()
		with self.canvas.before:
			Color(*color)  # set the background color here
			self.rect = Rectangle(size=self.size, pos=self.pos)

# Input field used for any field with scrolling numbers
class ScrollInput(TextInput):
	def __init__(self, min_value=1, max_value=100, increment=1, fi_mode=int, round_value=6, allow_empty=False, **kwargs):
		super().__init__(**kwargs)
		self.multiline = False
		self.min_value = min_value
		self.max_value = max_value
		self.increment = increment
		self.fi_mode = fi_mode
		self.round_value = round_value
		self.input_filter = self.fi_mode.__name__
		self.allow_empty = allow_empty

	def on_focus(self, instance, value):
		if not value:
			if self.allow_empty and (value == '' or value == False):
				return
			try:
				value = self.fi_mode(self.text)
				if value < self.min_value:
					self.text = str(self.min_value)
				elif value > self.max_value:
					self.text = str(self.max_value)
				else:
					self.text = str(value)
			except ValueError:
				print('ScrollInput ValueError')
				print(value)
				# User entered an invalid value
				self.text = str(self.min_value)
				
	def on_touch_down(self, touch):
		if self.text == '':
			return
		if touch.is_mouse_scrolling and self.collide_point(*touch.pos):
			if touch.button == 'scrolldown':
				self.text = str(round(min(self.fi_mode(self.text) + self.increment,self.max_value),self.round_value))
			elif touch.button == 'scrollup':
				self.text = str(round(max(self.fi_mode(self.text) - self.increment,self.min_value),self.round_value))
		return super(ScrollInput, self).on_touch_down(touch)
# Special input field needed for the ResolutionSelector
class ComboCappedScrollInput(ScrollInput):
	def __init__(self, paired_field=None, **kwargs):
		super().__init__(**kwargs)
		self.paired_field = paired_field

	def on_focus(self, instance, value):
		if not value:
			# User has left the field
			try:
				value = self.fi_mode(self.text)
				if value*int(self.paired_field.text)>3145728:
					value = int(3145728 / int(self.paired_field.text))
				if value % 64 != 0:
					value = value - (value % 64)
				if value < self.min_value or value == '':
					self.text = str(self.min_value)
				elif value > self.max_value:
					self.text = str(self.max_value)
				else:
					self.text = str(value)
					self.value = str(value)
			except Exception as e:
				import traceback
				traceback.print_exc()
				
	def on_touch_down(self, touch):
		if touch.is_mouse_scrolling and self.collide_point(*touch.pos):
			if touch.button == 'scrolldown':
				if (int(self.text)+64)*int(self.paired_field.text)>3145728:
					pass
				else:
					self.text = str(round(min(self.fi_mode(self.text) + self.increment,self.max_value),self.round_value))
			elif touch.button == 'scrollup':
				self.text = str(round(max(self.fi_mode(self.text) - self.increment,self.min_value),self.round_value))
		return super(ScrollInput, self).on_touch_down(touch)

# A resolution selector that aims to have just about all the possible conveniences
class ResolutionSelector(BoxLayout):
	def __init__(self, **kwargs):
		super().__init__(orientation='horizontal', size_hint=(1, None), height=field_height, **kwargs)
		
		# Create width and height input fields for custom resolution
		self.resolution_width = ComboCappedScrollInput(text='640', increment=64, min_value=64, max_value=49152,
													 size_hint=(1, None), width=60, height=field_height, **input_colors)
		self.resolution_height = ComboCappedScrollInput(text='640', increment=64, min_value=64, max_value=49152, paired_field=self.resolution_width, 
													  size_hint=(1, None), width=60, height=field_height, **input_colors)
		self.resolution_width.paired_field = self.resolution_height

		# create label for the multiplication sign between width and height
		resolution_mult_label = Label(text='×', size_hint=(None, None), width=20, height=field_height)

		# create dropdown button for selecting image mode
		self.resolution_menu_button = Button(text='SquareNormal', size_hint=(None, None), width=150, height=field_height, **button_colors)

		# create dropdown menu for image modes
		img_dropdown = DropDown()
		
		# create button for each category
		for category, modes in RESOLUTIONS.items():
			category_label = BGLabel(text=category, size_hint_y=None, height=field_height, **bg_label_colors)
			img_dropdown.add_widget(category_label)
			# create button for each mode in category
			for mode in modes:
				img_button = Button(text=mode, size_hint_y=None, height=field_height, **dp_button_colors)
				img_button.bind(on_release=lambda img_button: self.set_size(img_button.text, self.resolution_width,
																			  self.resolution_height, img_dropdown))
				img_dropdown.add_widget(img_button)

		# Bind update_resolution_dropdown to changes in width and height input fields
		self.resolution_width.bind(text=self.update_resolution_dropdown)
		self.resolution_height.bind(text=self.update_resolution_dropdown)

		# Bind opening of dropdown menu to dropdown button
		self.resolution_menu_button.bind(on_release=lambda *args: img_dropdown.open(self.resolution_menu_button))
		img_dropdown.bind(on_select=lambda instance, x: setattr(self.resolution_menu_button, 'text', x))

		# Add widgets to layout
		self.add_widget(self.resolution_width)
		self.add_widget(resolution_mult_label)
		self.add_widget(self.resolution_height)
		self.add_widget(self.resolution_menu_button)

	def update_resolution_dropdown(self, *args):
		# If the values are empty
		if (self.resolution_width.text == '' or self.resolution_height.text == '') and (self.resolution_width.focus or self.resolution_height.focus):
				return
		# Get the current values of the width and height input fields
		width = int(self.resolution_width.text)
		height = int(self.resolution_height.text)

		# Check if the current values match any known resolutions
		for category, modes in RESOLUTIONS.items():
			for mode, size in modes.items():
				if width == size['width'] and height == size['height']:
					# If a matching resolution is found, set the dropdown button text to the mode name
					setattr(self.resolution_menu_button, 'text', mode)
					return
		# If no matching resolution is found, set the dropdown button text to "Custom"
		setattr(self.resolution_menu_button, 'text', 'Custom')

	# Function for the img mode dropdown, called upon clicking a valid resolution button
	def set_size(self, mode, width_input, height_input, img_dropdown):
		mode_data = None
		for category in RESOLUTIONS.values():
			if mode in category:
				mode_data = category[mode]
				break
		if mode_data is None:
			return

		width_input.text = str(mode_data['width'])
		height_input.text = str(mode_data['height'])
		img_dropdown.dismiss()
		setattr(self.resolution_menu_button, 'text', str(mode))

# Popup for configuring settings
class ConfigWindow(Popup):
	def process_token(self, instance):
		token = self.token_input.text
		match = re.search(r'"auth_token":"([^"]+)"', token)
		if match:
			token = match.group(1)
		result = generate_as_is('',token,'',token_test=True)
		if result == 'Success':
			self.token_input.text = token
			token_file_content = f"""#Only the access token goes into this file. Do not share it with anyone else as that's against NAI ToS. Using it on multiple of your own devices is fine.
AUTH='{token}'
"""
			write_config_file('4.Token(DO NOT SHARE)',token_file_content)
			self.update_token_state(None, result)
			update_global_img_gen('AUTH', token)
			#print(f'Token test successful.')
		else:
			self.update_token_state(None, result)
			#print(f'Invalid access token. Please retry setting your access token or check your internet connection.')
			return

	def update_token_state(self,instance,state):
		if state=='Success':
			self.token_state._update_color(None, [0,1,0,1])
			self.token_state.text = '✔️'
		else:
			self.token_state._update_color(None, [1,0,0,1])
			self.token_state.text = '❌'

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		# Set up and add all the elements for the theme configurator
		layout = BoxLayout(orientation='vertical')
		
		#layout.add_widget(ColorPickerDropDown(options=THEME))
		theme_example_layout = GridLayout(cols=2)
		
		# Set up and add all the necessary elements for token handling
		token_button = Button(text='Set token (DO NOT SHARE):', on_release=self.process_token, size_hint=(1,None), size=(100,field_height))
		self.token_state = BGLabel(font_name='NotoEmoji', text='❔', background_color=[0.5, 0.5, 0.5, 1], size_hint=(None,None), size=(field_height,field_height))
		token_layout = BoxLayout(orientation='horizontal')
		self.token_input = TextInput(text=AUTH, multiline=False, size_hint=(1,None), size=(100+field_height,field_height))
		token_layout.add_widget(token_button)
		token_layout.add_widget(self.token_state)
		token_layout.add_widget(self.token_input)
		layout.add_widget(token_layout)
		
		self.content = layout

# Classes for the theme configurator
class ThemeButton(Button):
	def __init__(self, starting_color, **kwargs):
		super().__init__(**kwargs)
		self.bind(size=self._update_rect, pos=self._update_rect)
	
	#Will be called once upon opening the dropdown and initializing these buttons
	def _update_rect(self, instance, value):
		self.canvas.before.clear()
		with self.canvas.before:
			Color(*self.associated_dict['value'])
			self.rect = Rectangle(pos=[self.pos[0]+self.size[0]+10,self.pos[1]+10], size=[30,30])
			self.border1 = Line(rectangle=[self.rect.pos[0]-2, self.rect.pos[1]-2, self.rect.size[0]+4, self.rect.size[1]+4], width=2)
			self.border2 = Line(rectangle=[self.rect.pos[0]-4, self.rect.pos[1]-4, self.rect.size[0]+8, self.rect.size[1]+8], width=2)
			Color(0, 0, 0)
			self.border3 = Line(rectangle=[self.rect.pos[0]-6, self.rect.pos[1]-6, self.rect.size[0]+12, self.rect.size[1]+12], width=2)
			Color(1, 1, 1)
			self.border4 = Line(rectangle=[self.rect.pos[0]-8, self.rect.pos[1]-8, self.rect.size[0]+16, self.rect.size[1]+16], width=2)
		
	def set_color(self, rgba):
		# update the color of the rectangle
		self.canvas.before.clear()
		with self.canvas.before:
			Color(*rgba)
			self.rect = Rectangle(pos=[self.pos[0]+self.size[0]+10,self.pos[1]+10], size=[30,30])
			self.border1 = Line(rectangle=[self.rect.pos[0]-2, self.rect.pos[1]-2, self.rect.size[0]+4, self.rect.size[1]+4], width=2)
			self.border2 = Line(rectangle=[self.rect.pos[0]-4, self.rect.pos[1]-4, self.rect.size[0]+8, self.rect.size[1]+8], width=2)
			Color(0, 0, 0)
			self.border3 = Line(rectangle=[self.rect.pos[0]-6, self.rect.pos[1]-6, self.rect.size[0]+12, self.rect.size[1]+12], width=2)
			Color(1, 1, 1)
			self.border4 = Line(rectangle=[self.rect.pos[0]-8, self.rect.pos[1]-8, self.rect.size[0]+16, self.rect.size[1]+16], width=2)
class ColorPickerDropDown(BoxLayout):
	def __init__(self, options, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'vertical'
		self.options = options
		self.dropdown = DropDown()
		self.color_picker = ColorPicker()
		self.color_picker.bind(color=self._on_color_picker_color)
		self.dropdown_button = Button(text='', on_release=self.dropdown.open, size_hint=(1,None), height=field_height)
		first=True
		for option in self.options:
			option_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
			color_button = ThemeButton(text=option["name"], starting_color=option["value"], size_hint_x=None, width=250)
			color_button.associated_dict=option

			option_box.add_widget(color_button)
			self.dropdown.add_widget(option_box)

			color_button.bind(on_release=lambda btn: self.dropdown.select(color_button))
			color_button.bind(on_release=lambda btn, option=option: self._on_option_button_press(option,btn))
			if first:
				self._on_option_button_press(options[0],color_button)
				first=False

		self.add_widget(self.dropdown_button)
		self.add_widget(self.color_picker)
		

	def _on_option_button_press(self, option, button):
		self.selected_option = button
		self.color_picker.color = option["value"]
		self.dropdown_button.text = option["name"]

	def _on_color_picker_color(self, instance, selected_color):
		self.selected_option.set_color(selected_color)
		self.selected_option.associated_dict["value"]=selected_color

# The main app
class ImageGeneratorTasker(App):
	# Checks the attached list for newly generated image paths
	def update_preview(self, time):
		try:
			new_image = PREVIEW_QUEUE.pop()
			self.preview.load_image(new_image)
		except:
			pass

	# Function to enable file dropping
	def _on_file_drop(self, window, file_path, x, y):
		import win32api
		import win32con
		import win32gui
		hwnd = win32gui.GetActiveWindow()
		win32api.SendMessage(hwnd, win32con.WM_USER + 10, 50, 0)
		file_path=file_path.decode()
		# Check if file is a python file or image
		try:
			if str(file_path).endswith('.py'):
				print(f'Loading settings from .py file')
				# Open file and read settings dictionary
				with open(file_path, "rb") as f:
					file_text = f.read().decode('utf_16')
					settings = ast.literal_eval(file_text[9:])
					
					if self.name_import.enabled: self.name_input.text = settings["name"]
					if self.folder_name_import.enabled: self.folder_name_input.text = settings["folder_name"]
					if self.enumerator_plus_import.enabled: self.enumerator_plus_input.text = settings["enumerator_plus"]
					if self.model_import.enabled: self.model_button.text = settings["model"]
					if self.steps_import.enabled: 
						if type(settings["steps"]) == list:
							self.steps_slider_min.value = str(settings["steps"][0])
							self.steps_slider_max.value = str(settings["steps"][1])
						else:
							self.steps_slider_min.value = str(settings["steps"])
							self.steps_slider_max.value = str(settings["steps"])
					if self.scale_import.enabled:
						if type(settings["scale"]) == list:
							self.scale_input_min.text = str(settings["scale"][0])
							self.scale_input_max.text = str(settings["scale"][1])
						else:
							self.scale_input_min.text = str(settings["scale"])
							self.scale_input_max.text = str(settings["scale"])
					if self.resolution_import.enabled: 
						self.resolution_selector.resolution_width.text = str(settings["img_mode"]["width"])
						self.resolution_selector.resolution_height.text = str(settings["img_mode"]["height"])
					if self.prompt_import.enabled:
						if type(settings["prompt"])!=str:
							self.prompt_f.enabled = True
							self.prompt_f_input.load_prompts(settings["prompt"])
						else:
							self.prompt_f.enabled = False
							self.prompt_input.text = str(settings["prompt"])
					if self.uc_import.enabled:
						if type(settings["UC"])!=str:
							self.uc_f.enabled = True
							if settings.get('negative_prompt'):
								self.uc_f_input.load_prompts(settings["negative_prompt"])
							else:
								self.uc_f_input.load_prompts(settings["UC"])
						else:
							self.uc_f.enabled = False
							if settings.get('negative_prompt'):
								self.uc_input.text = settings["negative_prompt"]
							else:
								self.uc_input.text = settings["UC"]

					if settings.get('collage_dimensions'):
						self.mode_switcher.switch_cc('')
						if self.cc_dim_import.enabled: 
							self.cc_dim_width.text = str(settings["collage_dimensions"][0])
							self.cc_dim_height.text = str(settings["collage_dimensions"][1])
						if self.cc_seed_import.enabled: self.cc_seed_grid.load_seeds(settings["seed"])
						if type(settings["sampler"]) == list and self.cc_sampler_import.enabled:
							self.cc_sampler_input.text = ', '.join(settings["sampler"][0])
						elif self.cc_sampler_import.enabled:
							self.cc_sampler_input.text = settings["sampler"]
					else:
						self.mode_switcher.switch_is('')
						if self.is_sampler_import.enabled: 
							sampler = settings["sampler"]
							if sampler.endswith('_dyn'):
								self.is_sampler_smea.enabled = True
								self.is_sampler_dyn.enabled = True
								sampler = sampler[:-4]
							elif sampler.endswith('_smea'):
								self.is_sampler_smea.enabled = True
								self.is_sampler_dyn.enabled = False
								sampler = sampler[:-5]
							else:
								self.is_sampler_smea.enabled = False
								self.is_sampler_dyn.enabled = False
							self.is_sampler_button.text = sampler
						if self.is_seed_import.enabled: self.is_seed_input.text = str(settings["seed"])
						if self.is_range_import.enabled:
							self.is_quantity.text = str(settings["quantity"])
							if settings["video"] == 'standard':
								self.is_video.enabled = True
							else:
								self.is_video.enabled = False
							self.is_fps.text = str(settings["FPS"])
				print(f'Loading from .py settings file successful')
					
			elif file_path.endswith('.jpg') or file_path.endswith('.png'):
				print(f'Loading settings from picture detected')
				self.mode_switcher.switch_is('')
				with PILImage.open(file_path) as img:
					metadata = {
					"size": img.size,
					"info": img.info
					}
				comment_dict = json.loads(metadata["info"]["Comment"])
				if self.name_import.enabled: self.name_input.text = os.path.splitext(os.path.basename(file_path))[0]
				# Should be refactored to folder_name_user if at all
				#if self.folder_name_import.enabled: self.folder_name_input.text = os.path.dirname(file_path)
				if self.model_import.enabled:
					if metadata["info"]["Source"] == 'Stable Diffusion 1D09D794' or metadata["info"]["Source"] == 'Stable Diffusion F64BA557': # v1.2/1.3 
						self.model_button.text = 'nai-diffusion-furry'
					elif metadata["info"]["Source"] == 'Stable Diffusion 81274D13' or metadata["info"]["Source"] == 'Stable Diffusion 3B3287AF': # Initial release/silent update with ControlNet
						self.model_button.text = 'nai-diffusion'
					elif metadata["info"]["Source"] == 'Stable Diffusion 1D44365E' or metadata["info"]["Source"] == 'Stable Diffusion F4D50568': # Initial release/silent update with ControlNet
						self.model_button.text = 'safe-diffusion'
					else:
						print(f'Error while determining model, defaulting to Full')
						self.model_button.text = 'nai-diffusion'
				if self.steps_import.enabled: self.steps_slider_min.value = str(comment_dict["steps"])
				if self.scale_import.enabled: self.scale_input_min.text = str(comment_dict["scale"])
				if self.resolution_import.enabled: 
					self.resolution_selector.resolution_width.text = str(metadata["size"][0])
					self.resolution_selector.resolution_height.text = str(metadata["size"][1])
				if self.is_seed_import.enabled: self.is_seed_input.text = str(comment_dict["seed"])
				
				if self.is_sampler_import.enabled:
					sampler_string = str(comment_dict["sampler"])
					if sampler_string == 'nai_smea_dyn':
						self.is_sampler_button.text = 'k_euler_ancestral'
						self.is_sampler_smea.enabled = True
						self.is_sampler_dyn.enabled = True
					elif sampler_string == 'nai_smea':
						self.is_sampler_button.text = 'k_euler_ancestral'
						self.is_sampler_smea.enabled = True
						self.is_sampler_dyn.enabled = False
					else:
						self.is_sampler_button.text = sampler_string
						if comment_dict.get('sm_dyn'):
							if comment_dict["sm_dyn"]:
								self.is_sampler_smea.enabled = True
								self.is_sampler_dyn.enabled = True
						elif comment_dict.get('sm'):
							if comment_dict["sm"]:
								self.is_sampler_smea.enabled = True
								self.is_sampler_dyn.enabled = False
						else:
							self.is_sampler_smea.enabled = False
							self.is_sampler_dyn.enabled = False
				if self.prompt_import.enabled:
					self.prompt_f.enabled = False
					self.prompt_input.text = str(metadata["info"]["Description"])
				if self.uc_import.enabled:
					self.uc_f.enabled = False
					self.uc_input.text = comment_dict["uc"]
				print(f'Loading from picture successful')
			else:
				# Ignore file if it doesn't meet the requirements
				print(f'Unusable file detected (drop a .py, .png or .jpg file)')
		except Exception as e:
			import traceback
			traceback.print_exc()
		return
		
	# Functions needed for the steps slider
	def on_steps_value_change_min(self, instance, value):
		self.steps_counter_min.text = str(int(value))
	def on_steps_value_change_max(self, instance, value):
		self.steps_counter_max.text = str(int(value))
		
	def build(self):
		# Binding the file dropping function
		Window.bind(on_drop_file=self._on_file_drop)
		Window.size = (1850, 1000)
		Window.clearcolor = THEME[3]['value']
		self.config_window = ConfigWindow(title='Configure Settings')
		layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

		# Mode Switcher
		mode_label = Label(text='Mode:', **l_row_size1, **label_color)
		settings_button = Button(text='⚙️', font_size=font_large, on_release=self.config_window.open, **imp_row_size1, **button_colors)
		settings_button.font_name = 'NotoEmoji'
		self.mode_switcher = ModeSwitcher(app=self, size_hint=(1, None), size=(100, field_height))
	
		# Name
		name_label = Label(text='Name:', **l_row_size1, **label_color)
		self.name_import = ImportButton(**imp_row_size1)
		self.name_input = TextInput(multiline=False, size_hint=(1, None), size=(100, field_height), **input_colors)

		# Folder Name
		folder_name_label = Label(text='Folder Name:', **l_row_size1, **label_color)
		self.folder_name_import = ImportButton(**imp_row_size1)
		self.folder_name_input = TextInput(multiline=False, size_hint=(1, None), size=(100, field_height), **input_colors)

		# Enumerator Plus
		enumerator_plus_label = Label(text='Enumerator Plus:', **l_row_size1, **label_color)
		self.enumerator_plus_import = ImportButton(**imp_row_size1)
		self.enumerator_plus_input = TextInput(multiline=False, size_hint=(1, None), size=(100, field_height), **input_colors)

		# Model
		self.model_label = Label(text='Model:', **l_row_size1, **label_color)
		self.model_import = ImportButton(**imp_row_size1)
		
		self.model_dropdown = DropDown()
		self.model_button = ScrollDropDownButton(self.model_dropdown, text='nai-diffusion', size_hint=(1, None), size=(100, field_height), **button_colors)
		self.model_button.bind(on_release=self.model_dropdown.open)

		for model_name in MODELS.values():
			btn = Button(text=model_name, size_hint_y=None, height=field_height, **dp_button_colors)
			btn.bind(on_release=lambda btn: self.model_dropdown.select(btn.text))
			self.model_dropdown.add_widget(btn)
		self.model_dropdown.bind(on_select=lambda instance, x: setattr(self.model_button, 'text', x))

		# Seed - Cluster Collage
		cc_seed_label = Label(text='Seed:', **l_row_size2, **label_color)
		self.cc_seed_import = ImportButton(**imp_row_size2)
		self.cc_seed_grid=SeedGrid(size_hint=(1, 1))

		# Seed - Image Sequence
		is_seed_label = Label(text='Seed:', **l_row_size1, **label_color)
		self.is_seed_import = ImportButton(**imp_row_size1)
		is_seed_randomize = Button(text='Randomize', size_hint=(None, None), size=(100, field_height), **button_colors)
		self.is_seed_input = ScrollInput(min_value=0, max_value=4294967295, text='', multiline=False, size_hint=(1, None), size=(100, field_height), allow_empty=True, **input_colors)
		is_seed_randomize.bind(on_release=lambda btn: setattr(self.is_seed_input, 'text', str(generate_seed())))
		is_seed_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		is_seed_layout.add_widget(is_seed_randomize)
		is_seed_layout.add_widget(self.is_seed_input)

		# Steps
		steps_label = Label(text='Steps:', **l_row_size1, **label_color)
		self.steps_import = ImportButton(**imp_row_size1)
		steps_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		self.steps_slider_min = Slider(min=1, max=50, value=28, step=1)
		self.steps_counter_min = Label(text=str(28), size_hint=(None, None), size=(50, field_height), **label_color)
		self.steps_slider_max = Slider(min=1, max=50, value=28, step=1)
		self.steps_counter_max = Label(text=str(28), size_hint=(None, None), size=(50, field_height), **label_color)
		self.steps_slider_min.bind(value=self.on_steps_value_change_min)
		self.steps_slider_max.bind(value=self.on_steps_value_change_max)
		steps_layout.add_widget(self.steps_slider_min)
		steps_layout.add_widget(self.steps_counter_min)
		steps_layout.add_widget(self.steps_slider_max)
		steps_layout.add_widget(self.steps_counter_max)

		# Scale
		scale_label = Label(text='Scale:', **l_row_size1, **label_color)
		self.scale_import = ImportButton(**imp_row_size1)
		scale_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), size=(400, field_height))
		#The API actually accepts much, much higher scale values, though there really seems no point in going higher than 100 at all
		self.scale_input_min = ScrollInput(min_value=1.1, max_value=100, fi_mode=float, increment=0.1, text='10', multiline=False, size_hint=(1, None), size=(100, field_height), **input_colors, font_size=font_small)
		self.scale_input_max = ScrollInput(min_value=1.1, max_value=100, fi_mode=float, increment=0.1, text='10', multiline=False, size_hint=(1, None), size=(100, field_height), **input_colors, font_size=font_small)
		scale_layout.add_widget(self.scale_input_min)
		scale_layout.add_widget(self.scale_input_max)

		# Sampler - Cluster Collage
		cc_sampler_label = Label(text='Sampler:', size_hint = (None, None), size = (170, field_height*2), **label_color)	
		self.cc_sampler_import = ImportButton(size_hint = (None, None), size = (field_height, field_height*2))
		self.cc_sampler_input = TextInput(multiline=True, size_hint=(1, 1), height=field_height*2, **input_colors)
		cc_clear_button = Button(text='Clear', size_hint=(None, 1), size=(60, field_height*2), **button_colors)
		cc_clear_button.bind(on_release=lambda button: setattr(self.cc_sampler_input, 'text', ''))
		cc_sampler_button = Button(text='Add Sampler', size_hint=(None, 1), size=(150, field_height*2), **button_colors)

		cc_sampler_injector = ConditionalInjectorDropdown(size_hint=(None, 1), width=field_height, dropdown_list=NAI_SAMPLERS, button_text='+', target=self.cc_sampler_input, inject_identifier='S')
		cc_sampler_dropdown = DropDown()

		cc_sampler_layout = BoxLayout(orientation='horizontal',size_hint=(1, None), height=field_height*2)
		cc_sampler_layout.add_widget(self.cc_sampler_input)
		cc_sampler_layout.add_widget(cc_clear_button)
		cc_sampler_layout.add_widget(cc_sampler_injector)

		# Sampler - Image Sequence
		is_sampler_label = Label(text='Sampler:', **l_row_size1, **label_color)		
		self.is_sampler_import = ImportButton(**imp_row_size1)
		is_sampler_dropdown = DropDown()
		self.is_sampler_button = ScrollDropDownButton(is_sampler_dropdown, text='k_dpmpp_2m', size_hint=(1, None), size=(100, field_height), **button_colors)
		self.is_sampler_button.bind(on_release=is_sampler_dropdown.open)
		for sampler_name in NAI_SAMPLERS_RAW:
			btn = Button(text=sampler_name, size_hint_y=None, height=field_height, **dp_button_colors)
			btn.bind(on_release=lambda btn: is_sampler_dropdown.select(btn.text))
			is_sampler_dropdown.add_widget(btn)
		is_sampler_dropdown.bind(on_select=lambda instance, x: setattr(self.is_sampler_button, 'text', x))
		
		is_sampler_layout = BoxLayout(orientation='horizontal',size_hint=(1, None), height=field_height)
		self.is_sampler_smea = StateShiftButton(text='SMEA', size_hint=(None, 1), size=(80,field_height))
		self.is_sampler_dyn = StateShiftButton(text='Dyn', size_hint=(None, 1), size=(80,field_height))

		self.is_sampler_smea.bind(enabled=lambda instance, value: on_smea_disabled(value, self.is_sampler_dyn))
		self.is_sampler_dyn.bind(enabled=lambda instance, value: on_dyn_enabled(value, self.is_sampler_smea))
		is_sampler_layout.add_widget(self.is_sampler_button)
		is_sampler_layout.add_widget(self.is_sampler_smea)
		is_sampler_layout.add_widget(self.is_sampler_dyn)

		# Resolution
		resolution_label = Label(text='Resolution:', **l_row_size1, **label_color)
		self.resolution_import = ImportButton(**imp_row_size1)
		self.resolution_selector = ResolutionSelector()

		# Prompt
		prompt_label = Label(text='Prompt:', **l_row_size2, **label_color)
		prompt_buttons_layout = BoxLayout(orientation='vertical', **imp_row_size2)
		self.prompt_import = ImportButton()
		self.prompt_input = TextInput(multiline=True, size_hint=(1, 1), size=(100, field_height*4), **input_colors)
		self.prompt_input.font_size = 23
		self.prompt_input.font_name = 'Unifont'
		prompt_injector = InjectorDropdown(dropdown_list=PROMPT_CHUNKS, button_text='+', target=self.prompt_input)
		
		prompt_buttons_layout.add_widget(prompt_injector)
		prompt_buttons_layout.add_widget(self.prompt_import)
		
		prompt_layout = BoxLayout(orientation='horizontal')
		prompt_token_counter=TokenCostBar(clip_calculator, MAX_TOKEN_COUNT, size_hint=(None, 1), width=20)
		prompt_layout.add_widget(self.prompt_input)
		prompt_layout.add_widget(prompt_token_counter)
		self.prompt_input.bind(text=prompt_token_counter.calculate_token_cost)
		# Create the f-string variant
		self.prompt_f_input = PromptGrid(size_hint=(1, 1), size=(100, field_height*4))
		self.prompt_f = StateFButton(self.mode_switcher, self.prompt_input, self.prompt_f_input.prompt_inputs[0], prompt_injector)
		prompt_layout.add_widget(self.prompt_f_input)
		self.prompt_f.standard_widgets = prompt_layout.children[1:]
		self.prompt_f.f_widgets = [prompt_layout.children[0]]
		self.mode_switcher.hide_widgets([prompt_layout.children[0]])
		prompt_buttons_layout.add_widget(self.prompt_f)

		# UC
		uc_label = Label(text='Undesired Content:', **l_row_size2, **label_color)
		uc_buttons_layout = BoxLayout(orientation='vertical', **imp_row_size2)
		self.uc_import = ImportButton()
		self.uc_input = TextInput(multiline=True, size_hint=(1, 1), size=(100, field_height*4), **input_colors)
		self.uc_input.font_size = 23
		self.uc_input.font_name = 'Unifont'
		uc_injector = InjectorDropdown(dropdown_list=UC_CHUNKS, button_text='+', target=self.uc_input, inject_identifier='UC')
		
		uc_buttons_layout.add_widget(uc_injector)
		uc_buttons_layout.add_widget(self.uc_import)
		
		uc_layout = BoxLayout(orientation='horizontal')
		uc_token_counter=TokenCostBar(clip_calculator, MAX_TOKEN_COUNT, size_hint=(None, 1), width=20)
		uc_layout.add_widget(self.uc_input)
		uc_layout.add_widget(uc_token_counter)
		self.uc_input.bind(text=uc_token_counter.calculate_token_cost)
		# Create the f-string variant
		self.uc_f_input = PromptGrid(size_hint=(1, 1), size=(100, field_height*4))
		self.uc_f = StateFButton(self.mode_switcher, self.uc_input, self.uc_f_input.prompt_inputs[0], uc_injector)
		uc_layout.add_widget(self.uc_f_input)
		self.uc_f.standard_widgets = uc_layout.children[1:]
		self.uc_f.f_widgets = [uc_layout.children[0]]
		self.mode_switcher.hide_widgets([uc_layout.children[0]])
		uc_buttons_layout.add_widget(self.uc_f)

		# Collage Dimensions
		cc_dim_label = Label(text='Collage Dimensions:', **l_row_size1, **label_color)
		self.cc_dim_import = ImportButton(**imp_row_size1)
		cc_dim_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.cc_dim_width = ScrollInput(text='3', size_hint=(1, None), width=60, height=field_height, **input_colors)
		self.cc_dim_height = ScrollInput(text='3', size_hint=(1, None), width=60, height=field_height, **input_colors)
		cc_dim_layout.add_widget(self.cc_dim_width)
		cc_dim_layout.add_widget(self.cc_dim_height)

		# Image Sequence Quantity
		is_range_label = Label(text='Image Sequence Range:', **l_row_size1, **label_color)
		self.is_range_import = ImportButton(**imp_row_size1)
		is_range_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.is_quantity = ScrollInput(text='28', min_value=1, max_value=100000, size_hint=(1, None), width=60, height=field_height, **input_colors)
		self.is_video = StateShiftButton(text='🎬',font_name='NotoEmoji')
		is_range_layout.add_widget(self.is_quantity)
		is_range_layout.add_widget(self.is_video)
		is_fps_label = Label(text='FPS:', size_hint=(None, None), size=(60,field_height), **label_color)
		self.is_fps = ScrollInput(text=str(BASE_FPS), min_value=7, max_value=144, size_hint=(1, None), width=60, height=field_height, **input_colors)
		is_range_layout.add_widget(is_fps_label)
		is_range_layout.add_widget(self.is_fps)

		# Action buttons
		action_buttons_label = Label(text='Create images:', **l_row_size1, **label_color)
		action_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.single_img_button = Button(text='Generate Image', size_hint=(1, None), height=field_height, **button_colors)
		self.single_img_button.bind(on_release=self.generate_single_image)
		self.queue_button = Button(text='Queue Task', size_hint=(1, None), height=field_height, **button_colors)
		self.queue_button.bind(on_release=self.on_queue_button_press)
		self.process_button = Button(text='Process Tasks', size_hint=(1, None), height=field_height, **button_colors)
		self.process_button.bind(on_release=self.on_process_button_press)
		action_buttons_layout.add_widget(self.single_img_button)
		action_buttons_layout.add_widget(self.queue_button)
		action_buttons_layout.add_widget(self.process_button)

		# Cancel buttons
		cancel_buttons_label = Label(text='Cancel/Wipe:', **l_row_size1, **label_color)
		cancel_buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.wipe_queue_button = Button(text='Wipe Queue', size_hint=(1, None), height=field_height, **button_colors)
		self.wipe_queue_button.bind(on_release=wipe_queue)
		self.cancel_button = Button(text='Cancel Processing', size_hint=(1, None), height=field_height, **button_colors)
		self.cancel_button.bind(on_release=cancel_processing)
		cancel_buttons_layout.add_widget(self.wipe_queue_button)
		cancel_buttons_layout.add_widget(self.cancel_button)

		# Add all elements to layout, which is the primary block for interactions on the left, split into the label/button/input columns
		input_layout = GridLayout(cols=3)
		input_layout.add_widget(mode_label)
		input_layout.add_widget(settings_button)
		input_layout.add_widget(self.mode_switcher)

		input_layout.add_widget(name_label)
		input_layout.add_widget(self.name_import)
		input_layout.add_widget(self.name_input)

		input_layout.add_widget(folder_name_label)
		input_layout.add_widget(self.folder_name_import)
		input_layout.add_widget(self.folder_name_input)

		#input_layout.add_widget(enumerator_plus_label)
		#input_layout.add_widget(self.enumerator_plus_import)
		#input_layout.add_widget(self.enumerator_plus_input)

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
		input_layout.add_widget(steps_layout)	

		input_layout.add_widget(scale_label)
		input_layout.add_widget(self.scale_import)
		input_layout.add_widget(scale_layout)

		input_layout.add_widget(cc_sampler_label)
		input_layout.add_widget(self.cc_sampler_import)
		input_layout.add_widget(cc_sampler_layout)

		input_layout.add_widget(is_sampler_label)
		input_layout.add_widget(self.is_sampler_import)
		input_layout.add_widget(is_sampler_layout)		

		input_layout.add_widget(resolution_label)
		input_layout.add_widget(self.resolution_import)
		input_layout.add_widget(self.resolution_selector)

		input_layout.add_widget(prompt_label)
		input_layout.add_widget(prompt_buttons_layout)
		input_layout.add_widget(prompt_layout)

		input_layout.add_widget(uc_label)
		input_layout.add_widget(uc_buttons_layout)
		input_layout.add_widget(uc_layout)

		input_layout.add_widget(cc_dim_label)
		input_layout.add_widget(self.cc_dim_import)
		input_layout.add_widget(cc_dim_layout)

		input_layout.add_widget(is_range_label)
		input_layout.add_widget(self.is_range_import)
		input_layout.add_widget(is_range_layout)

		input_layout.add_widget(action_buttons_label)
		input_layout.add_widget(Label(text='',size_hint=(None, None),size=(0,0)))
		input_layout.add_widget(action_buttons_layout)

		input_layout.add_widget(cancel_buttons_label)
		input_layout.add_widget(Label(text='',size_hint=(None, None),size=(0,0)))
		input_layout.add_widget(cancel_buttons_layout)

		# The super_layout is highest layout in the hierarchy and this also the one that is returned.
		# It has the user interaction section left, the console/metadata section in the middle, and the image preview on the right
		
		console = Console()
		
		task_counter_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		
		meta_layout = BoxLayout(orientation='vertical', size_hint=(0.5, 1))
		meta_layout.add_widget(console)
		
		self.preview = ImagePreview()
		
		self.super_layout = BoxLayout(orientation='horizontal')
		self.super_layout.add_widget(input_layout)
		self.super_layout.add_widget(meta_layout)
		self.super_layout.add_widget(self.preview)

		self.cc_exclusive_widgets = [cc_seed_label,self.cc_seed_grid,cc_sampler_label,cc_sampler_layout,cc_dim_label,cc_dim_layout,
			self.cc_seed_import,self.cc_sampler_import,self.cc_dim_import]
		self.is_exclusive_widgets = [is_sampler_label,is_sampler_layout,is_seed_label,is_seed_layout,is_range_label, is_range_layout,
			self.is_seed_import,self.is_sampler_import, self.is_range_import]
		self.import_buttons = [self.name_import, self.folder_name_import, self.enumerator_plus_import, self.model_import, self.cc_seed_import, self.is_seed_import,
			self.steps_import, self.scale_import, self.cc_sampler_import, self.is_sampler_import, self.resolution_import, self.prompt_import, self.uc_import,
			self.cc_dim_import, self.is_range_import]

		self.mode_switcher.hide_widgets(self.is_exclusive_widgets)
		Clock.schedule_interval(self.update_preview, 0.2)
		self.cancel_button.disabled = True
		return self.super_layout

	def on_queue_button_press(self, instance):
		# Get shared settings from text inputs and sliders
		name = self.name_input.text
		folder_name = self.folder_name_input.text
		enumerator_plus = self.enumerator_plus_input.text
		model = self.model_button.text
		steps = [int(self.steps_slider_min.value),(self.steps_slider_max.value)]
		if steps[0] == steps[1]:
			steps=steps[0]
		scale = [float(self.scale_input_min.text), float(self.scale_input_max.text)]
		if scale[0] == scale[1]:
			scale=scale[0]
		img_mode = {'width': int(self.resolution_selector.resolution_width.text),
								'height': int(self.resolution_selector.resolution_height.text)}
		if self.prompt_f.enabled:
			if self.prompt_f_input.prompt_inputs[0].text == '':
				print("Prompt field can't be empty! Task not added.")
				return
			prompt = [['f"""' + self.prompt_f_input.prompt_inputs[i].text + '"""'] for i in range(self.prompt_f_input.prompt_rows)]
		else:
			if self.prompt_input.text == '':
				print("Prompt field can't be empty! Task not added.")
				return
			prompt = self.prompt_input.text
		if self.uc_f.enabled:
			uc = [['f"""' + self.uc_f_input.prompt_inputs[i].text + '"""'] for i in range(self.uc_f_input.prompt_rows)]
		else:
			uc = self.uc_input.text
		
		settings = {'name': name, 'folder_name': folder_name, 'enumerator_plus': enumerator_plus, 'model': model, 'scale': scale, 'steps': steps, 'img_mode': img_mode,
		'prompt': prompt, 'UC': uc}

		if self.mode_switcher.cc_active: # Cluster collage specific settings
			seeds = [[self.cc_seed_grid.seed_inputs[j+i*int(self.cc_seed_grid.seed_cols_input.text)].text for j in range(int(self.cc_seed_grid.seed_cols_input.text))] for i in range(int(self.cc_seed_grid.seed_rows_input.text))]
			seed = [[str(generate_seed()) if value == '' else value for value in inner_list] for inner_list in seeds]
			if self.cc_sampler_input.text == '':
				print("Sampler field can't be empty! Task not added.")
				return
			if self.cc_sampler_input.text.__contains__(','):
				sampler = [list(filter(None, self.cc_sampler_input.text.split(", "))),'']
			else:
				sampler = self.cc_sampler_input.text
			collage_dimensions = [int(self.cc_dim_width.text), int(self.cc_dim_height.text)]
			settings.update({'seed': seed, 'sampler': sampler, 'collage_dimensions': collage_dimensions})
			prompt_stabber(settings, img_save_mode='Resume')
		else: # Image sequence specific settings
			if not self.is_seed_input.text == '':
				seed = self.is_seed_input.text
			else:
				seed = str(generate_seed())
			sampler = self.is_sampler_button.text
			if self.is_sampler_dyn.enabled:
				sampler+='_dyn'
			elif self.is_sampler_smea.enabled:
				sampler+='_smea'
			quantity = int(self.is_quantity.text)
			if self.is_video.enabled:
				video = 'standard'
			else:
				video = ''
			settings.update({'seed': int(seed), 'sampler': sampler, 'quantity': quantity, 'video': video, 'FPS': int(self.is_fps.text)})
			render_loop(settings, img_save_mode='Resume')
		print(settings)
	def generate_single_image(self, instance):
		self.single_img_button.disabled = True
		self.queue_button.disabled = True
		self.process_button.disabled = True
		self.wipe_queue_button.disabled = True
		
		if self.mode_switcher.cc_active:
			if not self.cc_seed_grid.seed_inputs[0].text == '':
				seed = self.cc_seed_grid.seed_inputs[0].text
			else:
				seed = str(generate_seed())
			if self.cc_sampler_input.text.__contains__(','):
				sampler = self.cc_sampler_input.text.split(", ")[0]
			else:
				sampler = self.cc_sampler_input.text
		else:
			if not self.is_seed_input.text == '':
				seed = self.is_seed_input.text
			else:
				seed = str(generate_seed())
			sampler = self.is_sampler_button.text
			if self.is_sampler_dyn.enabled:
				sampler+='_dyn'
			elif self.is_sampler_smea.enabled:
					sampler+='_smea'
		settings = {'name': self.name_input.text,
		'folder_name': self.folder_name_input.text,
		'folder_name_extra': '',
		'enumerator_plus': self.enumerator_plus_input.text,
		'model': self.model_button.text,
		'seed': int(seed),
		'sampler': sampler,
		'scale': float(self.scale_input_min.text),
		'steps': int(self.steps_slider_min.value),
		'img_mode': {'width': int(self.resolution_selector.resolution_width.text),
								'height': int(self.resolution_selector.resolution_height.text)},
		'prompt': self.prompt_input.text,
		'UC': self.uc_input.text}
		
		print(settings)
		future = EXECUTOR.submit(generate_as_is,settings,'')
		future.add_done_callback(self.on_process_complete)

	def on_process_button_press(self, instance):	
		global PREVIEW_QUEUE, FUTURE
		self.single_img_button.disabled = True
		self.queue_button.disabled = True
		self.process_button.disabled = True
		self.wipe_queue_button.disabled = True
		self.cancel_button.disabled = False
		try:
			FUTURE = EXECUTOR.submit(process_queue,preview=PREVIEW_QUEUE)
			FUTURE.add_done_callback(self.on_process_complete)
		except Exception as e:
			import traceback
			traceback.print_exc()
			self.on_process_complete(None,immediate_preview=False)
			PREVIEW_QUEUE=[]
			print('Task queue has been wiped due to an exception')

	def on_process_complete(self, future, immediate_preview=True):
		try:
			if immediate_preview and future.result() != 'Error':
				PREVIEW_QUEUE.append(future.result())
		except Exception as e:
			import traceback
			traceback.print_exc()
		self.single_img_button.disabled = False
		self.queue_button.disabled = False
		self.process_button.disabled = False
		self.wipe_queue_button.disabled = False
		self.cancel_button.disabled = True

if __name__ == '__main__':
	ImageGeneratorTasker().run()