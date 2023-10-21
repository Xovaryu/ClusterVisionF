"""
initialization.py
	This module handles all the needed initialization at the start

01.	GlobalState
			GlobalState is a class that's responsible for organizing all the information that's shared back and forth between all modules
			GlobalState is a singleton using an adjusted __new__ instead of __init__
02.	handle_exceptions
			This is a decorator function used to wrap just about any and every function outside of the Kivy main thread, no matter what it is
			Its purpose is to prevent any and all silent crashes, make the program maximally robust and report all errors both in the console as well as the app
			Functions that get this wrapper do not halt the program and use traceback to report issues visibly both in the attached terminal and the console in the app
			The wrapper also saves the last error message to GS.LAST_ERROR, making it available for quick copying in the UI
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
	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance.FULL_DIR = full_dir			
			cls._instance.WAIT_TIME = 1
			cls._instance.PRODUCED_IMAGES = 0
			cls._instance.SKIPPED_IMAGES = 0
			cls._instance.QUEUED_IMAGES = 0
			cls._instance.PROCESSING_QUEUE = deque()
			cls._instance.PROCESSING_QUEUE_LEN = 0
			cls._instance.FINISHED_TASKS = 0
			cls._instance.SKIPPED_TASKS = 0
			cls._instance.WAITS_SHORT = 0
			cls._instance.WAITS_LONG = 0
			cls._instance.EXECUTOR = ThreadPoolExecutor()
			cls._instance.FUTURES = []
			cls._instance.CANCEL_REQUEST = False
			cls._instance.PAUSE_REQUEST = False
			cls._instance.OVERWRITE_IMAGES = False
			cls._instance.GENERATE_IMAGES = True
			cls._instance.LAST_ERROR = None
			cls._instance.LAST_TASK_REPORT = time.time()
			cls._instance.LAST_SEED = ''
			cls._instance.PRE_LAST_SEED = ''
			cls._instance.PREVIEW_QUEUE = []
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
			GS.LAST_ERROR = traceback.format_exc()
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
		GS.TT_FONTS = [TTFont(x) for x in font_list]
	except:
		traceback.print_exc()
		print(f'Loading fonts failed. Is the Fonts folder or any of the default/custom specified fonts missing? FONT_LIST: {font_list}')
		sys.exit()
	GS.FONT_LIST = font_list
load_fonts()
