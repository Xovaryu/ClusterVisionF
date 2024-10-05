"""
NovelAI Diffusion.py
This provider is for base NovelAI generation similar to using SD
"""
from initialization import handle_exceptions, GlobalState
GS = GlobalState()
class NAIDGenerationProvider():
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
				'skip_cfg_above_sigma': settings.get('skip_cfg_above_sigma', False),
				'skip_cfg_below_sigma': settings.get('skip_cfg_below_sigma', False),
				
				'prefer_brownian': settings.get('prefer_brownian', False),
				'legacy': settings.get('legacy', False),
				'legacy_v3_extend': settings.get('legacy_v3_extend', False),
				'cfg_sched_eligibility': settings.get('cfg_sched_eligibility', 'enable_for_post_summer_samplers'), # String, and very unknown and unclear purpose
				'explike_fine_detail': settings.get('explike_fine_detail', False), # Boolean, unknown purpose
				'minimize_sigma_inf': settings.get('minimize_sigma_inf', False), # Boolean, unknown purpose
				'uncond_per_vibe': settings.get('uncond_per_vibe', True), # Boolean
				'wonky_vibe_correlation': settings.get('wonky_vibe_correlation', True), # Boolean
				'version': 1, # No idea what this value precisely does
				'params_version': 1, # This isn't being returned with images, but is listed in the swagger list, probably meant to be the same as above?
				
				# These variables seem to have been axed
				#'uncond_scale': 1,#float(settings["negative_prompt_strength"])/100,
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
		return [json_construct,settings["name"]]

	def generate_image(self, img_settings):
		# Code to interact with NAID's API to generate an image
		return generation_result

	def handle_result(self, result):
		# Handle how the result is processed or returned
		pass
