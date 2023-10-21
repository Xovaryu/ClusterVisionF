"""
kivy_widgets.py
	This module contains all the kivy classes that are used to build the UI

01.	FTextInput
			Extends TextInput with a key combination that allows quick insertion of the special f-string braces
02.	ScrollInput
			Significantly upgrades TextInput with the ability to scroll number when hovering if there are only scrollable numbers present
03.	FScrollInput
			Has the extras of both classes above
04.	ComboCappedScrollInput
			A class used for special ScrollInputs that are linked to a collective maximum value
05.	SeedScrollInput
			This class adds clear/randomize functionality when pressing c/r for use in seed fields
06.	TokenCostBar
			Used to calculate how many tokens have been used relative to what the model supports (at least it should do so eventually)
07.	ImagePreview
			This class shows generated images in the UI
08.	DoubleEmojiButton + ImportButton + PauseButton
			These classes are buttons using emojis to make their use and state quickly apparent
09.	StateShiftButton
			Similar to the classes above but with definable text instead
10.	InjectorDropdown + ConditionalInjectorDropdown
			This class creates a dropdown that is tied to a text field and can inject it's valuees, the conditional variant supports on/off buttons in the dropdown
11.	ScrollDropDownButton
			This is just a slightly more advanced dropdown button that supports scrolling when hovering
12.	ModeSwitcher
			This class makes the 3 mode buttons at the top of the GUI and tracks the state for other functions to use
13.	SeedGrid
			This is a complex class that creates a grid of text fields for seeds to be used in cluster collages
14.	PromptGrid
			Somewhat similar to above this is used for f-string prompts to allow splitting the text field for conveniences
15.	Console
			A class made to expose console outputs right in the UI
16.	BGLabel
			A simple class that adds a colorable background to a Label
17.	ResolutionSelector
			A class that makes a complete resolution selector and loads available resolutions and their names from the user settings
18.	FileHandlingWindow
			A popup for setting f-strings according to which file strings are built
19.	ConfigWindow
			A popup for various settings
	
"""
from initialization import handle_exceptions, GlobalState, CH
GS = GlobalState()

import sys
import copy
import re
import io
import traceback
import itertools
from PIL import Image as PILImage
import image_generator as IM_G
import text_manipulation as TM
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.effects.dampedscroll import ScrollEffect
from kivy.graphics import Color, Rectangle, Line
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock

###Provisory copy for now
RESOLUTIONS = copy.deepcopy(GS.NAI_RESOLUTIONS)
RESOLUTIONS.update(GS.USER_RESOLUTIONS)
from kivy.core.text import LabelBase
field_height=30
font_hyper=20
font_large=19
font_small=15
input_colors={'foreground_color': GS.THEME["InText"]["value"], 'background_color': GS.THEME["InBg"]["value"]}
label_color={'color': GS.THEME["ProgText"]["value"]}
bg_label_colors={'color': GS.THEME["CatText"]["value"], 'background_color': GS.THEME["CatBg"]["value"]}
button_colors={'color': GS.THEME["MBtnText"]["value"], 'background_color': GS.THEME["MBtnBg"]["value"]}
dp_button_colors={'color': GS.THEME["DBtnText"]["value"], 'background_color': GS.THEME["DBtnBg"]["value"]}

l_row_size1={'size_hint':(None, None),'size':(120, field_height)}
l_row_size2={'size_hint':(None, 1),'size':(120, field_height)}
imp_row_size1={'size_hint':(None, None),'size':(field_height, field_height)}
imp_row_size2={'size_hint':(None, 1),'size':(field_height, field_height)}
#Load in fonts
LabelBase.register(name='Roboto', fn_regular=GS.FULL_DIR + 'Fonts/Roboto-Regular.ttf')
#LabelBase.register(name='Symbola', fn_regular=GS.FULL_DIR + 'Fonts/Symbola.ttf')
LabelBase.register(name='Unifont', fn_regular=GS.FULL_DIR + 'Fonts/unifont_jp-15.0.01.ttf')
#LabelBase.register(name='NotoSansJP', fn_regular=GS.FULL_DIR + 'Fonts/NotoSansJP-VF.ttf')
LabelBase.register(name='NotoEmoji', fn_regular=GS.FULL_DIR + 'Fonts/NotoEmoji-VariableFont_wght.ttf')


# Converts a color in the format kivy uses into a tag that the KW.Console class can use
@handle_exceptions
def rgba_to_string(color):
	return '[color={}{}'.format(''.join(hex(int(c * 255))[2:].zfill(2) for c in color), ']')

# Functions used to link the SMEA and Dyn buttons in such a way that enabling Dyn makes sure SMEA is enabled, and that disabled SMEA disabled Dyn
@handle_exceptions
def on_smea_disabled(value, linked_button):
	if not value:
		linked_button.enabled = False
@handle_exceptions
def on_dyn_enabled(value, linked_button):
	if value:
		linked_button.enabled = True


class FTextInput(TextInput):
	# Checks if a user pressed 8 or 9 with CTRL to insert f braces
	@handle_exceptions
	def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
		if 'ctrl' in modifiers and 'shift' in modifiers and keycode[1] == 'f':
			# Get the current cursor position, add the brace (by rewrtiting the text), and update the cursor position
			cursor = self.cursor
			self.text = self.text[:cursor[0]] + '⁅⁆' + self.text[cursor[0]:]
			self.cursor = (cursor[0] + 1, self.cursor[1])
		return super().keyboard_on_key_down(keyboard, keycode, text, modifiers)
# Input field used for any field with scrolling numbers
class ScrollInput(TextInput):
	@handle_exceptions
	def __init__(self, min_value=1, max_value=100, increment=1, fi_mode=int, round_value=6, allow_empty=False, **kwargs):
		super().__init__(**kwargs)
		self.multiline = False
		self.min_value = min_value
		self.max_value = max_value
		self.increment = increment
		self.round_value = round_value
		if fi_mode == int or fi_mode == float:
			self.fi_mode = fi_mode
			self.input_filter = fi_mode.__name__
			self.hybrid_mode = False
		else:
			self.fi_mode = float
			self.hybrid_mode = True
		self.allow_empty = allow_empty

	# Ensures that the fields only have valid text when losing focus
	@handle_exceptions
	def on_focus(self, instance, value):
		if not value:
			if self.allow_empty:
				if (self.text == ''):
					return
			else:
				if (self.text == ''):
					self.text = format(self.min_value, f'.{self.round_value}f').rstrip('0').rstrip('.')
					return
			if self.hybrid_mode and not str(self.text).replace('.', '', 1).replace('-', '', 1).isdigit():
				return
			try:
				value = self.fi_mode(self.text)
				if value < self.min_value:
					self.text = format(self.min_value, f'.{self.round_value}f').rstrip('0').rstrip('.')
				elif value > self.max_value:
					self.text = format(self.max_value, f'.{self.round_value}f').rstrip('0').rstrip('.')
				else:
					self.text = format(value, f'.{self.round_value}f').rstrip('0').rstrip('.')
			except ValueError:
				# User entered an invalid value, this normally shouldn't be possible
				self.text = format(self.min_value, f'.{self.round_value}f').rstrip('0').rstrip('.')

	@handle_exceptions
	def on_touch_down2(self, touch):
		# First we call the parent on_touch_down function so Kivy can do it's standard work like setting focus to the text field
		super().on_touch_down(touch)
		if not touch.is_mouse_scrolling or not self.collide_point(*touch.pos) or self.text == '' :
			return
		if not str(self.text).replace('.', '', 1).replace('-', '', 1).isdigit():
			return
		if touch.button in ('scrolldown', 'scrollup'):
			if self.selection_text:
				#...
				target_value = self.selection_text
				self.selection_text='FAFAAS'
			
			print (self.selection_text)
			print (self.selection_from)
			print (self.selection_to)
		
		
		keyboard = Window.request_keyboard(None, self)
		if 'alt' in Window._modifiers:
			if 'shift' in Window._modifiers:
				current_increment = self.increment / 1000
			elif 'ctrl' in Window._modifiers:
				current_increment = self.increment / 100
			else:
				current_increment = self.increment / 10
		elif 'shift' in Window._modifiers:
			if 'ctrl' in Window._modifiers:
				current_increment = self.increment * 1000
			else:
				current_increment = self.increment * 100
		elif 'ctrl' in Window._modifiers:
			current_increment = self.increment * 10
		else:
			current_increment = self.increment
		if self.fi_mode == int and current_increment < 1:
			current_increment = 1
		
		
		
		if touch.button == 'scrolldown':
			#self.text = format(min(self.fi_mode(self.text) + current_increment,self.max_value), f'.{self.round_value}f').rstrip('0').rstrip('.')
			pass
		elif touch.button == 'scrollup':
			#self.text = format(max(self.fi_mode(self.text) - current_increment,self.min_value), f'.{self.round_value}f').rstrip('0').rstrip('.')
			pass

	@handle_exceptions
	def calculate_increment(self):
		keyboard = Window.request_keyboard(None, self)
		if 'alt' in Window._modifiers:
			if 'shift' in Window._modifiers:
				current_increment = self.increment / 1000
			elif 'ctrl' in Window._modifiers:
				current_increment = self.increment / 100
			else:
				current_increment = self.increment / 10
		elif 'shift' in Window._modifiers:
			if 'ctrl' in Window._modifiers:
				current_increment = self.increment * 1000
			else:
				current_increment = self.increment * 100
		elif 'ctrl' in Window._modifiers:
			current_increment = self.increment * 10
		else:
			current_increment = self.increment
		if self.fi_mode == int and current_increment < 1:
			current_increment = 1
		return current_increment

	@handle_exceptions
	def on_touch_down(self, touch):
		# Call the parent on_touch_down function for Kivy's standard behavior
		super().on_touch_down(touch)
		if not touch.is_mouse_scrolling or not self.collide_point(*touch.pos) or not self.text:
			return
		
		if touch.button in ('scrolldown', 'scrollup'):
			if self.selection_text:
				# Text is selected, adjust the selected part
				
				try:
					value = self.fi_mode(self.selection_text)

					# Determine the selected range direction
					if self.selection_from < self.selection_to:
						start, end = self.selection_from, self.selection_to
					else:
						start, end = self.selection_to, self.selection_from

					increment = self.calculate_increment()
					new_value = value + increment if touch.button == 'scrolldown' else value - increment
					new_value = min(max(new_value, self.min_value), self.max_value)

					# Replace the selected text with the new value
					self.text = self.text[:start] + str(new_value) + self.text[end:]

					# Maintain the selection with adjusted indexes
					self.select_text(start, start + len(str(new_value)))
				except ValueError:
					pass

			else:
				# No text selected, adjust the value

				try:
					value = self.fi_mode(self.text)
					overwrite_text = True
				except ValueError:
					overwrite_text = False

				if not overwrite_text:
					# Check if the text contains a valid number using regex
					number_match = re.search(r'[-+]?\d*\.\d+|[-+]?\d+', self.text)
					if number_match:
						start, end = number_match.start(), number_match.end()
						number_text = number_match.group(0)

						try:
							value = self.fi_mode(number_text)
							increment = self.calculate_increment()
							new_value = value + increment if touch.button == 'scrolldown' else value - increment
							new_value = min(max(new_value, self.min_value), self.max_value)

							new_text = self.text[:start] + str(new_value) + self.text[end:]
							self.text = new_text

							# Maintain the selection with adjusted indexes
							self.select_text(start, start + len(str(new_value)))
						except ValueError:
							pass

				if overwrite_text:
					increment = self.calculate_increment()
					new_value = value + increment if touch.button == 'scrolldown' else value - increment
					new_value = min(max(new_value, self.min_value), self.max_value)

					# Set the whole text to the new value
					self.text = str(new_value)


# Combines both classes above
class FScrollInput(FTextInput, ScrollInput):
	pass
# Special input field needed for the ResolutionSelector
class ComboCappedScrollInput(ScrollInput):
	@handle_exceptions
	def __init__(self, paired_field=None, **kwargs):
		super().__init__(**kwargs)
		self.paired_field = paired_field

	@handle_exceptions
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
				traceback.print_exc()

	@handle_exceptions
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
# Special input field used in the SeedGrid to allow quick randomizing/clearing of individual fields
class SeedScrollInput(ScrollInput):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	# Checks if a user pressed r or c in a SeedGrid field to randomize or clear it's contents
	@handle_exceptions
	def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
		if keycode[1] == 'r':
			self.text = str(IM_G.generate_seed())
		elif keycode[1] == 'c':
			self.text = ''
		elif keycode[1] == 'p':
			self.text = GS.PRE_LAST_SEED
		elif keycode[1] == 'l':
			self.text = GS.LAST_SEED
		return super().keyboard_on_key_down(keyboard, keycode, text, modifiers)

# This is a widget to at least approximate the token cost of a prompt
class TokenCostBar(BoxLayout):
	@handle_exceptions
	def __init__(self, clip_calculator, max_token_count, **kwargs):
		super(TokenCostBar, self).__init__(**kwargs)
		self.clip_calculator = clip_calculator
		self.max_token_count = max_token_count
		self.color_threshold = self.max_token_count / 2
		self.token_cost = 0
		self.bind(pos=self.update_rect, size=self.update_rect)

	@handle_exceptions
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
			bar_height = min(1, self.token_cost / self.max_token_count) * self.height
			Rectangle(pos=self.pos, size=(self.width, bar_height))
	
	@handle_exceptions
	def calculate_token_cost(self, instance, text):
		self.token_cost = self.clip_calculator.calculate_token_cost(text)
		self.update_rect()

# A class for the big image preview
class ImagePreview(AsyncImage):
	@handle_exceptions
	def __init__(self, **kwargs):
		super(ImagePreview, self).__init__(**kwargs)
		self.texture = Texture.create(size=(1,1), colorfmt='rgba')
		self.fit_mode = 'contain'

	@handle_exceptions
	def load_image(self, image_data):
		try:
			image = PILImage.open(io.BytesIO(image_data))
			if image.mode != 'RGBA':
				image = image.convert('RGBA')
			self.texture = Texture.create(size=(image.size[0], image.size[1]), colorfmt='rgba')
			flipped_image = image.transpose(PILImage.FLIP_TOP_BOTTOM)
			self.texture.blit_buffer(flipped_image.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
			Clock.schedule_once(lambda dt: setattr(self, 'opacity', 1))
		except:
			traceback.print_exc()

# These next classes are responsible for various buttons that change states in the UI
class DoubleEmojiButton(Button):
	enabled = BooleanProperty(True)

	@handle_exceptions
	def __init__(self, symbol1='', symbol2='', **kwargs):
		super().__init__(**kwargs)
		self.font_size = 23 ###Consider checking for values like these and making them variables
		self.font_name = 'NotoEmoji'
		self.bind(enabled=self.on_state_changed)
		self.symbol1 = symbol1
		self.symbol2 = symbol2
		self.on_state_changed()

	@handle_exceptions
	def on_state_changed(self, *args):
		if self.enabled:
			self.background_color = (0, 1, 0, 1)  # Green
			self.text = self.symbol1
		else:
			self.background_color = (1, 0, 0, 1)  # Red
			self.text = self.symbol2

	@handle_exceptions
	def on_release(self):
		self.enabled = not self.enabled
class ImportButton(DoubleEmojiButton):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(symbol1='📥', symbol2='🚫', **kwargs)
class PauseButton(DoubleEmojiButton):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(symbol1='▶️', symbol2='⏸️',font_name='Unifont',**kwargs)

# Used for various places where a button to switch between two states is needed like SMEA/Dyn
class StateShiftButton(Button):
	enabled = BooleanProperty(False)
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.font_size=font_large
		self.bind(enabled=self.on_state_changed)
		self.on_state_changed()

	@handle_exceptions
	def on_state_changed(self, *args):
		if self.enabled:
			self.background_color = (0, 1, 0, 1)  # Green
		else:
			self.background_color = (1, 0, 0, 1)  # Red

	@handle_exceptions
	def on_release(self):
		self.enabled = not self.enabled
class StateFButton(StateShiftButton):
	@handle_exceptions
	def __init__(self, mode_switcher, standard_target, f_target, injector, standard_widgets = [], f_widgets = [], enabled = True, **kwargs):
		self.text = 'f'
		self.mode_switcher = mode_switcher
		self.standard_target = standard_target
		self.f_target = f_target
		self.injector = injector
		self.standard_widgets = standard_widgets
		self.f_widgets = f_widgets
		self.enabled = enabled
		super().__init__(**kwargs)
		self.on_state_changed()
	@handle_exceptions
	def on_state_changed(self, *args):
		super(StateFButton, self).on_state_changed(*args)
		if self.enabled:
			self.mode_switcher.hide_widgets(self.standard_widgets)
			self.mode_switcher.unhide_widgets(self.f_widgets)
			if not self.injector == None:
				self.injector.target = self.f_target
		else:
			self.mode_switcher.unhide_widgets(self.standard_widgets)
			self.mode_switcher.hide_widgets(self.f_widgets)
			if not self.injector == None:
				self.injector.target = self.standard_target

# These classes are for injector dropdowns, dropdowns that are attached to a field and can inject their values into it
class InjectorDropdown(BoxLayout):
	@handle_exceptions
	def __init__(self, dropdown_list=[], button_text='', target=None, inject_identifier='P', **kwargs):
		super().__init__(**kwargs)
		self.orientation='vertical'
		self.target=target
		self.inject_identifier=inject_identifier
		self.dropdown = DropDown(auto_width=False,size_hint=(1, None))
		dropdown_button = Button(text=button_text, size_hint=(None, 1), width=field_height, height=field_height*2, **button_colors)
		dropdown_button.bind(on_release=lambda *args: self.dropdown.open(dropdown_button))
		# Update the dropdown button text when an item is selected
		self.dropdown.bind(on_select=lambda instance, x: setattr(dropdown_button, 'text', x))
		self.add_widget(dropdown_button)

		# Create a button for each item in the list
		for item in dropdown_list:
			self.add_button(item)

	@handle_exceptions
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

	@handle_exceptions
	def copy_to_clipboard(self, string, item_layout):
		Clipboard.copy(string)

	@handle_exceptions
	def prepend_to_text_box(self, string, item_layout):
		self.target.text = string + self.target.text

	@handle_exceptions
	def append_to_text_box(self, string, item_layout):
		self.target.text += string
class ConditionalInjectorDropdown(InjectorDropdown):
	@handle_exceptions
	def __init__(self, dropdown_list=[], button_text='', target=None, **kwargs):
		super().__init__(dropdown_list=dropdown_list, button_text=button_text, target=target, **kwargs)

	@handle_exceptions
	def add_button(self, item, *args):
		item_layout, item_string = super(ConditionalInjectorDropdown, self).add_button(item, *args)
		if not (item_string == 'ddim, ' or item_string == 'plms, '):
			sampler_smea = StateShiftButton(text='SMEA', size_hint=(None, 1), size=(70,field_height))
			sampler_dyn = StateShiftButton(text='Dyn', size_hint=(None, 1), size=(70,field_height))

			sampler_smea.bind(enabled=lambda instance, value: on_smea_disabled(value, sampler_dyn))
			sampler_dyn.bind(enabled=lambda instance, value: on_dyn_enabled(value, sampler_smea))
			item_layout.add_widget(sampler_smea, index=1)
			item_layout.add_widget(sampler_dyn, index=1)

	@handle_exceptions
	def copy_to_clipboard(self, string, item_layout):
		string = self.attach_smea_dyn(string, item_layout)
		Clipboard.copy(string)

	@handle_exceptions
	def prepend_to_text_box(self, string, item_layout):
		string = self.attach_smea_dyn(string, item_layout)
		self.target.text = string + self.target.text

	@handle_exceptions
	def append_to_text_box(self, string, item_layout):
		string = self.attach_smea_dyn(string, item_layout)
		self.target.text += string
	
	@handle_exceptions
	def attach_smea_dyn(self, string, item_layout):
		if type(item_layout.children[1]) == StateShiftButton:
			if item_layout.children[1].enabled: #Dyn
				string = string[:-2] + '_dyn' + string[-2:]
			elif item_layout.children[2].enabled: #SMEA
				string = string[:-2] + '_smea' + string[-2:]
		return string

# A slightly more advanced dropdown button that allows scrolling values without opening the dropdown
class ScrollDropDownButton(Button):
	@handle_exceptions
	def __init__(self, associated_dropdown, **kwargs):
		self.associated_dropdown = associated_dropdown
		super().__init__(**kwargs)

	@handle_exceptions
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

# Class for the Cluster Collage/Image Sequence/Cluster Sequence buttons at the top, also handles showing/hiding the according elements and has bools for its state
class ModeSwitcher(BoxLayout):
	@handle_exceptions
	def __init__(self, app='', **kwargs):
		super(ModeSwitcher, self).__init__(**kwargs)
		self.app=app
		self.cc_active = True
		self.is_active = False
		self.cs_active = False
		self.cc_button = Button(text='Cluster Collage', on_press=self.switch_cc)
		self.is_button = Button(text='Image Sequence', on_press=self.switch_is)
		self.cs_button = Button(text='Cluster Sequence', on_press=self.switch_cs)
		self.add_widget(self.cc_button)
		self.add_widget(self.is_button)
		self.add_widget(self.cs_button)
		self.cc_button.background_color = (0, 1, 0, 1)
		self.is_button.background_color = (1, 0, 0, 1)
		self.cs_button.background_color = (1, 0, 0, 1)
	
	# These functions are responsible for switching between the cluster collage and image sequence layouts
	@handle_exceptions
	def switch_cc(self, f):
		if self.cc_active == True:
			return
		self.cc_active = True
		self.is_active = False
		self.cs_active = False
		self.cc_button.background_color = (0, 1, 0, 1)
		self.is_button.background_color = (1, 0, 0, 1)
		self.cs_button.background_color = (1, 0, 0, 1)
		self.unhide_widgets(self.app.cc_exclusive_widgets)
		self.hide_widgets(self.app.is_exclusive_widgets)

	@handle_exceptions
	def switch_is(self, f):
		if self.is_active == True:
			return
		self.cc_active = False
		self.is_active = True
		self.cs_active = False
		self.cc_button.background_color = (1, 0, 0, 1)
		self.is_button.background_color = (0, 1, 0, 1)
		self.cs_button.background_color = (1, 0, 0, 1)
		self.unhide_widgets(self.app.is_exclusive_widgets)
		self.hide_widgets(self.app.cc_exclusive_widgets)

	@handle_exceptions
	def switch_cs(self, f):
		if self.cs_active == True:
			return
		self.cc_active = False
		self.is_active = False
		self.cs_active = True
		self.cc_button.background_color = (1, 0, 0, 1)
		self.is_button.background_color = (1, 0, 0, 1)
		self.cs_button.background_color = (0, 1, 0, 1)
		self.unhide_widgets(self.app.is_exclusive_widgets+self.app.cc_exclusive_widgets)
		self.hide_widgets(self.app.non_cs_widgets)
	
	# These functions hide and unhide widgets
	@handle_exceptions
	def hide_widgets(self, widgets):
		for widget in widgets:
			if widget.opacity != 0 and widget.height != 0 and widget.width != 0:
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

	@handle_exceptions
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
	@handle_exceptions
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
		for seed_list in GS.SEED_LISTS:
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

	@handle_exceptions
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
			seed_input = SeedScrollInput(text='', min_value=0, max_value=4294967295, increment=1000, multiline=False, **input_colors, font_size=font_small, allow_empty=True)
			self.seed_inputs.append(seed_input)
			self.cc_seed_grid.add_widget(seed_input)

	@handle_exceptions
	def load_seeds(self, seeds):
		try:
			self.seed_rows_input.text, self.seed_cols_input.text = str(len(seeds)), str(len(seeds[0]))
			self.adjust_grid_size()
			for seed_input, value in zip(self.seed_inputs, itertools.chain(*seeds)):
				seed_input.text = str(value)
		except:
			traceback.print_exc()

	@handle_exceptions
	def randomize(self):
		for widget in self.cc_seed_grid.children:
			if isinstance(widget, TextInput):
				widget.text = str(IM_G.generate_seed())

	@handle_exceptions
	def clear(self):
		for widget in self.cc_seed_grid.children:
			if isinstance(widget, TextInput):
				widget.text = ''

# PromptGrid class for the use of f-strings in prompting
class PromptGrid(GridLayout):
	@handle_exceptions
	def __init__(self, **kwargs):
		super(PromptGrid, self).__init__(**kwargs)
		self.rows = 1
		self.prompt_rows = 1
		self.prompt_inputs = []
		self.prompt_eval_list = BoxLayout(orientation='vertical', size_hint=(1, 1), size=(100, field_height*4))
		self.btn1 = Button(text='Row+', size_hint=(1, None), size=(100, field_height), **button_colors)
		self.btn1.bind(on_release=lambda btn: self.on_increase_rows())
		self.btn2 = Button(text='Row-', size_hint=(1, None), size=(100, field_height), **button_colors)
		self.btn2.bind(on_release=lambda btn: self.on_decrease_rows())
		self.btn3 = Button(text='Copy ⁅⁆', size_hint=(1, None), size=(100, field_height), **button_colors)
		self.btn3.bind(on_release=lambda btn: Clipboard.copy('⁅⁆'))
		self.btn3.font_name = 'Unifont'
		self.btn4 = Button(text='Inject ⁅⁆', size_hint=(1, None), size=(100, field_height), **button_colors)
		self.btn4.bind(on_release=lambda btn: setattr(self.prompt_inputs[0], 'text', self.prompt_inputs[0].text+'⁅⁆'))
		self.btn4.font_name = 'Unifont'
		self.btn5 = Button(text='Inject ⁅Seq.⁆', size_hint=(1, None), size=(100, field_height), **button_colors)
		self.btn5.bind(on_release=lambda btn: setattr(self.prompt_inputs[0], 'text', self.prompt_inputs[0].text+'''⁅'♥‼¡'*n⁆'''))
		self.btn5.font_name = 'Unifont'
		self.btn6 = Button(text='Inject ⁅List⁆', size_hint=(1, None), size=(100, field_height), **button_colors)
		self.btn6.bind(on_release=lambda btn: setattr(self.prompt_inputs[0], 'text', self.prompt_inputs[0].text+'''⁅['0','1','...'][n]⁆'''))
		self.btn6.font_name = 'Unifont'
		self.btn_grid = GridLayout(cols=1, size_hint=(None, 1), width=115)
		self.btn_grid.add_widget(self.btn1)
		self.btn_grid.add_widget(self.btn2)
		self.btn_grid.add_widget(self.btn3)
		self.btn_grid.add_widget(self.btn4)
		self.btn_grid.add_widget(self.btn5)
		self.btn_grid.add_widget(self.btn6)
		self.add_widget(self.btn_grid)
		self.add_widget(self.prompt_eval_list)
		
		self.adjust_grid_size(1)

	@handle_exceptions
	def adjust_grid_size(self, rows):
		self.prompt_rows = rows
		# retain the text of the existing inputs
		prompt_input_texts = [input.text for input in self.prompt_inputs]
		self.prompt_inputs.clear()
		self.prompt_eval_list.clear_widgets()
		for i in range(rows):
			prompt_input = FTextInput(multiline=True, text='⁅⁆', **input_colors)
			prompt_input.font_size = 23
			prompt_input.font_name = 'Unifont'
			if i < len(prompt_input_texts):
				prompt_input.text = prompt_input_texts[i]
			self.prompt_inputs.append(prompt_input)
			self.prompt_eval_list.add_widget(prompt_input)

	@handle_exceptions
	def load_prompts(self, prompts):
		try:
			self.adjust_grid_size(len(prompts))
			for i in range(len(prompts)):
				self.prompt_inputs[i].text = str(prompts[i])[6:-5].replace("\\'","'")
		except:
			traceback.print_exc()

	@handle_exceptions
	def on_increase_rows(self):
		rows = min(self.prompt_rows + 1, 5)
		self.adjust_grid_size(rows)

	@handle_exceptions
	def on_decrease_rows(self):
		rows = max(self.prompt_rows - 1, 1)
		self.adjust_grid_size(rows)

# In order to use the previous generation metadata, this class replicates a functional read-only console
class Console(BoxLayout):
	#A proper passing function is needed to prevent program breaking recursion
	class TerminalPass():
		@handle_exceptions
		def __init__(self, type='', parent=None, **kwargs):
			self.type = type
			self.parent = parent
		@handle_exceptions
		def write(self, message):
			self.parent.process_message(message, self.type)
		@handle_exceptions
		def flush(self):
			pass

	@handle_exceptions
	def __init__(self, max_lines=200, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'vertical'
		self.max_lines = max_lines

		self.output_text = Label(text='', font_size=12, size_hint=(1,None), valign='top', markup=True)
		self.output_text.bind(
			width=lambda *x: self.output_text.setter('text_size')(self.output_text, (self.output_text.width, None)),
			texture_size=lambda *x: self.output_text.setter('height')(self.output_text, self.output_text.texture_size[1]))
		self.output_scroll = ScrollView(size_hint=(1, 1), effect_cls=ScrollEffect)
		self.output_scroll.add_widget(self.output_text)
		self.add_widget(self.output_scroll)
		self._stdout = sys.stdout
		self._stderr = sys.stderr
		sys.stdout = self.pass_out = self.TerminalPass(type='out', parent=self)
		sys.stderr = self.pass_err = self.TerminalPass(type='err', parent=self)

	# No @handle_exceptions here. As the function that is responsible for intercepting and splitting terminal messsages it's handled differently
	def process_message(self, message, type):
		def update_label_text(dt):
			try:
				if message.startswith("[Warning]"):
					self._stdout.write(message)
					self.output_text.text += f'{rgba_to_string(GS.THEME["ConWarn"]["value"])}{message[len("[Warning] "):]}[/color]'
				elif type == 'out':
					self._stdout.write(message)
					self.output_text.text += f'{rgba_to_string(GS.THEME["ConNorm"]["value"])}{message}[/color]'
				elif type == 'err':
					self._stderr.write(message)
					self.output_text.text += f'{rgba_to_string(GS.THEME["ConErr"]["value"])}{message}[/color]'

				# Split the text into lines
				lines = self.output_text.text.splitlines()
				# Check if the line length was exceeded
				if len(lines) > self.max_lines:
					# Join the lines back together into a single string
					trimmed_text = '\n'.join(lines[-self.max_lines:])
					# Find the index of the next closing color tag
					next_closing_tag_idx = trimmed_text.find('[/color]')
					# Trim accordingly and update the text
					self.output_text.text = trimmed_text[next_closing_tag_idx + len('[/color]'):]
			except:
				# As this function would loop when using the normal print statement but still needs debugging support, this manual try/except block as wrapped in
				self._stderr.write(traceback.format_exc())

		Clock.schedule_once(update_label_text)
	@handle_exceptions
	def flush(self):
		pass

# A special label with a convenient integrated background, used for stuff like categories in dropdown lists
class BGLabel(Label):
	@handle_exceptions
	def __init__(self, background_color=[0, 0, 0.3, 1],**kwargs):
		super(BGLabel, self).__init__(**kwargs)
		with self.canvas.before:
			Color(*background_color)  # set the background color here
			self.rect = Rectangle(size=self.size, pos=self.pos)
		self.bind(size=self._update_rect, pos=self._update_rect)

	@handle_exceptions
	def _update_rect(self, instance, value):
		self.rect.pos = instance.pos
		self.rect.size = instance.size

	@handle_exceptions
	def _update_color(self, instance, color):
		self.canvas.before.clear()
		with self.canvas.before:
			Color(*color)  # set the background color here
			self.rect = Rectangle(size=self.size, pos=self.pos)


# A resolution selector that aims to have just about all the possible conveniences
class ResolutionSelector(BoxLayout):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(orientation='horizontal', size_hint=(1, None), height=field_height, **kwargs)
		
		# Create width and height input fields for custom resolution
		self.resolution_width = ComboCappedScrollInput(text='1024', increment=64, min_value=64, max_value=49152,
													 size_hint=(1, None), width=60, height=field_height, **input_colors)
		self.resolution_height = ComboCappedScrollInput(text='1024', increment=64, min_value=64, max_value=49152, paired_field=self.resolution_width, 
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

	@handle_exceptions
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
	@handle_exceptions
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
class FileHandlingWindow(Popup):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		# Set up and add all the elements for the theme configurator
		layout = BoxLayout(orientation='vertical')
		
		images_layout = BoxLayout(orientation='horizontal')
		images_label = Label(text='Images:', size_hint=(None,None), size=(130,field_height))
		self.images_input = TextInput(text = "placeholder 1", multiline=True, size_hint=(1, None), size=(100, field_height*3), **input_colors)
		images_layout.add_widget(images_label)
		images_layout.add_widget(self.images_input)
		
		videos_layout = BoxLayout(orientation='horizontal')
		videos_label = Label(text='Videos:', size_hint=(None,None), size=(130,field_height))
		self.videos_input = TextInput(text = "placeholder 2", multiline=True, size_hint=(1, None), size=(100, field_height*3), **input_colors)
		videos_layout.add_widget(videos_label)
		videos_layout.add_widget(self.videos_input)
		
		cc_layout = BoxLayout(orientation='horizontal')
		cc_label = Label(text='Cluster Collages:', size_hint=(None,1), size=(130,field_height))
		self.cc_input = TextInput(text = "placeholder 3", multiline=True, size_hint=(1, None), size=(100, field_height*3), **input_colors)
		cc_layout.add_widget(cc_label)
		cc_layout.add_widget(self.cc_input)
		
		settings_layout = BoxLayout(orientation='horizontal')
		settings_label = Label(text='Settings:', size_hint=(None,None), size=(130,field_height))
		self.settings_input = TextInput(text = "placeholder 4", multiline=True, size_hint=(1, None), size=(100, field_height*3), **input_colors)
		settings_layout.add_widget(settings_label)
		settings_layout.add_widget(self.settings_input)
		
		layout.add_widget(images_layout)
		layout.add_widget(videos_layout)
		layout.add_widget(cc_layout)
		layout.add_widget(settings_layout)
		
		self.content = layout

# Popup for configuring settings
class ConfigWindow(Popup):
	@handle_exceptions
	def process_token(self, instance):
		token = self.token_input.text
		match = re.search(r'"auth_token":"([^"]+)"', token)
		if match:
			token = match.group(1)
		result = IM_G.generate_as_is(None,None,True,token)
		if result == 'Success':
			self.token_input.text = token
			token_file_content = f"""#Only the access token goes into this file. Do not share it with anyone else as that's against NAI ToS. Using it on multiple of your own devices is fine.
AUTH='{token}'
"""
			CH.write_config_file('4.Token(DO NOT SHARE)',token_file_content)
			self.update_token_state(None, result)
			GS.AUTH = token
		else:
			self.update_token_state(None, result)
			return

	@handle_exceptions
	def update_token_state(self,instance,state):
		if state=='Success':
			self.token_state._update_color(None, [0,1,0,1])
			self.token_state.text = '✔️'
		else:
			self.token_state._update_color(None, [1,0,0,1])
			self.token_state.text = '❌'

	@handle_exceptions
	def switch_eval_behavior(self,instance,label):
		if not instance.enabled:
			label.text = 'f-strings are evaluated in guarded mode'
		else:
			label.text = '''WARNING: f-strings are evaluated without restrictions, be thrice certain you don't blindly import malicious settings'''

	@handle_exceptions
	def check_for_error(self,instance):
		if GS.LAST_ERROR != None:
			self.copy_error_button.disabled = False

	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.bind(on_open=self.check_for_error)
		# Set up and add all the elements for the theme configurator
		layout = BoxLayout(orientation='vertical')
		
		theme_example_layout = GridLayout(cols=2)
		
		
		skip_button = StateShiftButton(text='Skip Generation',on_release=lambda instance: setattr(GS, 'GENERATE_IMAGES', not GS.GENERATE_IMAGES), size_hint=(1,None), size=(100,field_height))
		
		vid_params_label = Label(text='vid_params = ', size_hint=(None,None), size=(100,field_height))
		self.vid_params_input = TextInput(text = "{'fps': 10,'codec': 'vp9','pixelformat': 'yuvj444p',}", multiline=False, size_hint=(1, None), size=(100, field_height), **input_colors)
		vid_params_layout = BoxLayout(orientation='horizontal')
		#vid_params_layout.add_widget(vid_params_label)
		#vid_params_layout.add_widget(self.vid_params_input)
		
		eval_guard_label = Label(text='f-strings are evaluated in guarded mode', size_hint=(1,None), size=(100,field_height))
		self.eval_guard_button = DoubleEmojiButton(symbol1='🔰️', symbol2='⚠️',on_release=lambda eval_guard_button: self.switch_eval_behavior(eval_guard_button,eval_guard_label),size_hint=(None,None), size=(field_height,field_height))
		eval_guard_layout = BoxLayout(orientation='horizontal')
		eval_guard_layout.add_widget(self.eval_guard_button)
		eval_guard_layout.add_widget(eval_guard_label)
		
		# Set up and add all the necessary elements for token handling
		token_button = Button(text='Set NovelAI token (DO NOT SHARE):', on_release=self.process_token, size_hint=(1,None), size=(100,field_height))
		self.token_state = BGLabel(font_name='NotoEmoji', text='❔', background_color=[0.5, 0.5, 0.5, 1], size_hint=(None,None), size=(field_height,field_height))
		token_layout = BoxLayout(orientation='horizontal')
		self.token_input = TextInput(text=GS.AUTH, multiline=False, size_hint=(1,None), size=(100+field_height,field_height))
		token_layout.add_widget(token_button)
		token_layout.add_widget(self.token_state)
		token_layout.add_widget(self.token_input)
		self.copy_error_button = Button(text="Copy last error to clipboard", on_release=lambda btn: Clipboard.copy(GS.LAST_ERROR), size_hint=(1,None), size=(100,field_height), disabled=True)
		
		layout.add_widget(skip_button)
		layout.add_widget(vid_params_layout)
		layout.add_widget(eval_guard_layout)
		layout.add_widget(token_layout)
		layout.add_widget(self.copy_error_button)
		#layout.add_widget(ColorPickerDropDown(options=GS.THEME))
		#GS.bind(THEME[0]["value"]=setattr(self.token_input.foreground_color,THEME[0]["value"]))
		self.content = layout

# Classes for the theme configurator
class ThemeButton(Button):
	@handle_exceptions
	def __init__(self, starting_color, **kwargs):
		super().__init__(**kwargs)
		self.bind(size=self._update_rect, pos=self._update_rect)
	
	#Will be called once upon opening the dropdown and initializing these buttons
	@handle_exceptions
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

	@handle_exceptions
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
	@handle_exceptions
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

	@handle_exceptions
	def _on_option_button_press(self, option, button):
		self.selected_option = button
		self.color_picker.color = option["value"]
		self.dropdown_button.text = option["name"]

	@handle_exceptions
	def _on_color_picker_color(self, instance, selected_color):
		self.selected_option.set_color(selected_color)
		self.selected_option.associated_dict["value"]=selected_color

### Add decorators!
# Similar to the InjectorDropdown this class provides a single button and attached dropdown system, used to handle saved images
class ImageGeneratorDropdown(BoxLayout):
	pass

# Class for image generation entries both those created via AI as well as those loaded from disk
class ImageGenerationEntry(BoxLayout):
	def __init__(self, image, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'horizontal'

		# Load the image from the provided png_data
		self.image = ImagePreview()
		self.image.load_image(image)
		self.add_widget(self.image)
		
		### Add all the needed buttons
		# View function, click on thumbnail?
		# ControlNet functions
		# Metadata injector functions

# Class for a loaded set of metadata from an image in cache
###to be created and destroyed as needed or maybe better to make one and repurpose it?
###...we have the hide/unhide functions, maybe use those for objects and then go through a loop trying to load them and hiding unhiding them accordingly?
class ImageGenerationMetadata(BoxLayout):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'vertical'
		self.metadata_types = [
		['Name'],
		['Model'],
		['Seed'],
		['Steps'],
		['Scale'],
		['Sampler'],
		['Decrisper'],
		['Resolutions'],
		['Prompt'],
		['Neg. Prompt'],
		]
		### Add fields for found metadata
		### Add buttons for each location for metadata
		load_values()
	
	def create_metatada_field(metadata_type):
		###Needs name, import button, value as label
		field = BoxLayout(orientation='horizontal')
		setattr(self, metadata_type[0], fieldq )
		
		
	def load_values():
		for metadata in metadata_types:
			###Use try_to_load from main.py?
			if try_to_load(STUFF) == True:
				pass###unhide element
			else:
				pass###hide element