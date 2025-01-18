"""
NovelAI Diffusion.py
This provider is for base NovelAI generation similar to using SD
"""
from initialization import handle_exceptions, GlobalState
import io
import json
import zipfile
import requests
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
import kivy_widgets as KW
from GenerationProviders.Resources import NAI_CLIP_Tokenizer
GS = GlobalState()

class NAIDGenerationProvider():
	@handle_exceptions
	def __init__(self, name, **kwargs):
		self.name = name
		self.widgets = []
		self.CONSTANTS = {
			#The URL to which the requests are sent
			'URL': 'https://image.novelai.net/ai/generate-image',
			'URL_ANNOTATE': 'https://image.novelai.net/ai/annotate-image',
			
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

	# Takes the settings and reformats them for NAI's API
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
				#'skip_cfg_above_sigma': settings.get('skip_cfg_above_sigma', False),
				#'skip_cfg_below_sigma': settings.get('skip_cfg_below_sigma', False),
				
				'prefer_brownian': settings.get('prefer_brownian', False),
				'legacy': settings.get('legacy', False),
				'legacy_v3_extend': settings.get('legacy_v3_extend', False),
				'cfg_sched_eligibility': settings.get('cfg_sched_eligibility', 'enable_for_post_summer_samplers'), # String, and very unknown and unclear purpose
				'explike_fine_detail': settings.get('explike_fine_detail', False), # Boolean, unknown purpose
				'minimize_sigma_inf': settings.get('minimize_sigma_inf', False), # Boolean, unknown purpose
				'uncond_per_vibe': settings.get('uncond_per_vibe', True), # Boolean
				'wonky_vibe_correlation': settings.get('wonky_vibe_correlation', True), # Boolean
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

	@handle_exceptions
	def claim_model(self, source_string):
		model = self.CONSTANTS['MODEL_MAPPING'].get(source_string, False)
		if model:
			return [self, model, self.CONSTANTS['MODELS'].get(model)]
		else:
			return False

	# This call is excused from @handle_exceptions because it is made within a try/except loop that handles any failure and explicitly needs to do so
	def generate_image(self, prompt, test):
		api_header = f'Bearer {test if test else GS.AUTH}'
		response = requests.post(
			self.CONSTANTS['URL'], json.dumps(prompt[0]),
			headers={
				'Authorization': api_header,
				'Content-Type': 'application/json',
				'accept': 'application/json',
			}
		)
		if test and response.status_code == 200:
			return 'Success'
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
				return 'Connection Error'
			return 'Error'
		elif response == None:
			print(f'[Warning] Failed to get any server response')
			return 'Connection Error'
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

	# This is the code that NovelAI uses to calculate the according value for Variety+, while skip_cfg_below_sigma is normally 0
	@handle_exceptions
	def variety_plus(self, height, width):
		reference_size = (1216//8, 832//8)
		desired_size = (height//8, width//8)
		snr_coeff = (math.prod(desired_size) / math.prod(reference_size))**.5
		skip_cfg_above_sigma=19 * snr_coeff
		return skip_cfg_above_sigma

	@handle_exceptions
	def initialize_ui(self):
		KW.create_dropdown_entries(GS.MAIN_APP.model_dropdown, self.CONSTANTS['MODELS'], self.widgets)
		KW.create_dropdown_entries(GS.MAIN_APP.sampler_dropdown, self.CONSTANTS['SAMPLERS'], self.widgets)
		KW.create_dropdown_entries(GS.MAIN_APP.noise_schedule_dropdown, self.CONSTANTS['NOISE_SCHEDULERS'], self.widgets)
		KW.create_dropdown_entries(GS.MAIN_APP.sampler_injector_dropdown, self.CONSTANTS['SAMPLERS'], self.widgets, target_text_field=GS.MAIN_APP.sampler_input,
			extra_widget_classes=[SMEAModButtonPair], delimiter = ', ')
		KW.create_dropdown_entries(GS.MAIN_APP.prompt_dropdown, self.CONSTANTS['PROMPT_CHUNKS'], self.widgets, target_text_field=GS.MAIN_APP.prompt.input)
		KW.create_dropdown_entries(GS.MAIN_APP.uc_dropdown, self.CONSTANTS['UCS'], self.widgets, target_text_field=GS.MAIN_APP.uc.input)
		### Need to add the Variety+ things
		#sigma_thresholding_label = Label(text='Sigma Thresh.:', **GS.l_row_size)
		#GS.MAIN_APP.is_range_import = KW.ImportButton(**GS.imp_row_size)
		# Off/Variety+/Manual

		GS.hide_widgets(self.widgets)

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
			GS.MAIN_APP.generation_provider_button.text = self.name
			GS.MAIN_APP.prompt_token_counter.token_calculator = clip_calculator
			GS.MAIN_APP.uc_token_counter.token_calculator = clip_calculator
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

	@handle_exceptions
	def switch_from(self):
			GS.MAIN_APP.decrisp_guidance_input.disabled = False
			GS.MAIN_APP.decrisp_percentile_input.disabled = False
		

class SMEAModButtonPair(BoxLayout):
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
		self.tokenizer = NAI_CLIP_Tokenizer.SimpleTokenizer(GS.FULL_DIR + 'GenerationProviders/Resources/bpe_simple_vocab_16e6.txt.gz')

	@handle_exceptions
	def calculate_token_cost(self, text):
		tokens = self.tokenizer.encode(text)
		return len(tokens)
clip_calculator = CLIPCostCalculator()
