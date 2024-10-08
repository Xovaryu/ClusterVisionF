"""
kivy_widgets.py
	This module contains all the kivy classes that are used to build the UI

01.	ThemeRegisterBehavior
			This behavior completely streamlines the process of dynamically applying themes to widgets
02.	ToolTipBehavior + ToolTip
			These two classes together take care of setting up tooltips
			They do it in such a manner that in the end all that has to be done to get high quality tooltips is to make any given widget have all relevant tooltip_types
03.	Label + Button + TextInput + DropDownEntryButton + ConfirmButton
			These are mostly just the default Kivy widgets but with applied behaviors and some small goodies
04.	BgLabel
			A simple class that adds a colorable background to a Label
05.	FTextInput
			Extends TextInput with a key combination that allows quick insertion of the special f-string braces
06.	ScrollInput
			Significantly upgrades TextInput with the ability to scroll numbers when hovering if there are only scrollable numbers present or when a valid number is selected
07.	FScrollInput
			Has the extras of both classes above
08.	ComboCappedScrollInput
			A class used for special ScrollInputs that are linked to a collective maximum value
09.	SeedScrollInput
			This class adds clear/randomize functionality when pressing c/r for use in seed fields
10.	TokenCostBar
			Used to calculate how many tokens have been used relative to what the model supports (at least it should do so eventually)
11.	ImagePreview
			This class shows generated images in the UI
12.	DoubleEmojiButton + ImportButton + PauseButton
			These classes are buttons using emojis to make their use and state quickly apparent
13.	StateShiftButton
			Similar to the classes above but with definable text instead
14.	StateFButton
			Used for the (negative) prompt fields to switch the text input and rehook the injector
15.	InjectorDropDown + SamplerInjectorDropDown
			This class creates a dropdown that is tied to a text field and can inject it's valuees, the conditional variant supports on/off buttons in the dropdown
16.	ScrollDropDownButton
			This is just a slightly more advanced dropdown button that supports scrolling when hovering
17.	ModeSwitcher
			This class makes the 3 mode buttons at the top of the GUI and tracks the state for other functions to use
18.	SeedGrid
			This is a complex class that creates a grid of text fields for seeds to be used in cluster collages
19.	PromptGrid
			Somewhat similar to above this is used for f-string prompts to allow splitting the text field for conveniences
20.	Console
			A class made to expose console outputs right in the UI
21.	ResolutionSelector
			A class that makes a complete resolution selector and loads available resolutions and their names from the user settings
22.	FileHandlingWindow
			A popup for setting f-strings according to which file strings are built
23.	ConfigWindow
			A popup for various settings
24.	ThemeButton
			ThemeButtons are special dropdown list buttons that properly display the current color of the associated theme value
25.	ThemeLayout + ThemeWindow
			A full pre-assembled layout for the entire theme handling part currently implemented into the configuration window
26.	ErrorPopup
			This is an error popup that is currently only used for the token setting and testing
27.	ExecPopup
			This is a hidden popup that has one primary use, and that is debugging
			To that end this popup allows direct use of exec() and is as such littered with warnings, and never gets initialized until the user manually opens and activates it
28.	DropOverlay
			Gives a few quick pointers on how loading files works (with help of the background) as well as pointing out to users how to get tooltips
29.	ImageGenerationEntry + BorderedImage + PermissiveScrollViewBehavior + PermissiveDropDown
			Classes for image generation entries, both those created via AI as well as those imported
			ImageGenerationEntry is a class for layouts that include all the relevant UI elements to fully organize a single image for i2i/VT/history/metadata
			BorderedImage is an upgraded Image that can show 3 types of concurrently possible borders to further clarify image states
			PermissiveDropDown is a special type of dropdown that respects any widgets it contains that use hover scrolling for their functionality
30.	MetadataViewer
			This class creates a proper metadata viewer that can parse and display both EXIf/alpha metadata verbatim
"""
from initialization import handle_exceptions, GlobalState, CH
GS = GlobalState()

import sys
import os
import copy
import re
import io
import traceback
import itertools
import kivy
import json
import time
import webbrowser
from PIL import Image as PILImage
from PIL import ImageDraw as PILImageDraw
import image_generator as IM_G
import text_manipulation as TM
from file_loading import load_metadata_dicts
import documentation as DOC
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.effects.dampedscroll import ScrollEffect
from kivy.graphics import Color, Rectangle, Line, Triangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.bubble import Bubble
from kivy.uix.modalview import ModalView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.image import AsyncImage, Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty, NumericProperty, ListProperty

###Provisory copy for now
RESOLUTIONS = copy.deepcopy(GS.NAI_RESOLUTIONS)
RESOLUTIONS.update(GS.USER_RESOLUTIONS)
from kivy.core.text import LabelBase
field_height=30
font_hyper=20
font_large=19
font_small=15

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

# Functions used to link the SMEA and Dyn buttons in such a way that enabling Dyn makes sure SMEA is enabled, and that disabling SMEA disables Dyn
@handle_exceptions
def on_smea_disabled(value, linked_button):
	if not value:
		linked_button.enabled = False
@handle_exceptions
def on_dyn_enabled(value, linked_button):
	if value:
		linked_button.enabled = True

# Used to dynamically slightly adjust colors in the program while staying true to the selected theme
@handle_exceptions
def adjust_color(color, adjustment_factor=0.07):
	r, g, b, a = color
	
	# Calculate perceived brightness
	brightness = (0.299 * r + 0.587 * g + 0.114 * b)
	
	# Decide whether to lighten or darken based on brightness
	if brightness > 0.5:
		# Darken
		r = max(0, r - adjustment_factor)
		g = max(0, g - adjustment_factor)
		b = max(0, b - adjustment_factor)
	else:
		# Lighten
		r = min(1, r + adjustment_factor)
		g = min(1, g + adjustment_factor)
		b = min(1, b + adjustment_factor)
	
	return (r, g, b, a)

# Will take the input widgets and break them and all of their children up for garbage collection
@handle_exceptions
def nuke_widgets(widgets):
	if not isinstance(widgets, list):
		widgets = [widgets]
	all_children = []
	def recurse(current_widget):
		if hasattr(current_widget, 'children'):
			# Recurse into children first
			for child in current_widget.children:
				recurse(child)
			# Add the current widget after its children
			all_children.append(current_widget)
		if hasattr(current_widget, 'tooltip'):
			recurse(current_widget.tooltip)
	for widget in widgets:
		recurse(widget)

	for widget in all_children:
		if widget.parent:
			widget.parent.remove_widget(widget)
		if hasattr(widget, 'deregister'):
			widget.deregister()
		if hasattr(widget, 'clear_widgets'):
			widget.clear_widgets()
		for attr in list(widget.__dict__):
			del attr
		if hasattr(widget, 'events'):
			for event_name in list(widget.events()):
				for bound_func in widget.get_property_observers(event_name):
					widget.unbind(**{event_name: bound_func})

# 01. Simplifies the dynamic applying of themes by creating a standardized way of fetching and setting colors for all relevant widgets
class ThemeRegisterBehavior(object):
	@handle_exceptions
	def __init__(self, register_to = GS.theme_self_updating_widgets, text_color_dict = None, bg_color_dict = None, fg_color_dict = None, 
			alternate_update_func = None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		register_to.append(self) if register_to != None else None
		self.text_color_dict = text_color_dict
		if self.text_color_dict != None:
			self.color = self.text_color_dict["value"]
		self.bg_color_dict = bg_color_dict
		if self.bg_color_dict != None:
			self.background_color = self.bg_color_dict["value"]
		self.fg_color_dict = fg_color_dict
		if self.fg_color_dict != None:
			self.foreground_color = self.fg_color_dict["value"]
		self.alternate_update_func = alternate_update_func

	@handle_exceptions
	def update_color(self, instance):
		if self.text_color_dict != None:
			self.color = self.text_color_dict["value"]
		if self.bg_color_dict != None:
			self.background_color = self.bg_color_dict["value"]
		if self.fg_color_dict != None:
			self.foreground_color = self.fg_color_dict["value"]
		if self.alternate_update_func != None:
			self.alternate_update_func()
			
	@handle_exceptions
	def deregister(self):
		if self in GS.theme_self_updating_widgets:
			GS.theme_self_updating_widgets.remove(self)

# 02. Can be attached to widgets to give them a fully functional tooltip according to the tooltip_types attribute, read from documentation.py
class ToolTipBehavior(object):
	tooltip_depth = 1
	
	@handle_exceptions
	def __init__(self, tooltip_types=[], *args, **kwargs):
		self.tooltip_types = []        
		for type in tooltip_types:
			self.tooltip_types.append(type)
		super().__init__(*args, **kwargs)

	@handle_exceptions
	def finalize_tooltip(self):
		self.tooltip_depth -= 1
		if self.tooltip_depth == 0:
			# Create a unique key based on the tooltip types
			key = tuple(sorted(self.tooltip_types))
			
			if key in GS.tooltip_widgets:
				# If the widget already exists, use the cached version
				bglabel = GS.tooltip_widgets[key]
			else:
				# If not, create a new BgLabel and cache it
				text = ''
				for type in self.tooltip_types:
					text += type + '\n'
					text += DOC.TOOLTIPS[type] + '\n\n\n'
				
				bglabel = BorderLabel(text=text[:-3], size_hint_y=1, text_color_dict=GS.theme["TTText"], bg_color_dict=GS.theme["TTBg"], markup=True, font_name='Unifont')
				bglabel.bind(
					on_ref_press=self.open_link,
					width=handle_exceptions(lambda *x: bglabel.setter('text_size')(bglabel, (bglabel.width, None))),
					)
				GS.tooltip_widgets[key] = bglabel
			
			del self.tooltip_depth
			try:
				self.tooltip = ToolTip(self, bglabel)
			except:
				print(self, self.text)
	
	@handle_exceptions
	def open_link(self, instance, value):
		webbrowser.open(value)
		
	@handle_exceptions
	def on_touch_down(self, touch):
		if not self.collide_point(*touch.pos):
			return
		if touch.button == 'right':
			# Disable the right click  
			touch.button = ''
			self.tooltip.open(self)
			return
		super().on_touch_down(touch)

# Tooltips are CVF's way of explaining itself, they appear when rightclicking elements
class ToolTip(DropDown, ThemeRegisterBehavior):
	@handle_exceptions
	def __init__(self, associated_widget, text_widget, **kwargs):
		self.associated_widget = associated_widget
		self.text_widget = text_widget
		super().__init__(**kwargs)
		self.auto_width=False
		self.size_hint=(1, None)
		self.bubble = BoxLayout(size_hint_y=None,height=400, padding = 2)
		self.add_widget(self.bubble)
		self.arrow_size = (20, 10)  # Adjust as needed
		self.bind(size=self.update_content,pos=self.update_content)

		with self.canvas.after:
			self.arrow_color_instruction = Color(*GS.theme["TTBgOutline"]["value"])
			self.arrow = Triangle(points=[0, 0, 0, 0, 0, 0])
		self.update_color(None)

	@handle_exceptions
	def open(self, instance):
		if self.text_widget.text == '':
			return
		super().open(instance)
		
		if self.text_widget.parent:
			self.text_widget.parent.remove_widget(self.text_widget)
		self.bubble.add_widget(self.text_widget)
		
		Clock.schedule_once(self.update_content)

	@handle_exceptions
	def update_content(self, instance=None, whatever=None):
		self.bubble.height = self.text_widget.texture_size[1]+self.bubble.padding[1]+self.bubble.padding[3]
		tip_pos = self.to_window(*self.pos)
		widget_pos = self.associated_widget.to_window(*self.associated_widget.pos)

		if tip_pos[1] > widget_pos[1]:
			y = self.y-self.arrow_size[1]+10
		else:   
			y = self.top+self.arrow_size[1]

		widget_center_x = int(widget_pos[0] + self.associated_widget.width / 2)
		x = widget_center_x - self.x

		if y == self.y:  # Arrow pointing down
			points = [
				x - self.arrow_size[0] / 2, y,
				x + self.arrow_size[0] / 2, y,
				x, y - self.arrow_size[1]
			]
		else:  # Arrow pointing up
			points = [
				x - self.arrow_size[0] / 2, y - self.arrow_size[1],
				x + self.arrow_size[0] / 2, y - self.arrow_size[1],
				x, y
			]
		self.arrow.points = points
		self.arrow_color_instruction.rgba = self.arrow_color
	
	@handle_exceptions
	def update_color(self, instance):
		super().update_color(instance)
		self.arrow_color = GS.theme["TTBgOutline"]["value"]
	

# 03. These are simply basic Kivy widgets that are slightly updated to automatically register themselves for applications of themes
class Label(Label, ThemeRegisterBehavior):
	@handle_exceptions
	def __init__(self, text_color_dict = GS.theme["ProgText"], **kwargs):
		super().__init__(text_color_dict = text_color_dict, **kwargs)

class Button(ToolTipBehavior, Button, ThemeRegisterBehavior):
	@handle_exceptions
	def __init__(self, text_color_dict = GS.theme["MBtnText"], bg_color_dict = GS.theme["MBtnBg"], **kwargs):
		super().__init__(text_color_dict = text_color_dict, bg_color_dict = bg_color_dict, **kwargs)
		self.finalize_tooltip()

class TextInput(ToolTipBehavior, TextInput, ThemeRegisterBehavior):
	@handle_exceptions
	def __init__(self, fg_color_dict = GS.theme["InText"], bg_color_dict = GS.theme["InBg"],**kwargs):		
		super().__init__(fg_color_dict = fg_color_dict, bg_color_dict = bg_color_dict, **kwargs)
		self.finalize_tooltip()

# Functionally just a normal button that registers and uses theme colors differently
class DropDownEntryButton(Button):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(text_color_dict = GS.theme["DBtnText"], bg_color_dict = GS.theme["DBtnBg"],**kwargs)

# This is a button used for actions that we really don't want users to perform accidentally, such as deleting any loaded images that might still be used
class ConfirmButton(Button):
	is_armed = BooleanProperty(False)
	countdown = NumericProperty(0)

	@handle_exceptions
	def __init__(self, func, **kwargs):
		super(ConfirmButton, self).__init__(**kwargs)
		self.func = func
		self.original_text = self.text
		self.bind(on_release=self.on_button_click)
		self.clock_event = None

	@handle_exceptions
	def on_button_click(self, instance):
		if not self.is_armed:
			self.arm()
		else:
			self.trigger_action()
			self.disarm()

	@handle_exceptions
	def arm(self):
		self.is_armed = True
		self.countdown = 3
		self.text = f"{self.original_text} ({self.countdown})"
		self.clock_event = Clock.schedule_interval(self.update_countdown, 1)

	@handle_exceptions
	def disarm(self):
		self.is_armed = False
		self.text = self.original_text
		if self.clock_event:
			self.clock_event.cancel()

	@handle_exceptions
	def update_countdown(self, dt):
		self.countdown -= 1
		if self.countdown > 0:
			self.text = f"{self.original_text} ({self.countdown})"
		else:
			self.disarm()

	@handle_exceptions
	def trigger_action(self):
		self.func()

	@handle_exceptions
	def on_is_armed(self, instance, value):
		if value:
			self.background_color = adjust_color(GS.theme["MBtnBg"]["value"])
		else:
			self.background_color = GS.theme["MBtnBg"]["value"]

# 04. A special label with a convenient integrated background, used for stuff like more complex dropdown lists
class BgLabel(Label):
	@handle_exceptions
	def __init__(self, text_color_dict = GS.theme["BgLText"], bg_color_dict = GS.theme["BgLBg"],**kwargs):
		super().__init__(text_color_dict = text_color_dict, **kwargs)
		self.bg_color_dict = bg_color_dict
		self.bind(size=self.update_rect, pos=self.update_rect)
		self.update_color(None)

	@handle_exceptions
	def update_rect(self, instance, value):
		self.rect.pos = instance.pos
		self.rect.size = instance.size

	@handle_exceptions
	def update_color(self, instance):
		super().update_color(instance)
		self.canvas.before.clear()
		with self.canvas.before:
			Color(*self.bg_color_dict["value"])  # set the background color here
			self.rect = Rectangle(size=self.size, pos=self.pos)

class BorderLabel(BgLabel):
	@handle_exceptions
	def __init__(self, text_color_dict=GS.theme["BgLText"], bg_color_dict=GS.theme["BgLBg"],
				 border_color_dict=GS.theme["TTBgOutline"], border_width=2, **kwargs):
		self.border_color_dict = border_color_dict
		self.border_width = border_width
		super().__init__(text_color_dict=text_color_dict, bg_color_dict=bg_color_dict, **kwargs)
	
	@handle_exceptions
	def update_rect(self, instance, value):
		# Update the border position and size
		self.border_rect.pos = (instance.pos[0] - self.border_width, instance.pos[1] - self.border_width)
		self.border_rect.size = (instance.size[0] + 2 * self.border_width, instance.size[1] + 2 * self.border_width)
		
		# Update the background position and size
		super().update_rect(instance, value)

	@handle_exceptions
	def update_color(self, instance):
		super().update_color(instance)
		
		# Update the border color
		with self.canvas.before:
			Color(*self.border_color_dict["value"])  # Set the border color here
			self.border_rect = Rectangle(size=(self.width + 2 * self.border_width, 
											   self.height + 2 * self.border_width), 
										 pos=(self.x - self.border_width, self.y - self.border_width))
			
			# Set the background color over the border
			Color(*self.bg_color_dict["value"])
			self.rect = Rectangle(size=self.size, pos=self.pos)

# 05. This class merely extends TextInput to allow quick inserting of f-braces
class FTextInput(TextInput):
	@handle_exceptions
	def __init__(self, **kwargs):
		self.tooltip_depth += 1
		super().__init__(**kwargs)
		self.font_name='Unifont'
		self.tooltip_types.append('F-Input')
		self.finalize_tooltip()
		
	# Checks if a user pressed CTRL+SHIFT+F to insert f-braces
	@handle_exceptions
	def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
		if 'ctrl' in modifiers and 'shift' in modifiers and keycode[1] == 'f':
			# Get the current cursor position, add the brace (by rewrtiting the text), and update the cursor position
			cursor = self.cursor
			self.text = self.text[:cursor[0]] + '⁅⁆' + self.text[cursor[0]:]
			self.cursor = (cursor[0] + 1, self.cursor[1])
		return super().keyboard_on_key_down(keyboard, keycode, text, modifiers)

# 06. Input field used for any field with scrolling numbers
class ScrollInput(TextInput):
	@handle_exceptions
	def __init__(self, min_value=1, max_value=100, increment=1, fi_mode=int, round_value=6, allow_empty=False, **kwargs):
		self.tooltip_depth += 1
		super().__init__(**kwargs)
		self.tooltip_types.append('Scroll-Input')
		self.multiline = False
		self.min_value = min_value
		self.max_value = max_value
		self.increment = increment
		self.round_value = round_value
		if fi_mode == int or fi_mode == float:
			self.fi_mode = fi_mode
			self.input_filter = fi_mode.__name__
			self.hybrid_mode = False
		elif fi_mode == 'hybrid_int':
			self.fi_mode = int
			self.hybrid_mode = True
		elif fi_mode == 'hybrid_float':
			self.fi_mode = float
			self.hybrid_mode = True
		self.allow_empty = allow_empty
		self.finalize_tooltip()

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

	# When scrolling to change numerical values this function sets the new value based on the old value and increment according to which buttons are pressed
	@handle_exceptions
	def calculate_new_value(self, value, positive):
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
		
		current_increment = self.fi_mode(current_increment)
		new_value = value + current_increment if positive else value - current_increment
		new_value = min(max(new_value, self.min_value), self.max_value)
		new_value = round(new_value,self.round_value)
		return new_value

	@handle_exceptions
	def on_touch_down(self, touch):
		if not self.collide_point(*touch.pos):
			return
		# Call the parent on_touch_down function for Kivy's standard behavior
		super().on_touch_down(touch)
		if not touch.is_mouse_scrolling or not self.text:
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

					new_value = str(self.calculate_new_value(value, touch.button == 'scrolldown'))

					# Replace the selected text with the new value
					self.text = self.text[:start] + new_value + self.text[end:]

					# Maintain the selection with adjusted indexes
					self.select_text(start, start + len(new_value))
				except ValueError:
					pass

			else: # No text selected, try the entire field
				try:
					value = self.fi_mode(self.text)
					overwrite_text = True
				except ValueError:
					overwrite_text = False

				if not overwrite_text: # Something in the field interferes, check if the text contains a valid number using regex
					number_match = re.search(r'[-+]?\d*\.\d+|[-+]?\d+', self.text)
					if number_match:
						start, end = number_match.start(), number_match.end()
						number_text = number_match.group(0)

						try:
							value = self.fi_mode(number_text)
							new_value = self.calculate_new_value(value, touch.button == 'scrolldown')

							new_text = self.text[:start] + str(new_value) + self.text[end:]
							self.text = new_text

							# Maintain the selection with adjusted indexes
							self.select_text(start, start + len(str(new_value)))
						except ValueError:
							pass
				else: #The field can be parsed, simply adjust it directly
					new_value = self.calculate_new_value(value, touch.button == 'scrolldown')

					# Set the whole text to the new value
					self.text = str(new_value)

# 07. Combines both classes above
class FScrollInput(FTextInput, ScrollInput):
	pass

# 08. Special input field needed for the ResolutionSelector
class ComboCappedScrollInput(ScrollInput):
	@handle_exceptions
	def __init__(self, paired_field=None, **kwargs):
		self.tooltip_depth += 1
		super().__init__(**kwargs)
		self.paired_field = paired_field
		self.tooltip_types = ['Resolution Scroll-Input']
		self.finalize_tooltip()

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
		if not self.collide_point(*touch.pos):
			return
		if touch.is_mouse_scrolling:
			if touch.button == 'scrolldown':
				if (int(self.text)+64)*int(self.paired_field.text)>3145728:
					pass
				else:
					self.text = str(round(min(self.fi_mode(self.text) + self.increment,self.max_value),self.round_value))
			elif touch.button == 'scrollup':
				self.text = str(round(max(self.fi_mode(self.text) - self.increment,self.min_value),self.round_value))
		super(ScrollInput, self).on_touch_down(touch)

# 09. Special input field used in the SeedGrid to allow quick randomizing/clearing of individual fields
class SeedScrollInput(ScrollInput):
	@handle_exceptions
	def __init__(self, **kwargs):
		self.tooltip_depth += 1
		super().__init__(**kwargs)
		self.tooltip_types.insert(0, 'Seed')
		self.finalize_tooltip()

	# Checks if a user pressed r or c in a SeedGrid field to randomize or clear it's contents
	@handle_exceptions
	def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
		if keycode[1] == 'r':
			self.text = str(IM_G.generate_seed())
		elif keycode[1] == 'c' and 'ctrl' not in modifiers:
			self.text = ''
		elif keycode[1] == 'p':
			self.text = GS.pre_last_seed
		elif keycode[1] == 'l':
			self.text = GS.last_seed
		return super().keyboard_on_key_down(keyboard, keycode, text, modifiers)

# 10. This is a widget to at least approximate the token cost of a prompt
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

# 11. A class for the big image preview
class ImagePreview(Image):
	@handle_exceptions
	def __init__(self, **kwargs):
		super(ImagePreview, self).__init__(**kwargs)
		self.texture = Texture.create(size=(1,1), colorfmt='rgba')
		self.fit_mode = 'contain'
		self.last_associated_image_entry = None

	@handle_exceptions
	def load_image(self, image_entry):
		try:
			image = PILImage.open(io.BytesIO(image_entry.raw_image_data))
			if image.mode != 'RGBA':
				image = image.convert('RGBA')
			self.texture = Texture.create(size=(image.size[0], image.size[1]), colorfmt='rgba')
			flipped_image = image.transpose(PILImage.FLIP_TOP_BOTTOM)
			self.texture.blit_buffer(flipped_image.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
			Clock.schedule_once(handle_exceptions(lambda dt: setattr(self, 'opacity', 1)))
			if self.last_associated_image_entry != None:
				self.last_associated_image_entry.preview.displayed = False
			self.last_associated_image_entry = image_entry
		except:
			traceback.print_exc()

# 12. These next classes are responsible for various buttons that change states in the UI
class DoubleEmojiButton(Button):
	enabled = BooleanProperty(True)

	@handle_exceptions
	def __init__(self, symbol1='', symbol2='', **kwargs):
		super().__init__(alternate_update_func = (lambda: self.on_enabled()), **kwargs)
		self.font_size = 23 ###Consider checking for values like these and making them variables
		self.font_name = 'NotoEmoji'
		self.symbol1 = symbol1
		self.symbol2 = symbol2
		self.on_enabled()

	@handle_exceptions
	def on_enabled(self, *args):
		if self.enabled:
			self.background_color = GS.theme["SBtnBgOn"]["value"]
			self.text = self.symbol1
		else:
			self.background_color = GS.theme["SBtnBgOff"]["value"]
			self.text = self.symbol2
		self.color = GS.theme["SBtnText"]["value"]

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

# 13. Used for various places where a button to switch between two states is needed like SMEA/Dyn
class StateShiftButton(Button):
	enabled = BooleanProperty(False)
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(alternate_update_func = (lambda: self.on_enabled()), **kwargs)
		self.font_size=font_large
		self.on_enabled()

	@handle_exceptions
	def on_enabled(self, *args):
		if self.enabled:
			self.background_color = GS.theme["SBtnBgOn"]["value"]
		else:
			self.background_color = GS.theme["SBtnBgOff"]["value"]
		self.color = GS.theme["SBtnText"]["value"]

	@handle_exceptions
	def on_release(self):
		self.enabled = not self.enabled

# 14. Both the prompt and negative prompt use one of these buttons to handle the switching and the injector
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
		self.on_enabled()
	@handle_exceptions
	def on_enabled(self, *args):
		super(StateFButton, self).on_enabled(*args)
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

# 15. These classes are for injector dropdowns, dropdowns that are attached to a field and can inject their values into it
class InjectorDropDown(BoxLayout):
	@handle_exceptions
	def __init__(self, dropdown_list=[], button_text='', target=None, inject_identifier='P', **kwargs):
		super().__init__(**kwargs)
		self.orientation='vertical'
		self.target=target
		self.inject_identifier=inject_identifier
		self.dropdown = DropDown(auto_width=False,size_hint=(1, None)) # Here me make sure that the dropdown uses the whole window
		dropdown_button = Button(text=button_text, size_hint=(None, 1), width=field_height, height=field_height*2)
		dropdown_button.bind(on_release=handle_exceptions(lambda *args: self.dropdown.open(dropdown_button)))
		# Update the dropdown button text when an item is selected
		self.dropdown.bind(on_select=handle_exceptions(lambda instance, x: setattr(dropdown_button, 'text', x)))
		self.add_widget(dropdown_button)

		# Create a button for each item in the list
		for item in dropdown_list:
			self.add_button(item)

	@handle_exceptions
	def add_button(self, item):
		item_string = item['string']  # Store the string in a local variable
		# Create a label for the name and string
		item_label = BgLabel(text=f'[u]{item["name"]}[/u]\n{item_string}',markup=True,size_hint=(1, 1))
		item_label.bind(
			width=handle_exceptions(lambda *args, item_label=item_label: item_label.setter('text_size')(item_label, (item_label.width, None))),
			texture_size=handle_exceptions(lambda *args, item_label=item_label: item_label.setter('height')(item_label, item_label.texture_size[1]))
		)
		# Create a box layout for the item
		item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height*2)
		# Create a button to copy the string to the clipboard
		copy_button = Button(text='Copy', font_size=font_large, size_hint=(None, None), width=50, height=field_height*2)
		copy_button.bind(on_release=handle_exceptions(lambda *args, item_string=item_string, item_layout=item_layout: self.copy_to_clipboard(item_string, item_layout)))
		# Create a button to prepend the string to the text box
		prepend_button = Button(text='>' + self.inject_identifier, font_size=font_large, size_hint=(None, None), width=50, height=field_height*2)
		prepend_button.bind(on_release=handle_exceptions(lambda *args, item_string=item_string, item_layout=item_layout: self.prepend_to_text_box(item_string, item_layout)))
		# Create a button to append the string to the text box
		append_button = Button(text=self.inject_identifier + '<', font_size=font_large, size_hint=(None, None), width=50, height=field_height*2)
		append_button.bind(on_release=handle_exceptions(lambda *args, item_string=item_string, item_layout=item_layout: self.append_to_text_box(item_string, item_layout)))
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

class SamplerInjectorDropDown(InjectorDropDown):
	@handle_exceptions
	def __init__(self, dropdown_list=[], button_text='', target=None, **kwargs):
		super().__init__(dropdown_list=dropdown_list, button_text=button_text, target=target, **kwargs)

	@handle_exceptions
	def add_button(self, item, *args):
		item_layout, item_string = super(SamplerInjectorDropDown, self).add_button(item, *args)
		if not (item_string == 'ddim' or item_string == 'plms'):
			sampler_smea = StateShiftButton(text='SMEA', size_hint=(None, 1), size=(70,field_height))
			sampler_dyn = StateShiftButton(text='Dyn', size_hint=(None, 1), size=(70,field_height))

			sampler_smea.bind(enabled=handle_exceptions(lambda instance, value: on_smea_disabled(value, sampler_dyn)))
			sampler_dyn.bind(enabled=handle_exceptions(lambda instance, value: on_dyn_enabled(value, sampler_smea)))
			item_layout.add_widget(sampler_smea, index=1)
			item_layout.add_widget(sampler_dyn, index=1)

	@handle_exceptions
	def copy_to_clipboard(self, string, item_layout):
		string = self.attach_noise_smea_dyn(string, item_layout)
		Clipboard.copy(string)

	@handle_exceptions
	def prepend_to_text_box(self, string, item_layout):
		string = self.attach_noise_smea_dyn(string, item_layout)
		self.target.text = string + self.target.text

	@handle_exceptions
	def append_to_text_box(self, string, item_layout):
		string = self.attach_noise_smea_dyn(string, item_layout)
		self.target.text += string

	@handle_exceptions
	def attach_noise_smea_dyn(self, string, item_layout):
		string += '_' + GS.MAIN_APP.noise_schedule_button.text
		if type(item_layout.children[1]) == StateShiftButton: # If the sampler doesn't have these buttons that's a sign that it's not supported anyway and we skip
			if item_layout.children[1].enabled: #Dyn
				string += '_dyn'
			elif item_layout.children[2].enabled: #SMEA
				string += '_smea'
		return string + ', '

# 16. A slightly more advanced dropdown button that allows scrolling values without opening the dropdown
class ScrollDropDownBehavior(object):
	@handle_exceptions
	def __init__(self, associated_dropdown, get_children_func=None, set_state_func=None, **kwargs):
		self.associated_dropdown = associated_dropdown
		self.get_children_func = get_children_func or (lambda: self.associated_dropdown.children[0].children)
		self.set_state_func = set_state_func or (lambda index: setattr(self, 'text', self.children[index].text))
		super().__init__(**kwargs)
		self.bind(on_release=associated_dropdown.open)

	@handle_exceptions
	def on_touch_down(self, touch):
		if not self.collide_point(*touch.pos):
			return
		if touch.is_mouse_scrolling:
			if touch.button == 'scrolldown' or touch.button == 'scrollup':
				self.children = self.get_children_func()
				current_index = 0
				for i, child in enumerate(self.children):
					if child.text == self.text:
						current_index = i
						break
			if touch.button == 'scrolldown':
				# Get next index dropdown list
				index = (current_index + 1) % len(self.children)
			elif touch.button == 'scrollup':
				# Get previous index dropdown list
				index = (current_index - 1) % len(self.children)
			self.set_state_func(index)
		return super().on_touch_down(touch)
class ScrollDropDownButton(ScrollDropDownBehavior, Button):
	pass
class ScrollDropDownImage(ScrollDropDownBehavior, AsyncImage):
	border = ListProperty([16, 16, 16, 16])
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
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
			Clock.schedule_once(handle_exceptions(lambda dt: setattr(self, 'opacity', 1)))
		except:
			traceback.print_exc()

# 17. Class for the Cluster Collage/Image Sequence/Cluster Sequence buttons at the top, also handles showing/hiding the according elements and has bools for its state
class ModeSwitcher(BoxLayout):
	@handle_exceptions
	def __init__(self, app='', **kwargs):
		super(ModeSwitcher, self).__init__(**kwargs)
		self.app=app
		self.cc_active = True
		self.is_active = False
		self.cs_active = False
		self.cc_button = Button(text='Cluster Collage', on_press=self.switch_cc, register_to = None, tooltip_types=['Cluster Collage'])
		self.is_button = Button(text='Image Sequence', on_press=self.switch_is, register_to = None, tooltip_types=['Image Sequence'])
		self.cs_button = Button(text='Cluster Sequence', on_press=self.switch_cs, register_to = None, tooltip_types=['Cluster Sequence'])
		self.add_widget(self.cc_button)
		self.add_widget(self.is_button)
		self.add_widget(self.cs_button)
		self.update_state_color(None)
	
	# These functions are responsible for switching between the cluster collage and image sequence layouts
	@handle_exceptions
	def switch_cc(self, f):
		if self.cc_active == True:
			return
		self.cc_active, self.is_active, self.cs_active = True, False, False
		self.update_state_color(None)
		self.unhide_widgets(self.app.cc_exclusive_widgets)
		self.hide_widgets(self.app.is_exclusive_widgets)

	@handle_exceptions
	def switch_is(self, f):
		if self.is_active == True:
			return
		self.cc_active, self.is_active, self.cs_active = False, True, False
		self.update_state_color(None)
		self.unhide_widgets(self.app.is_exclusive_widgets)
		self.hide_widgets(self.app.cc_exclusive_widgets)

	@handle_exceptions
	def switch_cs(self, f):
		if self.cs_active == True:
			return
		self.cc_active, self.is_active, self.cs_active = False, False, True
		self.update_state_color(None)
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
				
				widget.ori_children = widget.children[::-1]
				widget.clear_widgets()

	@handle_exceptions
	def unhide_widgets(self, widgets):
		try:
			for widget in widgets:
				widget.opacity = widget.ori_opacity
				widget.height = widget.ori_height
				widget.width = widget.ori_width
				widget.size_hint_y = widget.ori_size_hint_y
				widget.size_hint_x = widget.ori_size_hint_x
				
				widget.clear_widgets()
				for child in widget.ori_children:
					widget.add_widget(child)
		except:
			pass
	
	@handle_exceptions
	def update_state_color(self, instance):
		self.cc_button.background_color = GS.theme["SBtnBgOn"]["value"] if self.cc_active else GS.theme["SBtnBgOff"]["value"]
		self.is_button.background_color = GS.theme["SBtnBgOn"]["value"] if self.is_active else GS.theme["SBtnBgOff"]["value"]
		self.cs_button.background_color = GS.theme["SBtnBgOn"]["value"] if self.cs_active else GS.theme["SBtnBgOff"]["value"]
		self.cc_button.color, self.is_button.color, self.cs_button.color = GS.theme["SBtnText"]["value"], GS.theme["SBtnText"]["value"], GS.theme["SBtnText"]["value"]

# 18. SeedGrid class for seed grids when making cluster collages
class SeedGrid(GridLayout):
	@handle_exceptions
	def __init__(self, **kwargs):
		super(SeedGrid, self).__init__(**kwargs)
		self.cols=2
		self.seed_inputs = []
		self.cc_seed_grid = GridLayout(cols=3, size_hint=(1, 1), size=(100, field_height*4))
		
		self.seed_cols_input = ScrollInput(text='3', size_hint=(1, None), width=60, height=field_height)
		self.seed_rows_input = ScrollInput(text='3', size_hint=(1, None), width=60, height=field_height)
		self.seed_mult_label = Label(text='×', size_hint=(None, None), width=20, height=field_height)
		self.dim_input_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=field_height)
		self.dim_input_layout.add_widget(self.seed_cols_input)
		self.dim_input_layout.add_widget(self.seed_mult_label)
		self.dim_input_layout.add_widget(self.seed_rows_input)
		self.seed_cols_input.bind(text=self.adjust_grid_size)
		self.seed_rows_input.bind(text=self.adjust_grid_size)

		self.btn1 = Button(text='Randomize', size_hint=(1, None), size=(100, field_height))
		self.btn1.bind(on_release=handle_exceptions(lambda btn: self.randomize()))
		self.btn2 = Button(text='Clear', size_hint=(1, None), size=(100, field_height))
		self.btn2.bind(on_release=handle_exceptions(lambda btn: self.clear()))
		self.btn3 = Button(text='Load List', size_hint=(1, None), size=(100, field_height))

		# create label for the multiplication sign between width and height
		self.seed_list_dropdown = DropDown()
		self.btn3.bind(on_release=self.seed_list_dropdown.open)
		for seed_list in GS.SEED_LISTS:
			btn = DropDownEntryButton(text=seed_list["name"], size_hint_y=None, height=field_height)
			btn.bind(on_release=handle_exceptions(lambda btn, seed_list=seed_list: (self.load_seeds(seed_list["seeds"]), self.seed_list_dropdown.dismiss())))
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
			nuke_widgets(self.seed_inputs.pop())

		# add any missing input widgets
		while len(self.seed_inputs) < num_inputs:
			seed_input = SeedScrollInput(text='', min_value=0, max_value=4294967295, increment=1000, multiline=False, font_size=font_small, allow_empty=True, fi_mode=int)
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

# 19. PromptGrid class for the use of f-strings in prompting
class PromptGrid(GridLayout):
	@handle_exceptions
	def __init__(self, tooltip_types='Prompt', **kwargs):
		super().__init__(**kwargs)
		self.rows = 1
		self.prompt_rows = 1
		self.prompt_inputs = []
		self.prompt_eval_list = BoxLayout(orientation='vertical', size_hint=(1, 1), size=(100, field_height*4))
		self.btn1 = Button(text='Row+', size_hint=(1, None), size=(100, field_height))
		self.btn1.bind(on_release=handle_exceptions(lambda btn: self.on_increase_rows()))
		self.btn2 = Button(text='Row-', size_hint=(1, None), size=(100, field_height))
		self.btn2.bind(on_release=handle_exceptions(lambda btn: self.on_decrease_rows()))
		self.btn3 = Button(text='Copy ⁅⁆', size_hint=(1, None), size=(100, field_height))
		self.btn3.bind(on_release=handle_exceptions(lambda btn: Clipboard.copy('⁅⁆')))
		self.btn3.font_name = 'Unifont'
		self.btn4 = Button(text='Inject ⁅⁆', size_hint=(1, None), size=(100, field_height))
		self.btn4.bind(on_release=handle_exceptions(lambda btn: setattr(self.prompt_inputs[0], 'text', self.prompt_inputs[0].text+'⁅⁆')))
		self.btn4.font_name = 'Unifont'
		self.btn5 = Button(text='Inject ⁅Seq.⁆', size_hint=(1, None), size=(100, field_height))
		self.btn5.bind(on_release=handle_exceptions(lambda btn: setattr(self.prompt_inputs[0], 'text', self.prompt_inputs[0].text+'''⁅'♥‼¡'*n⁆''')))
		self.btn5.font_name = 'Unifont'
		self.btn6 = Button(text='Inject ⁅List⁆', size_hint=(1, None), size=(100, field_height))
		self.btn6.bind(on_release=handle_exceptions(lambda btn: setattr(self.prompt_inputs[0], 'text', self.prompt_inputs[0].text+'''⁅['0','1','...'][n]⁆''')))
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
			prompt_input = FTextInput(multiline=True, text='⁅⁆', tooltip_types=['Prompt'])
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
				prompt_str = str(prompts[i])
				if prompt_str.startswith('''['f"""''') and prompt_str.endswith('''"""']'''): # Legacy format - strip the `['f"""` and `"""]`
					self.prompt_inputs[i].text = prompt_str[6:-5].replace("\\'", "'")
				else:
					self.prompt_inputs[i].text = prompt_str
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

# 20. In order to use the previous generation metadata, this class replicates a functional read-only console
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
	def __init__(self, max_lines=180, **kwargs):
		super().__init__(**kwargs)
		self.update_console_colors()
		self.orientation = 'vertical'
		self.max_lines = max_lines
		self.message_cache = ''
		self.error_cache = ''
		self.ui_console_cache = ''
		self.flush_scheduled = False

		self.output_text = Label(text='', font_size=12, size_hint=(1,None), markup=True)
		self.output_text.bind(
			width=handle_exceptions(lambda *x: self.output_text.setter('text_size')(self.output_text, (self.output_text.width, None))),
			texture_size=handle_exceptions(lambda *x: self.output_text.setter('height')(self.output_text, self.output_text.texture_size[1])))
		self.output_scroll = ScrollView(size_hint=(1, 1), effect_cls=ScrollEffect)
		self.output_scroll.add_widget(self.output_text)
		self.add_widget(self.output_scroll)
		self._stdout = sys.stdout
		self._stderr = sys.stderr
		sys.stdout = self.pass_out = self.TerminalPass(type='out', parent=self)
		sys.stderr = self.pass_err = self.TerminalPass(type='err', parent=self)
		Clock.schedule_interval(self.flush_message_caches, 0.5)

	# No @handle_exceptions here. As the function that is responsible for intercepting and splitting terminal messsages it's handled differently, lest we get loops
	def process_message(self, message, type):
		try:
			if message.startswith("[Warning]"):
				self.message_cache += message
				self.ui_console_cache += f'{self.rgba_to_string(GS.current_console_colors["ConWarn"]["value"])}{message[len("[Warning] "):]}[/color]'
			elif type == 'out':
				self.message_cache += message
				if message.replace(' ', '').replace('\n', '') == '':
					self.ui_console_cache += message
				else:
					self.ui_console_cache += f'{self.rgba_to_string(GS.current_console_colors["ConNorm"]["value"])}{message}[/color]'
			elif type == 'err':
				self.error_cache += message
				self.ui_console_cache += f'{self.rgba_to_string(GS.current_console_colors["ConErr"]["value"])}{message}[/color]'
		except:
			# As this function would loop when using the normal print statement but still needs debugging support we also use _stderr for exceptions
			self._stderr.write(traceback.format_exc())

	# Because any printing of messages is generally speaking aggressively inefficient and performance hungry, we cache everything and flush it twice per second
	# Excused from @handle_exceptions for the same reasons as the function above
	def flush_message_caches(self, dt):
		try:
			self.fix_console_text = False
			if self.message_cache != '':
				self._stdout.write(self.message_cache)
				self.message_cache = ''
			if self.error_cache != '':
				self._stderr.write(self.error_cache)
				self.error_cache = ''
			if self.ui_console_cache != '':
				if self.output_text.text:
					if self.output_text.text[-1] != '\n':
						self.ui_console_cache = '\n' + self.ui_console_cache
				self.output_text.text += self.ui_console_cache
				self.ui_console_cache = ''
				self.fix_console_text = True
			
			if self.fix_console_text:
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
				self._stderr.write(traceback.format_exc())

	# Converts a color in the format kivy uses into a tag that the KW.Console class can use
	@handle_exceptions
	def rgba_to_string(self, color):
		return '[color={}{}'.format(''.join(hex(int(c * 255))[2:].zfill(2) for c in color), ']')

	@handle_exceptions
	def update_console_colors(self):
		if not getattr(self, 'output_text', False):
			GS.current_console_colors = {"ConNorm": copy.deepcopy(GS.theme["ConNorm"]), "ConWarn": copy.deepcopy(GS.theme["ConWarn"]), "ConErr": copy.deepcopy(GS.theme["ConErr"])}
			return
		else:
			replacement_list = [[self.rgba_to_string(x), self.rgba_to_string(y)] for x, y in zip(
			[GS.current_console_colors["ConNorm"]["value"], GS.current_console_colors["ConWarn"]["value"], GS.current_console_colors["ConErr"]["value"]],
			[GS.theme["ConNorm"]["value"], GS.theme["ConWarn"]["value"], GS.theme["ConErr"]["value"]])]
			for colors in replacement_list:
				self.output_text.text = self.output_text.text.replace(str(colors[0]), str(colors[1]))
			GS.current_console_colors["ConNorm"]["value"] = copy.copy(GS.theme["ConNorm"]["value"])
			GS.current_console_colors["ConWarn"]["value"] = copy.copy(GS.theme["ConWarn"]["value"])
			GS.current_console_colors["ConErr"]["value"] = copy.copy(GS.theme["ConErr"]["value"])

	@handle_exceptions
	def flush(self):
		pass

# 21. A resolution selector that aims to have just about all the possible conveniences
class ResolutionSelector(BoxLayout):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(orientation='horizontal', size_hint=(1, None), height=field_height, **kwargs)
		
		# Create width and height input fields for custom resolution
		self.resolution_width = ComboCappedScrollInput(text='1024', increment=64, min_value=64, max_value=49152,
													 size_hint=(1, None), width=60, height=field_height)
		self.resolution_height = ComboCappedScrollInput(text='1024', increment=64, min_value=64, max_value=49152, paired_field=self.resolution_width, 
													  size_hint=(1, None), width=60, height=field_height)
		self.resolution_width.paired_field = self.resolution_height

		# create label for the multiplication sign between width and height
		resolution_mult_label = Label(text='×', size_hint=(None, None), width=20, height=field_height)

		# create dropdown button for selecting image mode
		self.resolution_menu_button = Button(text='SquareNormal', size_hint=(None, None), width=150, height=field_height)

		# create dropdown menu for image modes
		img_dropdown = DropDown()
		
		# create button for each category
		for category, modes in RESOLUTIONS.items():
			category_label = BgLabel(text=category, size_hint_y=None, height=field_height)
			img_dropdown.add_widget(category_label)
			# create button for each mode in category
			for mode in modes:
				img_button = DropDownEntryButton(text=mode, size_hint_y=None, height=field_height)
				img_button.bind(on_release=handle_exceptions(lambda img_button: self.set_size(img_button.text, self.resolution_width,
																			  self.resolution_height, img_dropdown)))
				img_dropdown.add_widget(img_button)

		# Bind update_resolution_dropdown to changes in width and height input fields
		self.resolution_width.bind(text=self.update_resolution_dropdown)
		self.resolution_height.bind(text=self.update_resolution_dropdown)

		# Bind opening of dropdown menu to dropdown button
		self.resolution_menu_button.bind(on_release=handle_exceptions(lambda *args: img_dropdown.open(self.resolution_menu_button)))
		img_dropdown.bind(on_select=handle_exceptions(lambda instance, x: setattr(self.resolution_menu_button, 'text', x)))

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

# 22. Popup for configuring settings
class FileHandlingWindow(Popup):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		content = BoxLayout(orientation='vertical')
		
		images_layout = BoxLayout(orientation='horizontal')
		images_label = Label(text='Images:', size_hint=(None,None), size=(130,field_height))
		self.images_input = TextInput(text = "placeholder 1", multiline=True, size_hint=(1, None), size=(100, field_height*3))
		images_layout.add_widget(images_label)
		images_layout.add_widget(self.images_input)
		
		videos_layout = BoxLayout(orientation='horizontal')
		videos_label = Label(text='Videos:', size_hint=(None,None), size=(130,field_height))
		self.videos_input = TextInput(text = "placeholder 2", multiline=True, size_hint=(1, None), size=(100, field_height*3))
		videos_layout.add_widget(videos_label)
		videos_layout.add_widget(self.videos_input)
		
		cc_layout = BoxLayout(orientation='horizontal')
		cc_label = Label(text='Cluster Collages:', size_hint=(None,1), size=(130,field_height))
		self.cc_input = TextInput(text = "placeholder 3", multiline=True, size_hint=(1, None), size=(100, field_height*3))
		cc_layout.add_widget(cc_label)
		cc_layout.add_widget(self.cc_input)
		
		settings_layout = BoxLayout(orientation='horizontal')
		settings_label = Label(text='Settings:', size_hint=(None,None), size=(130,field_height))
		self.settings_input = TextInput(text = "placeholder 4", multiline=True, size_hint=(1, None), size=(100, field_height*3))
		settings_layout.add_widget(settings_label)
		settings_layout.add_widget(self.settings_input)
		
		content.add_widget(images_layout)
		content.add_widget(videos_layout)
		content.add_widget(cc_layout)
		content.add_widget(settings_layout)

# 23. Popup for configuring settings
class ConfigWindow(Popup):
	@handle_exceptions
	def process_token(self, instance):
		token = self.token_input.text
		match = re.search(r'"auth_token":"([^"]+)"', token)
		if match:
			token = match.group(1)
		future = GS.EXECUTOR.submit(IM_G.generate_as_is,None,None,True,token)

	@handle_exceptions
	def process_token_callback(self, result, token):
		if result == 'Success':
			self.token_input.text = token
			token_file_content = f"""#Only the access token goes into this file. Do not share it with anyone else as that's against NAI ToS. Using it on multiple of your own devices is fine.
AUTH='{token}'
"""
			CH.write_config_file(os.path.join(GS.SETTINGS_DIR, "3.Token(DO NOT SHARE).py"),token_file_content)
			Clock.schedule_once(lambda dt: self.update_token_state(result))
			GS.AUTH = token
		else:
			Clock.schedule_once(lambda dt: self.update_token_state(result))
			return

	@handle_exceptions
	def update_token_state(self,state):
		if state=='Success':
			self.token_state.update_color(None)
			self.token_state.text = '✔️'
		else:
			self.token_state.update_color(None)
			self.token_state.text = '❌'

	@handle_exceptions
	def switch_eval_behavior(self,instance,label):
		if not instance.enabled:
			label.text = 'f-strings are evaluated in guarded mode'
		else:
			label.text = '''WARNING: f-strings are evaluated without restrictions, be thrice certain you don't blindly import malicious settings'''

	@handle_exceptions
	def check_for_error(self, instance):
		if GS.last_error != None:
			self.copy_error_button.disabled = False
	
	@handle_exceptions
	def open(self, instance):
		modifiers = EventLoop.window.modifiers
		if 'ctrl' in modifiers and 'shift' in modifiers and 'alt' in modifiers:
			GS.exec_popup.open()
		else:
			return super().open(instance)

	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.size_hint = (0.97, 0.97)
		self.bind(on_open=self.check_for_error)
		# Set up and add all the elements for the theme configurator
		layout = BoxLayout(orientation='vertical')
		
		user_settings_label = Label(text='User Settings:', size_hint=(1,None), size=(100,field_height), font_size=font_hyper)
		
		creator_name_label = Label(text='Creator name:', size_hint=(None,None), size=(300,field_height))
		creator_name_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
		self.creator_name_input = TextInput(text=GS.CREATOR_NAME, multiline=False, size_hint=(1,None), height=field_height)
		creator_name_layout.add_widget(creator_name_label)
		creator_name_layout.add_widget(self.creator_name_input)
		
		# Set up and add all the necessary elements for token handling
		token_button = Button(text='Set NovelAI token (DO NOT SHARE):', on_release=self.process_token, size_hint=(None,None), size=(300,field_height))
		self.token_state = BgLabel(font_name='NotoEmoji', text='❔', size_hint=(None,None), size=(field_height,field_height), register_to = None)
		token_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
		self.token_input = TextInput(text=GS.AUTH, multiline=False, size_hint=(1,None), size=(100+field_height,field_height))
		token_layout.add_widget(token_button)
		token_layout.add_widget(self.token_state)
		token_layout.add_widget(self.token_input)
		
		spacer_layout_1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
		generation_settings_label = Label(text='Generation Settings:', size_hint=(1,None), size=(100,field_height), font_size=font_hyper)
				
		history_length_label = Label(text='Generation history length:', size_hint=(None,None), size=(300,field_height))
		history_length_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
		self.history_length_input = ScrollInput(text='50', multiline=False, max_value=100000, size_hint=(1,None), height=field_height)
		history_length_layout.add_widget(history_length_label)
		history_length_layout.add_widget(self.history_length_input)
		
		skip_button = StateShiftButton(text='Skip Generation',on_release=handle_exceptions(lambda instance: setattr(GS, 'generate_images', not GS.generate_images)), size_hint=(1,None), size=(100,field_height))
		
		vid_params_label = Label(text='vid_params = ', size_hint=(None,None), size=(100,field_height))
		self.vid_params_input = TextInput(text = "{'fps': 10,'codec': 'vp9','pixelformat': 'yuvj444p',}", multiline=False, size_hint=(1, None), size=(100, field_height))
		vid_params_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
		vid_params_layout.add_widget(vid_params_label)
		vid_params_layout.add_widget(self.vid_params_input)
		
		eval_guard_label = Label(text='f-strings are evaluated in guarded mode', size_hint=(1,None), size=(100,field_height))
		self.eval_guard_button = DoubleEmojiButton(symbol1='🔰️', symbol2='⚠️',on_release=handle_exceptions(lambda eval_guard_button: self.switch_eval_behavior(eval_guard_button,eval_guard_label)),size_hint=(None,None), size=(field_height,field_height))
		eval_guard_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
		eval_guard_layout.add_widget(self.eval_guard_button)
		eval_guard_layout.add_widget(eval_guard_label)
		
		spacer_layout_2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
		misc_settings_label = Label(text='Misc Settings:', size_hint=(1,None), size=(100,field_height), font_size=font_hyper)
		
		self.copy_error_button = Button(text='Copy last error to clipboard', on_release=handle_exceptions(lambda btn: Clipboard.copy(GS.last_error)), size_hint=(1,None), size=(100,field_height), disabled=True)
		
		layout.add_widget(user_settings_label)
		layout.add_widget(creator_name_layout)
		layout.add_widget(token_layout)
		
		layout.add_widget(spacer_layout_1)
		layout.add_widget(generation_settings_label)
		layout.add_widget(history_length_layout)
		layout.add_widget(skip_button)
		#layout.add_widget(vid_params_layout)
		layout.add_widget(eval_guard_layout)
		
		layout.add_widget(spacer_layout_2)
		layout.add_widget(misc_settings_label)
		layout.add_widget(self.copy_error_button)
		self.add_widget(layout)

	# Saves the current state of the user settings
	@handle_exceptions
	def save_user_settings(self, instance, path=None):
		if self.theme_name_input.text != '' or path != None:
			config_content = f"""?
"""

# 24. Classes for the theme configurator
class ThemeButton(DropDownEntryButton):
	@handle_exceptions
	def __init__(self, starting_color, **kwargs):
		super().__init__(**kwargs)
		self.bind(size=self.update_rect, pos=self.update_rect)
	
	#Will be called once upon opening the dropdown and initializing these buttons, and then as needed, like when a new theme is set
	@handle_exceptions
	def update_rect(self, instance, value):
		self.canvas.before.clear()
		with self.canvas.before:
			Color(*self.associated_dict['value'])
			self.rect = Rectangle(pos=[self.pos[0]+self.size[0]+5,self.pos[1]+5], size=[40,40])
			Color(0, 0, 0) # For proper contrast and visibility the colors get a black/white double border
			self.black_border = Line(rectangle=[self.rect.pos[0]-1, self.rect.pos[1]-1, self.rect.size[0]+2, self.rect.size[1]+2], width=2)
			Color(1, 1, 1)
			self.white_border = Line(rectangle=[self.rect.pos[0]-3, self.rect.pos[1]-3, self.rect.size[0]+6, self.rect.size[1]+6], width=2)

# 25. A fully pre-assembled layout for the entire theme handling part, implemented into its own popup
class ThemeLayout(BoxLayout):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.orientation = 'vertical'
		self.selected_option = None
		self.dropdown = DropDown()
		self.color_picker = ColorPicker()
		self.color_picker.bind(color=self.on_color_picker_color)
		
		self.dropdown_button = ScrollDropDownButton(self.dropdown, text='', size_hint=(1,None), height=field_height,
		get_children_func=(lambda: [layout.children[0] for layout in self.dropdown_button.associated_dropdown.children[0].children]),
		set_state_func=(lambda index: self.on_option_button_press(self.dropdown_button.children[index])))
		self.theme_dropdown = DropDown(auto_width=False,size_hint=(1, None))
		self.open_folder_button = Button(text='📁', font_size=19, on_release=lambda btn: self.dropdown.select(os.startfile(GS.THEMES_DIR)), font_name = 'NotoEmoji', size_hint = (None, None), size = (field_height, field_height))
		
		first=True
		self.color_buttons = []
		# This loop builds the dropdown list for all the adjustable colors from the loaded theme
		for key, option in GS.theme.items():
			option_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
			color_button = ThemeButton(text=option["Name"], starting_color=option["value"], size_hint_x=None, width=250)
			color_button.associated_dict=option
			color_button.associated_key=key
			self.color_buttons.append(color_button)

			option_box.add_widget(color_button)
			self.dropdown.add_widget(option_box)

			color_button.bind(on_release=handle_exceptions(lambda btn: self.dropdown.select(color_button)))
			color_button.bind(on_release=handle_exceptions(lambda btn, option=option: self.on_option_button_press(btn)))
			if first:
				self.on_option_button_press(color_button)
				first=False
		
		self.apply_button = Button(text='Apply Theme', on_release=self.apply_theme, size_hint=(None,None), size=(120,field_height))
		self.load_button = Button(text='Load Theme', on_release=self.build_theme_dropdown, size_hint=(None,None), size=(120,field_height))
		self.save_button = Button(text='Save Theme', on_release=self.save_theme, size_hint=(None,None), size=(120,field_height))
		self.theme_name_input = TextInput(text='', multiline=False, size_hint=(1,None), height=field_height)
		self.theme_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
		self.theme_box.add_widget(self.open_folder_button)
		self.theme_box.add_widget(self.apply_button)
		self.theme_box.add_widget(self.load_button)
		self.theme_box.add_widget(self.save_button)
		self.theme_box.add_widget(self.theme_name_input)

		self.add_widget(self.color_picker)
		self.add_widget(self.dropdown_button)
		self.add_widget(self.theme_box)

	# Handles clicks on the dropdown buttons. It loads color and sets the necessary variables for adjusting the theme
	@handle_exceptions
	def on_option_button_press(self, button):
		self.selected_option = button
		self.color_picker.color = button.associated_dict["value"]
		self.dropdown_button.text = button.associated_dict["Name"]

	# Adjusts GS.theme
	@handle_exceptions
	def on_color_picker_color(self, instance, selected_color):
		self.selected_option.associated_dict["value"]=selected_color

	# Applies GS.theme to all the registered widgets and saves the applied theme to Current.py so it's used like that in future runs
	@handle_exceptions
	def apply_theme(self, instance):
		for color_button in self.color_buttons:
			color_button.update_rect(None, None)
		GS.MAIN_APP.drop_overlay.update_rect(None, 'rebuild')
		Window.clearcolor = GS.theme["ProgBg"]["value"]
		for widget in GS.theme_self_updating_widgets:
			widget.update_color(None)
		GS.MAIN_APP.console.update_console_colors()
		GS.MAIN_APP.mode_switcher.update_state_color(None)
		self.save_theme(None,'Current')

	# Called by the "Load Theme" button, always rebuilds the list from the current state of the themes folder
	@handle_exceptions
	def build_theme_dropdown(self,instance):
		self.theme_dropdown.clear_widgets()
		self.theme_files = [f for f in os.listdir(GS.THEMES_DIR) if f.endswith('.py')]
		for theme in self.theme_files:
			btn = DropDownEntryButton(text=os.path.splitext(theme)[0], size_hint_y = None, height = 44, width = 1000)
			btn.bind(on_release=lambda btn: self.load_theme(btn.text))
			self.theme_dropdown.add_widget(btn)
		self.theme_dropdown.open(self.load_button)

	# Called when a theme is selected from the dropdown, closes the dropdown, uses the config_handler to load the theme file, then applies it (which also saves it to Current.py)
	@handle_exceptions
	def load_theme(self, theme):
		self.theme_dropdown.dismiss()
		CH.load_config(os.path.join(GS.THEMES_DIR, f'{theme}.py'))
		path=GS.THEMES_DIR, f'{theme}.py'
		self.apply_theme(None)
		self.color_picker.color=GS.theme[self.selected_option.associated_key]["value"]

	# Saves the theme currently configured in the color picker using GS.theme, which isn't necessarily the applied theme the program currently uses
	@handle_exceptions
	def save_theme(self, instance, path=None):
		if self.theme_name_input.text != '' or path != None:
			config_content = f"""#Define your desired program colors here or from within CVF, the format is [R, G, B, A] with values from 0 to 1
THEME = {{
	'InText': {{'Name': 'Input: Text', 'value': {GS.theme["InText"]["value"]}}},
	'InBg': {{'Name': 'Input: Background', 'value': {GS.theme["InBg"]["value"]}}},
	
	'ProgText': {{'Name': 'Program Text', 'value': {GS.theme["ProgText"]["value"]}}},
	'ProgBg': {{'Name': 'Program Background', 'value': {GS.theme["ProgBg"]["value"]}}},
	
	'ConNorm': {{'Name': 'Console: Normal', 'value': {GS.theme["ConNorm"]["value"]}}},
	'ConWarn': {{'Name': 'Console: Warning', 'value': {GS.theme["ConWarn"]["value"]}}},
	'ConErr': {{'Name': 'Console: Error', 'value': {GS.theme["ConErr"]["value"]}}},
	
	'DBtnText': {{'Name': 'Dropdown Buttons: Text', 'value': {GS.theme["DBtnText"]["value"]}}},
	'DBtnBg': {{'Name': 'Dropdown Buttons: Background', 'value': {GS.theme["DBtnBg"]["value"]}}},
	
	'BgLText': {{'Name': 'BgLabel: Text', 'value': {GS.theme["BgLText"]["value"]}}},
	'BgLBg': {{'Name': 'BgLabel: Background', 'value': {GS.theme["BgLBg"]["value"]}}},
	
	'MBtnText': {{'Name': 'Main Buttons: Text', 'value': {GS.theme["MBtnText"]["value"]}}},
	'MBtnBg': {{'Name': 'Main Buttons: Background', 'value': {GS.theme["MBtnBg"]["value"]}}},
	
	'SBtnText': {{'Name': 'State Buttons: Text', 'value': {GS.theme["SBtnText"]["value"]}}},
	'SBtnBgOn': {{'Name': 'State Buttons: Active', 'value': {GS.theme["SBtnBgOn"]["value"]}}},
	'SBtnBgOff': {{'Name': 'State Buttons: Inactive', 'value': {GS.theme["SBtnBgOff"]["value"]}}},
	
	'TTText': {{'Name': 'Tooltip: Text', 'value': {GS.theme["TTText"]["value"]}}},
	'TTBg': {{'Name': 'Tooltip: Background', 'value': {GS.theme["TTBg"]["value"]}}},
	'TTBgOutline': {{'Name': 'Tooltip: Background Outline', 'value': {GS.theme["TTBgOutline"]["value"]}}},
}}
"""
			if path == None:
				CH.write_config_file(os.path.join(GS.THEMES_DIR, f'{self.theme_name_input.text}.py'),config_content)
			else:
				CH.write_config_file(os.path.join(GS.THEMES_DIR, f'{path}.py'),config_content)

class ThemeWindow(Popup):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.size_hint = (0.97, 0.97)
		# Set up and add all the elements for the theme configurator
		layout = BoxLayout(orientation='vertical')
		
		theme_example_layout = GridLayout(cols=2)
		self.theme_layout = ThemeLayout()
		self.add_widget(self.theme_layout)

# 26. This is an error popup that is currently only used for the token setting and testing
class ErrorPopup(ModalView):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs) 
		self.title = "Error"
		self.size_hint=(None, None)
		self.size=(dp(300),dp(100))
		self.padding = (dp(5), dp(5), dp(5), dp(5))
		self.content = BoxLayout(orientation='vertical')
		self.error_title = Label(text='', halign='left', valign='top', font_name = 'Roboto-Bold')
		self.error_title.bind(
		   width=lambda *x: 
			   self.error_title.setter('text_size')(self.error_title, (self.error_title.width, None)),
		   texture_size=lambda *x:
			   self.error_title.setter('height')(self.error_title, self.error_title.texture_size[1]))
		self.error_message = Label(text='', halign='left', valign='top')
		self.error_message.bind(
		   width=lambda *x: 
			   self.error_message.setter('text_size')(self.error_message, (self.error_message.width, None)),
		   texture_size=lambda *x:
			   self.error_message.setter('height')(self.error_message, self.error_message.texture_size[1]))
		self.content.add_widget(self.error_title)
		self.content.add_widget(self.error_message)
		self.add_widget(self.content)

	@handle_exceptions
	def show_generation_error(self, response):
		self.error_title.text = str(response.status_code)
		self.error_message.text = f"Server message: {json.loads(response.content)['message']}"
		self.open()
		return 'Error' # Reported above
GS.error_popup = ErrorPopup()

# 27. A spicy hidden developer dialogue, not intended for playing around and fun times
class ExecPopup(ModalView):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.size_hint=(None, None)
		self.size=(dp(400),dp(400))
		self.padding = (dp(5), dp(5), dp(5), dp(5))
		self.initial_warning_label = Label(text='''This is a developer tool for debugging first and foremost, it'll create and open an interface for arbitrary code execution.
Executing malicious code in here WILL damage your system. Do NOT use this if you don't know what you're doing and why.
Do NOT run code in here that you do not trust. You have been warned.''', font_name = 'Roboto-Bold')
		self.initial_warning_button = Button(text="I know what I'm doing, and I'm not going to run code that'll ruin this system, let me execute", font_name = 'Roboto-Bold')
		self.initial_warning_button.bind(on_release=self.exec_init)
		self.layout = BoxLayout(orientation='vertical')
		self.layout.add_widget(self.initial_warning_label)
		self.layout.add_widget(self.initial_warning_button)
		self.add_widget(self.layout)

	@handle_exceptions
	def exec_init(self, instance):
		self.layout.remove_widget(self.initial_warning_label)
		self.layout.remove_widget(self.initial_warning_button)
		self.ns = {}
		self.exec_input = TextInput(multiline=True, size_hint=(1, 1))
		self.verbose_button = Button(text="GS.verbose = True", font_name = 'Unifont', size_hint=(1, None), size=(100, field_height))
		self.verbose_button.bind(on_release=lambda x: setattr(GS, 'verbose', True))
		self.exec_button = Button(text="⚠⚠⚠EXECUTE⚠⚠⚠", font_name = 'Unifont', size_hint=(1, None), size=(100, field_height))
		self.exec_button.bind(on_release=handle_exceptions(lambda x: exec(self.exec_input.text, globals(), self.ns)))
		self.layout.add_widget(self.exec_input)
		self.layout.add_widget(self.verbose_button)
		self.layout.add_widget(self.exec_button)
		self.layout.add_widget(Label(text='CVF Version: ' + str(GS.VERSION), size_hint=(1, None), height = field_height))
GS.exec_popup = ExecPopup()

# 28. Gives a few quick pointers on how loading files works (with help of the background) as well as pointing out to users how to get tooltips
class DropOverlay(ModalView):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.size_hint = (1, 1)
		
		# Create a FloatLayout as the main container, with a BoxLayout to equal the main program space
		self.float_layout = FloatLayout()
		self.main_layout = BoxLayout(orientation='horizontal')
		
		left_x = GS.MAIN_APP.input_layout.size_hint_x
		right_x = GS.MAIN_APP.meta_layout.size_hint_x + GS.MAIN_APP.image_organization_layout.size_hint_x
		# Create two vertical BoxLayouts with background colors, the first equals the metadata field
		self.left_layout = BoxLayout(orientation='vertical', size_hint=(left_x, 1))
		# The second equals the console and image layout
		self.right_layout = BoxLayout(orientation='vertical', size_hint=(right_x, 1))

		self.left_layout.bind(pos=self.update_rect, size=self.update_rect)
		self.right_layout.bind(pos=self.update_rect, size=self.update_rect)
		self.update_rect(None, 'rebuild')
		
		# Create a close button
		close_button = Button(text='X', size_hint=(None, None), size=(40, 40),
							  pos_hint={'right': 1, 'top': 1})
		close_button.bind(on_release=self.dismiss)
		
		help_label = Label(text=DOC.HELP_TEXT, size_hint_y=1, markup=True)
		help_label.bind(
			#on_ref_press=self.open_link,
			width=handle_exceptions(lambda *x: help_label.setter('text_size')(help_label, (help_label.width, None))),
			)
		
		# Build the layout tree
		self.main_layout.add_widget(self.left_layout)
		self.main_layout.add_widget(self.right_layout)
		self.float_layout.add_widget(self.main_layout)
		self.float_layout.add_widget(close_button)
		self.float_layout.add_widget(help_label)
		self.add_widget(self.float_layout)

	# Updates the rectangle positions and also builts them in the first place or rebuilds them to change colors
	@handle_exceptions
	def update_rect(self, instance, value):
		if instance != self.right_layout:
			if value == 'rebuild':
				with self.left_layout.canvas.before:
					Color(*GS.theme["ProgBg"]["value"])  ### Program background
					self.left_rect = Rectangle(pos=self.left_layout.pos, size=self.left_layout.size)
			self.left_rect.pos = self.left_layout.pos
			self.left_rect.size = self.left_layout.size
		if instance != self.left_layout:
			if value == 'rebuild':
				with self.right_layout.canvas.before:
					Color(*adjust_color(GS.theme["ProgBg"]["value"]))
					self.right_rect = Rectangle(pos=self.right_layout.pos, size=self.right_layout.size)
			self.right_rect.pos = self.right_layout.pos
			self.right_rect.size = self.right_layout.size

# 29. Classes for image generation entries, both those created via AI as well as those imported
class ImageGenerationEntry(BoxLayout):
	destructible = BooleanProperty(True)

	@handle_exceptions
	def __init__(self, image, display=False, generation=False, initial_settings=['','0.7','0','','0.7','1'],**kwargs):
		super().__init__(**kwargs)
		self.lambdas = []
		self.orientation = 'horizontal'
		self.height = field_height*6
		self.size_hint_y = None
		self.generation = generation
		self.initial_settings = initial_settings
		self.i2i_true, self.vt_true = False, False
		for n in [0, 3]:
			if initial_settings[n] in ['true', 'True']:
				initial_settings[n] = ''
				if n == 0:
					self.i2i_true = True
				else:
					self.vt_true = True

		# The dropdown is best placed where it doesn't cover critical information, which these layouts here ensure
		self.left_layout = BoxLayout(size_hint_x=GS.MAIN_APP.input_layout.size_hint_x)
		# The second equals the console and is where the dropdown actually goes
		self.center_layout = FloatLayout(size_hint_x=GS.MAIN_APP.meta_layout.size_hint_x)
		# The third layout equals the image layout, the thing we do not want to hide while switching images
		self.right_layout = BoxLayout(size_hint_x=GS.MAIN_APP.image_organization_layout.size_hint_x)
		
		self.add_widget(self.left_layout)
		self.add_widget(self.center_layout)
		self.add_widget(self.right_layout)
		
		self.left_layout.bind(on_touch_down=self.on_outer_layouts_click)
		self.right_layout.bind(on_touch_down=self.on_outer_layouts_click)

		# Content area, using a BgLabel and BoxLayout occupying the same place to get a workable area with a theme registered background
		self.bg = BgLabel(text='', size_hint = (1, 1), pos_hint = {'x': 0, 'y': 0})
		self.content_area = BoxLayout(orientation='horizontal', size_hint=(1, 1), pos_hint = {'x': 0, 'y': 0})
		self.center_layout.add_widget(self.bg)
		self.center_layout.add_widget(self.content_area)

		# Create the preview image
		self.preview = BorderedImage(size_hint=(None, 1), width = self.height)
		self.preview.bind(on_touch_down=self.on_image_click)
		
		# Add the preview and content box to the layout
		self.content_box = BoxLayout(orientation='vertical', size_hint=(1, 1))
		self.content_area.add_widget(self.content_box)
		self.content_area.add_widget(self.preview)


		if not generation:
			self.setup_full_ui()
		else:
			self.setup_generation_ui()
			
		# Set the image
		self.set_image(image)
		
		if display:
			GS.MAIN_APP.preview.load_image(self)
			self.preview.displayed = True
			GS.MAIN_APP.metadata_viewer.switch_display(False)
		self.preview.img2img = self.i2i_true
		self.preview.vibe_transfer = self.vt_true

	def setup_full_ui(self):
		# Here we build up the necessary UI elements for image2image handling
		self.i2i_main_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
		self.i2i_top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 1))
		self.i2i_middle_layout = BoxLayout(orientation='horizontal', size_hint=(1, 1))
		self.i2i_bottom_layout = BoxLayout(orientation='horizontal', size_hint=(1, 1))
		
		self.i2i_button = StateShiftButton(text='I2I', enabled=self.i2i_true, width=30, size_hint_x=None, tooltip_types=['Image2image'])
		self.lambdas.append(lambda btn: setattr(self.preview, 'img2img', not btn.enabled))
		self.i2i_button.bind(on_release=handle_exceptions(self.lambdas[-1]))
		self.i2i_condition_label = Label(text='Condition:', width=80, size_hint_x=None)
		self.i2i_condition_input = FScrollInput(text=self.initial_settings[0], fi_mode='hybrid_float', size_hint_y=None, height=field_height, allow_empty=True, tooltip_types=['Truth Condition'])
		
		self.i2i_top_layout.add_widget(self.i2i_button)
		self.i2i_top_layout.add_widget(self.i2i_condition_label)
		self.i2i_top_layout.add_widget(self.i2i_condition_input)
		
		self.metadata_button = Button(text='MD', width=30, size_hint_x=None, tooltip_types=['Metadata Viewer'])
		self.lambdas.append(lambda btn: GS.MAIN_APP.metadata_viewer.display_metadata(self.raw_image_data))
		self.metadata_button.bind(on_release=handle_exceptions(self.lambdas[-1]))
		self.i2i_strength_label = Label(text='Strength:', width=80, size_hint_x=None)
		self.i2i_strength_input = FScrollInput(text=self.initial_settings[1], fi_mode='hybrid_float', min_value=0.01, max_value=0.99, size_hint_y=None, height=field_height, increment=0.1, tooltip_types=['Image2image Strength'])
		
		self.i2i_middle_layout.add_widget(self.metadata_button)
		self.i2i_middle_layout.add_widget(self.i2i_strength_label)
		self.i2i_middle_layout.add_widget(self.i2i_strength_input)
		
		self.lambdas.append(lambda: self.self_destruct())
		self.destruct_button = ConfirmButton(self.lambdas[-1], text='X', size_hint_y=None, height=field_height, tooltip_types=['Image Deletion'])
		self.i2i_noise_label = Label(text='Noise:', width=70, size_hint_x=None)
		self.i2i_noise_input = FScrollInput(text=self.initial_settings[2], fi_mode='hybrid_float', min_value=0, max_value=1, size_hint_y=None, height=field_height, increment=0.1, tooltip_types=['Image2image Noise'])
		
		self.i2i_bottom_layout.add_widget(self.destruct_button)
		self.i2i_bottom_layout.add_widget(self.i2i_noise_label)
		self.i2i_bottom_layout.add_widget(self.i2i_noise_input)
		
		self.i2i_main_layout.add_widget(self.i2i_top_layout)
		self.i2i_main_layout.add_widget(self.i2i_middle_layout)
		self.i2i_main_layout.add_widget(self.i2i_bottom_layout)
		
		# Here we build up the necessary UI elements for vibe transfer handling
		self.vt_main_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
		self.vt_top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 1))
		self.vt_middle_layout = BoxLayout(orientation='horizontal', size_hint=(1, 1))
		self.vt_bottom_layout = BoxLayout(orientation='horizontal', size_hint=(1, 1))
		
		self.vt_button = StateShiftButton(text='VT', enabled=self.vt_true, width=30, size_hint_x=None, tooltip_types=['Vibe Transfer'])
		self.lambdas.append(lambda btn: setattr(self.preview, 'vibe_transfer', not btn.enabled))
		self.vt_button.bind(on_release=handle_exceptions(self.lambdas[-1]))
		self.vt_condition_label = Label(text='Condition:', width=80, size_hint_x=None)
		self.vt_condition_input = FScrollInput(text=self.initial_settings[3], fi_mode='hybrid_float', size_hint_y=None, height=field_height, allow_empty=True, tooltip_types=['Truth Condition'])
		
		self.vt_top_layout.add_widget(self.vt_button)
		self.vt_top_layout.add_widget(self.vt_condition_label)
		self.vt_top_layout.add_widget(self.vt_condition_input)
		
		self.vt_strength_label = Label(text='Strength:', width=110, size_hint_x=None)
		self.vt_strength_input = FScrollInput(text=self.initial_settings[4], fi_mode='hybrid_float', min_value=-10, max_value=10, size_hint_y=None, height=field_height, increment=0.1, tooltip_types=['Vibe Transfer Strength'])
		

		self.vt_middle_layout.add_widget(self.vt_strength_label)
		self.vt_middle_layout.add_widget(self.vt_strength_input)
		
		self.vt_Information_label = Label(text='Info Ext.:', width=110, size_hint_x=None)
		self.vt_information_input = FScrollInput(text=self.initial_settings[5], fi_mode='hybrid_float', min_value=0.01, max_value=1, size_hint_y=None, height=field_height, increment=0.1, tooltip_types=['Vibe Transfer Information Extracted'])
		
		self.vt_bottom_layout.add_widget(self.vt_Information_label)
		self.vt_bottom_layout.add_widget(self.vt_information_input)
		
		self.vt_main_layout.add_widget(self.vt_top_layout)
		self.vt_main_layout.add_widget(self.vt_middle_layout)
		self.vt_main_layout.add_widget(self.vt_bottom_layout)
		
		# Adding the separate i2i and vt layouts to the content box
		self.content_box.add_widget(self.i2i_main_layout)
		self.content_box.add_widget(self.vt_main_layout)

		self.scrollable_sub_widgets = [self.i2i_condition_input, self.i2i_strength_input, self.i2i_noise_input,
			self.vt_condition_input, self.vt_strength_input, self.vt_information_input]

	def setup_generation_ui(self):
		# Set up the minimal UI for generation history
		self.metadata_button = Button(text='Metadata', size_hint_y=None, height=field_height, tooltip_types=['Metadata Viewer'])
		self.lambdas.append(lambda btn: GS.MAIN_APP.metadata_viewer.display_metadata(self.raw_image_data))
		self.metadata_button.bind(on_release=handle_exceptions(self.lambdas[-1]))
		self.load_button = Button(text='Load',size_hint_y=None, height=field_height)
		self.load_button.bind(on_release=self.load_as_permanent)
		self.lambdas.append(lambda: self.self_destruct())
		self.destruct_button = ConfirmButton(self.lambdas[-1], text='X', size_hint_y=None, height=field_height, tooltip_types=['Image Deletion'])
		
		self.padding_layout_top = BoxLayout(size_hint_y=None, height=field_height*1.5)
		self.center_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=field_height*3)
		self.padding_layout_bottom = BoxLayout(size_hint_y=None, height=field_height*1.5)
		
		self.center_layout.add_widget(self.metadata_button)
		self.center_layout.add_widget(self.destruct_button)
		self.center_layout.add_widget(self.load_button)
		
		self.content_box.add_widget(self.padding_layout_top)
		self.content_box.add_widget(self.center_layout)
		self.content_box.add_widget(self.padding_layout_bottom)
		
	@handle_exceptions
	def load_as_permanent(self, instance):
		# Create a new permanent ImageGenerationEntry
		new_entry = ImageGenerationEntry(self.raw_image_data, display=self.preview.displayed, generation=False)
		
		# Add the new entry to the loaded images dropdown
		GS.MAIN_APP.loaded_images_dropdown.add_widget(new_entry)
		
		# Remove this entry from the generated images dropdown
		GS.MAIN_APP.generated_images_dropdown.remove_widget(self)
		
		# Self-destruct this temporary entry
		self.self_destruct()

	@handle_exceptions
	def set_image(self, image):
		if isinstance(image, str): # When we get a string that means we have a file path we need to read in
			with open(image, 'rb') as f:
				self.raw_image_data = f.read()
		else: # This is for when we get raw PNG data from generations
			self.raw_image_data = image
		
		buf = io.BytesIO(self.raw_image_data)
		self.preview.image.texture = CoreImage(buf, ext='png').texture

	@handle_exceptions
	def on_image_click(self, instance, touch):
		if instance.collide_point(*touch.pos):
			GS.MAIN_APP.preview.load_image(self)
			self.preview.displayed = True
			GS.MAIN_APP.metadata_viewer.switch_display(False)

	@handle_exceptions
	def on_outer_layouts_click(self, instance, touch):
		if instance.collide_point(*touch.pos):
			self.parent.parent.dismiss()

	@handle_exceptions
	def self_destruct(self):
		if self.destructible:
			if GS.MAIN_APP.preview.last_associated_image_entry:
				if GS.MAIN_APP.preview.last_associated_image_entry.preview == self.preview:
					GS.MAIN_APP.preview.last_associated_image_entry = None
			if not self.generation:
				for scrollable_sub_widget in self.scrollable_sub_widgets:
					self.parent.parent.unregister_scrollable(scrollable_sub_widget)
			if GS.last_i2i_image == self:
				GS.last_i2i_image = None
			del self.raw_image_data
			self.preview.image.texture = None			
			for lamb in self.lambdas:
				del lamb
			nuke_widgets(self)

	@handle_exceptions
	def on_destructible(self, *args):
		self.destruct_button.disabled = not self.destructible

	@handle_exceptions
	def on_parent(self, *args):
		if not self.generation and self.parent != None:
			for scrollable_sub_widget in self.scrollable_sub_widgets:
				self.parent.parent.register_scrollable(scrollable_sub_widget)

class BorderedImage(BoxLayout):
	displayed = BooleanProperty(False)
	img2img = BooleanProperty(False)
	vibe_transfer = BooleanProperty(False)

	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.padding = 4
		self.image = Image()
		self.add_widget(self.image)
		
		self.border_width = 2
		self.bind(size=self.update_borders, pos=self.update_borders)
		self.bind(displayed=self.update_borders, vibe_transfer=self.update_borders)

	@handle_exceptions
	def on_img2img(self, *args):#ensure_single_img2img_state
		if self.img2img:
			if GS.last_i2i_image != self.parent.parent.parent and GS.last_i2i_image != None:
				GS.last_i2i_image.i2i_button.enabled = False
				GS.last_i2i_image.preview.img2img = False
			GS.last_i2i_image = self.parent.parent.parent
		self.update_borders()

	@handle_exceptions
	def update_borders(self, *args):
		self.canvas.before.clear()
		with self.canvas.before:
			if self.displayed:
				self.draw_full_border(1, 0, 0, 0.8, 0, 0)  # Red
			if self.img2img:
				self.draw_corner_border(0, 1, 0, 0, 0.8, 0)  # Green
			if self.vibe_transfer:
				self.draw_middle_border(0, 0, 1, 0, 0, 0.8)  # Blue

	@handle_exceptions
	def draw_full_border(self, r1, g1, b1, r2, g2, b2):
		x1, y1 = self.x + self.border_width, self.y + self.border_width
		x2, y2 = self.x + self.width - self.border_width, self.y + self.height - self.border_width
		
		Color(r1, g1, b1)
		Line(points=[x1, y1, x2, y1, x2, y2], width=self.border_width)
		Color(r2, g2, b2)
		Line(points=[x1, y1, x1, y2, x2, y2], width=self.border_width)

	@handle_exceptions
	def draw_corner_border(self, r1, g1, b1, r2, g2, b2):
		corner_length = min(self.width, self.height) / 6
		x1, y1 = self.x + self.border_width, self.y + self.border_width
		x2, y2 = self.x + self.width - self.border_width, self.y + self.height - self.border_width
		
		Color(r1, g1, b1)
		Line(points=[x1, y1, x1 + corner_length, y1, x1, y1, x1, y1 + corner_length], width=self.border_width)
		Line(points=[x2, y2, x2 - corner_length, y2, x2, y2, x2, y2 - corner_length], width=self.border_width)
		Color(r2, g2, b2)
		Line(points=[x2, y1, x2 - corner_length, y1, x2, y1, x2, y1 + corner_length], width=self.border_width)
		Line(points=[x1, y2, x1 + corner_length, y2, x1, y2, x1, y2 - corner_length], width=self.border_width)

	@handle_exceptions
	def draw_middle_border(self, r1, g1, b1, r2, g2, b2):
		middle_length = min(self.width, self.height) / 3
		mid_x, mid_y = self.x + self.width / 2, self.y + self.height / 2
		x1, y1 = self.x + self.border_width, self.y + self.border_width
		x2, y2 = self.x + self.width - self.border_width, self.y + self.height - self.border_width
		
		Color(r1, g1, b1)
		Line(points=[mid_x - middle_length/2, y1, mid_x + middle_length/2, y1], width=self.border_width)
		Line(points=[x2, mid_y - middle_length/2, x2, mid_y + middle_length/2], width=self.border_width)
		Color(r2, g2, b2)
		Line(points=[mid_x - middle_length/2, y2, mid_x + middle_length/2, y2], width=self.border_width)
		Line(points=[x1, mid_y - middle_length/2, x1, mid_y + middle_length/2], width=self.border_width)

# Used for image entries to allow most areas to scroll the dropdown, while still allowing scroll fields to have priority
class PermissiveScrollViewBehavior(object):
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.scrollable_sub_widgets = []

	@handle_exceptions
	def register_scrollable(self, widget):
		if widget not in self.scrollable_sub_widgets:
			self.scrollable_sub_widgets.append(widget)

	@handle_exceptions
	def unregister_scrollable(self, widget):
		if widget in self.scrollable_sub_widgets:
			self.scrollable_sub_widgets.remove(widget)

	@handle_exceptions
	def on_touch_down(self, touch):
		if self.collide_point(*touch.pos):
			for child in self.scrollable_sub_widgets:
				child_pos = child.to_widget(*touch.pos)
				if child.collide_point(*child_pos):
					touch.push()
					touch.apply_transform_2d(self.to_local)
					child.on_touch_down(touch)
					touch.pop()
					return True
		return super().on_touch_down(touch)

class PermissiveDropDown(PermissiveScrollViewBehavior, DropDown):
	pass

# 30. This class creates a proper metadata viewer that can parse and display both EXIf/alpha metadata verbatim
class MetadataViewer(BoxLayout):
	class PermissiveScrollView(PermissiveScrollViewBehavior, ScrollView):
		pass
	
	@handle_exceptions
	def __init__(self, **kwargs):
		super().__init__(orientation='vertical', **kwargs)
		self.scroll_view = self.PermissiveScrollView(effect_cls=ScrollEffect)
		self.content_layout = BoxLayout(orientation='vertical', size_hint_y=None)
		self.content_layout.bind(minimum_height=self.content_layout.setter('height'))
		self.scroll_view.add_widget(self.content_layout)
		self.add_widget(self.scroll_view)


	@handle_exceptions
	def display_metadata(self, raw_image_data):
		#self.content_layout.clear_widgets()
		nuke_widgets(self.content_layout.children)
		alpha_dict, exif_dict, size_fallback = load_metadata_dicts(raw_image_data)
		self.add_dict_to_layout("Alpha Channel Metadata", alpha_dict)
		self.add_dict_to_layout("EXIF Metadata", exif_dict)
		self.switch_display(True)

	@handle_exceptions
	def add_dict_to_layout(self, title, data_dict):
		title_label = Label(text=f'[b]{title}[/b]', markup=True, size_hint_y=None, height=field_height, font_size=font_hyper)
		self.content_layout.add_widget(title_label)
		self.add_dict_items(data_dict)

	@handle_exceptions
	def add_dict_items(self, data_dict, indent=1):
		for key, value in data_dict.items():
			if key in ['prompt', 'uc']:
				row_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height*4)
				scrollable = True
			else:
				row_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=field_height)
				scrollable = False
			
			indent_label = Label(text='↳' * indent + ' ', font_name='Unifont', size_hint_x=None, width=11*indent)
			key_label = self.create_aligned_label(key, size_hint_x=None)
			
			row_label_layout = BoxLayout(orientation='horizontal', size_hint_x=None, width=310)
			row_label_layout.add_widget(indent_label)
			row_label_layout.add_widget(key_label)
			row_layout.add_widget(row_label_layout)
			
			
			if isinstance(value, dict):
				self.content_layout.add_widget(row_layout)
				self.add_dict_items(value, indent + 1)
			else:
				value_str = str(value)
				if len(value_str) > 1500:
					value_str = value_str[:1500]
				value_input = TextInput(text=value_str, readonly=True, multiline=scrollable)
				if scrollable:
					self.scroll_view.register_scrollable(value_input)
				row_layout.add_widget(value_input)
				self.content_layout.add_widget(row_layout)

	@handle_exceptions
	def create_aligned_label(self, text, size_hint_x=None):
		label = Label(text=text, markup=True, halign='left', valign='middle')
		label.bind(
			width=lambda *x: setattr(label, 'text_size', (label.width, None)),
			texture_size=lambda *x: setattr(label, 'height', label.texture_size[1])
		)
		return label

	@handle_exceptions
	def switch_display(self, show_metadata):
		if show_metadata == 'invert':
			if self.opacity == 0:
				show_metadata = True
			else:
				show_metadata = False
		GS.MAIN_APP.mode_switcher.unhide_widgets([self] if show_metadata else [GS.MAIN_APP.preview])
		GS.MAIN_APP.mode_switcher.hide_widgets([GS.MAIN_APP.preview] if show_metadata else [self])
