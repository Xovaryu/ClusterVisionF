"""
initialization.py
	This module handles all the needed initialization at the start

01.	GlobalState
			GlobalState is a class that's responsible for organizing all the information that's shared back and forth between all modules
			GlobalState is a singleton using an adjusted __new__ instead of __init__
			The point of this is to make sure that the program structure remains understandable, functional and easy to change and improve
02.	handle_exceptions
			This is a decorator function used to wrap just about any and every function outside of the Kivy main thread, no matter what it is
			Its purpose is to prevent any and all silent crashes, make the program maximally robust and report all errors both in the console as well as the app
			Functions that get this wrapper do not halt the program and use traceback to report issues visibly both in the attached terminal and the console in the app
			The wrapper also saves the last error message to GS.last_error, making it available for quick copying in the UI
03.	load_fonts
			This function is responsible for loading in all the default and possibly user defined prompts
			Because of the importance of these fonts, the program can't properly start without these
"""
from fontTools.ttLib import TTFont
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import sys
import os
import traceback
import functools
import time
from PIL import ImageFont
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty

# Fetch the current running dir
if getattr(sys, 'frozen', False):
    # Running in a bundle
    full_dir = os.path.dirname(sys.executable) + '/'
else:
    # Running in a normal Python environment
    full_dir = os.path.dirname(os.path.realpath(__file__)) + '/'

# 1. The big singleton class to be employed whenever any global state or variable is needed
class GlobalState(EventDispatcher):
	_instance = None
	queued_images = NumericProperty(0)
	produced_images = NumericProperty(0)
	skipped_images = NumericProperty(0)
	queued_tasks = NumericProperty(0)
	finished_tasks = NumericProperty(0)
	skipped_tasks = NumericProperty(0)

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance.VERSION = 5.3
			cls._instance.MAIN_APP = None
			cls._instance.FULL_DIR = full_dir
			cls._instance.EXECUTOR = ThreadPoolExecutor()
			
			cls._instance.theme = None
			cls._instance.futures = []
			cls._instance.wait_time = 1
			cls._instance.processing_queue = deque()
			cls._instance.cancel_request = False
			cls._instance.pause_request = False
			cls._instance.overwrite_images = False
			cls._instance.generate_images = True
			cls._instance.last_error = None
			cls._instance.last_task_report = time.time()
			cls._instance.last_seed = ''
			cls._instance.pre_last_seed = ''
			cls._instance.preview_queue = []
			cls._instance.registered_text_inputs = []
			cls._instance.registered_menu_buttons = []
			cls._instance.registered_dropdown_buttons = []
			cls._instance.registered_state_buttons = []
			cls._instance.registered_labels = []
			cls._instance.registered_bglabels = []
			cls._instance.registered_tooltiplabels =  []
			cls._instance.verbose =  False
			cls._instance.skip = 0
			cls._instance.end = False
		return cls._instance
GS = GlobalState()

# 2. A decorator function to avoid silent crashes and make debugging and error reporting consistent
def handle_exceptions(func):
	@functools.wraps(func) # Needed to allow Kivy's bind method to work without issues
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except:
			traceback.print_exc()
			GS.last_error = traceback.format_exc()
	return wrapper

# The config handler must be imported at this later point since it loads values into the GlobalState and like all modules uses @handle_exceptions
import config_handler as CH

# 3. Loads the font list primarily for cluster collages
# No @handle_exceptions due to custom exception handling and this being an all or nothing function
def load_fonts():
	try:
		font_list = GS.CUSTOM_FONT_LIST_PREPEND + [
			# Roboto font, freeware from dafont.com
			full_dir + 'Fonts/Roboto-Regular.ttf',
			# Google Noto fonts provided with the OFL v1.1 license
			full_dir + 'Fonts/NotoEmoji-VariableFont_wght.ttf',
			full_dir + 'Fonts/NotoSansJP-VF.ttf',
			full_dir + 'Fonts/NotoSansSC-VF.ttf',
			full_dir + 'Fonts/NotoSansTC-VF.ttf',
			full_dir + 'Fonts/NotoSansKR-VF.ttf',
			full_dir + 'Fonts/NotoSansHK-VF.ttf',
			# Symbola font, freeware from fontlibrary.org
			full_dir + 'Fonts/Symbola.ttf',
			# GNU Unifont from unifoundry.com provided with OFL v1.1 and GNU GPL 2+ with the GNU font embedding exception
			full_dir + 'Fonts/unifont_jp-15.0.01.ttf',
		] + GS.CUSTOM_FONT_LIST_APPEND
		GS.FONT_OBJS = [ImageFont.truetype(str(x), GS.FONT_SIZE) for x in font_list]
#		GS.TT_FONTS = [TTFont(x) for x in font_list]

		cached_fonts = []
		for font_path in font_list:
			try:
				font = TTFont(font_path)
				cmap = font.getBestCmap()
				cached_font = {
					'font_obj': ImageFont.truetype(str(font_path), GS.FONT_SIZE),
					'font': font,
					'cmap': cmap
				}
				cached_fonts.append(cached_font)
			except Exception as e:
				print(f"Error loading font {font_path}: {e}")

		GS.CACHED_FONTS = cached_fonts
		GS.FONT_LIST = font_list
	except:
		traceback.print_exc()
		print(f'Loading fonts failed. Is the Fonts folder or any of the default/custom specified fonts missing? FONT_LIST: {font_list}')
		sys.exit()

load_fonts()