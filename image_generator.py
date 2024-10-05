"""
image_generator.py
	This module is responsible for the actual image (and video) generation

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
06.	attach_metadata_header + process_entry_to_subimage + create_image_stripe
			Takes an almost finished cluster collage and puts the metadata header on it, and saves it
			process_entry_to_subimage and create_image_stripe are used when attaching image thumbnails to the collage for i2i/VT
07.	generate_as_is
			Takes in the provided settings and then generates a single image from them
08.	cluster_collage + cluster_collage_processor
			Creates and queues a task to create a cluster collage, which can then later be finished by the according processor function
09.	image_sequence + image_sequence_processor
			Same as above, just for image sequences
10.	cluster_sequence + cluster_sequence_processor
			Same as above, just for cluster sequences which is a combination of the two types of tasks above
11.	steps_guidance_pre_processor
			This function is responsible for taking non-f user input and turning it into lists of the actual scales/steps to render
12.	f_variables_processor
			A big function used to gather up the F-string processing in one place
13.	process_queue
			This is the main loop to process all tasks in the queue
14.	process_task
			A simple function called per task that calls the correct processor to perform it
15.	wipe_queue
			Does what it says, wipes the queue and resets some relevant settings
"""

from initialization import handle_exceptions, GlobalState
GS = GlobalState()
import text_manipulation as TM
import kivy_widgets as KW
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

from kivy.clock import Clock

from pympler.tracker import SummaryTracker
GS.tracker = SummaryTracker()

# ---Primary Functions---



# 2. The primary function to generate images. Sends the request and will persist until it is fulfilled, then saves the image, and returns the path
# Currently NAI specific
@handle_exceptions
def image_gen(auth,prompt,filepath,enumerator,token_test=False):
	skipped = False
	retry_time=5
	while GS.generate_images or token_test:
		while not GS.MAIN_APP.pause_button.enabled:
			time.sleep(0.2)
		if GS.cancel_request:
			print('Image generation cancelled')
			return
		api_header=f'Bearer {auth}'
		if not GS.overwrite_images and not token_test:
			if os.path.isfile(filepath):
				print(f'[Warning] {filepath} is already present and has not been overwritten')
				skipped = True
				break
		response = None
		try:
			if True:
				print(f'''{enumerator}\nDecrisp: {prompt[0]["parameters"]["dynamic_thresholding"]}{" | MS: " + str(prompt[0]["parameters"]["dynamic_thresholding_mimic_scale"]) + " | " + str(prompt[0]["parameters"]["dynamic_thresholding_percentile"]) + "%ile" if prompt[0]["parameters"]["dynamic_thresholding"] else ""}''')
				print(f'''Model: {prompt[0]["model"]}\nPrompt:\n{prompt[0]["input"]}\nUC:\n{prompt[0]["parameters"]["negative_prompt"]}''')

			start=time.time()
			response=requests.post(GS.URL,json.dumps(prompt[0]),headers={'Authorization': api_header,'Content-Type': 'application/json','accept': 'application/json',})
			end=time.time()
			processing_time=end-start
			print(f'Response Time: {(processing_time)}s')
			if token_test:
				if response.status_code == 200:
					return 'Success'
				else:
					return 'Error' # Passed to the testing function and reported there
			
			
			if response.status_code == 400 or response.status_code == 401:
				print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
				return 'Error' # Reported above
			elif response.status_code == 429:
				print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
				raise ValueError('Server refused to respond with an image due to specific circumstances.')
			elif response.status_code >= 402 and response.status_code < 500:
				print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
				return 'Error' # Reported above
			elif response.status_code >= 500:
				print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
				raise ValueError('Server failed to respond with an image.')

			with zipfile.ZipFile(io.BytesIO(response.content), "r") as zip_file:
				for file_name in zip_file.namelist():
					if file_name.endswith(".png"):
						with zip_file.open(file_name) as png_file:
							image_data = png_file.read()
							Clock.schedule_once(lambda dt: GS.MAIN_APP.generated_images_dropdown.add_widget(
							KW.ImageGenerationEntry(image_data, GS.MAIN_APP.show_last_generation_button.enabled, True)))
							with open(filepath, 'wb+') as t:
								t.write(image_data)
							t.close()
			break
		except:
			traceback.print_exc() if GS.verbose else None
			if token_test:
				return 'Error' # Passed to the testing function and reported there
			if response == None:
				print(f'[Warning] Failed to get any server response')
			elif response.status_code >= 500:
				try:
					print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
				except:
					print(f'[Warning] {response.status_code} | No proper server message received')
			else:
				None if GS.verbose else traceback.print_exc()
			print(f'[Warning] Creation error encounted. Retrying after: {min(retry_time,15)}s')
			for i in range(min(retry_time,15)):
				time.sleep(1)
				if GS.cancel_request: break
			retry_time+=5
			continue
		time.sleep(float(GS.MAIN_APP.wait_time_input.text)) # Waiting for the specified amount to avoid getting limited or frying the GPU etc

	if not skipped and GS.generate_images:
		GS.produced_images += 1
	else:
		GS.skipped_images += 1
	GS.pre_last_seed = GS.last_seed
	GS.last_seed = str(prompt[0]['parameters']['seed'])
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
	writer = imageio.get_writer(full_vid_folder_path+extension, mode='I', format='ffmpeg', quality=10, **vid_params)
	#print(vid_params['fps'])
	# Determine frame size from the first completed image future
	first_img_future_or_str = img_futures.get()
	expecting_strs = False # IS will return paths while CS will return the cluster collages directly, so we need to check for what we're working with
	if type(first_img_future_or_str) == str:
		first_img = Image.open(first_img_future_or_str)
		expecting_strs = True
	elif first_img_future_or_str:
		first_img = first_img_future_or_str.result()
	else:
		print('Video processing cancelled')
		return
	h, w, _ = np.array(first_img).shape
	frameSize = (w, h)
	
	# Write first frame to video
	writer.append_data(np.array(first_img))
	del first_img # The images must be deleted manually from memory here and in the loop after usage, lest they persist in the RAM

	# Write remaining frames to video
	for _ in range(num_frames - 1):
		img = img_futures.get()
		if GS.cancel_request:
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

@handle_exceptions
def make_vid_ffmpeg(vid_params, vid_path, img_futures, num_frames):

	# Build FFmpeg command
	ffmpeg_cmd = ['ffmpeg', '-y'] 
	
	ffmpeg_cmd.extend(['-framerate', vid_params['fps']])  
	ffmpeg_cmd.extend(['-i', 'pipe:'])
	
	ffmpeg_cmd.extend(['-vcodec', vid_params['codec'], '-qscale:v', '3'])
	ffmpeg_cmd.extend([vid_path])

	# Start pipe 
	p = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

	# Handle first frame
	first_img = handle_img(img_futures.get())
	
	# Encode first frame 
	buffer = BytesIO() 
	first_img.save(buffer, format="PNG")
	frame = buffer.getvalue()   
	p.stdin.write(frame)

	# Cleanup first frame
	buffer.close()
	del first_img

	# Write remainder frames
	for _ in range(num_frames - 1):
		
		img = handle_img(img_futures.get())
		
		buffer = BytesIO()
		img.save(buffer, format="PNG")
		
		p.stdin.write(buffer.getvalue())  
		
		buffer.close()
		del img
		
	# Finalize FFmpeg  
	p.stdin.close()
	p.wait()

	print_status(vid_path)
	
	
# Helper handles both future and string paths from queue   
def handle_img(img):
	if isinstance(img, str):
		return Image.open(img)  
	else:
		return img.result()
		
def print_status(vid_path):
	if os.path.exists(vid_path):
		print("Video created")
	else: 
		print("[Warning] Video creation failed")

# 5. Takes in a list of images and turns them into a collage
@handle_exceptions
def make_collage(imgs,name,row_length=5,name_extra="",passed_image_mode=False,folder_name='',pass_image=False):
	row=[]
	rows=[]
	n=0
	multirow=False
	for img in imgs:
		if passed_image_mode==False:
			with Image.open(img) as img:
				img_copy = img.copy()
				row.append(np.array(img_copy))
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
	draw.text((10,line_height*1),f'Creator: {GS.MAIN_APP.config_window.creator_name_input.text}',font=font,fill=(200,200,255,0))
	# Name, using the FFW to make symbols available
	draw, img_header, used_lines_name, _=TM.fallback_font_writer(draw, img_header, f'Name: {settings["name"]}', 10, line_height*2, left_meta_block, 1, line_height, (255,255,255,0))
	if settings["model"] == 'safe-diffusion':
		model = 'NovelAI Diffusion Curated V1.0.1'
	elif settings["model"] == 'nai-diffusion':
		model = 'NovelAI Diffusion Full V1.0.1'
	elif settings["model"] == 'nai-diffusion-2':
		model = 'NovelAI Diffusion Full V2'
	elif settings["model"] == 'nai-diffusion-3':
		model = 'NovelAI Diffusion Full V3'
	elif settings["model"] == 'nai-diffusion-furry-3':
		model = 'NovelAI Diffusion Furry V3'
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
	if (isinstance(steps, str) and "⁅" in steps) or type(steps) != list:
		steps_string = 'Steps: ' + str(steps)
	elif len(settings["meta"]["steps"]) > 1:
		steps_string = 'Steps: ' + str(settings["meta"]["steps"][0]) + '→' + str(settings["meta"]["steps"][-1])
	else:
		steps_string = 'Steps: ' + str(settings["meta"]["steps"][0])
	draw, img_header, used_lines_steps, _=TM.fallback_font_writer(draw, img_header, steps_string, 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = '|')
	currently_used_lines=currently_used_lines+used_lines_steps

	# Guidance, using the FFW to linebreak at |
	available_lines = available_lines - used_lines_steps
	scale = settings["scale"]
	if (isinstance(scale, str) and "⁅" in scale) or type(scale) != list:
		guidance_string = 'Scale: ' + str(scale)
	elif len(settings["meta"]["scale"]) > 1:
		guidance_string = 'Scale: ' + str(settings["meta"]["scale"][0]) + '→' + str(settings["meta"]["scale"][-1])
	else:
		guidance_string = 'Scale: ' + str(settings["meta"]["scale"][0])
	draw, img_header, used_lines_scale, _=TM.fallback_font_writer(draw, img_header, guidance_string, 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = '|')
	currently_used_lines=currently_used_lines+used_lines_scale

	# The sampler string has been migrated to the same place the seed is on, the individual clusters

	# Decrisper
	decrisper_string = 'Decrisper: '
	if settings["dynamic_thresholding"] == False:
		decrisper_string += 'Off'
	else:
		decrisper_string += f'On | M. Scale: {settings["dynamic_thresholding_mimic_scale"]} | {settings["dynamic_thresholding_percentile"]}%ile'
	available_lines = available_lines - used_lines_scale
	draw, img_header, used_lines_decrisper, _=TM.fallback_font_writer(draw, img_header, decrisper_string, 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = '|')
	currently_used_lines=currently_used_lines+used_lines_decrisper

	# Undesired Content Strength
	available_lines = available_lines - used_lines_decrisper
	draw, img_header, used_lines_ucs, _=TM.fallback_font_writer(draw, img_header, 'Undesired Content Strength: '+settings["negative_prompt_strength"]+'%', 10,
		line_height*currently_used_lines, left_meta_block, available_lines, line_height, (255,255,255,0), break_symbol = ',')
	currently_used_lines=currently_used_lines+used_lines_ucs

	#Draw the prompt and UC on the right side
	full_prompt=settings["prompt"]
	draw, img_header, used_lines_prompt, _=TM.fallback_font_writer(draw, img_header, full_prompt, left_meta_block, line_height*0, img_collages.size[0]-left_meta_block,
		currently_used_lines, line_height, (180,255,180,0), explicit_space = True)
	currently_used_lines=max(currently_used_lines,used_lines_prompt)
	available_lines = currently_used_lines-used_lines_prompt

	full_UC=settings["negative_prompt"]
	time.sleep(10)
	draw, img_header, used_lines_uc, _=TM.fallback_font_writer(draw, img_header, full_UC, left_meta_block, line_height*(used_lines_prompt),
		img_collages.size[0]-left_meta_block, available_lines, line_height, (255,180,180,0), explicit_space = True)

	# Process entries into subimages
	if settings.get('image_entries'):
		subimages = [process_entry_to_subimage(entry, line_height) for entry in settings["image_entries"]]
		image_stripe = create_image_stripe(subimages, img_collages.width, line_height)
		image_stripe_height = image_stripe.height
	else:
		image_stripe_height = 0	

	# Combine header, stripe, and collage
	full_img = Image.new('RGB', (img_collages.width, img_header.height + image_stripe_height + img_collages.height))
	full_img.paste(img_header, (0, 0))
	if settings.get('image_entries'):
		full_img.paste(image_stripe, (0, img_header.height))
	full_img.paste(img_collages, (0, img_header.height + image_stripe_height))

	if settings.get('folder_name_user'):
		settings["folder_name_extra"] = settings["folder_name_user"]+f'/{settings["name"]}'
		path = f'__0utput__/{TM.replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages{settings["folder_name_user"]}/'
		os.makedirs(path, exist_ok=True)
		final_path = f'{path}{TM.replace_forbidden_symbols(settings["name"])}_Collage({TM.replace_forbidden_symbols(name_extra)}).jpg'
	else:
		path = f'__0utput__/{TM.replace_forbidden_symbols(settings["folder_name"])}/#ClusterCollages/'
		os.makedirs(path, exist_ok=True)
		final_path = path + f'{TM.replace_forbidden_symbols(settings["name"])}_Collage({TM.replace_forbidden_symbols(name_extra)}).jpg'
	full_img.save(final_path, quality=90)
	print("Cluster collage created")
	if cc=='':
		full_img = None
	return full_img

@handle_exceptions
def process_entry_to_subimage(entry, line_height):
	# Initial setup
	subimage_height = line_height * 7  # 6 lines of text + 1 line buffer
	thumb_size = line_height * 6
	text_color = (255, 255, 255, 0)

	# Process thumbnail
	thumb = Image.open(io.BytesIO(entry["entry_reference"].raw_image_data))
	aspect_ratio = thumb.width / thumb.height
	if aspect_ratio >= 1:  # Width >= Height
		thumb_width = thumb_size
		thumb_height = int(thumb_width / aspect_ratio)
	else:  # Height > Width
		thumb_height = thumb_size
		thumb_width = int(thumb_height * aspect_ratio)
	thumb = thumb.resize((thumb_width, thumb_height), Image.LANCZOS)

	# Create initial subimage (will resize later)
	subimage = Image.new("RGB", (2000, subimage_height), (30, 30, 30))
	draw = ImageDraw.Draw(subimage)

	# Paste thumbnail
	subimage.paste(thumb, (5, 5))

	# Write text
	y_offset = 5
	max_line_width = 0

	def write_line(text, y):
		nonlocal draw, subimage, line_height, text_color, max_line_width
		truncated_text = text[:120]
		draw, subimage, _, line_width = TM.fallback_font_writer(draw, subimage, truncated_text, thumb_size + 10, y, 2000, 1, line_height, text_color)
		max_line_width = max(line_width, max_line_width)
		return y + line_height

	if "i2i" in entry and "vt" in entry:
		y_offset = write_line("I2I Cond: " + entry["i2i"]["condition"], y_offset)
		y_offset = write_line("I2I Str: " + entry["i2i"]["strength"], y_offset)
		y_offset = write_line("I2I Noise: " + entry["i2i"]["noise"], y_offset)
		y_offset = write_line("VT Cond: " + entry["vt"]["condition"], y_offset)
		y_offset = write_line("VT Str: " + entry["vt"]["strength"], y_offset)
		y_offset = write_line("VT Info: " + entry["vt"]["information"], y_offset)
	elif "i2i" in entry:
		y_offset = write_line("I2I Cond.:", y_offset)
		y_offset = write_line(entry["i2i"]["condition"], y_offset)
		y_offset = write_line("Str.:", y_offset)
		y_offset = write_line(entry["i2i"]["strength"], y_offset)
		y_offset = write_line("Noise:", y_offset)
		y_offset = write_line(entry["i2i"]["noise"], y_offset)
	elif "vt" in entry:
		y_offset = write_line("VT Cond.:", y_offset)
		y_offset = write_line(entry["vt"]["condition"], y_offset)
		y_offset = write_line("Str.:", y_offset)
		y_offset = write_line(entry["vt"]["strength"], y_offset)
		y_offset = write_line("Info.:", y_offset)
		y_offset = write_line(entry["vt"]["information"], y_offset)

	# Resize subimage to fit text
	final_width = max(thumb_size + 10, thumb_size + 15 + max_line_width)
	final_subimage = Image.new("RGB", (final_width, subimage_height), (30, 30, 30))
	final_subimage.paste(subimage, (0, 0))

	del thumb
	return final_subimage

@handle_exceptions
def create_image_stripe(subimages, stripe_width, line_height):
	if not subimages:
		return Image.new("RGB", (stripe_width, line_height), (30, 30, 30))

	stripe_height = subimages[0].height
	stripe = Image.new("RGB", (stripe_width, stripe_height), (30, 30, 30))

	x_offset = 0
	remaining_subimages = []

	for subimage in subimages:
		if x_offset + subimage.width <= stripe_width:
			stripe.paste(subimage, (x_offset, 0))
			x_offset += subimage.width
		else:
			remaining_subimages.append(subimage)

	if remaining_subimages:
		next_stripe = create_image_stripe(remaining_subimages, stripe_width, line_height)
		combined_stripe = Image.new("RGB", (stripe_width, stripe_height + next_stripe.height), (30, 30, 30))
		combined_stripe.paste(stripe, (0, 0))
		combined_stripe.paste(next_stripe, (0, stripe_height))
		return combined_stripe

	return stripe

# ---Rendering Functions---

# 7. Simply formats and passes the prompt to image_gen, used for simple generations, complex external logic or an auth token test
@handle_exceptions
def generate_as_is(settings,enumerator,token_test=False,token=''):
	if token_test: #This is the raw testing dict used when evaluating whether a NAI user token us usable or not
		settings = {'name': 'Test', 'folder_name': '', 'folder_name_extra': '', 'model': 'nai-diffusion-2', 'seed': 0, 'sampler': 'k_euler_ancestral', 'noise_schedule': 'native', 'scale': 10.0,
			'steps': 1, 'img_mode': {'width': 64, 'height': 64}, 'prompt': 'Test', 'negative_prompt': 'Test', 'smea': False, 'dyn': False, 'dynamic_thresholding': False,
			'dynamic_thresholding_mimic_scale': 10, 'dynamic_thresholding_percentile': 0.999, 'guidance_rescale': 0, 'negative_prompt_strength': 1}
		GS.MAIN_APP.config_window.process_token_callback(image_gen(token,module_factory.providers[GS.MAIN_APP.generation_provider_button.text].form_prompt(settings),'','',token_test=True), token)
		return
	prompt=module_factory.providers[GS.MAIN_APP.generation_provider_button.text].form_prompt(settings)
	filepath=TM.make_file_path(prompt,enumerator,settings["folder_name"],settings["folder_name_extra"])
	if GS.verbose:
		GS.last_fully_formed_prompt = prompt
	return image_gen(GS.AUTH,prompt,filepath,enumerator)

def decode_sampler_string(string, cluster_string = False):
	sampler_settings={}
	if string.endswith('_dyn'):
		sampler_settings["smea"] = True
		sampler_settings["dyn"] = True
		sampler_settings["sampler"] = string[:-4]
		if cluster_string:
			sd_string = 'SMEA+Dyn, '
	elif string.endswith('_smea'):
		sampler_settings["smea"] = True
		sampler_settings["dyn"] = False
		sampler_settings["sampler"] = string[:-5]
		if cluster_string:
			sd_string = 'SMEA, '
	else:
		sampler_settings["smea"] = False
		sampler_settings["dyn"] = False
		sampler_settings["sampler"] = string
		if cluster_string:
			sd_string = ''

	for noise_schedule in GS.NAI_NOISE_SCHEDULERS:
		if sampler_settings["sampler"].endswith('_' + noise_schedule):
			sampler_settings["sampler"] = sampler_settings["sampler"][:-len(noise_schedule)-1]
			if noise_schedule == 'default':
				sampler_settings["noise_schedule"] = GS.NAI_DEFAULT_NOISE_SCHEDULERS[sampler_settings["sampler"]]
			else:
				sampler_settings["noise_schedule"] = noise_schedule
			break
	if not sampler_settings.get('noise_schedule'):
		print('[Warning] Failed to determine noise schedule, attempting to fall back to default')
		sampler_settings["noise_schedule"] = GS.NAI_DEFAULT_NOISE_SCHEDULERS[sampler_settings["sampler"]]
	
	if cluster_string:
		matching_dict = next((d for d in GS.NAI_SAMPLERS if d['string'].strip(', ') == sampler_settings["sampler"]), None)
		if matching_dict:
			sampler_string = matching_dict['name']
		else:
			sampler_string = sampler_settings["sampler"]
		sampler_settings["sampler_string"] = f'{sampler_string} ({sd_string}{sampler_settings["noise_schedule"].capitalize()})'
	return sampler_settings

# 8. Takes a prompt and renders it across multiple seeds at multiple scales, then puts all generations into a cluster collage together with the metadata
# Does some pre-processing to form a task for a cluster collage, then adds it to the GS.processing_queue which will be processed with cluster_collage_processor
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
	GS.queued_images+=settings["meta"]["number_of_imgs"]

	settings["meta"]["processing_type"]='cluster_collage'
	if eval_guard:
		settings["meta"]["eval_guard"]=True
	else:
		settings["meta"]["eval_guard"]=False
	

	#Saving settings and configuring folder structure
	#conf_settings=copy.deepcopy(settings)
	conf_settings = {key: value for key, value in settings.items()}
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
	GS.processing_queue.append(settings)

# Called by process_task to generate a cluster collage from the settings
@handle_exceptions
def cluster_collage_processor(settings, cc='', cs_rendered_imgs=1):
	cc_enumerator = '' if cc == '' else f'(cc꞉{cc})'
	rendered_imgs = 1
	
	#img_settings=copy.deepcopy(settings)
	img_settings = {key: value for key, value in settings.items()}
	#Configures steps and scale lists
	steps_guidance_pre_processor(settings)

	#Configure the folder structure if the user specified something extra
	if img_settings.get('folder_name_user'):
		img_settings["folder_name_extra"]=img_settings["folder_name_user"]+f'/{TM.replace_forbidden_symbols(img_settings["name"])}'
	else:
		img_settings["folder_name_extra"]=f'/{TM.replace_forbidden_symbols(img_settings["name"])}'
	
	#This loop makes the initial collages
	color=np.array([30,30,30])
	if type(settings["sampler"]) != list:
		settings["sampler"]=[[settings["sampler"]], 0]
		single_sampler=True
	final_collages=[]
	for sampler in settings["sampler"][0]:
		img_settings.update(decode_sampler_string(sampler, True))
		sampler_collage_blocks=[]
		for seed_sub_list in settings["seed"]:
			collage_rows=[]
			for s, seed in enumerate(seed_sub_list):
				imgs=[]
				n=0
				for r in range(settings["collage_dimensions"][1]):
					for c in range(settings["collage_dimensions"][0]):
						if GS.cancel_request:
							return
						#Load in the correct values for steps, scale and seed
						img_settings["seed"]=seed
						if f_variables_processor(settings, img_settings, {'n':n,'c':c,'r':r,'cc':cc,'s':s}) == 'Error':
							return 'Error' # Reported in called function
						#Report the current queue position before rendering
						if time.time() - GS.last_task_report >= 1.0: # Limit reports to once a second to prevent swamping the console
							#GS.last_task_report = time.time()
							print(f'Processing task: {GS.finished_tasks+1+GS.skipped_tasks}/{GS.queued_tasks}')
							if cc != None: print(f'Rendering img (current cluster collage): {rendered_imgs}/{settings["meta"]["imgs_per_collage"]}')
							if cc != None: print(f'Rendering img (current CS task): {cs_rendered_imgs}/{settings["meta"]["number_of_imgs"]}')
							if cc == None: print(f'Rendering img (current CC task): {rendered_imgs}/{settings["meta"]["number_of_imgs"]}')
							print(f'Rendering img (complete queue): {GS.produced_images+1+GS.skipped_images}/{GS.queued_images}')
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
				collage_metadata=f'{seed} | {img_settings["sampler_string"]}'
				draw.text((10,-5),collage_metadata,font=font,fill=(255,255,255,0))
				color+=[5,5,5]
				collage_rows.append(bordered_collage)
			sampler_collage_blocks.append(make_collage(collage_rows,settings["name"],row_length=len(settings["seed"][0]),passed_image_mode=True,pass_image=True))
		# Implementing sampler dimensions later happens in row_length here
		final_collages.append(make_collage(sampler_collage_blocks,settings["name"],row_length=1,passed_image_mode=True,pass_image=True))
	if 'single_sampler' in locals():
		cluster_collage=make_collage(final_collages,settings["name"],row_length=len(settings["seed"]),passed_image_mode=True,folder_name=settings["folder_name"],pass_image=True)
	else:
		if settings["sampler"][1] == 'vertical':
			row_cutoff=1
		elif type(settings["sampler"][1]) == int:
			row_cutoff=settings["sampler"][1]
		else:
			row_cutoff=10000
		cluster_collage=make_collage(final_collages,settings["name"],row_length=row_cutoff,passed_image_mode=True,folder_name=settings["folder_name"],pass_image=True)
	future = GS.EXECUTOR.submit(attach_metadata_header, cluster_collage, settings, f'Cluster{cc_enumerator}[{img_settings["sampler"]}]',f' - cc: {cc}' if cc!='' else '')
	if cc==None: GS.finished_tasks+=1
	return future

# 9. Does some pre-processing to form a task for an image sequence, then adds it to the GS.processing_queue which will be processed with image_sequence_processor
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
	GS.queued_images+=settings["meta"]["number_of_imgs"]
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
	GS.processing_queue.append(settings)

# Called by process_task to generate an image sequence from the settings
@handle_exceptions
def image_sequence_processor(settings):
	imgs=[]
	#img_settings=copy.deepcopy(settings)
	img_settings = {key: value for key, value in settings.items()}

	steps_guidance_pre_processor(settings)

	img_settings["folder_name_extra"]=''
	rendered_imgs=1
	
	### To be replaced later
	vid_params = {
		'fps': settings["FPS"],
		'codec': 'vp9',
		'pixelformat': 'yuv444p',
	}
	
	#If video generation is requested, start the according thread before the image generation loop which will use the img_results queue
	vid = False
	img_results = Queue()
	if settings["video"] == 'standard':
		vid = True
		img_results = Queue()
		GS.EXECUTOR.submit(make_vid, vid_params, settings["meta"]["vid_folder"], img_results, settings["quantity"])

	for n in range(settings["quantity"]):
		img_settings.update(decode_sampler_string(settings["sampler"]))
		if GS.cancel_request:
			return
		if f_variables_processor(settings, img_settings, {'n':n}) == 'Error':
			return 'Error' # Reported in called function
		enumerator=f'''({img_settings["seed"]})(#{str((n+1)).rjust(4,'0')})'''
		enumerator+=f'(Scale꞉{img_settings["scale"]})(Steps꞉{img_settings["steps"]})'
		if time.time() - GS.last_task_report >= 1.0: # Limit reports to once a second to prevent swamping the console
			GS.last_task_report = time.time()
			print(f'Processing task: {GS.finished_tasks+1+GS.skipped_tasks}/{GS.queued_tasks}')
			print(f'Rendering img (current IS task): {rendered_imgs}/{settings["meta"]["number_of_imgs"]}')
			print(f'Rendering img (complete queue): {GS.produced_images+1+GS.skipped_images}/{GS.queued_images}')
		if vid:
			img_results.put(generate_as_is(img_settings,enumerator))
		else:
			generate_as_is(img_settings,enumerator)
		rendered_imgs+=1
	GS.finished_tasks+=1

# 10. Does some pre-processing to form a task for a cluster sequence, then adds it to the GS.processing_queue which will be processed with cluster_sequence_processor
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
	GS.queued_images += settings["meta"]["number_of_imgs"]
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
	GS.processing_queue.append(settings)

# Called by process_task to generate a cluster sequence (a sequence of cluster collages) from the settings
@handle_exceptions
def cluster_sequence_processor(settings):
	### To be replaced later
	vid_params = {
		'fps': settings["FPS"],
		'codec': 'vp9',
		'pixelformat': 'yuv444p',
	}

	# If video generation is requested, start the according thread before the image generation loop which will use the img_results queue
	# Otherwise run cluster_collage_processor making sure that its result gets discarded
	vid = False
	if settings["video"] == 'standard':
		vid = True
		img_results = Queue()
		GS.EXECUTOR.submit(make_vid, vid_params, settings["meta"]["vid_folder"], img_results, settings["quantity"])
	for cc in range(settings["quantity"]):
		if vid:
			img_results.put(cluster_collage_processor(settings, cc, 1+cc*settings["meta"]["imgs_per_collage"]))
		else:
			cluster_collage_processor(settings, cc, 1+cc*settings["meta"]["imgs_per_collage"])
	GS.finished_tasks+=1

# ---Rendering pre-processing functions---

# 11. This function handles the pre-processing of steps and scale, it takes the settings from the user input and makes it computible per image
@handle_exceptions
def steps_guidance_pre_processor(settings):
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
	else:
		settings["meta"]["steps"] = settings["steps"]

	if type(settings["scale"])==list and quantity != 1:
		settings["meta"]["scale"] = [round(x,6) for x in np.linspace(settings["scale"][0], settings["scale"][-1], quantity).tolist()]
	elif not type(settings["scale"]) == str:
		if any(isinstance(settings["scale"], type) for type in [int, float]):
			settings["meta"]["scale"]=[settings["scale"]]
		else:
			settings["meta"]["scale"]=[settings["scale"][0]]
	else:
		settings["meta"]["scale"] = settings["scale"]

# 12. This function makes sure to process f-strings from other simpler fields
# The var dict uses variables with only 1 or 2 letters as these are the variables the user can and should directly use in their written conditions
@handle_exceptions
def f_variables_processor(settings, img_settings, var_dict):
	for key, func1, func2 in [("steps", int, int), ("scale", float, handle_exceptions(lambda x: round(x, 6))), ("guidance_rescale", float, handle_exceptions(lambda x: round(x, 6)))]:
		value = settings[key]
		if isinstance(value, str):
			img_settings[key] = func2(func1(TM.f_string_processor([str(value)], settings["meta"]["eval_guard"], var_dict)))
		elif not settings["meta"].get(key):
			img_settings[key] = func2(func1(value))
		else:
			img_settings[key] = (settings["meta"][key][0] if len(settings["meta"][key]) == 1 else func2(settings["meta"][key][var_dict['n']]))
	#if img_settings["dynamic_thresholding"]:
	#	img_settings["dynamic_thresholding_mimic_scale"] = float(TM.f_string_processor([str(settings["dynamic_thresholding_mimic_scale"])],settings["meta"]["eval_guard"],var_dict))
	#	img_settings["dynamic_thresholding_percentile"] = float(TM.f_string_processor([str(settings["dynamic_thresholding_percentile"])],settings["meta"]["eval_guard"],var_dict))
	#else: # Without this there might be trouble if settings without specifications for dynamic thresholding are passed
	#	img_settings["dynamic_thresholding_mimic_scale"] = 10
	#	img_settings["dynamic_thresholding_percentile"] = 0.999
	img_settings["negative_prompt_strength"] = float(TM.f_string_processor([str(settings["negative_prompt_strength"])],settings["meta"]["eval_guard"],var_dict))
	for prompt_type in ["prompt", "negative_prompt"]:
		if type(settings[prompt_type]) != str:
			img_settings[prompt_type] = TM.f_string_processor(settings[prompt_type], settings["meta"]["eval_guard"], var_dict)
			if img_settings[prompt_type] == 'Error':
				return 'Error' # Reported in called function

	if settings.get('image_entries'):
		img_settings["img2img"] = None
		img_settings["vibe_transfer"] = []

		for entry_data in settings["image_entries"]:
			entry = entry_data["entry_reference"]
			
			# Process img2img
			if "i2i" in entry_data:
				print(entry_data["i2i"])
				i2i_condition = TM.f_string_processor([entry_data["i2i"]["condition"]], settings["meta"]["eval_guard"], var_dict)
				if i2i_condition not in ['True', 'False']:
					print(f'[Warning] Malformed image2image condition string encountered: {entry_data["i2i"]["condition"]}')
					return 'Error' # Reported above
				
				if i2i_condition == 'True':
					if img_settings["img2img"] is not None:
						print(f'[Warning] Multiple image2image conditions evaluated to True: {entry_data["i2i"]["condition"]} | {img_settings["meta"]["last_true_i2i"]}')
						return 'Error' # Reported above
					
					img_settings["img2img"] = {
						'image': base64.b64encode(entry.raw_image_data).decode('utf-8'),
						'extra_noise_seed': int(img_settings["seed"]),
						'strength': float(TM.f_string_processor([entry_data["i2i"]["strength"]], settings["meta"]["eval_guard"], var_dict)),
						'noise': float(TM.f_string_processor([entry_data["i2i"]["noise"]], settings["meta"]["eval_guard"], var_dict)),
					}
					img_settings["meta"]["last_true_i2i"] = entry_data["i2i"]["condition"]
			
			# Process vibe transfer
			if "vt" in entry_data:
				vt_condition = TM.f_string_processor([entry_data["vt"]["condition"]], settings["meta"]["eval_guard"], var_dict)
				if vt_condition not in ['True', 'False']:
					print(f'[Warning] Malformed vibe transfer condition string encountered: {entry_data["vt"]["condition"]}')
					return 'Error' # Reported above
				
				if vt_condition == 'True':
					print(len(img_settings["vibe_transfer"]))
					if len(img_settings["vibe_transfer"]) > 15:
						print(f'[Warning] More than 16 VT conditions evaluated to True.')
						return 'Error' # Reported above
					img_settings["vibe_transfer"].append({
						'image': base64.b64encode(entry.raw_image_data).decode('utf-8'),
						'strength': float(TM.f_string_processor([entry_data["vt"]["strength"]], settings["meta"]["eval_guard"], var_dict)),
						'information_extracted': float(TM.f_string_processor([entry_data["vt"]["information"]], settings["meta"]["eval_guard"], var_dict)),
					})
	return None  # Explicit return of None if no errors occurred

# ---Task processing functions---

# 13. This is the primary loop for iterating over the processing queue, which will either cancel and wipe if requested, skip if requested, or process the next task in the queue
@handle_exceptions
def process_queue():
	GS.cancel_request = False
	GS.queued_tasks = len(GS.processing_queue)
	for n in range(GS.queued_tasks):
		if GS.cancel_request:
			GS.cancel_request = False
			wipe_queue()
			print('Task queue cancelled')
			return
		if GS.skip > 0:
			GS.skipped_tasks += 1
			print(f'Skipping task {GS.skipped_tasks}| There are {GS.queued_tasks} tasks left')
			GS.skipped_images += GS.processing_queue.popleft()["meta"]["number_of_imgs"]
			GS.skip -= 1
		else:
			if GS.end:
				print('Requested end of queue reached, finishing up')
				return
			result = process_task(GS.processing_queue.popleft())
			if result == 'Error':
				wipe_queue()
				print('[Warning] Critical fault during queue processing detected, task queue wiped')
				return
	print('Task queue processed')
	wipe_queue()

# 14. Called by process_queue. Cancels processing if requested, otherwise calls the according function to process the next task
@handle_exceptions
def process_task(settings):
	if GS.cancel_request:
		return
	if settings["meta"]["processing_type"]=='cluster_collage':
		result = cluster_collage_processor(settings)
	elif settings["meta"]["processing_type"]=='image_sequence':
		result = image_sequence_processor(settings)
	elif settings["meta"]["processing_type"]=='cluster_sequence':
		result = cluster_sequence_processor(settings)
	return result

# 15. Empties the queue and resets counters to 0
@handle_exceptions
def wipe_queue(instance=None):
	GS.processing_queue.clear()
	GS.queued_tasks = 0
	GS.skipped_tasks = 0
	GS.finished_tasks = 0
	GS.produced_images = 0
	GS.skipped_images = 0
	GS.queued_images = 0
	for entry in GS.MAIN_APP.loaded_images_dropdown.children[0].children:
		entry.destructible = True
	GS.MAIN_APP.pause_button.enabled = True
	print('Task queue wiped')

import importlib
import inspect
class ModuleFactory:
	def __init__(self, provider_folder=GS.FULL_DIR + '/GenerationProviders'):
		self.provider_folder = provider_folder
		self.load_providers()

	def load_providers(self):
		self.providers = {}
		for filename in os.listdir(self.provider_folder):
			if filename.endswith(".py"):
				provider_name = filename[:-3]
				module_path = os.path.join(self.provider_folder, filename)
				
				spec = importlib.util.spec_from_file_location(provider_name, module_path)
				module = importlib.util.module_from_spec(spec)
				spec.loader.exec_module(module)
				
				# Look for a class that ends with 'Provider' in the module
				provider_class = None
				for name, obj in inspect.getmembers(module):
					if inspect.isclass(obj) and name.endswith('Provider'):
						provider_class = obj
						break
				
				if provider_class:
					self.providers[provider_name] = provider_class()
				else:
					print(f"Warning: No Provider class found in {filename}")

	def get_provider(self, name):
		return self.providers.get(name)

	def list_providers(self):
		return list(self.providers.keys())
module_factory = ModuleFactory()