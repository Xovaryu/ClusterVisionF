from ConfigHandler import *
import sys
import os
import io
import time
import requests
import json
import base64
import time
import subprocess
import math
import random
import copy
import numpy as np
import glob
import cv2
import zipfile

from concurrent.futures import ThreadPoolExecutor
from PIL import ImageFont, ImageDraw, Image, ImageOps
from collections import deque
from fontTools.ttLib import TTFont

#Global variables
PRODUCED_IMAGES=0
SKIPPED_IMAGES=0
QUEUED_IMAGES=0
PROCESSING_QUEUE=deque()
PROCESSING_QUEUE_LEN=0
FINISHED_TASKS=0
SKIPPED_TASKS=0
WAITS_SHORT=0
WAITS_LONG=0
EXECUTOR = ThreadPoolExecutor()
FUTURES = []
CANCEL_REQUEST = False
PAUSE_REQUEST = False
BS = '\\' # This is here because f-strings do not yet (until Python 3.12 most likely) support backstrings in the evaluated part, necessitating this BS workaround

#Font list for cluster collages

if getattr(sys, 'frozen', False):
    # Running in a bundle
    FULL_DIR = os.path.dirname(sys.executable) + '/'
else:
    # Running in a normal Python environment
    FULL_DIR = os.path.dirname(os.path.realpath(__file__)) + '/'

#FULL_DIR = os.path.dirname(os.path.realpath(__file__)) + '/'
FONT_LIST = CUSTOM_FONT_LIST_PREPEND + [
	#Roboto font, freeware from dafont.com
	FULL_DIR + 'Fonts/Roboto-Regular.ttf',
	#Google Noto fonts provided with the OFL v1.1 license
	FULL_DIR + 'Fonts/NotoEmoji-VariableFont_wght.ttf',
	FULL_DIR + 'Fonts/NotoSansJP-VF.ttf',
	FULL_DIR + 'Fonts/NotoSansSC-VF.ttf',
	FULL_DIR + 'Fonts/NotoSansTC-VF.ttf',
	FULL_DIR + 'Fonts/NotoSansKR-VF.ttf',
	FULL_DIR + 'Fonts/NotoSansHK-VF.ttf',
	#Symbola font, freeware from fontlibrary.org
	FULL_DIR + 'Fonts/Symbola.ttf',
	#GNU Unifont from unifoundry.com provided with OFL v1.1 and GNU GPL 2+ with the GNU font embedding exception
	FULL_DIR + 'Fonts/unifont_jp-15.0.01.ttf',
] + CUSTOM_FONT_LIST_APPEND
try:
	FONT_OBJS = [ImageFont.truetype(str(x), FONT_SIZE) for x in FONT_LIST]
	TT_FONTS = [TTFont(x) for x in FONT_LIST]
except Exception as e:
	import traceback
	traceback.print_exc()
	print(f'Loading fonts failed. FONT_LIST: {FONT_LIST}')
	sys.exit()
###
# Primary Functions
###

#This function is used to make sure files with the according symbols can be saved
def replace_forbidden_symbols(string):
	string=string.replace('"','{QuotM}').replace('/','{Slash}').replace('\\','{BackSlash}').replace('?','{QuestM}').replace('*','{Asterisk}')
	return string.replace(':','{Colon}').replace('<','{LesserT}').replace('>','{GreaterT}').replace('|','{VertLine}')

#Takes the settings and reformats them for NAI's API
#(Using UC presets in the way the website would does not work currently)
def form_prompt(settings,number=1,noise=0.1,strength=0.4):
	json_construct={
		#This is the prompt, Quality Tags are not configured separately and net to be appended here manually
		'input': settings["prompt"],
		#"input": settings["QT"]+settings["prompt"], # Deprecated
		#Model as in UI (Curated/Full/Furry)
		'model': settings["model"],															
		'parameters': {
			#Seed as in UI
			'seed': settings["seed"],
			#Undesired Content as in UI
			'negative_prompt': settings["UC"],
			#Image Width as in UI
			'width': settings["img_mode"]["width"],
			#Image Height as in UI
			'height': settings["img_mode"]["height"],	
			#Number of images to generate, currently this script isn't configured to handle more than 1 at a time
			'n_samples': number,
			#Sampler as in UI
			'sampler': settings["sampler"],
			#Scale as in UI
			'scale': settings["scale"],
			#Steps as in UI
			'steps': settings["steps"],
			#Noise as in UI and thus ineffective for standard generation
			'noise': noise,
			#Strength as in UI and thus ineffective for standard generation
			'strength': strength,
			'sm': settings["smea"],
			'sm_dyn': settings["dyn"],
			}
		}
	return [json_construct,settings["name"]]

def make_file_path(prompt,enumerator,folder_name,folder_name_extra,img_save_mode):
	if not img_save_mode: print(f'{enumerator}\nModel: {prompt[0]["model"]}\nPrompt:\n{prompt[0]["input"]}\nUC:\n{prompt[0]["parameters"]["negative_prompt"]}')
	prompt[1]=replace_forbidden_symbols(prompt[1])
	folder_name=replace_forbidden_symbols(folder_name)
	enumerator=replace_forbidden_symbols(enumerator)
	if folder_name!='':
		filepath=f'__0utput__/{folder_name+folder_name_extra}/{prompt[1]+enumerator}.png'
		if not os.path.exists(f'__0utput__/{folder_name+folder_name_extra}'): os.makedirs(f'__0utput__/{folder_name+folder_name_extra}')
	else:
		filepath=f'__0utput__/{prompt[1]+enumerator}.png'
	return filepath

#The primary function to generate images. Sends the request and will persist until it is fulfilled, then saves the image, and returns the path
#img_save_mode is a debugging variable and will return only the paths if set to True to avoid repetitive generations
def image_gen(auth,prompt,filepath,img_save_mode='Resume',token_test=False):
	global PRODUCED_IMAGES, SKIPPED_IMAGES, WAITS_SHORT, WAITS_LONG, PAUSE_REQUEST
	while PAUSE_REQUEST:
		time.sleep(0.2)
	api_header=f'Bearer {auth}'
	retry_time=5

	skipped = False
	while not img_save_mode == 'Skip':
		if img_save_mode == 'Resume':
			if os.path.isfile(filepath):
				skipped = True
				break
		if token_test:
			resp=requests.post(URL,json.dumps(prompt[0]),headers={'Authorization': api_header,'Content-Type': 'application/json','accept': 'application/json',})
			resp_content=resp.content
			resp_length=len(resp_content)
			if resp_length>1000:
				return 'Success'
			elif resp_content == b'{"statusCode":401,"message":"Invalid accessToken."}' or resp_content == b'{"statusCode":400,"message":"Invalid Authorization header content."}':
				return 'Error'
		try:
			start=time.time()
			resp=requests.post(URL,json.dumps(prompt[0]),headers={'Authorization': api_header,'Content-Type': 'application/json','accept': 'application/json',})
			resp_content=resp.content
			resp_length=len(resp_content)
			if resp_length>1000:
				print(f'Response length: {resp_length}')
			elif resp_content == b'{"statusCode":401,"message":"Invalid accessToken."}' or resp_content == b'{"statusCode":400,"message":"Invalid Authorization header content."}':
				print(f'Invalid access token. Please fetch your current token from the website.')
				return 'Error'
			else:
				print(f'Likely fault detected: {resp_content}')
			
			#Deprecated
			#base64_image=resp_content.splitlines()[2].replace(b"data:", b"")
			#decoded=base64.b64decode(base64_image)
			#Check for server load to respect terms. Typical generation times are between 3 and 4 seconds
			end=time.time()
			processing_time=end-start
			print(f'NAI Server Generation Time:{(processing_time)}s')
			with zipfile.ZipFile(io.BytesIO(resp_content), "r") as zip_file:
				for file_name in zip_file.namelist():
					if file_name.endswith(".png"):
						with zip_file.open(file_name) as png_file:
							with open(filepath,'wb+') as t:
								t.write(png_file.read())
							t.close()
							#image_data = io.BytesIO(png_file.read())
							#image = Image.open(image_data)
			print('`??')
			break
		except:
			return 'Error'
			print(f'Creation error encounted. Retrying after: {min(retry_time,90)}s')
			time.sleep(min(retry_time,90))
			print('RETRYING NOW')
			retry_time+=5
			continue
		time.sleep(WAIT_TIME) # Waiting for the specified amount to avoid getting limited

	if not img_save_mode == 'Skip' or skipped:
		PRODUCED_IMAGES += 1
		#with open(filepath,'wb+') as t:
		#	t.write(image_data)
		#t.close()
		#image.save(filepath)
	else:
		SKIPPED_IMAGES += 1
	if 'PREVIEW_QUEUE' in globals():
		PREVIEW_QUEUE.append(filepath)
	print(f'File Path:\n{filepath}\n\n')
	return filepath

#Function to generate seeds in the way NAI would
def generate_seed():
	return math.floor(random.random()*(2**32)-1);

def generate_seed_cluster(dimensions):
	seed_list=[]
	for rows in range(dimensions[0]):
		row=[]
		for columns in range(dimensions[1]):
			row.append(generate_seed())
		seed_list.append(row)
	return seed_list

###
#Additional Media Functions
###
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

def format_double_triple_fstring(text):
	return str('[{}]'.format("'''" + text + "'''"))

#Saves used settings
def save_settings(folder_name,settings,sub_folder=''):
	if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}'): os.makedirs(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}')
	with open(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}/settings꞉{replace_forbidden_symbols(settings["name"])}.py','w',encoding="utf_16") as file:
		file.write('settings={\n')
		for key, value in settings.items():
			if key == 'meta':
				continue
			if isinstance(value, list) and all(isinstance(item, list) for item in value):
				file.write(f"{repr(key)}: [")
				for item in value:
					# Make sure that f-strings get saved correctly
					if key == 'prompt' or key == 'UC':
						for elem in item:
							file.write(f"""\n{escape_quotes_for_saving(format_double_triple_fstring(elem))},""")
					# Make sure that seed lists get saved correctly
					elif key == 'seed':
						file.write(f"\n[{', '.join(repr(elem) for elem in item)}],")
				file.write(f"],\n")
			else:
				file.write(f"{repr(key)}: {repr(value)},\n")
		file.write('}')
	file.close

#Creates a video from all PNG files in a folder. Needs them to be properly sorted by name
#Hence do make sure not to have other PNG files there, collages are saved as JPG
def make_vid(img_folder,fps=7,base_path='__0utput__/'):
	print('Making video')
	img_folder=replace_forbidden_symbols(img_folder)
	file_list=glob.glob(f'{base_path+img_folder}/*.png')
	h,w,_=np.array(Image.open(file_list[0])).shape
	frameSize=(w,h)
	out=cv2.VideoWriter(f'{base_path+img_folder}/{img_folder}.webm',cv2.VideoWriter_fourcc(*'vp09'),fps,frameSize)
	for filename in file_list:
		img=cv2.imdecode(np.fromfile(filename,dtype=np.uint8),-1)
		out.write(img)
	out.release()
	print('Finished making video')

#Calls flowframes to interpolate an existing video, will run in parallel
def interpolate_vid(vid_path,factor=4,output_mode=2,base_path='__0utput__/'):
	vid_path=replace_forbidden_symbols(vid_path)
	SW_MINIMIZE = 6
	info = subprocess.STARTUPINFO()
	info.dwFlags = subprocess.STARTF_USESHOWWINDOW
	info.wShowWindow = SW_MINIMIZE
	path=f'{os.getcwd()}/{base_path+vid_path}/{vid_path}.webm'
	p = subprocess.Popen([FLOWFRAMES_PATH,path,'-start','-quit-when-done',
	f'-factor={factor}',f'-output-mode={output_mode}'],startupinfo=info)
	print("Interpolating video in Flowframes")

#Simply combines the above functions into a single call
def make_interpolated_vid(vid_path,fps=7,factor=4,output_mode=2,base_path='__0utput__/'):
	make_vid(vid_path,fps,base_path)
	interpolate_vid(vid_path,factor,output_mode,base_path)

#Takes in a list of images and turns them into a collage
def make_collage(imgs,name,row_length=5,name_extra="",passed_image_mode=False,folder_name='',pass_image=False):
	row=[]
	rows=[]
	n=0
	multirow=False
	for img in imgs:
		if passed_image_mode==False:
			try:
				row.append(np.array(Image.open(img)))
			except Exception as e:
				import traceback
				traceback.print_exc()
				print(f"Invalid image file encountered, unable to make collage")
				return
		else:
			row.append(img)
		n+=1
		if n==row_length:
			multirow=True
			rows.append(np.hstack(row))
			n=0
			row=[]
	if multirow:
		collage=np.vstack(rows)
	else:
		collage=np.hstack(row)

	if pass_image==False:
		folder_name,name,name_extra=replace_forbidden_symbols(folder_name),replace_forbidden_symbols(name),replace_forbidden_symbols(name_extra)
		if passed_image_mode==False:
			path=f'{os.path.dirname(os.path.abspath(imgs[0]))}/{name}_Collage{name_extra}.jpg'
		else:
			path=f'__0utput__/{folder_name}/{name}_Collage{name_extra}.jpg'
		Image.fromarray(collage).save(path, quality=90)
		return path
	else:
		return collage

#Attaches a metadata header to the picture and saves it
def attach_metadata_header(img_collages,settings,name_extra):
	img_collages=Image.fromarray(img_collages)
	#Text configuration
	line_height=FONT_SIZE+5
	font=ImageFont.truetype(FONT_LIST[0],FONT_SIZE)
	left_meta_block=900
	
	#Creating the header
	starting_amount_lines = 8
	img_header = Image.new("RGB", (img_collages.width, line_height*starting_amount_lines), (0, 0, 0))
	draw = ImageDraw.Draw(img_header)
	
	#Draw the basic metadata on the left side
	draw.text((10,line_height*0),f"Xovaryu's Prompt Stabber",font=font,fill=(255,220,255,0))
	draw.text((10,line_height*1),f'Creator: {CREATOR_NAME}',font=font,fill=(200,200,255,0))
	draw, img_header, used_lines_name=fallback_font_writer(draw, img_header, f'Name: {settings["name"]}', 10, line_height*2, left_meta_block, 1, line_height, (255,255,255,0))
	if settings["model"] == 'safe-diffusion':
		model = 'NovelAI Diffusion Curated v1.0'
	elif settings["model"] == 'nai-diffusion':
		model = 'NovelAI Diffusion Full v1.0'
	elif settings["model"] == 'nai-diffusion-furry':
		model = 'NovelAI Diffusion Furry v1.3'
	draw.text((10,line_height*(2+used_lines_name)),f'NovelAI Model: {model}',font=font,fill=(255,255,255,0))
	draw.text((10,line_height*(3+used_lines_name)),f'Resolution: {settings["img_mode"]}',font=font,fill=(255,255,255,0))
	currently_used_lines=4+used_lines_name
	available_lines = starting_amount_lines - currently_used_lines
	draw, img_header, used_lines_steps=fallback_font_writer(draw, img_header, 'Steps: '+'|'.join([str(steps) for steps in settings["meta"]["steps"]]), 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = '|')
	currently_used_lines=currently_used_lines+used_lines_steps
	available_lines = available_lines - used_lines_steps
	draw, img_header, used_lines_scale=fallback_font_writer(draw, img_header, 'Scale: '+'|'.join([str(scale) for scale in settings["meta"]["scale"]]), 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = '|')
	currently_used_lines=currently_used_lines+used_lines_scale
	available_lines = available_lines - used_lines_scale
	draw, img_header, used_lines_samplers=fallback_font_writer(draw, img_header, 'Sampler: '+', '.join(settings["sampler"][0]), 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = ',')

	currently_used_lines=currently_used_lines+used_lines_samplers
	#Draw the prompt and UC on the right side
	full_prompt=settings["prompt"]
	draw, img_header, used_lines_prompt=fallback_font_writer(draw, img_header, full_prompt, left_meta_block, line_height*0, img_collages.size[0]-left_meta_block,
		currently_used_lines, line_height, (180,255,180,0), explicit_space = True)
	currently_used_lines=max(currently_used_lines,used_lines_prompt)
	available_lines = currently_used_lines-used_lines_prompt

	full_UC=settings["UC"]
	draw, img_header, used_lines_uc=fallback_font_writer(draw, img_header, full_UC, left_meta_block, line_height*(used_lines_prompt),
		img_collages.size[0]-left_meta_block, available_lines, line_height, (255,180,180,0), explicit_space = True)

	#Combining and saving
	full_img = Image.new('RGB', (img_collages.width, img_header.height + img_collages.height))
	full_img.paste(img_header, (0, 0))
	full_img.paste(img_collages, (0, img_header.height))
	if settings.get('folder_name_user'):
		settings["folder_name_extra"]=settings["folder_name_user"]+f'/{settings["name"]}'
		path=f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages{settings["folder_name_user"]}/'
		if not os.path.exists(path): os.makedirs(path)
		full_img.save(f'{path}{replace_forbidden_symbols(settings["name"])}_Collage({replace_forbidden_symbols(name_extra)}).jpg', quality=90)
	else:
		full_img.save(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/{replace_forbidden_symbols(settings["name"])}_Collage({replace_forbidden_symbols(name_extra)}).jpg', quality=90)

# These 3 functions are responsible for handling f-strings being formatted properly when writing onto the metadata header
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

#Writes a text character by character, going through a list of fonts and trying to find one that has the requested character
def fallback_font_writer(draw, img, text, x, y, wrap_x, available_y_lines, line_height, fill, break_symbol='any', explicit_space=False):
	# Initialize needed variables
	starting_x = x
	line_width = 0
	used_lines = 1
	safety_offset_x = 75
	newline = False
	char_task = deque()
	last_symbol = -1  # index of last symbol in deque

	text, indexes = find_evaluated_fstring_braces(unpack_list(text))

	for char_index, char in enumerate(text):
		if any(start <= char_index < end for start, end in indexes):
			contextual_fill = (fill[0],fill[1],0,fill[3])
		else:
			contextual_fill = fill
		# Try to render the character with each font in the font list
		font_used = None
		for n in range(len(FONT_LIST)):
			# Check if the font has the character in its character map
			if ord(char) in TT_FONTS[n]['cmap'].getBestCmap().keys():
				font_used = FONT_OBJS[n]
				break
		# If no font was able to render the character, skip it
		if not font_used:
			print(f'Warning: Unable to render character: {ord(char)}')
			continue

		# Get the size of the character and update the line width and x position
		char_bbox = draw.textbbox((0, 0), char, font=font_used)
		width, height = char_bbox[2] - char_bbox[0], char_bbox[3] - char_bbox[1]
		if line_width + width > wrap_x - safety_offset_x:  # check if new line needed
			# check for last symbol in the deque, if within last 20 chars
			if last_symbol >= 0 and len(char_task) - last_symbol <= 20:
				# pop all chars up to last symbol, including it
				for i in range(last_symbol + 1):
					task = char_task.popleft()
					if explicit_space:
						if i == range(last_symbol + 1)[-1] and task[1] == ' ':
							draw.text((task[0], y), "—", font=FONT_OBJS[0], fill=(255,255,255,0))
							#print(f'drawing explicit space')
						else:
							draw.text((task[0], y), task[1], font=task[2], fill=task[4])
							#print(f'type SFW drawing {task[1]}')
					else:
						draw.text((task[0], y), task[1], font=task[2], fill=task[4])
						#print(f'type SF drawing {task[1]}')
				last_symbol = -1  # reset last symbol index
			else:
				# empty the deque and draw all symbols
				while len(char_task) > 0:
					task = char_task.popleft()
					if explicit_space:
						if len(char_task) == 0 and task[1] == ' ':
							draw.text((task[0], y), "—", font=FONT_OBJS[0], fill=(255,255,255,0))
							#print(f'drawing explicit space')
						else:
							draw.text((task[0], y), task[1], font=task[2], fill=task[4])
							#print(f'type NSW drawing {task[1]}')
					else:
						draw.text((task[0], y), task[1], font=task[2], fill=task[4])
						#print(f'type NS drawing {task[1]}')

			# start new line
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

		# add character task to deque
		char_task.append((x, char, font_used, width, contextual_fill))
		line_width += width
		x += width

		# check if char is suitable for line breaking
		if break_symbol == 'any':
			if not ((char >= 'a' and char <= 'z') or (char >= 'A' and char <= 'Z')):
				last_symbol = len(char_task) - 1
		else:
			if char == break_symbol:
				last_symbol = len(char_task) - 1

	# draw remaining characters in deque
	while len(char_task) > 0:
		task = char_task.popleft()
		draw.text((task[0], y), task[1], font=task[2], fill=task[4])
		#print(f'type Dump drawing {task[1]}')

	return draw, img, used_lines

###
#Rendering Functions
###

#Simply formats and passes the prompt on without changes, used for simple generations or complex external logic
def generate_as_is(settings,enumerator,img_save_mode='Resume',token_test=False,token=''):
	if token_test:
		settings = {'name': 'Test', 'folder_name': '', 'folder_name_extra': '', 'enumerator_plus': '', 'model': 'nai-diffusion', 'seed': 0, 'sampler': 'k_euler_ancestral', 'scale': 10.0,
			'steps': 1, 'img_mode': {'width': 64, 'height': 64}, 'prompt': 'Test', 'negative_prompt': 'Test', 'smea': False, 'dyn': False}
		return image_gen(enumerator,form_prompt(settings),'',img_save_mode='Overwrite',token_test=True)
	final_settings=copy.deepcopy(settings)
	if settings["sampler"].endswith('_dyn'):
		final_settings["smea"] = True
		final_settings["dyn"] = True
		final_settings["sampler"] = settings["sampler"][:-4]
	elif settings["sampler"].endswith('_smea'):
		final_settings["smea"] = True
		final_settings["dyn"] = False
		final_settings["sampler"] = settings["sampler"][:-5]
	else:
		final_settings["smea"] = False
		final_settings["dyn"] = False
	prompt=form_prompt(final_settings)
	filepath=make_file_path(prompt,enumerator,settings["folder_name"],settings["folder_name_extra"],img_save_mode)
	return image_gen(AUTH,prompt,filepath,img_save_mode,token_test)

#Takes a prompt and renders it across multiple seeds at multiple scales, then puts all generations into a big collage together with the metadata
#If a seed list is passed or the default is used, make sure it has enough seeds for the requested amount of scales (collage_width²)
#Does some pre-processing, then adds a task to the PROCESSING_QUEUE which will be processed with prompt_stabber_process
def prompt_stabber(settings,eval_guard=True,img_save_mode='Resume'):
	global QUEUED_IMAGES

	#Configures the seed list
	if settings["seed"]=='default':
		settings["seed"]=PROMPT_STABBER_DEFAULT_SEEDS
	elif settings["seed"][0]=='random':
		settings["seed"]=generate_seed_cluster(settings["seed"][1])

	#Adjusts all needed meta parameters
	settings["meta"]={}
	settings["meta"]["imgs_per_collage"]=settings["collage_dimensions"][0]*settings["collage_dimensions"][1]
	if not isinstance(settings["sampler"], list):
		samplers=1
	else:
		samplers=len(settings["sampler"][0])
	settings["meta"]["number_of_seeds"] = len(settings["seed"])*len(settings["seed"][0])
	settings["meta"]["number_of_imgs"]=settings["meta"]["imgs_per_collage"]*samplers*settings["meta"]["number_of_seeds"]
	QUEUED_IMAGES+=settings["meta"]["number_of_imgs"]

	settings["meta"]["processing_type"]='stab'
	settings["meta"]["img_save_mode"]=img_save_mode
	if eval_guard:
		settings["meta"]["eval_guard"]=True
	else:
		settings["meta"]["eval_guard"]=False
	#Finally, add the task and move on
	PROCESSING_QUEUE.append(settings)

def prompt_stabber_process(settings):
	global PRODUCED_IMAGES,QUEUED_IMAGES,FINISHED_TASKS,SKIPPED_IMAGES,SKIPPED_TASKS,FUTURE_LIST, EXECUTOR, CANCEL_REQUEST

	#Saving settings and configuring folder structure
	conf_settings=copy.deepcopy(settings)
	if conf_settings.get('folder_name_user'):
		user_extra='/'+conf_settings["folder_name_user"]
	else:
		user_extra=''
	if settings["folder_name"]=="":
		conf_settings["folder_name"]=settings["name"]
		if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(conf_settings["folder_name"])}/#ClusterCollages/'):
			os.makedirs(f'__0utput__/{replace_forbidden_symbols(conf_settings["folder_name"])}/#ClusterCollages/')
		save_settings(conf_settings["folder_name"],settings,sub_folder='/#ClusterCollages'+user_extra)
		settings["folder_name"]=settings["name"]
	else:
		if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/'):
			os.makedirs(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/')
		save_settings(conf_settings["folder_name"],settings,sub_folder='/#ClusterCollages'+user_extra)

	rendered_imgs=1
	img_settings=copy.deepcopy(settings)

	#Configures steps and scale lists
	settings["meta"]["steps"] = []
	settings["meta"]["scale"] = []

	print(settings["steps"])
	print(settings["scale"])
	if type(settings["steps"]) == list and settings["meta"]["imgs_per_collage"] != 1:
		settings["meta"]["steps"] = np.linspace(settings["steps"][0], settings["steps"][-1], settings["meta"]["imgs_per_collage"]).tolist()
	else:
		if isinstance(settings["steps"], int):
			settings["meta"]["steps"]=[settings["steps"]]
		else:
			settings["meta"]["steps"]=[settings["steps"][0]]

	if type(settings["scale"])==list and settings["meta"]["imgs_per_collage"] != 1:
		settings["meta"]["scale"] = [round(x,6) for x in np.linspace(settings["scale"][0], settings["scale"][-1], settings["meta"]["imgs_per_collage"]).tolist()]
	else:
		if any(isinstance(settings["scale"], type) for type in [int, float]):
			settings["meta"]["scale"]=[settings["scale"]]
		else:
			settings["meta"]["scale"]=[settings["scale"][0]]

	#Configure the folder structure if the user specified something extra
	if img_settings.get('folder_name_user'):
		img_settings["folder_name_extra"]=img_settings["folder_name_user"]+f'/{replace_forbidden_symbols(img_settings["name"])}'
	else:
		img_settings["folder_name_extra"]=f'/{replace_forbidden_symbols(img_settings["name"])}'

	#This loop makes the initial collages
	color=np.array([30,30,30])
	if not isinstance(settings["sampler"], list):
		settings["sampler"]=[[settings["sampler"]],1]
		single_sampler=True
	
	final_collages=[]
	for sampler in settings["sampler"][0]:
		img_settings["sampler"]=sampler
		sampler_collage_blocks=[]
		for seed_sub_list in settings["seed"]:
			collage_rows=[]
			for seed in seed_sub_list:
				imgs=[]
				for n in range(settings["meta"]["imgs_per_collage"]):
					#Load in the correct values for steps, scale and seed
					if len(settings["meta"]["steps"]) == 1:
						img_settings["steps"]=settings["meta"]["steps"][0]
					else:
						print(settings["meta"]["steps"])
						img_settings["steps"]=int(settings["meta"]["steps"][n])
					if len(settings["meta"]["scale"]) == 1:
						img_settings["scale"]=settings["meta"]["scale"][0]
					else:
						img_settings["scale"]=round(settings["meta"]["scale"][n],6)
					img_settings["seed"]=seed
					#Process f-string if necessary
					if type(settings["prompt"])!=str:
						img_settings["prompt"] = f_string_processor(settings["prompt"],n,settings["meta"]["eval_guard"])
						if 'Error' == img_settings["prompt"]:
							return 'Error'
					if type(settings["UC"])!=str:
						img_settings["UC"] = f_string_processor(settings["UC"],n,settings["meta"]["eval_guard"])
						if 'Error' == img_settings["UC"]:
							return 'Error'
					#Report the current queue position before rendering
					if CANCEL_REQUEST:
						return
					print(f'Processing task: {FINISHED_TASKS+1+SKIPPED_TASKS}/{PROCESSING_QUEUE_LEN}')
					print(f'Rendering img (current task): {rendered_imgs}/{settings["meta"]["number_of_imgs"]}')
					print(f'Rendering img (complete queue): {PRODUCED_IMAGES+1+SKIPPED_IMAGES}/{QUEUED_IMAGES}')
					imgs.append(generate_as_is(img_settings,f'(Seed꞉{seed})(n꞉ {n})(Scale꞉{img_settings["scale"]})(Steps꞉{img_settings["steps"]})(Sampler꞉{sampler})',settings["meta"]["img_save_mode"]))
					rendered_imgs+=1
				# This part is responsable for creating the structure defined by the collage_dimensions
				if settings["meta"]["imgs_per_collage"]==1:
					collage=(imgs[0])
				else:
					collage=make_collage(imgs,settings["name"],row_length=settings["collage_dimensions"][0],name_extra=f'(Seed꞉{seed})(Sampler꞉{sampler})')
				# Once that is done the collages get bordered
				bordered_collage=cv2.copyMakeBorder(np.array(Image.open(collage)),35,15,15,15,cv2.BORDER_CONSTANT,None,value=(int(color[0]),int(color[1]),int(color[2])))
				font=ImageFont.truetype(FULL_DIR+CC_SEEDS_FONT[0],CC_SEEDS_FONT[1])
				img_pil=Image.fromarray(bordered_collage)
				draw=ImageDraw.Draw(img_pil)
				collage_metadata=f'{seed}'
				if not len(settings["sampler"][0]) == 1:
					collage_metadata += f' | {sampler}'
				draw.text((10,-5),collage_metadata,font=font,fill=(255,255,255,0))
				processed_collage=np.array(img_pil)
				color+=[5,5,5]
				collage_rows.append(processed_collage)
			sampler_collage_blocks.append(make_collage(collage_rows,settings["name"],row_length=len(settings["seed"][0]),passed_image_mode=True,pass_image=True))
		# Implementing sampler dimensions later happens in row_length here
		final_collages.append(make_collage(sampler_collage_blocks,settings["name"],row_length=1,passed_image_mode=True,pass_image=True))
	if 'single_sampler' in locals():
		cluster_collage=make_collage(final_collages,settings["name"],row_length=len(settings["seed"]),passed_image_mode=True,folder_name=settings["folder_name"],pass_image=True)
	else:
		if settings["sampler"][1]=='vertical':
			row_cutoff=1
		else:
			row_cutoff=settings["meta"]["number_of_seeds"]
		cluster_collage=make_collage(final_collages,settings["name"],row_length=row_cutoff,passed_image_mode=True,folder_name=settings["folder_name"],pass_image=True)
	#FUTURES.append(EXECUTOR.submit(attach_metadata_header, cluster_collage, settings, f'Cluster[{settings["sampler"][0]}]'))
	attach_metadata_header(cluster_collage, settings, f'Cluster[{settings["sampler"][0]}]')
	FINISHED_TASKS+=1

#Renders a loop according to the settings and saves those
#Does some pre-processing, then adds a task to the PROCESSING_QUEUE which will be processed with render_loop_process
def render_loop(settings,eval_guard=True,img_save_mode='Resume'):
	global QUEUED_IMAGES
	number_of_imgs=settings["quantity"]
	QUEUED_IMAGES+=number_of_imgs

	#Configures the seed
	if settings["seed"]=='random':
		settings["seed"]=generate_seed()
	elif type(settings["seed"])==int:
		pass
	else:
		settings["seed"]=4246521898

	#Adjusts all needed meta parameters
	settings["meta"]={}
	settings["meta"]["number_of_imgs"]=number_of_imgs
	settings["meta"]["processing_type"]='loop'
	settings["meta"]["img_save_mode"]=img_save_mode
	if eval_guard:
		settings["meta"]["eval_guard"]=True
	else:
		settings["meta"]["eval_guard"]=False
	#Finally, add the task and move on
	PROCESSING_QUEUE.append(settings)

def render_loop_process(settings):
	global FINISHED_TASKS, CANCEL_REQUEST
	#Saves settings
	if settings["folder_name"]=="":
		folder=settings["name"]
		save_settings(folder,settings)
		settings["folder_name"]=folder
	else:
		save_settings(settings["folder_name"],settings)
	settings["quantity"]=range(0,settings["quantity"])
	imgs=[]
	img_settings=copy.deepcopy(settings)

	if type(settings["steps"]) == list:
		settings["meta"]["steps"] = np.linspace(settings["steps"][0], settings["steps"][-1], len(settings["quantity"])).tolist()
	else:
		if isinstance(settings["steps"], int):
			settings["meta"]["steps"]=[settings["steps"]]

	if type(settings["scale"])==list:
		settings["meta"]["scale"] = np.linspace(settings["scale"][0], settings["scale"][-1], len(settings["quantity"])).tolist()
	else:
		if any(isinstance(settings["scale"], type) for type in [int, float]):
			settings["meta"]["scale"]=[settings["scale"]]

	img_settings["folder_name_extra"]=''
	rendered_imgs=1
	for n in settings["quantity"]:
		enumerator=f'''({img_settings["seed"]})(#{str((n+1)).rjust(4,'0')})'''
		if len(settings["meta"]["steps"]) == 1:
			img_settings["steps"]=settings["meta"]["steps"][0]
		else:
			img_settings["steps"]=int(settings["meta"]["steps"][n])
		if len(settings["meta"]["scale"]) == 1:
			img_settings["scale"]=settings["meta"]["scale"][0]
		else:
			img_settings["scale"]=round(settings["meta"]["scale"][n],6)
		enumerator+=f'(Scale꞉{img_settings["scale"]})'
		enumerator+=f'(Steps꞉{img_settings["steps"]})'
		#Process f-string if necessary
		if type(settings["prompt"])!=str:
			img_settings["prompt"] = f_string_processor(settings["prompt"],n,settings["meta"]["eval_guard"])
			if 'Error' == img_settings["prompt"]:
				return 'Error'
		if type(settings["UC"])!=str:
			img_settings["UC"] = f_string_processor(settings["UC"],n,settings["meta"]["eval_guard"])
			if 'Error' == img_settings["UC"]:
				return 'Error'
		if CANCEL_REQUEST:
			return
		print(f'Processing task: {FINISHED_TASKS+1+SKIPPED_TASKS}/{PROCESSING_QUEUE_LEN}')
		print(f'Rendering img (current task): {rendered_imgs}/{settings["meta"]["number_of_imgs"]}')
		print(f'Rendering img (complete queue): {PRODUCED_IMAGES+1+SKIPPED_IMAGES}/{QUEUED_IMAGES}')
		imgs.append(generate_as_is(img_settings,enumerator,settings["meta"]["img_save_mode"]))
		rendered_imgs+=1
	if settings["video"] == 'standard':
		FUTURES.append(EXECUTOR.submit(make_vid,settings["folder_name"],fps=settings["FPS"]))
	elif settings["video"] == 'interpolated':
		FUTURES.append(EXECUTOR.submit(make_interpolated_vid,settings["folder_name"],fps=settings["FPS"],factor=FF_FACTOR,output_mode=FF_OUTPUT_MODE))
	FINISHED_TASKS+=1
	return imgs





# In order to make writing prompts in f-string style possible properly, some adjustments around brackets and backslashes are needed
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
		# Because of the conflict of {} used both in f-strings and strengthening in NAI, we instead give the user another type of braces to used
		elif char == '⁅':
			result += '{'
			brace_level += 1
		elif char == '⁆':
			result += '}'
			brace_level -= 1
		# Since f-string is evaluated based on triple ", any occurence of these in the f-string outside the evaluated area needs to be manually escapeds
		elif char == '"' and (3 < i < (len(text)-3)):
			result += '\\"'
		# And lastly whle backslashes would work outside of the evaluated parts they'd behave unexpected due to the way escaping works, so we double them up
		elif char == '\\':
			result += '\\\\'
		else:
			result += char
	if brace_level != 0:
		raise ValueError("Mismatched braces in input string.")
	return result


def f_string_processor(string_lists,n,eval_guard):
	processed_string=""
	for string_list in string_lists:
		if eval_guard:
			try:
				processed_string+=eval(f_string_pre_processor(string_list[0]),{'__builtins__':{}},{'n':n,'prompt_list':string_list})
			except Exception as e:
				import traceback
				traceback.print_exc()
				return 'Error'
		else:
			try:
				processed_string+=eval(f_string_pre_processor(string_list[0]),{},{'n':n,'prompt_list':string_list})
			except Exception as e:
				import traceback
				traceback.print_exc()
				return 'Error'
	return processed_string

###
# Task processing functions
###
def process_queue(skip=0,end=False,preview=None):
	global PROCESSING_QUEUE,PROCESSING_QUEUE_LEN,SKIPPED_IMAGES,SKIPPED_TASKS,PRODUCED_IMAGES,FINISHED_TASKS,QUEUED_IMAGES, CANCEL_REQUEST
	CANCEL_REQUEST = False
	if type(preview) == list:
		globals()['PREVIEW_QUEUE'] = preview
	PROCESSING_QUEUE_LEN=len(PROCESSING_QUEUE)
	for n in range(len(PROCESSING_QUEUE)):
		if CANCEL_REQUEST:
			CANCEL_REQUEST = False
			wipe_queue()
			print('Task queue cancelled')
			return
		if skip > 0:
			SKIPPED_TASKS += 1
			print(f'Skipping task {SKIPPED_TASKS}| There are {len(PROCESSING_QUEUE)} tasks left')
			SKIPPED_IMAGES += PROCESSING_QUEUE.popleft()["meta"]["number_of_imgs"]
			skip -= 1
		else:
			if end:
				if FINISHED_TASKS + SKIPPED_TASKS == end:
					print('Requested end of queue reached, finishing up')
					return
			result = process_task(PROCESSING_QUEUE.popleft())
			if result == 'Error':
				wipe_queue()
				print('Critical fault detected, task queue wiped')
				return
	print('Task queue processed')
	wipe_queue()

def process_task(settings):
	global CANCEL_REQUEST
	if CANCEL_REQUEST:
		return
	if settings["meta"]["processing_type"]=='stab':
		result = prompt_stabber_process(settings)
	elif settings["meta"]["processing_type"]=='loop':
		result = render_loop_process(settings)
	return result

def wipe_queue(instance=None):
	global PROCESSING_QUEUE, SKIPPED_TASKS, FINISHED_TASKS, PRODUCED_IMAGES, SKIPPED_IMAGES, QUEUED_IMAGES
	PROCESSING_QUEUE.clear()
	SKIPPED_TASKS=0
	FINISHED_TASKS=0
	PRODUCED_IMAGES=0
	SKIPPED_IMAGES=0
	QUEUED_IMAGES=0
	print('Task queue wiped')

def cancel_processing(instance=None):
	global CANCEL_REQUEST
	CANCEL_REQUEST = True

def update_global_img_gen(key, value):
	globals()[key] = value

#And lastly a simple debriefing function for some stats
def debriefing():
	global PRODUCED_IMAGES, EXECUTOR
	if EXECUTOR:
		EXECUTOR.shutdown(wait=True)
		if False:#Enable to debug issues with futures
			print(f'Futures: {FUTURES}')
			for future in FUTURES:
				try:
					print(f'Future result: {future.result()}')
				except Exception as e:
					import traceback
					traceback.print_exc()
	for n in range(5): print('GENERATION COMPLETE')
	print(f'Images generated:{PRODUCED_IMAGES}')
	print(f'Images skipped:{SKIPPED_IMAGES}')
	print(f'Short waits:{WAITS_LONG}')
	print(f'Long waits:{WAITS_SHORT}')