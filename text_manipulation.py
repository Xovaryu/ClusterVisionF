"""
text_manipulation.py
	This module contains functions and classes strictly related to text manipulation

01.	replace_forbidden_symbols
			Because operating systems forbid the use of certain symbols in file and folder names this function is added to replace those when needed
02.	find_evaluated_fstring_braces
			Because evaluated f-strings should have a different color on the cluster collage for proper readability
			This function is used to make this possible by analyzing the sting and returning all the start/end indexes of the f-string braces
03.	unpack_list
			This function is just needed to make the multiple combined prompt fields usable
04.	fallback_font_writer
			Highly complex function to achieve a flexible "Everything Font".
			Is used for writing the text on cluster collages to make sure that no matter what symbol combination a user might need, it can be done
05.	f_string_pre_processor
			Takes the text from the frontend and adjusts it so that it's actually a valid f-string
			Called from within f_string_processor
06.	f_string_processor
			Takes the passed list of f-strings and evaluates them, depending on settings in restricted or unrestricted mode
			Used in various places all throughout the code to handle the various f-string user inputs
07.	make_file_path
			!: Should probably be deprecated and removed completely
08.	escape_quotes_for_saving
			This simple function does what the title says, it escapes all quotes so that they can be saved and loaded from files properly
09.	save_settings + save_image_entries
			Takes a settings dict and then saves it as a neatly formatted .py file that can be re-imported later
			Though save_image_entries is technically not text manipulation, it is right along here with save_settings as it's called together with it, if at all
			!: Likely needs filepath adjustments
10.	FilePathHandler
			This class handles the various requirements of generating/evaluating filepaths correctly during task processing
			Initialized per task and called whenever a filepath needs to be generated right when a file needs to be written
"""
from initialization import handle_exceptions, GlobalState
GS = GlobalState()
import os
import zlib
import base64
import json
import traceback
from copy import deepcopy
from collections import deque
from PIL import ImageDraw, ImageOps
import numpy as np
import math

BS = '\\' # This is here because f-strings do not yet (until Python 3.12 most likely) support backstrings in the evaluated part, necessitating this BS workaround

# 1. Replaces any forbidden symbols that would end up in file/folder names
@handle_exceptions
def replace_forbidden_symbols(string):
	string=string.replace('"','{QuotM}').replace('/','{Slash}').replace('\\','{BackSlash}').replace('?','{QuestM}').replace('*','{Asterisk}')
	return string.replace(':','{Colon}').replace('<','{LesserT}').replace('>','{GreaterT}').replace('|','{VertLine}')

# 2. Finds any ⁅⁆ f-string braces and returns the string as well as the indexes of the braces
@handle_exceptions
def find_evaluated_fstring_braces(string):
	indexes = []
	brace_stack = []
	in_string = False
	quote = None
	for i, char in enumerate(string):
		if char == '⁅':
			if not in_string:
				brace_stack.append(i)
			else:
				pass
		elif char == '⁆':
			if not in_string:
				if len(brace_stack) > 0:
					start = brace_stack.pop()
					indexes.append((start, i+1))
				else:
					pass
			else:
				pass
		elif char in ("'", '"'):
			if in_string and char == quote:
				in_string = False
				quote = None
			elif not in_string:
				in_string = True
				quote = char
			else:
				pass
		else:
			pass
	return string, indexes

# 3. Unpacks a list of prompts, used by the fallback font writer to be able to handle the splittable f-string prompt lists in the UI
@handle_exceptions
def unpack_list(lst, in_list=False):
	result = ''
	for item in lst:
		if isinstance(item, str):
			if in_list and item.startswith('f'):
				result += item[4:-3]
			else:
				result += item
		elif isinstance(item, list):
			result += unpack_list(item, in_list=True)
	return result

# 4. Writes a text on a passed image, character by character, going through a list of fonts and trying to find one that has the requested character
@handle_exceptions
def fallback_font_writer(draw, img, text, x, y, wrap_x, available_y_lines, line_height, fill, break_symbol='any', explicit_space=False):
	# Initialize needed variables
	starting_x = x
	line_width = 0
	used_lines = 1
	safety_offset_x = 75
	newline = False
	char_task = deque()
	last_symbol = -1  # Index of last symbol in deque

	text, indexes = find_evaluated_fstring_braces(unpack_list(text))

	for char_index, char in enumerate(text):
		if available_y_lines == 0:
			img = ImageOps.expand(img, border=(0, 0, 0, line_height), fill=(0, 0, 0))
			draw = ImageDraw.Draw(img)
			available_y_lines += 1
		if any(start <= char_index < end for start, end in indexes):
			contextual_fill = (fill[0],fill[1],0,fill[3])
		else:
			contextual_fill = fill
		# Try to render the character with each font in the font list
		font_used = None
		for cached_font in GS.CACHED_FONTS:
			if ord(char) in cached_font['cmap'].keys():
				font_used = cached_font['font_obj']
				break
		# If no font was able to render the character, skip it
		if not font_used:
			print(f'Warning: Unable to render character: {ord(char)}')
			continue

		# Get the size of the character and update the line width and x position
		char_bbox = draw.textbbox((0, 0), char, font=font_used)
		width, height = char_bbox[2] - char_bbox[0], char_bbox[3] - char_bbox[1]
		if line_width + width > wrap_x - safety_offset_x:  # check if new line needed
			# Check for last symbol in the deque, if within last 20 chars
			if last_symbol >= 0 and len(char_task) - last_symbol <= 20:
				# Pop all chars up to last symbol, including it
				for i in range(last_symbol + 1):
					task = char_task.popleft()
					if explicit_space:
						if i == range(last_symbol + 1)[-1] and task[1] == ' ':
							draw.text((task[0], y), "—", font=GS.FONT_OBJS[0], fill=(255,255,255,0))
							#print(f'drawing explicit space')
						else:
							draw.text((task[0], y), task[1], font=task[2], fill=task[4])
							#print(f'type SFW drawing {task[1]}')
					else:
						draw.text((task[0], y), task[1], font=task[2], fill=task[4])
						#print(f'type SF drawing {task[1]}')
				last_symbol = -1  # reset last symbol index
			else:
				# Empty the deque and draw all symbols
				while len(char_task) > 0:
					task = char_task.popleft()
					if explicit_space:
						if len(char_task) == 0 and task[1] == ' ':
							draw.text((task[0], y), "—", font=GS.FONT_OBJS[0], fill=(255,255,255,0))
							#print(f'drawing explicit space')
						else:
							draw.text((task[0], y), task[1], font=task[2], fill=task[4])
							#print(f'type NSW drawing {task[1]}')
					else:
						draw.text((task[0], y), task[1], font=task[2], fill=task[4])
						#print(f'type NS drawing {task[1]}')

			# Start new line
			x = starting_x
			y += line_height
			used_lines += 1
			line_width = 0
			newline = True
			if used_lines > available_y_lines:
				img = ImageOps.expand(img, border=(0, 0, 0, line_height), fill=(0, 0, 0))
				draw = ImageDraw.Draw(img)
				available_y_lines += 1
			if len(char_task) > 0:
				x_offset = char_task[0][0] - starting_x
			while len(char_task) > 0:
				task = char_task.popleft()
				draw.text((task[0] - x_offset, y), task[1], font=task[2], fill=task[4])
				#print(f'type Overflow drawing {task[1]}')
				line_width += task[3]
				x += task[3]

		# Add character task to deque
		char_task.append((x, char, font_used, width, contextual_fill))
		line_width += width
		x += width

		# Check if char is suitable for line breaking
		if break_symbol == 'any':
			if not ((char >= 'a' and char <= 'z') or (char >= 'A' and char <= 'Z')):
				last_symbol = len(char_task) - 1
		else:
			if char == break_symbol:
				last_symbol = len(char_task) - 1

	# Draw remaining characters in deque
	while len(char_task) > 0:
		task = char_task.popleft()
		draw.text((task[0], y), task[1], font=task[2], fill=task[4])
		#print(f'type Dump drawing {task[1]}')

	return draw, img, used_lines, line_width

# 5. To make writing prompts in f-string style possible properly, some adjustments for brackets/quotes/backslashes are needed, this function handles that
@handle_exceptions
def f_string_pre_processor(text):
	result = ''
	brace_level = 0
	in_string_s = False
	in_string_d = False
	quote = None
	for i, char in enumerate(text):
		if in_string_s == True:
			if char =="'":
				in_string_s = False
			result += char
			continue
		if brace_level > 0 and char =="'" and not in_string_d:
			in_string_s = True
			result += char
			continue
		if in_string_d == True:
			if char =='"':
				in_string_d = False
			result += char
			continue
		if brace_level > 0 and char =='"' and not in_string_s:
			in_string_d = True
			result += char
			continue
		# f-strings can write out curly braces normally, but they need to be doubled, which is done here to not bother the user with that
		if char == '{':
			result += '{{'
		elif char == '}':
			result += '}}'
		# Because of the conflict of {} used both in f-strings and strengthening in NAI, we instead give the user different braces to use
		elif char == '⁅':
			result += '{'
			brace_level += 1
		elif char == '⁆':
			result += '}'
			brace_level -= 1
		# Since f-string is evaluated based on triple ", any occurence of these in the f-string outside the evaluated area needs to be manually escapeds
		elif char == '"' and brace_level == 0:
			result += '\\"'
		# And lastly whle backslashes would work outside of the evaluated parts they'd behave unexpected due to the way escaping works, so we double them up
		elif char == '\\':
			result += '\\\\'
		else:
			result += char
	if brace_level != 0:
		raise ValueError(f"[Warning] Mismatched braces in input string. b_l: {brace_level} | text: {text}")
	return result

# 6. This function takes an f-string, uses the pre-processor, and evaluates it according to the passed variables
# No @handle_exceptions since this function has it's own exception handling
def f_string_processor(string_list, eval_guard, var_dict):
	processed_string=""
	for string in string_list:
		if eval_guard:
			try: # Here we manually override access to builtins for extra safety
				processed_string+=eval('f"""'+f_string_pre_processor(string)+'"""',{'np': np,'math': math,'__builtins__':{}},{'prompt_list':string}|var_dict)
			except:
				#print(f"Full Call Stack: {''.join(traceback.format_stack())}")
				traceback.print_exc()
				return 'Error' # Reported above
		else:
			try:
				processed_string+=eval('f"""'+f_string_pre_processor(string)+'"""',{'np': np,'math': math},{'prompt_list':string}|var_dict)
			except:
				traceback.print_exc()
				return 'Error' # Reported above
	return processed_string

# 7. This function forms file paths for the generate_as_is function
@handle_exceptions
def make_file_path(prompt,enumerator,folder_name,folder_name_extra):
	prompt[1]=replace_forbidden_symbols(prompt[1])
	folder_name=replace_forbidden_symbols(folder_name)
	enumerator=replace_forbidden_symbols(enumerator)
	if folder_name!='':
		filepath=f'__0utput__/{folder_name+folder_name_extra}/{prompt[1]+enumerator}.png'
		dir = f'__0utput__/{folder_name+folder_name_extra}'
		os.makedirs(dir, exist_ok=True)
	else:
		filepath=f'__0utput__/{prompt[1]+enumerator}.png'
	return filepath

# 8. Helper function for formatting quotes for the .py settings files
@handle_exceptions
def escape_quotes_for_saving(text):
	result = ''
	for i, char in enumerate(text):
		if (8 > i) or (i > (len(text)-8)):
			result += char
		elif char == '"':
			result += '\\"'
		elif char == "'":
			result += "\\'"
		else:
			result += char
	return result

# 9. Saves used settings as a .py file that can be imported in the UI via drag and drop
@handle_exceptions
def save_settings(folder_name,settings,sub_folder=''):
	dir = f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}'
	os.makedirs(dir, exist_ok=True)
	with open(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}/settings꞉{replace_forbidden_symbols(settings["name"])}.py','w',encoding="utf_16") as file:
		file.write('settings={\n')
		for key, value in settings.items():
			if key == 'meta' or key == 'image_entries':
				continue
			if isinstance(value, list) and all(isinstance(item, list) for item in value):
				file.write(f"{repr(key)}: [")
				for item in value:
					# Make sure that f-strings get saved correctly
					if key == 'prompt' or key == 'negative_prompt':
						for elem in item:
							file.write(f"""\n{escape_quotes_for_saving(str('[{}]'.format("'''" + elem + "'''")))},""")
					# Make sure that seed lists get saved correctly
					elif key == 'seed':
						file.write(f"\n[{', '.join(repr(elem) for elem in item)}],")
				file.write(f"],\n")
			else:
				file.write(f"{repr(key)}: {repr(value)},\n")
		file.write('}')
	file.close

	if settings.get('image_entries'):
		save_image_entries(folder_name,settings,sub_folder)

@handle_exceptions
def save_image_entries(folder_name, settings, sub_folder=''):
	# Shallow copy of the list
	image_entries = settings["image_entries"][:]
	
	for i, entry in enumerate(image_entries):
		# Shallow copy of each dictionary to avoid changing original entry
		entry_copy = entry.copy()
		
		# Compress the raw image data
		compressed_image = zlib.compress(entry_copy["entry_reference"].raw_image_data, level=9)
		# Encode the compressed data
		entry_copy["entry_reference"] = base64.b64encode(compressed_image).decode('ascii')
		
		for type in ["vt", "i2i"]:
			if entry_copy.get(type):
				# Deep copy to modify safely without altering original
				type_copy = deepcopy(entry_copy[type])
				for key, value in type_copy.items():
					if value != '':
						type_copy[key] = escape_quotes_for_saving(str("'''" + value + "'''"))
				entry_copy[type] = type_copy
		
		# Replace the original entry with the modified copy
		image_entries[i] = entry_copy
	
	# Convert the entire structure to JSON
	json_data = json.dumps(image_entries, separators=(',', ':'))
	
	# Compress the JSON data
	compressed_data = zlib.compress(json_data.encode('utf-8'), level=9)
	
	with open(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}/image_entries꞉{replace_forbidden_symbols(settings["name"])}.cvfimgs', 'wb') as file:
		file.write(compressed_data)

# 10. Provides a centralized way for tasks to handle filepaths
@handle_exceptions
class FilePathHandler():
	def __init__(self, f_strings, **kwargs):
		self.f_strings = f_strings 
	def process_path(self, key, var_dict):
		filepath = f_string_processor(self.f_strings[key],True,var_dict)
		os.makedirs(os.path.dirname(filepath), exist_ok=True)
		return filepath
