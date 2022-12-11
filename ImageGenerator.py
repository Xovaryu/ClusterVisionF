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
from PIL import ImageFont, ImageDraw, Image

if not os.path.exists("NAID_User_Config.py"):
	f1=open("NAID_Config_Template.py","r")
	f2=open("NAID_User_Config.py","w",encoding="utf-8")
	f2.write(f1.read())
	f1.close()
	f2.close()
	print("Configuration file copied. Please set your auth token up.")
	time.sleep(7)
	exit()
else:
	from NAID_User_Config import *
from NAID_Constants import *

#Variables for the debriefing
PRODUCED_IMAGES=0
WAITS_SHORT=0
WAITS_LONG=0

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

#The primary function to generate images. Sends the request and will persist until it is fulfilled, then saves the image, and returns the path
#only_gen_path is a debugging variable and will return only the paths if set to True to avoid repetitive generations
def image_gen(auth,prompt,enumerator,folder_name,only_gen_path=False):
	print(f'\n{enumerator}\nPrompt:\n{prompt[0]["input"]}\nUC:\n{prompt[0]["parameters"]["uc"]}')
	global PRODUCED_IMAGES,WAITS_SHORT,WAITS_LONG
	api_header=f'Bearer {auth["auth_token"]}'
	wait_time=5
	prompt[1]=replace_forbidden_symbols(prompt[1])
	enumerator=replace_forbidden_symbols(enumerator)
	folder_name=replace_forbidden_symbols(folder_name)
	while not only_gen_path:
		time.sleep(1)#Waiting a tiny bit out of respect and to avoid getting limited
		try:
			start = time.time()
			resp=requests.post(URL,json.dumps(prompt[0]),headers={'Authorization': api_header,
													  'Content-Type': 'application/json',
													  'accept': 'application/json',})
			resp_content = resp.content
			resp_length=len(resp_content)
			if resp_length>1000:
				print(f'Response length: {resp_length}')
			else:
				print(f'Likely fault detected: {resp_content}')
			base64_image = resp_content.splitlines()[2].replace(b"data:", b"")
			decoded = base64.b64decode(base64_image)
			#Check for server load to respect terms. Typical generation times are between 3 and 4 seconds.
			end=time.time()
			processing_time = end-start
			print(f'NAI Server Generation Time:{(processing_time)}s')
			if processing_time>10:
				if processing_time>15:
					print('Server under heavy load (or very weak internet), taking a 2m chill pill')
					WAITS_LONG+=1
					time.sleep(120)
				else:
					print('Server under load, waiting half a minute')
					WAITS_SHORT+=1
					time.sleep(30)
			break
		except:
			print(f'CREATION ERROR ENCOUNTERED. RETRYING AFTER{min(wait_time,90)}s')
			time.sleep(min(wait_time,90))
			print('RETRYING NOW')
			wait_time+=5
			continue
	if folder_name!='':
		temp_filename=f'__0utput__/{folder_name}/{prompt[1]+enumerator}.png'
		if not os.path.exists(f'__0utput__/{folder_name}'): os.makedirs(f'__0utput__/{folder_name}')
	else:
		temp_filename=f'__0utput__/{prompt[1]+enumerator}.png'
	if not only_gen_path:
		with open(temp_filename,'wb+') as t:
			t.write(decoded)
		t.close()
	PRODUCED_IMAGES+=1
	print('File Path:\n'+temp_filename)
	return temp_filename

#Function to generate seeds in the way NAI would
def generate_seed():
    return math.floor(random.random()*(2**32)-1);

###
#Additional Media Functions
###

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
def attach_metadata_header(img,settings,name_extra):
	#Text configuration
	font_size=29
	font_size_offset=font_size+5
	newline_after=70*settings["collage_width"]
	font=ImageFont.truetype('./ebrima.ttf',font_size)
	#PIL
	headered_img=cv2.copyMakeBorder(img,300,0,0,0,cv2.BORDER_CONSTANT,None,value=(int(0),int(0),int(0)))
	img_pil=Image.fromarray(headered_img)
	draw=ImageDraw.Draw(img_pil)
	#Draw the basic metadata
	draw.text((10,-5+font_size_offset*0),f"Xovaryu's Prompt Stabber",font=font,fill=(255,220,255,0))
	draw.text((10,-5+font_size_offset*1),f'Name: {settings["name"]}',font=font,fill=(255,255,255,0))
	draw.text((10,-5+font_size_offset*2),f'NovelAI Model: {settings["model"]}',font=font,fill=(255,255,255,0))
	draw.text((10,-5+font_size_offset*3),f'Resolution {settings["img_mode"]}',font=font,fill=(255,255,255,0))
	draw.text((10,-5+font_size_offset*4),f'Sampler: {settings["sampler"]}',font=font,fill=(255,255,255,0))
	draw.text((10,-5+font_size_offset*5),f'Steps: {settings["steps"]}',font=font,fill=(255,255,255,0))
	draw.text((10,-5+font_size_offset*6),f'Scale: {settings["scale"]}',font=font,fill=(255,255,255,0))
	#Assembling the Prompt and breaking it up if needed, then drawing it left to the other metadata
	full_prompt=settings["QT"]+settings["prompt"]
	for n in range(int(len(full_prompt)/newline_after)):
		full_prompt=full_prompt[:newline_after*(n+1)]+"\n"+full_prompt[newline_after*(n+1):]
	draw.text((640,-5),f'Prompt: {full_prompt}',font=font,fill=(200,255,200,0))
	#Assembling the UC and breaking it up if needed, then drawing it beneath the prompt
	full_UC=UNDESIRED_CONTENT_LISTS[settings["UCp"]][1]+settings["UC"]
	for n in range(int(len(full_UC)/newline_after)):
		full_UC=full_UC[:newline_after*(n+1)]+'\n'+full_UC[newline_after*(n+1):]
	draw.text((640,-5+font_size_offset*5),f'Undesired Content: {full_UC}',font=font,fill=(255,200,200,0))
	#Deconversion and saving
	img_pil.save(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/ClusterCollages/{replace_forbidden_symbols(settings["name"])}_Collage({replace_forbidden_symbols(name_extra)}).jpg')

#Saves used settings
def save_settings(folder_name,settings,sub_folder=''):
	if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}'): os.makedirs(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}')
	t=open(f'__0utput__/{replace_forbidden_symbols(folder_name)}{sub_folder}/settings꞉{replace_forbidden_symbols(settings["name"])}.py','w',encoding="utf-8")
	t.write(f'settings={settings}')
	t.close
	
###
#Rendering Functions
###

#Simply formats and passes the prompt on without changes, used for simple generations or complex external logic
def generate_as_is(settings,enumerator,only_gen_path=False):
	return image_gen(auth,form_prompt(settings),enumerator,settings["folder_name"],only_gen_path)

#Renders a loop according to the settings and saves those
def render_loop(settings,eval_guard=True,save_config=True,only_gen_path=False):
	imgs=[]
	img_settings=copy.deepcopy(settings)
	if settings["folder_name"]=="":
		img_settings["folder_name"]=settings["name"]
	if save_config:
		save_settings(img_settings["folder_name"],settings)
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
				if eval_guard:
					img_settings["prompt"]+=eval(prompt_list[0],{"__builtins__":{}},{'n':n,'prompt_list':prompt_list})
				else:
					img_settings["prompt"]+=eval(prompt_list[0],{},{'n':n,'prompt_list':prompt_list})
		if type(settings["UC"])!=str:
			img_settings["UC"]=""
			for UC_list in settings["UC"]:
				if eval_guard:
					img_settings["UC"]+=eval(UC_list[0],{"__builtins__":{}},{'n':n,'UC_list':UC_list})
				else:
					img_settings["UC"]+=eval(UC_list[0],{},{'n':n,'UC_list':UC_list})
		
		imgs.append(image_gen(auth,form_prompt(img_settings),enumerator,img_settings["folder_name"],only_gen_path))
	return imgs

#Takes a prompt and renders it across multiple seeds at multiple scales, then puts all generations into a big collage together with the metadata
#If a seed list is passed or the default is used, make sure it has enough seeds for the requested amount of scales (collage_width²)
def prompt_stabber(settings):
	collage_width_squared=settings["collage_width"]*settings["collage_width"]
	img_settings=copy.deepcopy(settings)
	if settings["folder_name"]=="":
		img_settings["folder_name"]=settings["name"]
		if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(img_settings["folder_name"])}/ClusterCollages/'):
			os.makedirs(f'__0utput__/{replace_forbidden_symbols(img_settings["folder_name"])}/ClusterCollages/')
		save_settings(img_settings["folder_name"],settings,sub_folder='/ClusterCollages')
		settings["folder_name"]=settings["name"]
	else:
		if not os.path.exists(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/ClusterCollages/'):
			os.makedirs(f'__0utput__/{replace_forbidden_symbols(settings["folder_name"])}/ClusterCollages/')
		save_settings(settings["folder_name"],settings,sub_folder='/ClusterCollages')

	#Configures the seed list
	if settings["seed"]=="default":
		seed_list=PROMPT_STABBER_DEFAULT_SEEDS
	elif settings["seed"][0]=="random":
		seed_list=[]
		for rows in range(settings["seed"][1][0]):
			row=[]
			for columns in range(settings["seed"][1][1]):
				row.append(generate_seed())
			seed_list.append(row)
	else:
		seed_list=settings["seed"]
	
	#Configures steps and scale lists
	if type(settings["steps"])==list:
		if collage_width_squared==1:
			steps_list=[settings["steps"][0],0]
		else:
			steps_list=[settings["steps"][0],(settings["steps"][1]-settings["steps"][0])/(collage_width_squared-1)]
	else:
		steps_list=[settings["steps"],0]

	if type(settings["scale"])==list:
		if collage_width_squared==1:
			scale_list=[settings["scale"][0],0]
		else:
			scale_list=[settings["scale"][0],(settings["scale"][1]-settings["scale"][0])/(collage_width_squared-1)]
	else:
		scale_list=[settings["scale"],0]
	
	#This loop makes the initial collages
	collages=[]
	for seed_sub_list in seed_list:
		collage_row=[]
		for seed in seed_sub_list:
			imgs=[]
			for n in range(collage_width_squared):
				img_settings["scale"]=round(scale_list[0]+scale_list[1]*n,2)
				img_settings["steps"]=int(steps_list[0]+steps_list[1]*n)
				img_settings["seed"]=seed
				imgs.append(generate_as_is(img_settings,f'(Seed꞉{seed})(Scale꞉{img_settings["scale"]})(Steps꞉{img_settings["steps"]})',only_gen_path=False))
			if collage_width_squared==1:
				collage_row.append(*imgs)
			else:
				collage_row.append(make_collage(imgs,settings["name"],row_length=settings["collage_width"],name_extra=f'(Seed꞉{seed})(Sampler꞉{settings["sampler"]})'))
		collages.append(collage_row)
	
	#This loop puts the borders and seeds on the collages
	color=np.array([30,30,30])
	bordered_collages=[]
	for (collage_row,seed_sub_list) in zip(collages,seed_list):
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

	cluster_collage=make_collage(bordered_collages,settings["name"],row_length=len(seed_list[0]),passed_image_mode=True,folder_name=settings["folder_name"],pass_image=True)
	attach_metadata_header(cluster_collage,settings,f'Cluster[{settings["sampler"]}]')

#And lastly a simple debriefing function for some stats
def debriefing():
	global PRODUCED_IMAGES
	for n in range(5):
		print('GENERATION COMPLETE')
	print(f'Images generated:{PRODUCED_IMAGES}')
	print(f'Short waits:{WAITS_LONG}')
	print(f'Long waits:{WAITS_SHORT}')