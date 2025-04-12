"""
NovelAI Diffusion.py
This provider is for base NovelAI generation similar to using SD
"""
from initialization import handle_exceptions, GlobalState
import io
import json
import zipfile
import requests
import math
import os
import regex as re
from kivy.clock import Clock
import kivy_widgets as KW
import text_manipulation as TM
import file_loading as FL
import image_generator as IM_G
import config_handler as CH
from GenerationProviders.Resources.NovelAI import NAI_CLIP_Tokenizer
from kivy.event import EventDispatcher
from kivy.properties import DictProperty, StringProperty
GS = GlobalState()

class NAIDGenerationProvider():
	# The provider initialization function has to contain the constants that the provider needs to work
	@handle_exceptions
	def __init__(self, name, **kwargs):
		self.name = name
		self.widgets = []
		self.CONSTANTS = {
			#The URL_GEN_IMG to which the requests are sent
			'URL_GEN_IMG': 'https://image.novelai.net/ai/generate-image',
			'URL_ANNOTATE': 'https://image.novelai.net/ai/annotate-image',
			'URL_API': 'https://api.novelai.net',
			
			'SUB_TIERS': {
				0: ['Paper', GS.FULL_DIR + 'GenerationProviders/Resources/NovelAI/Assets/0 paper.svg'],
				1: ['Tablet', GS.FULL_DIR + 'GenerationProviders/Resources/NovelAI/Assets/1 tablet.svg'],
				2: ['Scroll', GS.FULL_DIR + 'GenerationProviders/Resources/NovelAI/Assets/2 scroll.svg'],
				3: ['Opus', GS.FULL_DIR + 'GenerationProviders/Resources/NovelAI/Assets/3 opus.svg'],
			},
			
			'MAX_RES': 3145728,
			'MAX_TOKEN_COUNT': 225,

			#This is the list of available NAI samplers
			'SAMPLERS': {
				'Euler Ancestral': 'k_euler_ancestral',
				'DPM++ 2M SDE': 'k_dpmpp_2m_sde',
				'DPM++ 2M': 'k_dpmpp_2m',
				'Heun': 'k_heun',
				'Euler': 'k_euler',
				'DPM2': 'k_dpm_2',
				'DPM2 Ancestral': 'k_dpm_2_ancestral',
				'DPM++ 2S Ancestral': 'k_dpmpp_2s_ancestral',
				'DPM++ SDE': 'k_dpmpp_sde',
				'DPM Fast': 'k_dpm_fast',
				'DPM Adaptive': 'k_dpm_adaptive',
				'DDIM': 'ddim',
				'K-LMS': 'k_lms',
			},

			'NOISE_SCHEDULERS': ['default','native','karras','exponential','polyexponential'],
			'DEFAULT_NOISE_SCHEDULERS': {
				'k_dpmpp_2m_sde': 'karras',
				'k_dpmpp_2m': 'exponential',
				'k_euler_ancestral': 'native',
				'k_heun': 'exponential',
				'k_euler': 'native',
				'k_dpm_2': 'native',
				'k_dpm_2_ancestral': 'native',
				'k_dpmpp_2s_ancestral': 'native',
				'k_dpmpp_sde': 'exponential',
				'k_dpm_fast': 'native',
				'k_dpm_adaptive': 'native',
				'ddim': None,
				'ddim_v3': None,
				'k_lms': 'karras',
			},

			#NAID uses these two vectors as standard quality tags
			'PROMPT_CHUNKS': {
				'Anime V2 Quality Tags': 'very aesthetic, best quality, absurdres, ',
				'Anime V3 Quality Tags': ', best quality, amazing quality, very aesthetic, absurdres',
				'Furry V3 Quality Tags': ', {best quality}, {amazing quality}',
			},
			#This is a list reflecting the online UI UC presets of NAI
			'UCS': {
				'Anime V2/3: Light': 'nsfw, lowres, jpeg artifacts, worst quality, watermark, blurry, very displeasing, ',
				
				'Anime V2: Heavy': 'nsfw, lowres, bad, text, error, missing, extra, fewer, cropped, jpeg artifacts, worst quality, bad quality, watermark, displeasing, unfinished, chromatic aberration, scan, scan artifacts, ',
				
				'Anime V3: Heavy': 'nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], ',
				'Anime V3: Human Focus': 'nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched pupils, heart-shaped pupils, glowing eyes, ',
				
				'Furry V3: Light': 'nsfw, {worst quality}, guide lines, unfinished, bad, url, tall image, widescreen, compression artifacts, unknown text, ',
				'Furry V3: Heavy': 'nsfw, {{worst quality}}, [displeasing], {unusual pupils}, guide lines, {{unfinished}}, {bad}, url, artist name, {{tall image}}, mosaic, {sketch page}, comic panel, impact (font), [dated], {logo}, ych, {what}, {where is your god now}, {distorted text}, repeated text, {floating head}, {1994}, {widescreen}, absolutely everyone, sequence, {compression artifacts}, hard translated, {cropped}, {commissioner name}, unknown text, '
			},

			'RESOLUTIONS': {
				'Small':{
					'PortraitSmall': {'width':512, 'height':768},
					'LandscapeSmall': {'width':768, 'height':512},
					'SquareSmall':	 {'width':640, 'height':640,},
				},
				'Normal':{
					'PortraitNormal': {'width':832, 'height':1216},
					'LandscapeNormal': {'width':1216,'height':832},
					'SquareNormal': {'width':1024,'height':1024},
				},
				'Large':{
					'PortraitLarge': {'width':1024, 'height':1536},
					'LandscapeLarge': {'width':1536,'height':1024},
					'SquareLarge': {'width':1472,'height':1472},
				},
				'Huge':{
					'PortraitHuge': {'width':1408, 'height':2112},
					'LandscapeHuge': {'width':2112,'height':1408},
					'SquareHuge': {'width':1728,'height':1728},
				},
				'Wallpaper':{
					'LandscapeWallpaper': {'width':1920,'height':1088},
					'PortraitWallpaper': {'width':1088,'height':1920},
				},
			},

			#These are the names used to address certain models
			'MODELS': {
				'NAI Diffusion Anime V3': 'nai-diffusion-3',
				'NAI Diffusion Furry V3': 'nai-diffusion-furry-3',
				'NAI Diffusion Anime V2': 'nai-diffusion-2',},

			'MODEL_MAPPING': {
				# NovelAI Legacy Models
				'Stable Diffusion 81274D13': 'nai-diffusion', # Full V1
				'Stable Diffusion 3B3287AF': 'nai-diffusion', # Full V1.0.1
				'Stable Diffusion 1D44365E': 'safe-diffusion', # Safe V1
				'Stable Diffusion F4D50568': 'safe-diffusion', # Safe V1.0.1
				'Stable Diffusion 1D09D794': 'nai-diffusion-furry', # V1.2
				'Stable Diffusion F64BA557': 'nai-diffusion-furry', # V1.3
				
				# Furry models
				'Stable Diffusion XL 9CC2F394': 'NAI Diffusion Furry V3', # V3
				'Stable Diffusion XL 37C2B166': 'NAI Diffusion Furry V3', # V3.0.1
				'Stable Diffusion XL C8704949': 'NAI Diffusion Furry V3', # V3 Inpaint
				'Stable Diffusion XL F306816B': 'NAI Diffusion Furry V3', # V3.0.1 Inpaint

				# Anime models
				'Stable Diffusion F1022D28': 'NAI Diffusion Anime V2', # Full V2
				'Stable Diffusion XL C1E1DE52': 'NAI Diffusion Anime V3', # Full V3
				'Stable Diffusion XL 8BA2AF87': 'NAI Diffusion Anime V3', # Full V3.0.1
				'Stable Diffusion XL 7BCCAA2C': 'NAI Diffusion Anime V3', # Full V3.0.2
				'Stable Diffusion XL 1120E6A9': 'NAI Diffusion Anime V3', # Inpaint V3
				
				# Fallback for legacy bug case
				'Stable Diffusion': 'NAI Anime Full V3'
			},
		}

	# ---UI Functions---

	# initialize_ui is called once for all providers upon program startup, creates all needed UI elements, and hides them at the end
	@handle_exceptions
	def initialize_ui(self):
		self.clip_calculator = CLIPCostCalculator()
		GS.NAI = NAIState()
		GS.NAI.AUTH = GS.AUTH
		KW.create_dropdown_entries(GS.MAIN_APP.model_dropdown, self.CONSTANTS['MODELS'], self.widgets)
		KW.create_dropdown_entries(GS.MAIN_APP.sampler_dropdown, self.CONSTANTS['SAMPLERS'], self.widgets)
		KW.create_dropdown_entries(GS.MAIN_APP.noise_schedule_dropdown, self.CONSTANTS['NOISE_SCHEDULERS'], self.widgets)
		KW.create_dropdown_entries(GS.MAIN_APP.sampler_injector_dropdown, self.CONSTANTS['SAMPLERS'], self.widgets, target_text_field=GS.MAIN_APP.sampler_input,
			extra_widget_classes=[SMEAModButtonPair], delimiter = ', ')
		KW.create_dropdown_entries(GS.MAIN_APP.prompt_dropdown, self.CONSTANTS['PROMPT_CHUNKS'], self.widgets, target_text_field=GS.MAIN_APP.prompt.input)
		KW.create_dropdown_entries(GS.MAIN_APP.uc_dropdown, self.CONSTANTS['UCS'], self.widgets, target_text_field=GS.MAIN_APP.uc.input)
		sigma_thresholding_row = KW.BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		sigma_thresholding_label = KW.Label(text='Sigma Thresh.:', **GS.l_row_size)
		GS.MAIN_APP.sigma_thresholding_import = KW.ImportButton(**GS.imp_row_size)
		sigma_thresholding_layout = KW.BoxLayout(orientation='horizontal')
		sigma_thresholding_skip_above = KW.Label(text='Skip Above:', **GS.l_row_size)
		GS.MAIN_APP.sigma_thresholding_skip_above_input = KW.FScrollInput(min_value=0, max_value=1000, fi_mode='hybrid_float', increment=0.1, text='0', multiline=False, size_hint=(1, None), size=(90, GS.UI_field_height), font_size=GS.UI_font_small,font_name='Unifont', disabled = True)
		GS.MAIN_APP.sigma_thresholding_dropdown = KW.DropDown()

		
		
		# This is a function that can be used both for the scrolling set_state_func as well as the on_select binding to switch states for sigma thresholding
		@handle_exceptions
		def sigma_input_state_func(index, btn=None):
			if btn == None:
				btn = GS.MAIN_APP.sigma_thresholding_dropdown.children[0].children[index]
			setattr(GS.MAIN_APP.sigma_thresholding_button, 'text', btn.text)
			setattr(GS.MAIN_APP.sigma_thresholding_skip_above_input, 'disabled', btn.text != 'Manual')
			
		GS.MAIN_APP.sigma_thresholding_dropdown.bind(on_select=sigma_input_state_func)
		GS.MAIN_APP.sigma_thresholding_button = KW.ScrollDropDownButton(GS.MAIN_APP.sigma_thresholding_dropdown, text='Off', size_hint=(None, None), size=(90, GS.UI_field_height), set_state_func=sigma_input_state_func)#tooltip_types=['Model']

		for text in ['Off', 'Variety+', 'Manual']:
			btn = KW.DropDownEntryButton(text=text, size_hint_y=None, height=GS.UI_field_height)
			btn.bind(on_release=handle_exceptions(lambda btn: GS.MAIN_APP.sigma_thresholding_dropdown.select(btn)))
			GS.MAIN_APP.sigma_thresholding_dropdown.add_widget(btn)

		sigma_thresholding_layout.add_widget(GS.MAIN_APP.sigma_thresholding_button)
		sigma_thresholding_layout.add_widget(sigma_thresholding_skip_above)
		sigma_thresholding_layout.add_widget(GS.MAIN_APP.sigma_thresholding_skip_above_input)

		sigma_thresholding_row.add_widget(sigma_thresholding_label)
		sigma_thresholding_row.add_widget(GS.MAIN_APP.sigma_thresholding_import)
		sigma_thresholding_row.add_widget(sigma_thresholding_layout)
		self.widgets.append(sigma_thresholding_row)
		GS.MAIN_APP.input_layout.add_widget(sigma_thresholding_row)
		
		token_button = KW.Button(text='Set NovelAI token (DO NOT SHARE):', on_release=self.process_token, size_hint=(None,None), size=(300,GS.UI_field_height))
		self.token_state = KW.BgLabel(font_name='NotoEmoji', text='❔', size_hint=(None,None), size=(GS.UI_field_height,GS.UI_field_height), register_to = None)
		token_layout = KW.BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		self.token_input = KW.TextInput(text=GS.NAI.AUTH, multiline=False, size_hint=(1,None), size=(100+GS.UI_field_height,GS.UI_field_height))
		token_layout.add_widget(token_button)
		token_layout.add_widget(self.token_state)
		token_layout.add_widget(self.token_input)
		self.widgets.append(token_layout)
		GS.MAIN_APP.config_window.layout.add_widget(token_layout)
		
		### NovelAI subscription layout
		# GS.NAI.subscription_state is a Kivy DictProperty that as such can be used in a bind statement, it is initialized as {}, and if possible will be updated regularly
		# When it is updated, it will contain a raw version of the dict that the NAI servers provide, which then needs to be processed for this layout
		# Subscription tier:
		# The current subscription tier is returned as a simple int under the key 'tier'
		# self.CONSTANTS['SUB_TIERS'] is a dict where the keys are matching int numbers and the values are [Display String, Asset Location String] lists
		# Expiration date:
		# The expiration date is a timestamp int under the key 'expiresAt'
		# Available Anlas:
		# The amount of available Anlas is a dict under the key 'trainingStepsLeft'
		# In that subdict the 'Subscription Anlas' are available as an int under the key 'fixedTrainingStepsLeft'
		# In that subdict the 'Paid Anlas' are available as an int under the key 'purchasedTrainingSteps'
		# I think it might be best that after all the widgets are written and sorted in, you define a function in place to update the texts and then bind it
		
		# subscription_layout = KW.BoxLayout(orientation='vertical', size_hint_y=None)
		# All the additional widgets and sublayouts to make up the total layout go here, and do note that ALL kivy widgets are to be initialized as KW.widget, no imports here
		# GS.UI_field_height is a constant that is to be used on sublayouts, and it defines the height for a comfortable fit of one line of text
				
		# The image assets that need to be integrated are present as .svg files, use KW.SvgWidget
		# KW.SvgWidget takes one argument, the svg path, and it has one function, set_svg which is called upon initialization, but it can also be called manually with a new path
		# The top line should show both the subscription tier as well as the expiration date
		# Should look like this: "Sub Tier: (Display String)(Associated .svg)" on the left and "Expires at: (formatted date)"
		# In order to make the formatted date use datetime.datetime.fromtimestamp(timestamp).strftime(GS.date_format)

		# Additionally the symbol for the anlas is available under "GS.FULL_DIR + 'GenerationProviders/Resources/NovelAI/Assets/anlas.svg'" and needs to be integrated
		# Both anlas types should be visible at once, on the top it should read like "Subscription Anlas: X(anlas.svg)"
		# And right below that "Paid Anlas: X(anlas.svg)"
		# subscription_layout.add_widget(self...)
		# self.widgets.append(subscription_layout)
				
		# Create the main subscription layout container.
		subscription_layout = KW.BoxLayout(orientation='vertical', size_hint_y=None)
		subscription_layout.height = GS.UI_field_height * 2  # Adjust height for three lines

		# --- Top Row: Tier & Expiration ---
		# This horizontal layout has two parts: left (subscription tier) and right (expiration date)
		tier_row = KW.BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)

		# Left side: Subscription Tier info.
		tier_box = KW.BoxLayout(orientation='horizontal')
		# Label to show the display string for the subscription tier.
		tier_label = KW.Label(
			text="Sub Tier: N/A", markup=True, halign='left', valign='middle',
			size_hint_x=None
		)
		tier_label.bind(texture_size=lambda inst, ts: setattr(inst, 'width', ts[0]))
		GS.tier_label = tier_label
		#tier_icon = KW.SvgWidget("", height=GS.UI_field_height)  # No size_hint, will size to content
		tier_icon_layout = KW.BoxLayout(orientation='horizontal', size_hint=(None, None), height=GS.UI_field_height)

		spacer_box = KW.BoxLayout(orientation='horizontal')
		
		# Expiration Label (right aligned, flexible)
		expiration_label = KW.Label(
			text="Expires at: N/A", markup=True, halign='right', valign='middle',
			size_hint_x=None
		)
		expiration_label.bind(texture_size=lambda inst, ts: setattr(inst, 'width', ts[0]))

		# Top row arrangement: left BoxLayout for tier, right for expiration.
		tier_row = KW.BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		tier_row.add_widget(tier_label)
		#tier_row.add_widget(tier_icon)
		tier_row.add_widget(spacer_box)
		tier_row.add_widget(expiration_label)

		# Updated Anlas Row (single row: label left aligned, SVG right after)
		anlas_label = KW.Label(text="Subscription+Paid Anlas: N/A", halign='left', height=GS.UI_field_height, size_hint = (None, None))
		anlas_label.bind(texture_size=lambda inst, ts: setattr(inst, 'width', ts[0]))
		#anlas_icon = KW.SvgWidget(GS.FULL_DIR + "GenerationProviders/Resources/NovelAI/Assets/anlas.svg", height=GS.UI_field_height)
		anlas_row = KW.BoxLayout(orientation='horizontal', size_hint_y=None, height=GS.UI_field_height)
		anlas_row.add_widget(anlas_label)
		#anlas_row.add_widget(anlas_icon)

		# Add all rows to the main subscription layout.
		subscription_layout.add_widget(tier_row)
		subscription_layout.add_widget(anlas_row)

		# Append to the list of UI widgets (assuming self.widgets is a list of added widgets)
		self.widgets.append(subscription_layout)

		# --- Update Function ---
		def update_subscription_info(instance, new_state):
			"""
			Update the subscription layout based on new_state, which is the raw dict received.
			"""
			# Get the subscription tier and look up its display values.
			tier = new_state.get('tier', None)
			if tier is not None and tier in self.CONSTANTS['SUB_TIERS']:
				display_string, svg_path = self.CONSTANTS['SUB_TIERS'][tier]
				tier_label.text = f"Sub Tier: {display_string}"
				Clock.schedule_once(lambda dt: tier_icon.set_svg(svg_path))
			else:
				tier_label.text = "Sub Tier: N/A"
				Clock.schedule_once(lambda dt: tier_icon.set_svg(""))

			# Format the expiration date.
			expires_timestamp = new_state.get('expiresAt', None)
			if expires_timestamp:
				import datetime
				formatted_date = datetime.datetime.fromtimestamp(expires_timestamp).strftime(GS.date_format)
				expiration_label.text = f"Expires at: {formatted_date}"
			else:
				expiration_label.text = "Expires at: N/A"

			# Update the available Anlas info.
			training_steps = new_state.get('trainingStepsLeft', {})
			sub_anlas = training_steps.get('fixedTrainingStepsLeft', 0)
			paid_anlas = training_steps.get('purchasedTrainingSteps', 0)
			anlas_label.text = f"Subscription+Paid Anlas: {sub_anlas}+{paid_anlas}"
			
		# Bind the update function to the subscription state property.
		GS.NAI.bind(subscription_state=update_subscription_info)

		GS.MAIN_APP.meta_layout.add_widget(subscription_layout, 0)
		
		GS.hide_widgets(self.widgets)

	# switch_to is called when the provider is called, and as such needs to unhide its elements and do anything else needed to prepare working with it
	@handle_exceptions
	def switch_to(self):
		if GS.MODULE_FACTORY.selected_provider != self:
			try:
				GS.MODULE_FACTORY.selected_provider.switch_from()
			except:
				pass
				
			GS.MAIN_APP.resolution_selector.resolution_width.combo_cap = self.CONSTANTS['MAX_RES']
			GS.MAIN_APP.resolution_selector.resolution_height.combo_cap = self.CONSTANTS['MAX_RES']
			GS.MAIN_APP.model_button.text = list(self.CONSTANTS['MODELS'])[0]
			GS.MAIN_APP.prompt_token_counter.token_calculator = self.clip_calculator
			GS.MAIN_APP.uc_token_counter.token_calculator = self.clip_calculator
			GS.MAIN_APP.prompt_token_counter.max_token_count = self.CONSTANTS['MAX_TOKEN_COUNT']
			GS.MAIN_APP.uc_token_counter.max_token_count = self.CONSTANTS['MAX_TOKEN_COUNT']
			GS.MAIN_APP.decrisp_guidance_input.disabled = True
			GS.MAIN_APP.decrisp_percentile_input.disabled = True
			GS.MAIN_APP.wait_time_input.min_value = 1
			if float(GS.MAIN_APP.wait_time_input.text) < 1:
				GS.MAIN_APP.wait_time_input.text = str(1)

			GS.unhide_widgets(self.widgets)
			GS.MODULE_FACTORY.hide_other_providers(self)
			GS.MODULE_FACTORY.selected_provider = self
			GS.MAIN_APP.generation_provider_button.text = self.name

	# switch_from is called when the provider is disabled in favor of another one, and as such needs to hide its elements again and reverse other changes that switch_to made
	@handle_exceptions
	def switch_from(self):
			GS.MAIN_APP.decrisp_guidance_input.disabled = False
			GS.MAIN_APP.decrisp_percentile_input.disabled = False
			GS.MAIN_APP.wait_time_input.min_value = math.inf

	# ---Generating Functions---

	# This function is responsible for adding all the provider specific settings into the settings dict when queueing any task or generating single images
	@handle_exceptions
	def update_settings(self):
		update_dict = {
			'sigma_thresholding_type': GS.MAIN_APP.sigma_thresholding_button.text,
			'sigma_thresholding_skip_above': GS.MAIN_APP.sigma_thresholding_skip_above_input.text,
		}
		return update_dict

	# This function is needed to process any f-strings in fields that the provider might be using
	@handle_exceptions
	def f_processor(self, settings, img_settings, var_dict):
		img_settings["sigma_thresholding_skip_above"] = float(TM.f_string_processor(settings["sigma_thresholding_skip_above"], settings["meta"]["eval_guard"], var_dict))

	# form_prompt takes the settings and reformats them so the provider can generate an image with them
	# Should be at least mostly in alignment with: https://image.novelai.net/docs/index.html
	@handle_exceptions
	def form_prompt(self, settings):
		#if settings["dynamic_thresholding_percentile"] <= 0:
		#	settings["dynamic_thresholding_percentile"] = 0.000001
		#	print("[Warning] Dynamic thresholding percentile too low, adjusting to 0.000001, check your settings")
		#elif settings["dynamic_thresholding_percentile"] > 1:
		#	settings["dynamic_thresholding_percentile"] = 1
		#	print("[Warning] Dynamic thresholding percentile too high, adjusting to 1, check your settings")
		json_construct={
			#This is the prompt, Quality Tags are not configured separately and net to be appended here manually
			'input': settings["prompt"],
			#Model as in UI (Curated/Full/Furry)
			'model': settings["model"],
			'parameters': {
				#Seed as in UI
				'seed': int(settings["seed"]),
				#Undesired Content as in UI
				'negative_prompt': settings["negative_prompt"],
				#Image Width as in UI
				'width': settings["img_mode"]["width"],
				#Image Height as in UI
				'height': settings["img_mode"]["height"],	
				'n_samples': settings.get('n_samples', 1), # Integer, handling of multiple images at once is currently NOT supported, and likely will not be due to need for fine control
				#Sampler as in UI
				'sampler': settings["sampler"],
				#Noise Schedule as in UI
				'noise_schedule': settings["noise_schedule"],
				#Guidance as in UI
				'scale': settings["scale"],
				#Prompt Guidance Rescale as in UI
				'cfg_rescale': settings["guidance_rescale"],
				#Steps as in UI
				'steps': settings["steps"],
				'sm': settings["smea"],
				'sm_dyn': settings["dyn"],
				# Decrisper
				'dynamic_thresholding': settings.get('dynamic_thresholding', False),
				'qualityToggle': settings.get('qualityToggle', False),
				
				
				'deliberate_euler_ancestral_bug': settings.get('deliberate_euler_ancestral_bug', False),
				**({'skip_cfg_above_sigma': None} if settings.get('sigma_thresholding_type', 'Off') == 'Off' else {}),
				**({'skip_cfg_above_sigma': self.variety_plus(settings["img_mode"]["height"], settings["img_mode"]["width"])} if settings.get('sigma_thresholding_type', 'Off') == 'Variety+' else {}),
				**({'skip_cfg_above_sigma': settings.get('sigma_thresholding_skip_above')} if settings.get('sigma_thresholding_type', 'Off') == 'Manual' else {}),
				
				#'prefer_brownian': settings.get('prefer_brownian', False),
				#'legacy': settings.get('legacy', False),
				#'legacy_v3_extend': settings.get('legacy_v3_extend', False),
				#'cfg_sched_eligibility': settings.get('cfg_sched_eligibility', 'enable_for_post_summer_samplers'), # String, and very unknown and unclear purpose
				#'explike_fine_detail': settings.get('explike_fine_detail', False), # Boolean, unknown purpose
				#'minimize_sigma_inf': settings.get('minimize_sigma_inf', False), # Boolean, unknown purpose
				#'uncond_per_vibe': settings.get('uncond_per_vibe', True), # Boolean
				#'wonky_vibe_correlation': settings.get('wonky_vibe_correlation', True), # Boolean
				#'version': 1, # No idea what this value precisely does
				#'params_version': 1, # This isn't being returned with images, but is listed in the swagger list, probably meant to be the same as above?
				
				# These variables seem to have been axed
				# These are settings for the decrisper that are NOT visible on the website, are nowadays deliberately ignored, but need to be passed otherwise their server fails to generate
				'dynamic_thresholding_mimic_scale': settings.get('dynamic_thresholding_mimic_scale', 10),
				'dynamic_thresholding_percentile': settings.get('dynamic_thresholding_percentile', 0.999),
			}
		}
		# Handle img2img
		if settings.get('img2img'):
			json_construct['action'] = "img2img"
			json_construct['parameters'].update(settings["img2img"])

		# Handle vibe transfer
		if settings.get('vibe_transfer'):
			vt_dict = {
				'reference_image_multiple': [],
				'reference_information_extracted_multiple': [],
				'reference_strength_multiple': []
			}
			
			for vt_item in settings["vibe_transfer"]:
				vt_dict['reference_image_multiple'].append(vt_item['image'])
				vt_dict['reference_information_extracted_multiple'].append(vt_item['information_extracted'])
				vt_dict['reference_strength_multiple'].append(vt_item['strength'])
			
			json_construct['parameters'].update(vt_dict)
		print(json_construct)
		return [json_construct,settings["name"]]

	# This function is excused from @handle_exceptions because it is called within a try/except loop that handles any failure and explicitly needs to do so
	@handle_exceptions
	def generate_image(self, prompt, test):
		# Choose the token based on whether we're testing.
		token = test if test else GS.NAI.AUTH

		# If a test token is provided, ensure the session is good.
		if test:
			value = self.make_NAI_session(token)
			if not value:
				return 'Error'
		# Attempt the image generation POST request.
		# We assume that GS.NAI.session already has the default Authorization header set.
		response = GS.NAI.session.post(
			self.CONSTANTS['URL_GEN_IMG'],
			data=json.dumps(prompt[0]),
			headers={
				'Content-Type': 'application/json',
				'accept': 'application/json',
			}
		)
		if test:
			if response.ok:
				return 'Success'
		
		# If the generation fails, try to reinitialize the session and retry once.
		if not response.ok:
			if not make_NAI_session(token):
				return 'Error'
			response = GS.NAI.session.post(
				self.CONSTANTS['URL_GEN_IMG'],
				data=json.dumps(prompt[0]),
				headers={
					'Content-Type': 'application/json',
					'accept': 'application/json',
				}
			)
		if response.status_code == 400 or response.status_code == 401:
			print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
			return 'Error'
		elif response.status_code == 429:
			print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
			raise ValueError('Server refused to respond with an image due to specific circumstances.')
		elif response.status_code >= 402 and response.status_code < 500:
			print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
			return 'Error'
		elif response.status_code >= 500:
			try:
				print(f'[Warning] {response.status_code} | Server message: {json.loads(response.content)["message"]}')
				return 'Error'
			except:
				print(f'[Warning] {response.status_code} | No proper server message received')
				return 'Retry'
			return 'Error'
		elif response == None:
			print(f'[Warning] Failed to get any server response')
			return 'Retry'
		return response

	@handle_exceptions
	def handle_result(self, result, filepath):
		try:
			with zipfile.ZipFile(io.BytesIO(result.content), "r") as zip_file:
				for file_name in zip_file.namelist():
					if file_name.endswith(".png"):
						with zip_file.open(file_name) as png_file:
							image_data = png_file.read()
							Clock.schedule_once(lambda dt: GS.MAIN_APP.generated_images_dropdown.add_widget(
							KW.ImageGenerationEntry(image_data, GS.MAIN_APP.show_last_generation_button.enabled, True)))
							with open(filepath, 'wb+') as t:
								t.write(image_data)
							t.close()
		except Exception as e:
			print(result)
			print(f'[Error] Failed to handle generation process result: {e}')
			raise e

	# ---Settings Functions---

	# When loading settings, this function needs to handle telling the program what model is associated with the data, which is also used to switch providers
	@handle_exceptions
	def claim_model(self, source_string):
		model = self.CONSTANTS['MODEL_MAPPING'].get(source_string, False)
		if model:
			return [self, model, self.CONSTANTS['MODELS'].get(model)]
		else:
			return False

	# Since providers will have their own types of settings that may not be handled by the main program, we need to make sure to handle those settings here
	@handle_exceptions
	def load_settings(self, file_type, settings):
		if file_type == 'py':
			FL.try_to_load('sigma_thresholding_type', GS.MAIN_APP.sigma_thresholding_button, settings, 'sigma_thresholding_type', True, 'text')
			FL.try_to_load('sigma_thresholding_skip_above', GS.MAIN_APP.sigma_thresholding_skip_above_input, settings, 'sigma_thresholding_skip_above', True, 'text')
			GS.MAIN_APP.sigma_thresholding_skip_above_input.disabled = (GS.MAIN_APP.sigma_thresholding_button == 'Manual')
		elif file_type == 'img':
			if settings.get('skip_cfg_above_sigma', False):
				if self.variety_plus(settings["height"], settings["width"]) == settings["skip_cfg_above_sigma"]:
					GS.MAIN_APP.sigma_thresholding_button.text = "Variety+"
					GS.MAIN_APP.sigma_thresholding_skip_above_input.disabled = True
				else:
					GS.MAIN_APP.sigma_thresholding_button.text = "Manual"
					GS.MAIN_APP.sigma_thresholding_skip_above_input.disabled = False
					FL.try_to_load('sigma_thresholding_skip_above', GS.MAIN_APP.sigma_thresholding_skip_above_input, settings, 'skip_cfg_above_sigma', True, 'text')
			else:
				GS.MAIN_APP.sigma_thresholding_button.text = "Off"
				GS.MAIN_APP.sigma_thresholding_skip_above_input.disabled = True

	# ---Optional Functions---

	# exit_cleanup is excused from @handle_exceptions as it doesn't work really anymore after the program is terminated
	# Debug print statements only work here when directly using the console instance
	def exit_cleanup(self):
		GS.NAI.session.close()

	# ---Provider-specific Functions---

	# This is the code that NovelAI uses to calculate the according value for Variety+, while skip_cfg_below_sigma is now deprecated and ignored by the API
	@handle_exceptions
	def variety_plus(self, height, width):
		reference_size = (1216//8, 832//8)
		desired_size = (height//8, width//8)
		snr_coeff = (math.prod(desired_size) / math.prod(reference_size))**.5
		skip_cfg_above_sigma=19 * snr_coeff
		return skip_cfg_above_sigma

	# This function is called when trying to set a new token, and as such needs to contain valid testing settings, which should be very lightweight
	@handle_exceptions
	def process_token(self, instance):
		token = self.token_input.text
		match = re.search(r'"auth_token":"([^"]+)"', token)
		if match:
			token = match.group(1)
		Clock.schedule_once(lambda dt: self.update_token_state('Pending'))
		future = GS.EXECUTOR.submit(lambda: self.process_token_callback(
			self.make_NAI_session(token),
			token
		))
		

	# The above function runs in a separate thread to not block the main thread, and will call this function with the result
	@handle_exceptions
	def process_token_callback(self, result, token):
		if result:
			self.token_input.text = token
			token_file_content = f"""#Only the access token goes into this file. Do not share it with anyone else as that's against NAI ToS. Using it on multiple of your own devices is fine.
AUTH='{token}'
"""
			CH.write_config_file(os.path.join(GS.SETTINGS_DIR, "3.Token(DO NOT SHARE).py"),token_file_content)
			GS.NAI.AUTH = token
		Clock.schedule_once(lambda dt: self.update_token_state(result))

	# Finally we do this in a separate function so we can schedule it for a clean UI update showing if the token passed the check or not
	@handle_exceptions
	def update_token_state(self,state):
		if state==True:
			self.token_state.update_color(None)
			self.token_state.text = '✔️'
		elif state=='Pending':
			self.token_state.update_color(None)
			self.token_state.text = '❓'
		else:
			self.token_state.update_color(None)
			self.token_state.text = '❌'

	@handle_exceptions
	def update_subscription_state(self):
		response = GS.NAI.session.get(self.CONSTANTS["URL_API"] + "/user/subscription", timeout=5)
		print(f'NAI subscription response: {response}') if GS.verbose else None
		if response.ok:
			GS.NAI.subscription_state = response.json()
			return response
		else:
			print(f'[Warning] Failed to get subscription state: {response.body}')
			return False

	# Gets a working session or makes a new one if the current one fails to return an ok, but does not check it afterwards
	@handle_exceptions
	def make_NAI_session(self, token=False):
		"""
		Returns a valid requests.Session() for the NovelAI API.
		If the global session is missing or nonfunctional, a new one is created.
		"""
		if not token:
			# Check if the session exists and is functional.
			if GS.NAI.session is not None:
				try:
					# Make a lightweight HEAD request and check the response.
					response = self.update_subscription_state()
					if response.ok:
						return True
				except Exception:
					pass
			elif GS.NAI.AUTH:
				token = GS.NAI.AUTH
			else:
				return False
		# Either there was no session or it failed the HEAD check.
		GS.NAI.session = requests.Session()
		GS.NAI.session.headers.update({'Authorization': f'Bearer {token}'})
		try:
			# Make a lightweight HEAD request and check the response.
			response = self.update_subscription_state()
			if response.ok:
				return True
			else:
				print('[Warning] Failed to create session with the NAI server, check your token.')
				return False
		except Exception:
			print('[Warning] Failed to create session with the NAI server, check your token.')
			return False

class NAIState(EventDispatcher):
	subscription_state = DictProperty({})
	AUTH = StringProperty('')
	session = None

class SMEAModButtonPair(KW.BoxLayout):
	@handle_exceptions
	def __init__(self, parent_layout, **kwargs):
		if getattr(parent_layout, 'gen_value', None) in ['ddim, ', 'plms, ']:
			self.parent_layout = None
			KW.nuke_widgets(self)
		else:
			super().__init__(orientation='horizontal', size_hint=(None, 1), width=120, **kwargs)
			self.parent_layout = parent_layout

			# Create the buttons
			self.smea_button = KW.StateShiftButton(text='SMEA', size_hint=(None, 1), width=70)
			self.dyn_button = KW.StateShiftButton(text='Dyn', size_hint=(None, 1), width=50)

			# Bind interdependent behavior
			self.smea_button.bind(
				enabled=self._handle_smea_state_change
			)
			self.dyn_button.bind(
				enabled=self._handle_dyn_state_change
			)

			# Add the buttons to this layout
			self.add_widget(self.smea_button)
			self.add_widget(self.dyn_button)
	
	@handle_exceptions
	def _handle_smea_state_change(self, instance, value):
		"""When SMEA is disabled, disable Dyn. Update parent's mod_values."""
		if not value:
			self.dyn_button.enabled = False
			self.parent_layout.mod_values['NAI_SMEA'] = ''
		else:
			self.parent_layout.mod_values['NAI_SMEA'] = '_smea'

	def _handle_dyn_state_change(self, instance, value):
		"""When Dyn is enabled, enable SMEA. Update parent's mod_values."""
		if value:
			self.smea_button.enabled = True
			self.parent_layout.mod_values['NAI_SMEA'] = '_dyn'

class CLIPCostCalculator:
	@handle_exceptions
	def __init__(self):
		self.tokenizer = NAI_CLIP_Tokenizer.SimpleTokenizer(GS.FULL_DIR + 'GenerationProviders/Resources/NovelAI/bpe_simple_vocab_16e6.txt.gz')

	@handle_exceptions
	def calculate_token_cost(self, text):
		tokens = self.tokenizer.encode(text)
		return len(tokens)

