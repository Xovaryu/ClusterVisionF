"""
image_generator.py
	This module is responsible for the actual image (and video) generation

01.	form_prompt
			Takes the settings dict and reformats it into the format NAI expects
02.	image_gen
			This is the primary function to generate images, it takes the finished settings, requests the generation from NAI's servers
			It will retry until either the generation was successful, or cancelled
03.	generate_seed + generate_seed_cluster
			generate_seeds makes a numerical seed like NAI would, and generate_seed_cluster simple takes in dimensions and makes an array of such seeds
04.	make_vid
			This function will create a video if requested, and it will run completely in parallel to the image generation, and it may as such occupy a decent chunk of RAM for some time
		interpolate_vid
			This function, if it was currently enabled, would allow the use of FlowFrames to interpolate a video
		make_interpolated_vid
			This function just combines the two functions above into a single call, still currently disabled
05.	make_collage
			Takes in a bunch of images and turns them into a simple collage
06.	attach_metadata_header
			Takes an almost finished cluster collage and puts the metadata header on it, and saves it
07.	generate_as_is
			Takes in the provided settings and then generates a single image from them
08.	cluster_collage + cluster_collage_processor
			Creates and queues a task to create a cluster collage, which can then later be finished by the according processor function
09.	image_sequence + image_sequence_processor
			Same as above, just for image sequences
10.	cluster_sequence + cluster_sequence_processor
			Same as above, just for cluster sequences which is a combination of the two types of tasks above
11.	steps_scale_pre_processor + steps_scale_processor
			These two functions are responsible for taking the user input and turning them into lists of the actual scales/steps to render
12.	process_queue
			This is the main loop to process all tasks in the queue
13.	process_task
			A simple function called per task that calls the correct processor to perform it
14.	wipe_queue
			Does what it says, wipes the queue and resets some relevant settings
"""

from initialization import handle_exceptions, GlobalState
GS = GlobalState()
import text_manipulation as TM
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
import imageio
import zipfile
import traceback

from PIL import ImageFont, ImageDraw, Image, ImageOps
Image.MAX_IMAGE_PIXELS = 900000000	
from queue import Queue
from collections import deque

# ---Primary Functions---

# 1. Takes the settings and reformats them for NAI's API
@handle_exceptions
def form_prompt(settings,number=1,noise=0.1,strength=0.4):
	if settings["dynamic_thresholding_percentile"] <= 0:
		settings["dynamic_thresholding_percentile"] = 0.000001
		print("[Warning] Dynamic thresholding percentile too low, adjusting to 0.000001, check your settings")
	elif settings["dynamic_thresholding_percentile"] > 1:
		settings["dynamic_thresholding_percentile"] = 1
		print("[Warning] Dynamic thresholding percentile too high, adjusting to 1, check your settings")
	json_construct={
		#This is the prompt, Quality Tags are not configured separately and net to be appended here manually
		'input': settings["prompt"],
		#Model as in UI (Curated/Full/Furry)
		'model': settings["model"],															
		'parameters': {
			#Seed as in UI
			'seed': settings["seed"],
			#Undesired Content as in UI
			'negative_prompt': settings["negative_prompt"],
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
			'dynamic_thresholding': settings["dynamic_thresholding"],
			'dynamic_thresholding_mimic_scale': settings["dynamic_thresholding_mimic_scale"],
			'dynamic_thresholding_percentile': settings["dynamic_thresholding_percentile"],
			'quality toggle': False,
			'ucPreset': 0,
			'uncond_scale': float(settings["negative_prompt_strength"])/100
			}
		}
	return [json_construct,settings["name"]]

# 2. The primary function to generate images. Sends the request and will persist until it is fulfilled, then saves the image, and returns the path
# Currently NAI specific
@handle_exceptions
def image_gen(auth,prompt,filepath,enumerator,token_test=False):
	skipped = False
	retry_time=5
	while GS.GENERATE_IMAGES:
		if GS.CANCEL_REQUEST:
			print('Image generation cancelled')
			return
		while GS.PAUSE_REQUEST:
			time.sleep(0.2)
		api_header=f'Bearer {auth}'
		if not GS.OVERWRITE_IMAGES and not token_test:
			if os.path.isfile(filepath):
				skipped = True
				#print("File already present, skipped generation")
				break
		if token_test:
			resp=requests.post(GS.URL,json.dumps(prompt[0]),headers={'Authorization': api_header,'Content-Type': 'application/json','accept': 'application/json',})
			resp_content=resp.content
			resp_length=len(resp_content)
			if resp_length>1000:
				return 'Success'
			elif resp_content == b'{"statusCode":401,"message":"Invalid accessToken."}' or resp_content == b'{"statusCode":400,"message":"Invalid Authorization header content."}':
				return 'Error'
		try:
			print(prompt)
			print(f'''{enumerator}\nDecrisp: {prompt[0]["parameters"]["dynamic_thresholding"]}{" | MS: " + str(prompt[0]["parameters"]["dynamic_thresholding_mimic_scale"]) + " | " + str(prompt[0]["parameters"]["dynamic_thresholding_percentile"]) + "%ile" if prompt[0]["parameters"]["dynamic_thresholding"] else ""}''')
			print(f'''Model: {prompt[0]["model"]}\nPrompt:\n{prompt[0]["input"]}\nUC:\n{prompt[0]["parameters"]["negative_prompt"]}''')

			start=time.time()
			resp=requests.post(GS.URL,json.dumps(prompt[0]),headers={'Authorization': api_header,'Content-Type': 'application/json','accept': 'application/json',})
			resp_content=resp.content
			resp_length=len(resp_content)
			if resp_length>1000:
				print(f'Response length: {resp_length}')
			elif resp_content == b'{"statusCode":401,"message":"Invalid accessToken."}' or resp_content == b'{"statusCode":400,"message":"Invalid Authorization header content."}':
				print(f'[Warning] Invalid access token. Please fetch your token from the website.')
				return 'Error'
			else:
				print(f'Likely fault detected: {resp_content}')
			end=time.time()
			processing_time=end-start
			print(f'NAI Server Generation Time:{(processing_time)}s')
			with zipfile.ZipFile(io.BytesIO(resp_content), "r") as zip_file:
				for file_name in zip_file.namelist():
					if file_name.endswith(".png"):
						with zip_file.open(file_name) as png_file:
							image_data = png_file.read()
							GS.PREVIEW_QUEUE.append(image_data)
							with open(filepath, 'wb+') as t:
								t.write(image_data)
							t.close()
			break
		except:
			traceback.print_exc()
			print(f'[Warning] Creation error encounted. Retrying after: {min(retry_time,15)}s')
			for i in range(min(retry_time,15)):
				time.sleep(1)
				if GS.CANCEL_REQUEST: break
			retry_time+=5
			continue
		time.sleep(GS.WAIT_TIME) # Waiting for the specified amount to avoid getting limited

	if not skipped and GS.GENERATE_IMAGES:
		GS.PRODUCED_IMAGES += 1
	else:
		GS.SKIPPED_IMAGES += 1
	GS.PRE_LAST_SEED = GS.LAST_SEED
	GS.LAST_SEED = str(prompt[0]['parameters']['seed'])
	return filepath

# 3. Function to generate seeds in the way NAI would
@handle_exceptions
def generate_seed():
	return math.floor(random.random()*(2**32)-1);

# This function uses generate_seed to generate a cluster of seeds
@handle_exceptions
def generate_seed_cluster(dimensions):
	seed_list=[]
	for rows in range(dimensions[0]):
		row=[]
		for columns in range(dimensions[1]):
			row.append(generate_seed())
		seed_list.append(row)
	return seed_list

# ---Additional Media Functions---
# 4. These are the functions to make videos if requested, though they are still in need of quite a bit of cleaning up and love
@handle_exceptions
def make_vid_ffmpeg(vid_path, img_futures, num_frames, fps=7, base_path='__0utput__', codec='vp9', quality=10, pixelformat='yuv420p'):
	print('Parallel video thread started')
	
	# Determine frame size from the first completed image future
	first_img_future = img_futures.get()
	h, w, _ = np.array(first_img_future.result()).shape
	frameSize = (w, h)

	# Mapping of codecs to file extensions
	codec_extensions = {
		'vp9': '.webm',
		'h264': '.mp4',
		'h265': '.mp4',
		'mpeg4': '.mp4',
		'libxvid': '.avi',
		# add more codecs and their extensions as needed
	}

	# Get the file extension for the chosen codec
	extension = codec_extensions.get(codec, '.webm')  # default to .webm if codec not in dict

	# Construct full video path with correct extension
	full_vid_folder_path = f'{base_path}/{vid_path}'
	os.makedirs(full_vid_folder_path, exist_ok=True)
	
	# Initialize video writer
	writer = imageio.get_writer(full_vid_folder_path+extension, fps=fps, codec=codec, quality=quality, pixelformat=pixelformat)

	# Write first frame to video
	writer.append_data(np.array(first_img_future.result()))

	# Write remaining frames to video
	for _ in range(num_frames - 1):
		future = img_futures.get()
		img = future.result()
		writer.append_data(np.array(img))
	writer.close()

	print('Finished making video')

@handle_exceptions
def make_vid(vid_params, vid_path, img_futures, num_frames, base_path='__0utput__'):
	print('Parallel video thread started')

	# Mapping of codecs to file extensions
	codec_extensions = {
		'vp9': '.webm',
		'h264': '.mp4',
		'h265': '.mp4',
		'mpeg4': '.mp4',
		'libxvid': '.avi',
		# add more codecs and their extensions as needed
	}
	# Get the file extension for the chosen codec
	extension = codec_extensions.get(vid_params['codec'], '.webm')  # default to .webm if codec not in dict

	# Construct full video path with correct extension
	full_vid_folder_path = f'{base_path}/{vid_path}'
	os.makedirs(full_vid_folder_path, exist_ok=True)
	
	# Initialize video writer
	writer = imageio.get_writer(full_vid_folder_path+extension, **vid_params)
	
	# Determine frame size from the first completed image future
	first_img_future_or_str = img_futures.get()
	expecting_strs = False # IS will return paths while CS will return the cluster collages directly, so we need to check for what we're working with
	if type(first_img_future_or_str) == str:
		first_img = Image.open(first_img_future_or_str)
		expecting_strs = True
	else:
		first_img = first_img_future_or_str.result()
	h, w, _ = np.array(first_img).shape
	frameSize = (w, h)
	
	# Write first frame to video
	writer.append_data(np.array(first_img))
	del first_img # The images must be deleted manually from memory here and in the loop after usage, lest they persist in the RAM

	# Write remaining frames to video
	for _ in range(num_frames - 1):
		img = img_futures.get()
		if GS.CANCEL_REQUEST:
			del img
			print('Video processing cancelled')
			writer.close()
			return
		if expecting_strs:
			img = Image.open(img)
		else:
			img = img.result()
		writer.append_data(np.array(img))
		del img
	writer.close()

	print('Finished making video')

# Calls flowframes to interpolate an existing video, will run in parallel
@handle_exceptions
def interpolate_vid(vid_path,factor=4,output_mode=2,base_path='__0utput__/'):
	vid_path=TM.replace_forbidden_symbols(vid_path)
	SW_MINIMIZE = 6
	info = subprocess.STARTUPINFO()
	info.dwFlags = subprocess.STARTF_USESHOWWINDOW
	info.wShowWindow = SW_MINIMIZE
	path=f'{os.getcwd()}/{base_path+vid_path}/{vid_path}.webm'
	p = subprocess.Popen([GS.FLOWFRAMES_PATH,path,'-start','-quit-when-done',
	f'-factor={factor}',f'-output-mode={output_mode}'],startupinfo=info)
	print("Interpolating video in Flowframes")

# Simply combines the above functions into a single call
@handle_exceptions
def make_interpolated_vid(vid_path,fps=7,factor=4,output_mode=2,base_path='__0utput__/'):
	make_vid(vid_path,fps,base_path)
	interpolate_vid(vid_path,factor,output_mode,base_path)

# 5. Takes in a list of images and turns them into a collage
@handle_exceptions
def make_collage(imgs,name,row_length=5,name_extra="",passed_image_mode=False,folder_name='',pass_image=False):
	row=[]
	rows=[]
	n=0
	multirow=False
	for img in imgs:
		if passed_image_mode==False:
			row.append(np.array(Image.open(img)))
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
		folder_name,name,name_extra=TM.replace_forbidden_symbols(folder_name),TM.replace_forbidden_symbols(name),TM.replace_forbidden_symbols(name_extra)
		if passed_image_mode==False:
			path=f'{os.path.dirname(os.path.abspath(imgs[0]))}/{name}_Collage{name_extra}.jpg'
		else:
			path=f'__0utput__/{folder_name}/{name}_Collage{name_extra}.jpg'
		Image.fromarray(collage).save(path, quality=90)
		return path
	else:
		return collage

# 6. This function handles the complex logic of parsing and writing all the metadata, combining it with the passed image and saving the finished cluster collage
@handle_exceptions
def attach_metadata_header(img_collages,settings,name_extra, cc=''):
	img_collages=Image.fromarray(img_collages)
	#Text configuration
	line_height=GS.FONT_SIZE+5
	font=ImageFont.truetype(GS.FONT_LIST[0],GS.FONT_SIZE)
	left_meta_block=900
	
	#Creating the header
	starting_amount_lines = 9
	img_header = Image.new("RGB", (img_collages.width, line_height*starting_amount_lines), (0, 0, 0))
	draw = ImageDraw.Draw(img_header)
	
	#Draw the basic metadata on the left side
	draw.text((10,line_height*0),f"ClusterVisionF"+cc,font=font,fill=(255,220,255,0))
	draw.text((10,line_height*1),f'Creator: {GS.CREATOR_NAME}',font=font,fill=(200,200,255,0))
	# Name, using the FFW to make symbols available
	draw, img_header, used_lines_name=TM.fallback_font_writer(draw, img_header, f'Name: {settings["name"]}', 10, line_height*2, left_meta_block, 1, line_height, (255,255,255,0))
	if settings["model"] == 'safe-diffusion':
		model = 'NovelAI Diffusion Curated V1.0.1'
	elif settings["model"] == 'nai-diffusion':
		model = 'NovelAI Diffusion Full V1.0.1'
	elif settings["model"] == 'nai-diffusion-2':
		model = 'NovelAI Diffusion Full V2'
	elif settings["model"] == 'nai-diffusion-furry':
		model = 'NovelAI Diffusion Furry V1.3'
	else:
		model = 'Unknown'
		print('[Warning] Unable to determine model for cluster collage')
	draw.text((10,line_height*(2+used_lines_name)),f'NovelAI Model: {model}',font=font,fill=(255,255,255,0))
	draw.text((10,line_height*(3+used_lines_name)),f'Resolution: {settings["img_mode"]}',font=font,fill=(255,255,255,0))
	currently_used_lines=4+used_lines_name
	
	# Steps, using the FFW to linebreak at |
	available_lines = starting_amount_lines - currently_used_lines
	steps = settings["steps"]
	steps_string = 'Steps: ' + (steps if isinstance(steps, str) and "⁅" in steps else '|'.join(str(s) for s in settings["meta"]["steps"]))
	draw, img_header, used_lines_steps=TM.fallback_font_writer(draw, img_header, steps_string, 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = '|')
	currently_used_lines=currently_used_lines+used_lines_steps
	
	# Scale, using the FFW to linebreak at |
	available_lines = available_lines - used_lines_steps
	scale = settings["scale"]
	scale_string = 'Scale: ' + (scale if isinstance(scale, str) and "⁅" in scale else '|'.join(str(s) for s in settings["meta"]["scale"]))
	draw, img_header, used_lines_scale=TM.fallback_font_writer(draw, img_header, scale_string, 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = '|')
	currently_used_lines=currently_used_lines+used_lines_scale
	
	# Sampler, using the FFW to linebreak at ,
	available_lines = available_lines - used_lines_scale
	draw, img_header, used_lines_samplers=TM.fallback_font_writer(draw, img_header, 'Sampler: '+', '.join(settings["sampler"][0]), 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = ',')
	currently_used_lines=currently_used_lines+used_lines_samplers
	
	decrisper_string = 'Decrisper: '
	if settings["dynamic_thresholding"] == False:
		decrisper_string += 'Off'
	else:
		decrisper_string += f'On | M. Scale: {settings["dynamic_thresholding_mimic_scale"]} | {settings["dynamic_thresholding_percentile"]}%ile'
	available_lines = available_lines - used_lines_samplers
	draw, img_header, used_lines_decrisper=TM.fallback_font_writer(draw, img_header, decrisper_string, 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = '|')
	currently_used_lines=currently_used_lines+used_lines_decrisper
	
	#Draw the prompt and UC on the right side
	full_prompt=settings["prompt"]
	draw, img_header, used_lines_prompt=TM.fallback_font_writer(draw, img_header, full_prompt, left_meta_block, line_height*0, img_collages.size[0]-left_meta_block,
		currently_used_lines, line_height, (180,255,180,0), explicit_space = True)
	currently_used_lines=max(currently_used_lines,used_lines_prompt)
	available_lines = currently_used_lines-used_lines_prompt

	full_UC=settings["negative_prompt"]
	draw, img_header, used_lines_uc=TM.fallback_font_writer(draw, img_header, full_UC, left_meta_block, line_height*(used_lines_prompt),
		img_collages.size[0]-left_meta_block, available_lines, line_height, (255,180,180,0), explicit_space = True)

	# Combining the collage and the metadata header to form the finished cluster collage and saving
	full_img = Image.new('RGB', (img_collages.width, img_header.height + img_collages.height))
	full_img.paste(img_header, (0, 0))
	full_img.paste(img_collages, (0, img_header.height))
	if settings.get('folder_name_user'):
		settings["folder_name_extra"] = settings["folder_name_user"]+f'/{settings["name"]}'
		path = f'__0utput__/{TM.replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages{settings["folder_name_user"]}/'
		os.makedirs(path, exist_ok=True)
		final_path = f'{path}{TM.replace_forbidden_symbols(settings["name"])}_Collage({TM.replace_forbidden_symbols(name_extra)}).jpg'
		full_img.save(final_path, quality=90)
	else:
		path = f'__0utput__/{TM.replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/'
		os.makedirs(path, exist_ok=True)
		final_path = path + f'{TM.replace_forbidden_symbols(settings["name"])}_Collage({TM.replace_forbidden_symbols(name_extra)}).jpg'
		full_img.save(final_path, quality=90)
	return full_img if cc!='' else None

# ---Rendering Functions---

# 7. Simply formats and passes the prompt to image_gen, used for simple generations, complex external logic or an auth token test
@handle_exceptions
def generate_as_is(settings,enumerator,token_test=False,token=''):
	if token_test:
		settings = {'name': 'Test', 'folder_name': '', 'folder_name_extra': '', 'model': 'nai-diffusion', 'seed': 0, 'sampler': 'k_euler_ancestral', 'scale': 10.0,
			'steps': 1, 'img_mode': {'width': 64, 'height': 64}, 'prompt': 'Test', 'negative_prompt': 'Test', 'smea': False, 'dyn': False, 'dynamic_thresholding': False,
			'dynamic_thresholding_mimic_scale': 10, 'dynamic_thresholding_percentile': 0.999, 'uncond_scale': 0.9}
		return image_gen(token,form_prompt(settings),'','',token_test=True)
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
	filepath=TM.make_file_path(prompt,enumerator,settings["folder_name"],settings["folder_name_extra"])
	return image_gen(GS.AUTH,prompt,filepath,enumerator)

# 8. Takes a prompt and renders it across multiple seeds at multiple scales, then puts all generations into a cluster collage together with the metadata
# Does some pre-processing to form a task for a cluster collage, then adds it to the GS.PROCESSING_QUEUE which will be processed with cluster_collage_processor
@handle_exceptions
def cluster_collage(settings,eval_guard=True):
	#Configures the seed list
	if settings["seed"]=='default':
		settings["seed"]=GS.PROMPT_STABBER_DEFAULT_SEEDS
	elif settings["seed"][0]=='random':
		settings["seed"]=generate_seed_cluster(settings["seed"][1])

	#Adjusts all needed meta parameters
	settings["meta"] = {}
	settings["meta"]["imgs_per_subcollage"] = settings["collage_dimensions"][0]*settings["collage_dimensions"][1]
	if not isinstance(settings["sampler"], list):
		samplers=1
	else:
		samplers=len(settings["sampler"][0])
	settings["meta"]["number_of_seeds"] = len(settings["seed"])*len(settings["seed"][0])
	settings["meta"]["number_of_imgs"] = settings["meta"]["imgs_per_collage"] = settings["meta"]["imgs_per_subcollage"]*samplers*settings["meta"]["number_of_seeds"]
	GS.QUEUED_IMAGES+=settings["meta"]["number_of_imgs"]

	settings["meta"]["processing_type"]='cluster_collage'
	if eval_guard:
		settings["meta"]["eval_guard"]=True
	else:
		settings["meta"]["eval_guard"]=False
	

	#Saving settings and configuring folder structure
	conf_settings=copy.deepcopy(settings)
	if settings["folder_name"]=="":
		conf_settings["folder_name"]=settings["name"]
		if not os.path.exists(f'__0utput__/{TM.replace_forbidden_symbols(conf_settings["folder_name"])}/#ClusterCollages/'):
			os.makedirs(f'__0utput__/{TM.replace_forbidden_symbols(conf_settings["folder_name"])}/#ClusterCollages/')
		TM.save_settings(conf_settings["folder_name"],settings,sub_folder='/#ClusterCollages')
		settings["folder_name"]=settings["name"]
	else:
		if not os.path.exists(f'__0utput__/{TM.replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/'):
			os.makedirs(f'__0utput__/{TM.replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/')
		TM.save_settings(conf_settings["folder_name"],settings,sub_folder='/#ClusterCollages')
	
	#Finally, add the task and move on
	GS.PROCESSING_QUEUE.append(settings)

# Called by process_task to generate a cluster collage from the settings
@handle_exceptions
def cluster_collage_processor(settings, cc='', cs_rendered_imgs=1):
	cc_enumerator = '' if cc == '' else f'(cc꞉{cc})'
	rendered_imgs = 1
	
	img_settings=copy.deepcopy(settings)

	#Configures steps and scale lists
	steps_scale_pre_processor(settings)

	#Configure the folder structure if the user specified something extra
	if img_settings.get('folder_name_user'):
		img_settings["folder_name_extra"]=img_settings["folder_name_user"]+f'/{TM.replace_forbidden_symbols(img_settings["name"])}'
	else:
		img_settings["folder_name_extra"]=f'/{TM.replace_forbidden_symbols(img_settings["name"])}'
	
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
			for s, seed in enumerate(seed_sub_list):
				imgs=[]
				n=0
				for r in range(settings["collage_dimensions"][1]):
					for c in range(settings["collage_dimensions"][0]):
						if GS.CANCEL_REQUEST:
							return
						#Load in the correct values for steps, scale and seed
						steps_scale_processor(settings,img_settings,{'n':n,'c':c,'r':r,'cc':cc,'s':s})
						img_settings["seed"]=seed
						#Process f-string if necessary
						if type(settings["prompt"])!=str:
							img_settings["prompt"] = TM.f_string_processor(settings["prompt"],settings["meta"]["eval_guard"],{'n':n,'c':c,'r':r,'cc':cc,'s':s})
							if 'Error' == img_settings["prompt"]:
								return 'Error'
						if type(settings["negative_prompt"])!=str:
							img_settings["negative_prompt"] = TM.f_string_processor(settings["negative_prompt"],settings["meta"]["eval_guard"],{'n':n,'c':c,'r':r,'cc':cc,'s':s})
							if 'Error' == img_settings["negative_prompt"]:
								return 'Error'
						f_variables_processor(settings, img_settings, {'n':n,'c':c,'r':r,'cc':cc,'s':s})
						#Report the current queue position before rendering
						if time.time() - GS.LAST_TASK_REPORT >= 1.0: #Limit reports to once a minute to prevent swamping the console
							GS.LAST_TASK_REPORT = time.time()
							print(f'Processing task: {GS.FINISHED_TASKS+1+GS.SKIPPED_TASKS}/{GS.PROCESSING_QUEUE_LEN}')
							if cc != None: print(f'Rendering img (current cluster collage): {rendered_imgs}/{settings["meta"]["imgs_per_collage"]}')
							if cc != None: print(f'Rendering img (current CS task): {cs_rendered_imgs}/{settings["meta"]["number_of_imgs"]}')
							if cc == None: print(f'Rendering img (current CC task): {rendered_imgs}/{settings["meta"]["number_of_imgs"]}')
							print(f'Rendering img (complete queue): {GS.PRODUCED_IMAGES+1+GS.SKIPPED_IMAGES}/{GS.QUEUED_IMAGES}')
						imgs.append(generate_as_is(img_settings,f'(Seed꞉{seed})(n꞉ {n})(r꞉ {r})(c꞉ {c}){cc_enumerator}(Scale꞉{img_settings["scale"]})(Steps꞉{img_settings["steps"]})(Sampler꞉{sampler})'))
						rendered_imgs += 1
						if cc != None: cs_rendered_imgs += 1
						n += 1
				# This part is responsible for creating the structure defined by the collage_dimensions
				if settings["meta"]["imgs_per_subcollage"]==1:
					collage=np.array(Image.open(imgs[0]))
				else:
					collage=make_collage(imgs,settings["name"],row_length=settings["collage_dimensions"][0],name_extra=f'(Seed꞉{seed})(Sampler꞉{sampler})',pass_image=True)
				# Once that is done the collages get bordered
				bordered_collage = ImageOps.expand(Image.fromarray(collage), border=(15, 35, 15, 15), fill=(int(color[0]), int(color[1]), int(color[2])))
				font=ImageFont.truetype(GS.FULL_DIR+GS.CC_SEEDS_FONT[0],GS.CC_SEEDS_FONT[1])
				draw=ImageDraw.Draw(bordered_collage)
				collage_metadata=f'{seed}'
				if not len(settings["sampler"][0]) == 1:
					collage_metadata += f' | {sampler}'
				draw.text((10,-5),collage_metadata,font=font,fill=(255,255,255,0))
				color+=[5,5,5]
				collage_rows.append(bordered_collage)
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
	future = GS.EXECUTOR.submit(attach_metadata_header, cluster_collage, settings, f'Cluster{cc_enumerator}[{settings["sampler"][0]}]',f' - cc: {cc}' if cc!='' else '')
	GS.FUTURES.append(future)
	GS.FUTURES.append(future)
	if cc==None: GS.FINISHED_TASKS+=1
	return future

# 9. Does some pre-processing to form a task for an image sequence, then adds it to the GS.PROCESSING_QUEUE which will be processed with image_sequence_processor
@handle_exceptions
def image_sequence(settings,eval_guard=True):
	#Configures the seed
	if settings["seed"]=='random':
		settings["seed"]=generate_seed()
	elif type(settings["seed"])==int:
		pass
	else:
		settings["seed"]=4246521898

	#Adjusts all needed meta parameters
	settings["meta"]={}
	settings["meta"]["number_of_imgs"]=settings["quantity"]
	GS.QUEUED_IMAGES+=settings["meta"]["number_of_imgs"]
	settings["meta"]["processing_type"]='image_sequence'
	if eval_guard:
		settings["meta"]["eval_guard"]=True
	else:
		settings["meta"]["eval_guard"]=False
	
	#Saves settings and configures folder settings
	if settings["folder_name"]=="":
		folder=settings["name"]
		TM.save_settings(folder,settings)
		settings["folder_name"]=folder
	else:
		TM.save_settings(settings["folder_name"],settings)
	settings["meta"]["vid_folder"] = f'{settings["folder_name"]}/#Videos/{settings["name"]}'
	#Finally, add the task and move on
	GS.PROCESSING_QUEUE.append(settings)

# Called by process_task to generate an image sequence from the settings
@handle_exceptions
def image_sequence_processor(settings):
	imgs=[]
	img_settings=copy.deepcopy(settings)

	steps_scale_pre_processor(settings)

	img_settings["folder_name_extra"]=''
	rendered_imgs=1
	
	### To be replaced later
	vid_params = {
		'fps': 10,
		'codec': 'vp9',
		'pixelformat': 'yuv444p',
	}
	
	#If video generation is requested, start the according thread before the image generation loop which will use the img_results queue
	vid = False
	img_results = Queue()
	if settings["video"] == 'standard':
		vid = True
		img_results = Queue()
		GS.FUTURES.append(GS.EXECUTOR.submit(make_vid, vid_params, settings["meta"]["vid_folder"], img_results, settings["quantity"]))
	elif settings["video"] == 'interpolated':
		vid = True
		img_results = Queue()
		GS.FUTURES.append(GS.EXECUTOR.submit(make_interpolated_vid, settings["meta"]["vid_folder"], img_results, settings["quantity"], fps=settings["FPS"], factor=FF_FACTOR,output_mode=FF_OUTPUT_MODE))

	for n in range(settings["quantity"]):
		if GS.CANCEL_REQUEST:
			return
		steps_scale_processor(settings, img_settings, {'n':n})
		enumerator=f'''({img_settings["seed"]})(#{str((n+1)).rjust(4,'0')})'''
		enumerator+=f'(Scale꞉{img_settings["scale"]})(Steps꞉{img_settings["steps"]})'
		#Process f-string if necessary
		f_variables_processor(settings, img_settings, {'n':n})
		if type(settings["prompt"])!=str:
			img_settings["prompt"] = TM.f_string_processor(settings["prompt"],settings["meta"]["eval_guard"],{'n':n})
			if 'Error' == img_settings["prompt"]:
				return 'Error'
		if type(settings["negative_prompt"])!=str:
			img_settings["negative_prompt"] = TM.f_string_processor(settings["negative_prompt"],settings["meta"]["eval_guard"],{'n':n})
			if 'Error' == img_settings["negative_prompt"]:
				return 'Error'
		if time.time() - GS.LAST_TASK_REPORT >= 1.0: #Limit reports to once a minute to prevent swamping the console
			GS.LAST_TASK_REPORT = time.time()
			print(f'Processing task: {GS.FINISHED_TASKS+1+GS.SKIPPED_TASKS}/{GS.PROCESSING_QUEUE_LEN}')
			print(f'Rendering img (current IS task): {rendered_imgs}/{settings["meta"]["number_of_imgs"]}')
			print(f'Rendering img (complete queue): {GS.PRODUCED_IMAGES+1+GS.SKIPPED_IMAGES}/{GS.QUEUED_IMAGES}')
		if vid:
			img_results.put(generate_as_is(img_settings,enumerator))
		else:
			generate_as_is(img_settings,enumerator)
		rendered_imgs+=1
	GS.FINISHED_TASKS+=1

# 10. Does some pre-processing to form a task for an cluster sequence, then adds it to the GS.PROCESSING_QUEUE which will be processed with cluster_sequence_processor
@handle_exceptions
def cluster_sequence(settings,eval_guard=True):
	#Configures the seed list
	if settings["seed"] == 'default': ### Probably deprecated
		settings["seed"] = GS.SEED_LISTS["Default 3x3"]
	elif settings["seed"][0] == 'random':
		settings["seed"] = generate_seed_cluster(settings["seed"][1])
	#Adjusts all needed meta parameters
	settings["meta"] = {}
	settings["meta"]["imgs_per_subcollage"] = settings["collage_dimensions"][0]*settings["collage_dimensions"][1]
	if not isinstance(settings["sampler"], list):
		samplers=1
	else:
		samplers=len(settings["sampler"][0])
	settings["meta"]["number_of_seeds"] = len(settings["seed"])*len(settings["seed"][0])
	settings["meta"]["imgs_per_collage"] = settings["meta"]["imgs_per_subcollage"]*samplers*settings["meta"]["number_of_seeds"]
	settings["meta"]["number_of_imgs"] = settings["meta"]["imgs_per_collage"]*settings["quantity"]
	GS.QUEUED_IMAGES += settings["meta"]["number_of_imgs"]
	settings["meta"]["processing_type"]='cluster_sequence'
	if eval_guard:
		settings["meta"]["eval_guard"]=True
	else:
		settings["meta"]["eval_guard"]=False
		
	#Saves settings and configures folder settings
	if settings["folder_name"]=="":
		folder=settings["name"]
		TM.save_settings(folder,settings)
		settings["folder_name"]=folder
	else:
		TM.save_settings(settings["folder_name"],settings)
	settings["meta"]["vid_folder"] = f'{settings["folder_name"]}/#Videos/{settings["name"]}'
	#Finally, add the task and move on
	GS.PROCESSING_QUEUE.append(settings)

# Called by process_task to generate a cluster sequence (a sequence of cluster collages) from the settings
@handle_exceptions
def cluster_sequence_processor(settings):
	### To be replaced later
	vid_params = {
		'fps': 10,
		'codec': 'vp9',
		'pixelformat': 'yuv444p',
	}

	# If video generation is requested, start the according thread before the image generation loop which will use the img_results queue
	# Otherwise run cluster_collage_processor making sure that its result gets discarded
	vid = False
	if settings["video"] == 'standard':
		vid = True
		img_results = Queue()
		GS.FUTURES.append(GS.EXECUTOR.submit(make_vid, vid_params, settings["meta"]["vid_folder"], img_results, settings["quantity"]))
	elif settings["video"] == 'interpolated':
		vid = True
		img_results = Queue()
		GS.FUTURES.append(GS.EXECUTOR.submit(make_interpolated_vid, vid_params, settings["meta"]["vid_folder"], img_results, settings["quantity"], fps=settings["FPS"], factor=FF_FACTOR,output_mode=FF_OUTPUT_MODE))
	for cc in range(settings["quantity"]):
		if vid:
			img_results.put(cluster_collage_processor(settings, cc, 1+cc*settings["meta"]["imgs_per_collage"]))
		else:
			cluster_collage_processor(settings, cc, 1+cc*settings["meta"]["imgs_per_collage"])
	GS.FINISHED_TASKS+=1

# ---Rendering pre-processing functions---

# 11. This function handles the pre-processing of steps and scale, it takes the settings from the user input and makes it computible per image
@handle_exceptions
def steps_scale_pre_processor(settings):
	settings["meta"]["steps"] = []
	settings["meta"]["scale"] = []
	if settings["meta"].get('imgs_per_collage'):
		quantity = settings["meta"]["imgs_per_subcollage"]
	else:
		quantity = settings["quantity"]
	if type(settings["steps"]) == list and quantity != 1:
		settings["meta"]["steps"] = np.linspace(settings["steps"][0], settings["steps"][-1], quantity).tolist()
	elif not type(settings["steps"]) == str:
		if isinstance(settings["steps"], int):
			settings["meta"]["steps"]=[settings["steps"]]
		else:
			settings["meta"]["steps"]=[settings["steps"][0]]

	if type(settings["scale"])==list and quantity != 1:
		settings["meta"]["scale"] = [round(x,6) for x in np.linspace(settings["scale"][0], settings["scale"][-1], quantity).tolist()]
	elif not type(settings["scale"]) == str:
		if any(isinstance(settings["scale"], type) for type in [int, float]):
			settings["meta"]["scale"]=[settings["scale"]]
		else:
			settings["meta"]["scale"]=[settings["scale"][0]]

# This function takes the passed variables and pre-processed steps/scale values and returns the desired value for the current image
@handle_exceptions
def steps_scale_processor(settings, img_settings, var_dict):
	for key, func1, func2 in [("steps", int, int), ("scale", float, lambda x: round(x, 6))]:
		value = settings[key]
		img_settings[key] = (func2(func1(TM.f_string_processor([['f"""' + str(value) + '"""']], settings["meta"]["eval_guard"], var_dict))) if isinstance(value, str)
			else (settings["meta"][key][0] if len(settings["meta"][key]) == 1 else func2(settings["meta"][key][var_dict['n']])))

# This function makes sure to process f-strings from other simpler fields
@handle_exceptions
def f_variables_processor(settings, img_settings, var_dict):
	img_settings["dynamic_thresholding_mimic_scale"] = float(TM.f_string_processor([['f"""'+str(settings["dynamic_thresholding_mimic_scale"])+'"""']],settings["meta"]["eval_guard"],var_dict))
	img_settings["dynamic_thresholding_percentile"] = float(TM.f_string_processor([['f"""'+str(settings["dynamic_thresholding_percentile"])+'"""']],settings["meta"]["eval_guard"],var_dict))
	img_settings["negative_prompt_strength"] = float(TM.f_string_processor([['f"""'+str(settings["negative_prompt_strength"])+'"""']],settings["meta"]["eval_guard"],var_dict))
	
# ---Task processing functions---

# 12. This is the primary loop for iterating over the processing queue, which will either cancel and wipe if requested, skip if requested, or process the next task in the queue
@handle_exceptions
def process_queue(skip=0,end=False,preview=None):
	GS.CANCEL_REQUEST = False
	GS.PROCESSING_QUEUE_LEN = len(GS.PROCESSING_QUEUE)
	for n in range(GS.PROCESSING_QUEUE_LEN):
		if GS.CANCEL_REQUEST:
			GS.CANCEL_REQUEST = False
			wipe_queue()
			print('Task queue cancelled')
			return
		if skip > 0:
			GS.SKIPPED_TASKS += 1
			print(f'Skipping task {GS.SKIPPED_TASKS}| There are {GS.PROCESSING_QUEUE_LEN} tasks left')
			GS.SKIPPED_IMAGES += GS.PROCESSING_QUEUE.popleft()["meta"]["number_of_imgs"]
			skip -= 1
		else:
			if end:
				if GS.FINISHED_TASKS + GS.SKIPPED_TASKS == end:
					print('Requested end of queue reached, finishing up')
					return
			result = process_task(GS.PROCESSING_QUEUE.popleft())
			if result == 'Error':
				wipe_queue()
				print('Critical fault detected, task queue wiped')
				return
	print('Task queue processed')
	wipe_queue()

# 13. Called by process_queue. Cancels processing if requested, otherwise calls the according function to process the next task
@handle_exceptions
def process_task(settings):
	if GS.CANCEL_REQUEST:
		return
	if settings["meta"]["processing_type"]=='cluster_collage':
		result = cluster_collage_processor(settings)
	elif settings["meta"]["processing_type"]=='image_sequence':
		result = image_sequence_processor(settings)
	elif settings["meta"]["processing_type"]=='cluster_sequence':
		result = cluster_sequence_processor(settings)
	return result

# 14. Empties the queue and resets counters to 0
@handle_exceptions
def wipe_queue(instance=None):
	GS.PROCESSING_QUEUE.clear()
	GS.SKIPPED_TASKS=0
	GS.FINISHED_TASKS=0
	GS.PRODUCED_IMAGES=0
	GS.SKIPPED_IMAGES=0
	GS.QUEUED_IMAGES=0
	print('Task queue wiped')