import os
import ast
import sys

if getattr(sys, 'frozen', False):
    # Running in a bundle
    FULL_DIR = os.path.dirname(sys.executable) + '/'
else:
    # Running in a normal Python environment
    FULL_DIR = os.path.dirname(os.path.realpath(__file__)) + '/'
FALLBACK_CONFIG = {
	'1.User_Settings':
"""#Video settings
BASE_FPS = 7
#If Flowframes is used and the path is different it has to go here.
FLOWFRAMES_PATH = ''
FF_FACTOR = 4
FF_OUTPUT_MODE = 2

#Settings for cluster collages
CREATOR_NAME = ''
CC_SEEDS_FONT = ['/Fonts/kanit-black.ttf',29]
#If needed you can specify a custom font list that will be loaded before the provided fonts
CUSTOM_FONT_LIST_PREPEND = []#Add fonts to be prioritized over the default
CUSTOM_FONT_LIST_APPEND = []#Add fonts that will be used as a fallback if all others fail
FONT_SIZE = 32

#Define custom QTs here
QUALITY_TAGS = {
'Picturesque': 'picturesque, '
}

#Additional waiting time between generations, set higher when still using NAI yourself in parallel to avoid getting limited
WAIT_TIME = 1

SEED_LISTS = [
	{'name': 'Default 3x3', 'seeds':
		[[4246521898,3725954486,916033042],
		[4132094759,2830623800,88736211],
		[2823232049,3881402690,808994933]]},
	{'name': 'Default 4x4', 'seeds': 
		[[3076815738, 1990129682, 3655402003, 3572297602],
		[439438776, 688831479, 1391759257, 2062017751],
		[396332814, 341256431, 4087186989, 3204503906],
		[251242884, 1287923751, 2025346986, 3668458118]]},
]

USER_RESOLUTIONS = {
	'Max':{
		'PortraitMax': {'width':1408, 'height':2112},
		'LandscapeMax': {'width':2112, 'height':1408},
		'SquareMax': {'width':1728, 'height':1728},
	},
	'Dakimakura1|3':{
		'Dakimakura1/3': {'width':384, 'height':1024},
		'Dakimakura1/3+': {'width':576, 'height':1536},
		'Dakimakura1/3++': {'width':768, 'height':2048},
		'Dakimakura1/3+++': {'width':1088, 'height':2880},
	},
}

USER_PROMPT_CHUNKS = [
]

USER_UCS = [
	{'name': 'Universal Underage', 'string': 'baby, toddler, child, '},
	{'name': 'Hyper SFW', 'string': 'nsfw, nips, vag, pantyshot, upskirt, cameltoe, nude, bare, navel, sex, lewd, spread legs, sexually suggestive, '},
	{'name': 'Negative Terms', 'string': 'blurry, trash, waste, ugly, hideous, disgusting, disturbing, horrible, deformed, bloody, horror, terrifying, horrendous, malicious, destruction, obliteration, damage, symmetry, disorder, nasty, '},
	{'name': 'Full: Inverted Positive Terms - Un', 'string': 'unsightly, unpicturesque, unquality, unmasterpiece, unnice, unlovely, unpleasant, unpretty, unfresh, unenchanting, undelightful, unclear, unspectacular, undazzling, ungorgeous, unbrilliant, unterrific, unsuperb, unmagnific, unsharp, unhot, unanatomy, '},
	{'name': 'Full: Inverted Positive Terms - In', 'string': 'insightly, inpicturesque, inquality, inquality, inmasterpiece, innice, inlovely, inpleasant, inpretty, infresh, inenchanting, indelightful, inclear, inspectacular, indazzling, ingorgeous, inbrilliant, interrific, insuperb, inmagnific, insharp, inhot, inanatomy, '},
]
""",
	'2.NAID_Constants':
"""#The URL to which the requests are sent
URL='https://api.novelai.net/ai/generate-image'
#This is a list reflecting the online UI UC presets of NAI
NAI_UCS=[
{'name': 'Full: Low Quality+Bad Anatomy', 'string': 'nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, '},
{'name': 'Full: Low Quality', 'string': 'nsfw, lowres, text, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, '},

{'name': 'Furry: Low Quality', 'string': 'nsfw, worst quality, low quality, what has science done, what, nightmare fuel, eldritch horror, where is your god now, why, '},
{'name': 'Furry: Bad Anatomy', 'string': 'nsfw, {worst quality}, low quality, distracting watermark, [nightmare fuel], {{unfinished}}, deformed, outline, pattern, simple background, '}
]

#This is the list of available NAI samplers
NAI_SAMPLERS_RAW=['k_dpmpp_2m', 'k_euler_ancestral', 'k_heun', 'k_euler', 'k_dpm_2', 'k_dpm_2_ancestral', 'k_dpmpp_2s_ancestral', 'k_dpmpp_sde', 'k_dpm_fast', 'k_dpm_adaptive', 'ddim', 'k_lms',]
NAI_SAMPLERS=[
{'name': 'DPM++ 2M | Converging', 'string': 'k_dpmpp_2m, '},
{'name': 'Euler Ancestral | Diverging', 'string': 'k_euler_ancestral, '},
{'name': 'Heun', 'string': 'k_heun, '},
{'name': 'Euler', 'string': 'k_euler, '},
{'name': 'DPM2', 'string': 'k_dpm_2, '},
{'name': 'DPM2 Ancestral', 'string': 'k_dpm_2_ancestral, '},
{'name': 'DPM++ 2S Ancestral', 'string': 'k_dpmpp_2s_ancestral, '},
{'name': 'DPM++ SDE', 'string': 'k_dpmpp_sde, '},
{'name': 'DPM Fast', 'string': 'k_dpm_fast, '},
{'name': 'DPM Adaptive', 'string': 'k_dpm_adaptive, '},
{'name': 'DDIM', 'string': 'ddim, '},
{'name': 'K-LMS | Deprecated, inefficient, glitchy', 'string': 'k_lms, '},
]

#NAID uses these two vectors as standard quality tags
NAI_PROMPT_CHUNKS=[
{'name': 'NAI Quality Tags', 'string': 'masterpiece, best quality, '},
]

#These are the names used to address certain models
NAI_MODELS={'NAI Curated':'safe-diffusion','NAI Full':'nai-diffusion','NAI Furry':'nai-diffusion-furry'}

NAI_RESOLUTIONS={
	'Normal':{
		'PortraitNormal': {'width':512, 'height':768},
		'LandscapeNormal': {'width':768, 'height':512},
		'SquareNormal':	 {'width':640, 'height':640,},
	},
	'Large':{
		'PortraitLarge': {'width':832, 'height':1280},
		'LandscapeLarge': {'width':1280,'height':832},
		'SquareLarge': {'width':1024,'height':1024},
	},
	'Large+':{
		'PortraitLarge+': {'width':1024, 'height':1536},
		'LandscapeLarge+': {'width':1536,'height':1024},
		'SquareLarge+': {'width':1472,'height':1472},
	},
	'Landscape':{
		'LandscapeWallpaper': {'width':1920,'height':1088},
		'PortraitWallpaper': {'width':1088,'height':1920},
	},
}""",
	'3.Theme':
"""#Define your desired program colors here, the format is [R, G, B, A] with values from 0 to 1
THEME=[
	{'name': 'Input: Text', 'value': [1, 1, 1, 1]},
	{'name': 'Input: Background', 'value': [0, 0, 0, 1]},
	{'name': 'Program Text', 'value': [1, 0, 1, 1]},
	{'name': 'Program Background', 'value': [0, 0, 0.3, 1]},
	{'name': 'Console: Normal', 'value': [0, 1, 0, 1]},
	{'name': 'Console: Error', 'value': [1, 0, 0, 1]},
	{'name': 'Categories: Text', 'value': [1, 1, 1, 1]},
	{'name': 'Categories: Background', 'value': [0.2, 0, 0.2, 1]},
	{'name': 'Main Buttons: Text', 'value': [1, 1, 1, 1]},
	{'name': 'Main Buttons: Background', 'value': [0.6, 0.6, 0.6, 1]},
	{'name': 'Dropdown Buttons: Text', 'value': [1, 1, 1, 1]},
	{'name': 'Dropdown Buttons: Background', 'value': [0, 0.6, 0.6, 1]},
]""",
	'4.Token(DO NOT SHARE)':
"""#Only the access token goes into this file. Do not share it with anyone else as that's against NAI ToS. Using it on multiple of your own devices is fine.
AUTH=''
""",
}

def write_config_file(config_name,content=False):
	config_file = os.path.join(FULL_DIR, f"{config_name}.py")
	if content:
		with open(config_file, "w", encoding="utf_16") as f:
			f.write(content)
	else:
		with open(config_file, "w", encoding="utf_16") as f:
			f.write(FALLBACK_CONFIG[config_name])

def load_config_file(config_name):
	try:
		config_file = os.path.join(FULL_DIR, f"{config_name}.py")
		if not os.path.exists(config_file):
			write_config_file(config_name)
		with open(config_file, "r", encoding="utf_16") as f:
			config_str = f.read()
		config_ast = ast.parse(config_str, filename=config_file)
		config_dict = {}
		for node in config_ast.body:
			if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
				target_name = node.targets[0].id
				value = ast.literal_eval(node.value)
				config_dict[target_name] = value
		globals().update(config_dict)
	except Exception as e:
		print(f'Failed to load {config_name}.py! Fix or delete the according file.')
		import traceback
		traceback.print_exc()

for config_name in FALLBACK_CONFIG:
	load_config_file(config_name)