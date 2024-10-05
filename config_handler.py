"""
config_handler.py
	This module is responsible for handling all configuration files
	It writes, loads and updates configuration files
"""

import os
import shutil
import ast
import sys
from initialization import handle_exceptions, GlobalState
GS = GlobalState()
from packaging.version import Version

FALLBACK_CONFIG = {
	'1.User_Settings':
"""#Video settings
BASE_FPS = 7

#Settings for cluster collages
CREATOR_NAME = ''
CC_SEEDS_FONT = ['/Fonts/Kanit-Black.ttf',29]
#If needed you can specify a custom font list that will be loaded before the provided fonts
CUSTOM_FONT_LIST_PREPEND = []#Add fonts to be prioritized over the default
CUSTOM_FONT_LIST_APPEND = []#Add fonts that will be used as a fallback if all others fail
FONT_SIZE = 32

#Define custom QTs here
QUALITY_TAGS = {
'Picturesque': 'picturesque, '
}

#Additional waiting time between generations
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
	{'name': 'Full: Inverted Positive Terms - In', 'string': 'insightly, inpicturesque, inquality, inmasterpiece, innice, inlovely, inpleasant, inpretty, infresh, inenchanting, indelightful, inclear, inspectacular, indazzling, ingorgeous, inbrilliant, interrific, insuperb, inmagnific, insharp, inhot, inanatomy, '},
]
""",
	'2.NAID_Constants':
f"""#The URL to which the requests are sent
NAID_CONST_VERSION = '{GS.VERSION}'
URL='https://image.novelai.net/ai/generate-image'
URL_ANNOTATE='https://image.novelai.net/ai/annotate-image'
#This is a list reflecting the online UI UC presets of NAI
NAI_UCS=[
{{'name': 'Full: Low Quality+Bad Anatomy', 'string': 'nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, '}},
{{'name': 'Full: Low Quality', 'string': 'nsfw, lowres, text, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, '}},

{{'name': 'Furry: Low Quality', 'string': 'nsfw, worst quality, low quality, what has science done, what, nightmare fuel, eldritch horror, where is your god now, why, '}},
{{'name': 'Furry: Bad Anatomy', 'string': 'nsfw, {{worst quality}}, low quality, distracting watermark, [nightmare fuel], {{{{unfinished}}}}, deformed, outline, pattern, simple background, '}}
]

#This is the list of available NAI samplers
NAI_SAMPLERS_RAW=['k_dpmpp_2m_sde', 'k_dpmpp_2m', 'k_euler_ancestral', 'k_heun', 'k_euler', 'k_dpm_2', 'k_dpm_2_ancestral', 'k_dpmpp_2s_ancestral', 'k_dpmpp_sde', 'k_dpm_fast', 'k_dpm_adaptive', 'ddim', 'k_lms',]
NAI_SAMPLERS=[
{{'name': 'DPM++ 2M SDE | Converging?', 'string': 'k_dpmpp_2m_sde, '}},
{{'name': 'DPM++ 2M | Converging', 'string': 'k_dpmpp_2m, '}},
{{'name': 'Euler Ancestral | Diverging', 'string': 'k_euler_ancestral, '}},
{{'name': 'Heun', 'string': 'k_heun, '}},
{{'name': 'Euler', 'string': 'k_euler, '}},
{{'name': 'DPM2', 'string': 'k_dpm_2, '}},
{{'name': 'DPM2 Ancestral', 'string': 'k_dpm_2_ancestral, '}},
{{'name': 'DPM++ 2S Ancestral', 'string': 'k_dpmpp_2s_ancestral, '}},
{{'name': 'DPM++ SDE', 'string': 'k_dpmpp_sde, '}},
{{'name': 'DPM Fast', 'string': 'k_dpm_fast, '}},
{{'name': 'DPM Adaptive', 'string': 'k_dpm_adaptive, '}},
{{'name': 'DDIM', 'string': 'ddim, '}},
{{'name': 'K-LMS | Deprecated, inefficient, glitchy', 'string': 'k_lms, '}},
]

NAI_NOISE_SCHEDULERS=['default','native','karras','exponential','polyexponential']
NAI_DEFAULT_NOISE_SCHEDULERS={{
'k_euler': 'karras',
'k_euler_ancestral': 'karras',
'k_dpmpp_2s_ancestral': 'karras',
'k_dpmpp_2m_sde': 'karras',
'k_dpmpp_2m': 'exponential',
'k_dpmpp_sde': 'karras',
'k_heun': 'exponential',
'k_dpm_2': 'native',
'k_dpm_2_ancestral': 'native',
'k_dpm_fast': 'native',
'k_dpm_adaptive': 'native',
'ddim': None,
'ddim_v3': None,
'k_lms': 'karras',
}}

#NAID uses these two vectors as standard quality tags
NAI_PROMPT_CHUNKS=[
{{'name': 'NAI Quality Tags (Old, prepended)', 'string': 'masterpiece, best quality, '}},
{{'name': 'NAI Quality Tags (New, appended)', 'string': ', best quality, amazing quality, very aesthetic, absurdres'}}, 
]

#These are the names used to address certain models
NAI_MODELS={{
'NAI Anime Full V3':'nai-diffusion-3',
'NAI Furry V3':'nai-diffusion-furry-3',
'NAI Anime Full V2':'nai-diffusion-2',
'NAI Furry':'nai-diffusion-furry',
'NAI Curated':'safe-diffusion',
'NAI Anime Full V1':'nai-diffusion',}}

NAI_RESOLUTIONS={{
	'Small':{{
		'PortraitSmall': {{'width':512, 'height':768}},
		'LandscapeSmall': {{'width':768, 'height':512}},
		'SquareSmall':	 {{'width':640, 'height':640,}},
	}},
	'Normal':{{
		'PortraitNormal': {{'width':832, 'height':1216}},
		'LandscapeNormal': {{'width':1216,'height':832}},
		'SquareNormal': {{'width':1024,'height':1024}},
	}},
	'Large':{{
		'PortraitLarge': {{'width':1024, 'height':1536}},
		'LandscapeLarge': {{'width':1536,'height':1024}},
		'SquareLarge': {{'width':1472,'height':1472}},
	}},
	'Landscape':{{
		'LandscapeWallpaper': {{'width':1920,'height':1088}},
		'PortraitWallpaper': {{'width':1088,'height':1920}},
	}},
}}""",
	'3.Token(DO NOT SHARE)':
"""#Only the access token goes into this file. Do not share it with anyone else as that's against NAI ToS. Using it on multiple of your own devices is fine.
AUTH=''
""",
	'Theme':
"""#Define your desired program colors here or from within CVF, the format is [R, G, B, A] with values from 0 to 1
THEME = {
	'InText': {'Name': 'Input: Text', 'value': [1.0, 1.0, 1.0, 1]},
	'InBg': {'Name': 'Input: Background', 'value': [0.23529411764705882, 0.23529411764705882, 0.23529411764705882, 1]},
	
	'ProgText': {'Name': 'Program Text', 'value': [1.0, 1.0, 1.0, 1]},
	'ProgBg': {'Name': 'Program Background', 'value': [0.2372087574241784, 0.2372087574241784, 0.2372087574241784, 1]},
	
	'ConNorm': {'Name': 'Console: Normal', 'value': [0, 1, 0, 1]},
	'ConWarn': {'Name': 'Console: Warning', 'value': [1, 1, 0, 1]},
	'ConErr': {'Name': 'Console: Error', 'value': [1, 0, 0, 1]},
	
	'DBtnText': {'Name': 'Dropdown Buttons: Text', 'value': [1, 1, 1, 1]},
	'DBtnBg': {'Name': 'Dropdown Buttons: Background', 'value': [1.0, 0.6442476057217617, 0.0, 1]},
	
	'BgLText': {'Name': 'BgLabel: Text', 'value': [1, 1, 1, 1]},
	'BgLBg': {'Name': 'BgLabel: Background', 'value': [0.12862318066972706, 0.0, 0.12862318066972706, 1]},
	
	'MBtnText': {'Name': 'Main Buttons: Text', 'value': [1, 1, 1, 1]},
	'MBtnBg': {'Name': 'Main Buttons: Background', 'value': [0.2382927636178841, 0.23754457136756696, 0.2382927636178841, 1]},
	
	'SBtnText': {'Name': 'State Buttons: Text', 'value': [1, 1, 1, 1]},
	'SBtnBgOn': {'Name': 'State Buttons: Active', 'value': [0.31063224001618855, 0.7158210883943184, 0.0, 1]},
	'SBtnBgOff': {'Name': 'State Buttons: Inactive', 'value': [0.8545098888458931, 0.0, 0.0, 1]},
	
	'TTText': {'Name': 'Tooltip: Text', 'value': [1.0, 1.0, 1.0, 1]},
	'TTBg': {'Name': 'Tooltip: Background', 'value': [0.23529411764705882, 0.23137254901960785, 0.23772779747182893, 1]},
	'TTBgOutline': {'Name': 'Tooltip: Background Outline', 'value': [1, 0.30000000000000004, 0.30000000000000004, 1]},
}
""",
}
THEMES = {
	'TemperedGray':
"""#Define your desired program colors here or from within CVF, the format is [R, G, B, A] with values from 0 to 1
THEME = {
	'InText': {'Name': 'Input: Text', 'value': [1.0, 1.0, 1.0, 1]},
	'InBg': {'Name': 'Input: Background', 'value': [0.23529411764705882, 0.23529411764705882, 0.23529411764705882, 1]},
	
	'ProgText': {'Name': 'Program Text', 'value': [1.0, 1.0, 1.0, 1]},
	'ProgBg': {'Name': 'Program Background', 'value': [0.2372087574241784, 0.2372087574241784, 0.2372087574241784, 1]},
	
	'ConNorm': {'Name': 'Console: Normal', 'value': [0, 1, 0, 1]},
	'ConWarn': {'Name': 'Console: Warning', 'value': [1, 1, 0, 1]},
	'ConErr': {'Name': 'Console: Error', 'value': [1, 0, 0, 1]},
	
	'DBtnText': {'Name': 'Dropdown Buttons: Text', 'value': [1, 1, 1, 1]},
	'DBtnBg': {'Name': 'Dropdown Buttons: Background', 'value': [1.0, 0.6442476057217617, 0.0, 1]},
	
	'BgLText': {'Name': 'BgLabel: Text', 'value': [1, 1, 1, 1]},
	'BgLBg': {'Name': 'BgLabel: Background', 'value': [0.12862318066972706, 0.0, 0.12862318066972706, 1]},
	
	'MBtnText': {'Name': 'Main Buttons: Text', 'value': [1, 1, 1, 1]},
	'MBtnBg': {'Name': 'Main Buttons: Background', 'value': [0.2382927636178841, 0.23754457136756696, 0.2382927636178841, 1]},
	
	'SBtnText': {'Name': 'State Buttons: Text', 'value': [1, 1, 1, 1]},
	'SBtnBgOn': {'Name': 'State Buttons: Active', 'value': [0.31063224001618855, 0.7158210883943184, 0.0, 1]},
	'SBtnBgOff': {'Name': 'State Buttons: Inactive', 'value': [0.8545098888458931, 0.0, 0.0, 1]},
	
	'TTText': {'Name': 'Tooltip: Text', 'value': [1.0, 1.0, 1.0, 1]},
	'TTBg': {'Name': 'Tooltip: Background', 'value': [0.23529411764705882, 0.23137254901960785, 0.23772779747182893, 1]},
	'TTBgOutline': {'Name': 'Tooltip: Background Outline', 'value': [1, 0.30000000000000004, 0.30000000000000004, 1]},
}
""",
	'OriginalBlue':
"""#Define your desired program colors here or from within CVF, the format is [R, G, B, A] with values from 0 to 1
THEME = {
	'InText': {'Name': 'Input: Text', 'value': [1, 1, 1, 1]},
	'InBg': {'Name': 'Input: Background', 'value': [0, 0, 0, 1]},
	
	'ProgText': {'Name': 'Program Text', 'value': [1, 0, 1, 1]},
	'ProgBg': {'Name': 'Program Background', 'value': [0, 0, 0.3, 1]},
	
	'ConNorm': {'Name': 'Console: Normal', 'value': [0, 1, 0, 1]},
	'ConWarn': {'Name': 'Console: Warning', 'value': [1, 1, 0, 1]},
	'ConErr': {'Name': 'Console: Error', 'value': [1, 0, 0, 1]},
	
	'DBtnText': {'Name': 'Dropdown Buttons: Text', 'value': [1, 1, 1, 1]},
	'DBtnBg': {'Name': 'Dropdown Buttons: Background', 'value': [0, 0.6, 0.6, 1]},
	
	'BgLText': {'Name': 'BgLabel: Text', 'value': [1, 1, 1, 1]},
	'BgLBg': {'Name': 'BgLabel: Background', 'value': [0.2, 0, 0.2, 1]},
	
	'MBtnText': {'Name': 'Main Buttons: Text', 'value': [1, 1, 1, 1]},
	'MBtnBg': {'Name': 'Main Buttons: Background', 'value': [0.6, 0.6, 0.6, 1]},
	
	'SBtnText': {'Name': 'State Buttons: Text', 'value': [1, 1, 1, 1]},
	'SBtnBgOn': {'Name': 'State Buttons: Active', 'value': [0, 1, 0, 1]},
	'SBtnBgOff': {'Name': 'State Buttons: Inactive', 'value': [1, 0, 0, 1]},
	
	'TTText': {'Name': 'Tooltip: Text', 'value': [0.9237999199237548, 0.8475998398475096, 1.0, 1]},
	'TTBg': {'Name': 'Tooltip: Background', 'value': [0.10459611779609065, 0.06973074519739375, 0.34865372598696903, 1]},
	'TTBgOutline': {'Name': 'Tooltip: Background Outline', 'value': [0.6, 0.85, 1, 1]},
}
""",
	'Obsidian':
"""#Define your desired program colors here or from within CVF, the format is [R, G, B, A] with values from 0 to 1
THEME = {
	'InText': {'Name': 'Input: Text', 'value': [1.0, 1.0, 1.0, 1]},
	'InBg': {'Name': 'Input: Background', 'value': [0.12862318066972706, 0.12862318066972706, 0.12862318066972706, 1]},
	
	'ProgText': {'Name': 'Program Text', 'value': [0.9074111241592825, 0.9074111241592825, 1.0, 1]},
	'ProgBg': {'Name': 'Program Background', 'value': [0.0, 0.0, 0.0, 1]},
	
	'ConNorm': {'Name': 'Console: Normal', 'value': [0, 1, 0, 1]},
	'ConWarn': {'Name': 'Console: Warning', 'value': [1, 1, 0, 1]},
	'ConErr': {'Name': 'Console: Error', 'value': [1, 0, 0, 1]},
	
	'DBtnText': {'Name': 'Dropdown Buttons: Text', 'value': [1, 1, 1, 1]},
	'DBtnBg': {'Name': 'Dropdown Buttons: Background', 'value': [0, 0.6, 0.6, 1]},
	
	'BgLText': {'Name': 'BgLabel: Text', 'value': [1, 1, 1, 1]},
	'BgLBg': {'Name': 'BgLabel: Background', 'value': [0.12862318066972706, 0.0, 0.12862318066972706, 1]},
	
	'MBtnText': {'Name': 'Main Buttons: Text', 'value': [1, 1, 1, 1]},
	'MBtnBg': {'Name': 'Main Buttons: Background', 'value': [0.23933661359454952, 0.46083342229813884, 0.23933661359454952, 1]},
	
	'SBtnText': {'Name': 'State Buttons: Text', 'value': [1, 1, 1, 1]},
	'SBtnBgOn': {'Name': 'State Buttons: Active', 'value': [0.0, 0.6786762036938186, 1.0, 1]},
	'SBtnBgOff': {'Name': 'State Buttons: Inactive', 'value': [0.8747347069499306, 0.7137254901960784, 0.0, 1]},
	
	'TTText': {'Name': 'Tooltip: Text', 'value': [0.7, 1, 0.775, 1]},
	'TTBg': {'Name': 'Tooltip: Background', 'value': [0.0, 0.0, 0.0, 1]},
	'TTBgOutline': {'Name': 'Tooltip: Background Outline', 'value': [0.4, 0.775, 1, 1]},
}
""",
	'Midnight':
"""#Define your desired program colors here or from within CVF, the format is [R, G, B, A] with values from 0 to 1
THEME = {
	'InText': {'Name': 'Input: Text', 'value': [0.8470588235294118, 0.8470588235294118, 1.0, 1]},
	'InBg': {'Name': 'Input: Background', 'value': [0.06044852155452447, 0.06044852155452447, 0.06044852155452447, 1]},
	
	'ProgText': {'Name': 'Program Text', 'value': [0.8431372549019608, 0.8431372549019608, 1.0, 1]},
	'ProgBg': {'Name': 'Program Background', 'value': [0.0, 0.0, 0.0, 1]},
	
	'ConNorm': {'Name': 'Console: Normal', 'value': [0, 1, 0, 1]},
	'ConWarn': {'Name': 'Console: Warning', 'value': [1, 1, 0, 1]},
	'ConErr': {'Name': 'Console: Error', 'value': [1, 0, 0, 1]},
	
	'DBtnText': {'Name': 'Dropdown Buttons: Text', 'value': [1, 1, 1, 1]},
	'DBtnBg': {'Name': 'Dropdown Buttons: Background', 'value': [0.0, 0.3764193445073129, 0.3764193445073129, 1]},
	
	'BgLText': {'Name': 'BgLabel: Text', 'value': [0.8447813245080247, 0.8447813245080247, 1, 1]},
	'BgLBg': {'Name': 'BgLabel: Background', 'value': [0.12862318066972706, 0.0, 0.12862318066972706, 1]},
	
	'MBtnText': {'Name': 'Main Buttons: Text', 'value': [0.8447813245080247, 0.8447813245080247, 1, 1]},
	'MBtnBg': {'Name': 'Main Buttons: Background', 'value': [0.2382927636178841, 0.23754457136756696, 0.2382927636178841, 1]},
	
	'SBtnText': {'Name': 'State Buttons: Text', 'value': [1, 1, 1, 1]},
	'SBtnBgOn': {'Name': 'State Buttons: Active', 'value': [0.0, 0.5425244653215189, 0.0, 1]},
	'SBtnBgOff': {'Name': 'State Buttons: Inactive', 'value': [0.6596149603216966, 0.0, 0.0, 1]},
	
	'TTText': {'Name': 'Tooltip: Text', 'value': [1.0, 1.0, 1.0, 1]},
	'TTBg': {'Name': 'Tooltip: Background', 'value': [0, 0, 0, 1]},
	'TTBgOutline': {'Name': 'Tooltip: Background Outline', 'value': [0.6273550227165644, 1.0, 0.571707145848315, 1.0]},
}
""",
	'BrightBurns':
"""#Define your desired program colors here or from within CVF, the format is [R, G, B, A] with values from 0 to 1
THEME = {
	'InText': {'Name': 'Input: Text', 'value': [0.0, 0.0, 0.0, 1]},
	'InBg': {'Name': 'Input: Background', 'value': [1.0, 1.0, 1.0, 1]},
	
	'ProgText': {'Name': 'Program Text', 'value': [0.0, 0.0, 0.0, 1]},
	'ProgBg': {'Name': 'Program Background', 'value': [1.0, 1.0, 1.0, 1]},
	
	'ConNorm': {'Name': 'Console: Normal', 'value': [0.0, 0.5771322879427437, 0.0, 1]},
	'ConWarn': {'Name': 'Console: Warning', 'value': [0.6967853706852787, 0.6967853706852787, 0.0, 1]},
	'ConErr': {'Name': 'Console: Error', 'value': [0.3894944990964957, 0.0, 0.0, 1]},
	
	'DBtnText': {'Name': 'Dropdown Buttons: Text', 'value': [1, 1, 1, 1]},
	'DBtnBg': {'Name': 'Dropdown Buttons: Background', 'value': [0.0, 1.0, 1.0, 1]},
	
	'BgLText': {'Name': 'BgLabel: Text', 'value': [0.0, 0.0, 0.0, 1]},
	'BgLBg': {'Name': 'BgLabel: Background', 'value': [0.9170558184613091, 0.9415303126586458, 0.9116170419730121, 1]},
	
	'MBtnText': {'Name': 'Main Buttons: Text', 'value': [1.0, 1.0, 1.0, 1]},
	'MBtnBg': {'Name': 'Main Buttons: Background', 'value': [1.0, 0.9968601973515363, 1.0, 1]},
	
	'SBtnText': {'Name': 'State Buttons: Text', 'value': [1, 1, 1, 1]},
	'SBtnBgOn': {'Name': 'State Buttons: Active', 'value': [0.0, 0.5425244653215189, 0.0, 1]},
	'SBtnBgOff': {'Name': 'State Buttons: Inactive', 'value': [0.6596149603216966, 0.0, 0.0, 1]},
	
	'TTText': {'Name': 'Tooltip: Text', 'value': [0.0, 0.0, 0.0, 1]},
	'TTBg': {'Name': 'Tooltip: Background', 'value': [1.0, 1.0, 1.0, 1]},
	'TTBgOutline': {'Name': 'Tooltip: Background Outline', 'value': [0.4738009273886657, 0.4738009273886657, 0.4738009273886657, 1]},
}
""",
}
GS.SETTINGS_DIR = os.path.join(GS.FULL_DIR, "Settings") 
GS.THEMES_DIR = os.path.join(GS.SETTINGS_DIR, "Themes")
os.makedirs(GS.THEMES_DIR, exist_ok=True)  

# This dict contains all the files that must be loaded to get the program running
CONFIG_FILES = {
	"1.User_Settings": os.path.join(GS.SETTINGS_DIR, "1.User_Settings.py"),
	"2.NAID_Constants": os.path.join(GS.SETTINGS_DIR, "2.NAID_Constants.py"),
	"3.Token(DO NOT SHARE)": os.path.join(GS.SETTINGS_DIR, "3.Token(DO NOT SHARE).py"),
	"Theme": os.path.join(GS.THEMES_DIR, "Current.py"),
}

# This block here is responsible for moving legacy config files to their new intended locations
FILES_TO_MOVE = ["1.User_Settings.py", "2.NAID_Constants.py", "3.Theme.py", "4.Token(DO NOT SHARE).py"] 
for file in FILES_TO_MOVE:
	# Build paths
	old_path = os.path.join(GS.FULL_DIR, file)
	if file == "3.Theme.py":
		new_path = os.path.join(GS.THEMES_DIR, "Current.py") 
	elif file == "4.Token(DO NOT SHARE).py":
		new_path = os.path.join(GS.SETTINGS_DIR, "3.Token(DO NOT SHARE).py") 
	else:
		new_path = os.path.join(GS.SETTINGS_DIR, file)

	# Check if old file exists
	if os.path.exists(old_path):
		# Move file to new location
		shutil.move(old_path, new_path)

# A simple config writing function that can either just take the name of the missing config file to write from the fallback, or a full location/content input
# Uses UTF-16 so there's as little problem as possible when using the deep variety of symbols SD in its different forms can make use of
@handle_exceptions
def write_config_file(config_name, content=None, load = False):
	if content: 
		with open(config_name, "w", encoding="utf-16") as f:
			f.write(content)
		if load:
			load_config(content, direct_mode = True)
	else:
		config_path = CONFIG_FILES.get(config_name)
		with open(config_path, "w", encoding="utf-16") as f:
			f.write(FALLBACK_CONFIG[config_name])
		if load:
			load_config(config_path)

# Simple function to recursively update and overwrite dicts without breaking references
@handle_exceptions
def merge_dicts(old, new):
    for key, value in new.items():
        if isinstance(value, dict):
            # Nested dict, merge recursively 
            old[key] = merge_dicts(old.get(key, {}), value)
        else:
            # Overwrite 
            old[key] = value 
    return old

# Excused from using @handle_exceptions due to custom error handling
def load_config(config, direct_mode = False):
	try:
		if direct_mode:
			config_str = config
		else:
			with open(config, "r", encoding="utf_16") as f:
				config_str = f.read()
		config_ast = ast.parse(config_str, filename=config)
		config_dict = {}
		for node in config_ast.body:
			if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
				target_name = node.targets[0].id
				value = ast.literal_eval(node.value)
				config_dict[target_name] = value
		for key, value in config_dict.items():
			if key == 'THEME':
				key = 'theme'
			existing_value = getattr(GS, key, None)
			#if key == 'theme' and existing_value != None:
			#	GS.old_console_colors = [existing_value["ConNorm"]["value"], existing_value["ConWarn"]["value"], existing_value["ConErr"]["value"]]
			if existing_value and isinstance(existing_value, dict):
				setattr(GS, key, merge_dicts(existing_value, value))
			else:
				setattr(GS, key, value)
	except Exception as e:
		print(f'Failed to load {config}.py! Fix or delete the according file.')
		import traceback
		traceback.print_exc()

# This loop uses the dict from above and figures out if the according config files exists and tries to load them if they do, and tries to create them if they don't
load_config(FALLBACK_CONFIG["Theme"], direct_mode = True)
for name, path in CONFIG_FILES.items():
	if not os.path.exists(path):
		print(f"{name} config not found at {path}, writing default...") ### Messages like these should probably be printed delayed so they appear in the application
		write_config_file(name, load = True) # using default configs
	else:  
		load_config(path) #load located config file

# Make sure that the NAID constants file is up to date
if getattr(GS, 'NAID_CONST_VERSION', None) == None:
	write_config_file("2.NAID_Constants", load = True)
elif Version(str(GS.NAID_CONST_VERSION)) < Version(str(GS.VERSION)):
	write_config_file("2.NAID_Constants", load = True)

# This loop ensures that default theme files are always present
for name, content in THEMES.items():
	if not os.path.exists(os.path.join(GS.THEMES_DIR, f"{name}.py")):
		write_config_file(os.path.join(GS.THEMES_DIR, f"{name}.py"), content)