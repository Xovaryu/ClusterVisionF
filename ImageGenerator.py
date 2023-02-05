import requests
import json
import base64
import time
import os
import subprocess
import math
import random
import copy
import numpy as np
import glob
import cv2

from concurrent.futures import ThreadPoolExecutor
from PIL import ImageFont, ImageDraw, Image, ImageOps
from collections import deque
from fontTools.ttLib import TTFont

if not os.path.exists("NAID_User_Config.py"):
	f1=open("NAID_Config_Template.py","r")
	f2=open("NAID_User_Config.py","w",encoding="utf-8")
	f2.write(f1.read())
	f1.close()
	f2.close()
	print("Configuration file copied. Please open NAID_User_Config.py, set up your auth token, and if desired the displayed name on cluster collages.")
	time.sleep(7)
	exit()
else:
	from NAID_User_Config import *
from NAID_Constants import *

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

#Font list for cluster collages
FONT_LIST = CUSTOM_FONT_LIST_PREPEND + [
	#Roboto font, freeware from dafont.com
	'fonts/Roboto-Regular.ttf',
	#Google Noto fonts provided with the OFL v1.1 license
	'fonts/NotoEmoji-VariableFont_wght.ttf',
	'fonts/NotoSansJP-VF.ttf',
	'fonts/NotoSansSC-VF.ttf',
	'fonts/NotoSansTC-VF.ttf',
	'fonts/NotoSansKR-VF.ttf',
	'fonts/NotoSansHK-VF.ttf',
	#Symbola font, freeware from fontlibrary.org
	'fonts/Symbola.ttf',
	#GNU Unifont from unifoundry.com provided with OFL v1.1 and GNU GPL 2+ with the GNU font embedding exception
	'fonts/unifont_jp-15.0.01.ttf',
] + CUSTOM_FONT_LIST_APPEND
FONT_OBJS = [ImageFont.truetype(x, FONT_SIZE) for x in FONT_LIST]
TT_FONTS = [TTFont(x) for x in FONT_LIST]

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
		"input": settings["QT"]+settings["prompt"],														
		#Model as in UI (Curated/Full/Furry)
		"model": settings["model"],															
		"parameters": {
			#Seed as in UI
			"seed": settings["seed"],
			#Undesired Content as in UI
			"uc": UNDESIRED_CONTENT_LISTS[settings["UCp"]][1]+settings["UC"],
			#UC Preset NOT as in UI. Complete UC needs assembling above and correctly saving the used preset doesn't work yet
			"ucPreset": UNDESIRED_CONTENT_LISTS[settings["UCp"]][0],
			#Image Width as in UI
			"width": settings["img_mode"]["width"],
			#Image Height as in UI
			"height": settings["img_mode"]["height"],	
			#Number of images to generate, currently this script isn't configured to handle more than 1 at a time
			"n_samples": number,
			#Sampler as in UI
			"sampler": settings["sampler"],
			#Scale as in UI
			"scale": settings["scale"],
			#Steps as in UI
			"steps": settings["steps"],
			#Noise as in UI and thus ineffective for standard generation
			"noise": noise,
			#Strength as in UI and thus ineffective for standard generation
			"strength": strength,
            }
        }
	return [json_construct,settings["name"]]

def make_file_path(prompt,enumerator,folder_name,folder_name_extra):
	print(f'{enumerator}\nPrompt:\n{prompt[0]["input"]}\nUC:\n{prompt[0]["parameters"]["uc"]}')
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
#only_gen_path is a debugging variable and will return only the paths if set to True to avoid repetitive generations
def image_gen(auth,prompt,filepath,only_gen_path=False):
	global PRODUCED_IMAGES, SKIPPED_IMAGES, WAITS_SHORT, WAITS_LONG
	api_header=f'Bearer {auth["auth_token"]}'
	retry_time=5
	while not only_gen_path:
		time.sleep(WAIT_TIME)#Waiting for the specified amount to avoid getting limited
		try:
			start=time.time()
			resp=requests.post(URL,json.dumps(prompt[0]),headers={'Authorization': api_header,'Content-Type': 'application/json','accept': 'application/json',})
			resp_content=resp.content
			resp_length=len(resp_content)
			if resp_length>1000:
				print(f'Response length: {resp_length}')
			else:
				print(f'Likely fault detected: {resp_content}')
			base64_image=resp_content.splitlines()[2].replace(b"data:", b"")
			decoded=base64.b64decode(base64_image)
			#Check for server load to respect terms. Typical generation times are between 3 and 4 seconds
			end=time.time()
			processing_time=end-start
			print(f'NAI Server Generation Time:{(processing_time)}s')
			if processing_time>40:
				if processing_time>60:
					print('Server under heavy load (or very weak internet), taking a 2m chill pill')
					WAITS_LONG+=1
					time.sleep(120)
				else:
					print('Server under load, waiting half a minute')
					WAITS_SHORT+=1
					time.sleep(30)
			break
		except:
			print(f'CREATION ERROR ENCOUNTERED. RETRYING AFTER{min(retry_time,90)}s')
			time.sleep(min(retry_time,90))
			print('RETRYING NOW')
			retry_time+=5
			continue

	if not only_gen_path:
		with open(filepath,'wb+') as t:
			t.write(decoded)
		t.close()
		PRODUCED_IMAGES += 1
	else:
		SKIPPED_IMAGES += 1
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

#Saves used settings
def save_settings(folder_name,settings,sub_folder=''):
	if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}'): os.makedirs(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}')
	t=open(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}/settings꞉{replace_forbidden_symbols(settings["name"])}.py','w',encoding="utf_16")
	t.write(f'settings={settings}')
	t.close
	
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
	for img in imgs:
		if passed_image_mode==False:
			row.append(np.array(Image.open(img)))
		else:
			row.append(img)
		n+=1
		if n==row_length:
			rows.append(np.hstack(row))
			n=0
			row=[]
	collage=np.vstack(rows)

	if pass_image==False:
		folder_name,name,name_extra=replace_forbidden_symbols(folder_name),replace_forbidden_symbols(name),replace_forbidden_symbols(name_extra)
		if passed_image_mode==False:
			path=f'{os.path.dirname(os.path.abspath(imgs[0]))}/{name}_Collage{name_extra}.jpg'
		else:
			path=f'__0utput__/{folder_name}/{name}_Collage{name_extra}.jpg'
		Image.fromarray(collage).save(path)
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
	img_header = Image.new("RGB", (img_collages.width, line_height*8), (0, 0, 0))
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
	draw.text((10,line_height*(3+used_lines_name)),f'Resolution {settings["img_mode"]}',font=font,fill=(255,255,255,0))
	draw.text((10,line_height*(4+used_lines_name)),f'Sampler: {settings["sampler"]}',font=font,fill=(255,255,255,0))
	draw.text((10,line_height*(5+used_lines_name)),f'Steps: {settings["steps"]}',font=font,fill=(255,255,255,0))
	draw.text((10,line_height*(6+used_lines_name)),f'Scale: {settings["scale"]}',font=font,fill=(255,255,255,0))

	currently_used_lines=7+used_lines_name
	#Draw the prompt and UC on the right side
	full_prompt=settings["QT"]+settings["prompt"]
	draw, img_header, used_lines_prompt=fallback_font_writer(draw, img_header, full_prompt, left_meta_block, line_height*0, img_collages.size[0]-left_meta_block, currently_used_lines, line_height, (200,255,200,0))
	currently_used_lines=max(currently_used_lines,used_lines_prompt)
	available_lines = currently_used_lines-used_lines_prompt

	full_UC=UNDESIRED_CONTENT_LISTS[settings["UCp"]][1]+settings["UC"]
	draw, img_header, used_lines_uc=fallback_font_writer(draw, img_header, full_UC, left_meta_block, line_height*(used_lines_prompt), img_collages.size[0]-left_meta_block, available_lines, line_height, (255,200,200,0))

	#Combining and saving
	full_img = Image.new('RGB', (img_collages.width, img_header.height + img_collages.height))
	full_img.paste(img_header, (0, 0))
	full_img.paste(img_collages, (0, img_header.height))
	if settings.get('folder_name_user'):
		settings["folder_name_extra"]=settings["folder_name_user"]+f'/{settings["name"]}'
		path=f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages{settings["folder_name_user"]}/'
		if not os.path.exists(path): os.makedirs(path)
		full_img.save(f'{path}{replace_forbidden_symbols(settings["name"])}_Collage({replace_forbidden_symbols(name_extra)}).jpg')
	else:
		full_img.save(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/{replace_forbidden_symbols(settings["name"])}_Collage({replace_forbidden_symbols(name_extra)}).jpg')
	

#Writes a text character by character, going through a list of fonts and trying to find one that has the requested character
def fallback_font_writer(draw, img, text, x, y, wrap_x, available_y_lines, line_height, fill):
	# Initialize needed variables
	starting_x = x
	line_width = 0
	used_lines = 1
	safety_offset_x = 75
	newline = False

	# Iterate through each character in the text
	for char in text:
		# Determine whether to draw the character in the current or a next line
		if line_width > wrap_x - safety_offset_x:
			x = starting_x
			y += line_height
			used_lines += 1
			newline = True
		#Make sure there's room to write
		if used_lines > available_y_lines:
			img = ImageOps.expand(img, border=(0, 0, 0, line_height), fill=(0, 0, 0))
			draw = ImageDraw.Draw(img)
			available_y_lines += 1
		# Try to render the character with each font in the font list
		font_used = None
		for n in range(len(FONT_LIST)):
			# Check if the font has the character in its character map
			if ord(char) in TT_FONTS[n]['cmap'].getBestCmap().keys():
				font_used = FONT_OBJS[n]
				draw.text((x, y), char, font=font_used, fill=fill)
				break
		# If a font was used, get the size of the character and update the x position
		if font_used:
			char_bbox = draw.textbbox((0, 0), char, font=font_used)
			width, height = char_bbox[2] - char_bbox[0], char_bbox[3] - char_bbox[1]
			if newline == True:
				line_width = width
				newline = False
			else:
				line_width += width
			x += width
		# If no font was able to render the character, skip it
		else:
			print(f'Warning: Unable to render character: {ord(char)}')
			continue
			newline = False
	return draw, img, used_lines

###
#Rendering Functions
###

#Simply formats and passes the prompt on without changes, used for simple generations or complex external logic
def generate_as_is(settings,enumerator,only_gen_path=False):
	prompt=form_prompt(settings)
	filepath=make_file_path(prompt,enumerator,settings["folder_name"],settings["folder_name_extra"])
	return image_gen(auth,prompt,filepath,only_gen_path)

#Takes a prompt and renders it across multiple seeds at multiple scales, then puts all generations into a big collage together with the metadata
#If a seed list is passed or the default is used, make sure it has enough seeds for the requested amount of scales (collage_width²)
#Does some pre-processing, then adds a task to the PROCESSING_QUEUE which will be processed with prompt_stabber_process
def prompt_stabber(settings,only_gen_path=False):
	global QUEUED_IMAGES
	
	#Configures the seed list
	if settings["seed"]=='default':
		seed_list=PROMPT_STABBER_DEFAULT_SEEDS
	elif settings["seed"][0]=='random':
		seed_list=generate_seed_cluster(settings["seed"][1])
	else:
		seed_list=settings["seed"]

	collage_width_squared=settings["collage_width"]*settings["collage_width"]
	number_of_imgs=collage_width_squared*len(seed_list)*len(seed_list[0])

	#Adjusts all needed parameters and adds the task
	QUEUED_IMAGES+=number_of_imgs
	settings["collage_width_squared"]=collage_width_squared
	settings["seed_list"]=seed_list
	settings["number_of_imgs"]=number_of_imgs
	settings["processing_type"]='stab'
	if only_gen_path:
		settings["only_gen_path"]=True
	else:
		settings["only_gen_path"]=False
	PROCESSING_QUEUE.append(settings)

def prompt_stabber_process(settings):
	global PRODUCED_IMAGES,QUEUED_IMAGES,FINISHED_TASKS,SKIPPED_IMAGES,SKIPPED_TASKS,FUTURE_LIST, EXECUTOR
	rendered_imgs=1
	img_settings=copy.deepcopy(settings)

	#Saving settings and configuring folder structure
	if settings["folder_name"]=="":
		img_settings["folder_name"]=settings["name"]
		if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(img_settings["folder_name"])}/#ClusterCollages/'):
			os.makedirs(f'__0utput__/{replace_forbidden_symbols(img_settings["folder_name"])}/#ClusterCollages/')
		save_settings(img_settings["folder_name"],settings,sub_folder='/#ClusterCollages')
		settings["folder_name"]=settings["name"]
	else:
		if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/'):
			os.makedirs(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/')
		save_settings(settings["folder_name"],settings,sub_folder='/#ClusterCollages')

	#Configures steps and scale lists
	if type(settings["steps"])==list:
		if settings["collage_width_squared"]==1:
			steps_list=[settings["steps"][0],0]
		else:
			steps_list=[settings["steps"][0],(settings["steps"][1]-settings["steps"][0])/(settings["collage_width_squared"]-1)]
	else:
		steps_list=[settings["steps"],0]

	if type(settings["scale"])==list:
		if settings["collage_width_squared"]==1:
			scale_list=[settings["scale"][0],0]
		else:
			scale_list=[settings["scale"][0],(settings["scale"][1]-settings["scale"][0])/(settings["collage_width_squared"]-1)]
	else:
		scale_list=[settings["scale"],0]

	#This loop makes the initial collages
	collages=[]
	for seed_sub_list in settings["seed_list"]:
		collage_row=[]
		for seed in seed_sub_list:
			imgs=[]
			if img_settings.get('folder_name_user'):
				img_settings["folder_name_extra"]=img_settings["folder_name_user"]+f'/{img_settings["name"]}'
			else:
				img_settings["folder_name_extra"]=f'/{img_settings["name"]}'
			for n in range(settings["collage_width_squared"]):
				img_settings["scale"]=round(scale_list[0]+scale_list[1]*n,2)
				img_settings["steps"]=int(steps_list[0]+steps_list[1]*n)
				img_settings["seed"]=seed
				print(f'Processing task: {FINISHED_TASKS+1+SKIPPED_TASKS}/{PROCESSING_QUEUE_LEN}')
				print(f'Rendering img (current task): {rendered_imgs}/{settings["number_of_imgs"]}')
				print(f'Rendering img (complete queue): {PRODUCED_IMAGES+1+SKIPPED_IMAGES}/{QUEUED_IMAGES}')
				imgs.append(generate_as_is(img_settings,f'(Seed꞉{seed})(Scale꞉{img_settings["scale"]})(Steps꞉{img_settings["steps"]})',settings["only_gen_path"]))
				rendered_imgs+=1
			if settings["collage_width_squared"]==1:
				collage_row.append(*imgs)
			else:
				collage_row.append(make_collage(imgs,settings["name"],row_length=settings["collage_width"],name_extra=f'(Seed꞉{seed})(Sampler꞉{settings["sampler"]})'))
		collages.append(collage_row)
	
	#This loop puts the borders and seeds on the collages
	color=np.array([30,30,30])
	bordered_collages=[]
	for (collage_row,seed_sub_list) in zip(collages,settings["seed_list"]):
		for (collage,seed) in zip(collage_row,seed_sub_list):
			bordered_collage_row=[]
			bordered_collage=cv2.copyMakeBorder(np.array(Image.open(collage)),35,15,15,15,cv2.BORDER_CONSTANT,None,value=(int(color[0]),int(color[1]),int(color[2])))
			font=ImageFont.truetype(*CC_SEEDS_FONT)
			img_pil=Image.fromarray(bordered_collage)
			draw=ImageDraw.Draw(img_pil)
			draw.text((10,-5),f'{seed}',font=font,fill=(255,255,255,0))
			seeded_collage=np.array(img_pil)
			bordered_collages.append(seeded_collage)
			color+=[5,5,5]

	cluster_collage=make_collage(bordered_collages,settings["name"],row_length=len(settings["seed_list"][0]),passed_image_mode=True,folder_name=settings["folder_name"],pass_image=True)
	FUTURES.append(EXECUTOR.submit(attach_metadata_header, cluster_collage, settings, f'Cluster[{settings["sampler"]}]'))
	#attach_metadata_header(cluster_collage, settings, f'Cluster[{settings["sampler"]}]')
	FINISHED_TASKS+=1

#Renders a loop according to the settings and saves those
#Does some pre-processing, then adds a task to the PROCESSING_QUEUE which will be processed with render_loop_process
def render_loop(settings,eval_guard=True,only_gen_path=False):
	global QUEUED_IMAGES
	number_of_imgs=len(settings["quantity"])

	#Configures the seed
	if settings["seed"]=='random':
		settings["seed"]=generate_seed()
	elif type(settings["seed"])==int:
		pass
	else:
		settings["seed"]=4246521898

	#Adjusts all other needed parameters and adds the task
	QUEUED_IMAGES+=number_of_imgs
	settings["number_of_imgs"]=number_of_imgs
	settings["processing_type"]='loop'
	if only_gen_path:
		settings["only_gen_path"]=True
	else:
		settings["only_gen_path"]=False
	if eval_guard:
		settings["eval_guard"]=True
	else:
		settings["eval_guard"]=False
	PROCESSING_QUEUE.append(settings)

def render_loop_process(settings):
	save_settings(settings["folder_name"],settings)
	imgs=[]
	img_settings=copy.deepcopy(settings)

	img_settings["folder_name_extra"]=''
	if settings["folder_name"]=="":
		img_settings["folder_name"]=settings["name"]
	rendered_imgs=1
	for n in settings["quantity"]:
		enumerator=f'''({img_settings["seed"]})(#{str((n+1)).rjust(4,'0')})'''
		if not(type(settings["scale"])==int or type(settings["scale"])==float):
			img_settings["scale"]=settings["scale"][0]+settings["scale"][1]*n
			enumerator+=f'(Scale꞉{img_settings["scale"]})'
		if type(settings["steps"])!=int:
			img_settings["steps"]=settings["steps"][0]+int(settings["steps"][1]*n)
			enumerator+=f'(Steps꞉{img_settings["steps"]})'
		if type(settings["prompt"])!=str:
			img_settings["prompt"]=""
			for prompt_list in settings["prompt"]:
				if settings["eval_guard"]:
					img_settings["prompt"]+=eval(prompt_list[0],{'__builtins__':{}},{'n':n,'prompt_list':prompt_list})
				else:
					img_settings["prompt"]+=eval(prompt_list[0],{},{'n':n,'prompt_list':prompt_list})
		if type(settings["UC"])!=str:
			img_settings["UC"]=""
			for UC_list in settings["UC"]:
				if settings["eval_guard"]:
					img_settings["UC"]+=eval(UC_list[0],{"__builtins__":{}},{'n':n,'UC_list':UC_list})
				else:
					img_settings["UC"]+=eval(UC_list[0],{},{'n':n,'UC_list':UC_list})
		print(f'Processing task: {FINISHED_TASKS+1+SKIPPED_TASKS}/{PROCESSING_QUEUE_LEN}')
		print(f'Rendering img (current task): {rendered_imgs}/{settings["number_of_imgs"]}')
		print(f'Rendering img (complete queue): {PRODUCED_IMAGES+1+SKIPPED_IMAGES}/{QUEUED_IMAGES}')
		imgs.append(generate_as_is(img_settings,enumerator,settings["only_gen_path"]))
		rendered_imgs+=1
	if settings['video'] == 'standard':
		FUTURES.append(EXECUTOR.submit(make_vid,settings['name'],fps=BASE_FPS))
	elif settings['video'] == 'interpolated':
		FUTURES.append(EXECUTOR.submit(make_interpolated_vid,settings['name'],fps=BASE_FPS,factor=FF_FACTOR,output_mode=FF_OUTPUT_MODE))
	return imgs

###
# Task processing functions
###

def process_queue(skip=0):
	global PROCESSING_QUEUE,PROCESSING_QUEUE_LEN,SKIPPED_IMAGES,SKIPPED_TASKS
	PROCESSING_QUEUE_LEN=len(PROCESSING_QUEUE)
	for n in range(len(PROCESSING_QUEUE)):
		if skip>0:
			SKIPPED_TASKS+=1
			print(f"Skipping task {SKIPPED_TASKS}| There are {len(PROCESSING_QUEUE)} tasks left")
			SKIPPED_IMAGES+=PROCESSING_QUEUE.popleft()["number_of_imgs"]
			skip-=1
		else:
			process_task(PROCESSING_QUEUE.popleft())

def process_task(settings):
	if settings["processing_type"]=='stab':
		prompt_stabber_process(settings)
	elif settings["processing_type"]=='loop':
		render_loop_process(settings)

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
	for n in range(5):
		print('GENERATION COMPLETE')
	print(f'Images generated:{PRODUCED_IMAGES}')
	print(f'Images skipped:{SKIPPED_IMAGES}')
	print(f'Short waits:{WAITS_LONG}')
	print(f'Long waits:{WAITS_SHORT}')