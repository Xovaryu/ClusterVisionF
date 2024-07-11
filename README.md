# ClusterVisionF

## Features
The purpose of ClusterVisionF at its core is a little different than what you get with other UIs, it's not merely to produce images as if the generating AI models are well known and understood, but also to generate high-quality comparable data to understand them in the first place. It's meant to aid in research and learning how to properly generate in the first place. To this end CVF's inputs such as text inputs aren't merely "dumb" text inputs, but programmable. Say you have an image and want to see it in different scales? Make scale a variable and get an image sequence or collage. But well, this is something you can, to a point, also do with other UIs. CVF can create sequences and collages with nigh arbitrary conditions and complexity.
Want a collage of an image that's the same except a part of the prompt, such as a species term? A direct comparison of monster girls? Just write a little list.
Want to make an XY collage where one axis is the scale and another is a list such as above? No problem.
Want to compare multiple images with slightly or totally different prompts on the same seed and across different seeds at once? You can make a cluster collage like that with virtually no extra work.
Want to make a sequence/video of cluster collages with that level of complexity but then changing steps/scale/whatever you want over time? Sure. If you can think of the conditions and relations you wanna test, there is a pretty solid chance CVF can do it, and without you having to create a ton of images while adjusting the settings yourself all the time.
The limit isn't quite the sky, but rather Python's f-strings.

## Usage
Currently this UI also needs an active NovelAI subscription, so keep that in mind (there is a hint about NAI's ToS at the end of this README).  
A full local Stable Diffusion integration is planned, and other APIs may be added as well... should I ever get wind of another online service that can be and would be valuable to integrate.
Currently you can either subscribe to my Patreon page (5$) to get a .zip with a single executable file (plus the necessary fonts folder) or run this repo manually. Both versions are functionally the same. Though CVF should properly support Linux and Mac as well, I currently lack the fiscal means to test that and ensure support.
If you opt to run this repo yourself, set up python and the dependencies as mentioned below. I strongly recommend Python 3.10. Other version may or may not work. Once Torch is actually used for SD other versions will almost certainly not work until Torch supports higher versions.
Clone/download the files from this repository to your preferred folder.
Once you have the folder set up with the files, run main.py, and set your token in the settings window (small gear icon in the upper left corner). To do that, fetch your authorization string from the NovelAI website, the gear icon to open User Settings, then Account, then "Get Persistent API Token", then put the entire string into the field and click "Set Token". You could also grab temporary tokens from the website via your browser's network tab but this is not recommended.
This is the UI you can expect, themes can be changed within the program:
![Main UI](https://files.catbox.moe/uzsa53.png)
![Config UI](https://files.catbox.moe/hcx1qp.png)
## Example Outputs
Video:
[![Video](https://img.youtube.com/vi/XZLiKBt1J_I/maxresdefault.jpg)](https://www.youtube.com/watch?v=XZLiKBt1J_I)
Cluster Collage:
![Sample Cluster Collage](https://files.catbox.moe/rejfan.jpg)

## Prerequisites
- Python 3.10 (other versions may or may not work)  
- The following packages (installable via PIP): requests, pillow, numpy, imageio, imageio[pyav], fontTools, kivy, transformers  

## Support me?
This tool is and will remain completely free to use, but if you could spare a bit of support that would be appreciated: https://www.patreon.com/Xovaryu (mild NSFW/18+ warning)  
I also have a discord server where I organize all my AI image generation endeavors including using this and other tools to try and gain a deeper understanding for certain characteristics of NAID, where we can share our results and so on: https://discord.gg/xJTwDVBa5b

## Change Log
### Version 5.3
#### Additions/Features
-Overhauled the UI element for samplers to be universal for any generation mode, and to support noise schedule as well  
-This new UI element contains one small number field which is the sampler cutoff, which determines how many many samplers are in one row (0 means no limit)  
-Added support for bulk settings import, you can now drop multiple .py files and they will all be automatically added into the queue  

#### Changes
-BREAKING: Noise schedule is now always explicitly resolved. Old sampler strings without it should still work, but may use a different noise schedule than the implicit one  
-Changed default sampler to euler in line with NAI's current default  
-Changed the default value for the f-string steps input back to 28  
-Added a hidden developer dialogue for heavy-handed bug hunting  
-Slightly cleaned up handling and reporting of image metadata load failures  
-Dropped support for Flowframes (for now at least)  
-The sampler list field required exact usage of spaces, but it really shouldn't fail just because of more or less spaces, improved that  
-Fixed the case of constants/variables in GS  
-A new URL is needed to run third party NAI image generations, and the constants file with those now updates automatically  
-Added live updated trackers for the state of queued/done/skipped tasks/images  

#### Bug Fixes
-Version 5.3.1: Fixed a missing line for single image generation that would guarantee instant failure
-RAM Leak: The list that is dynamically rebuilt for the "Load Theme" button didn't get unregistered and hence the buttons lingered after each click  
-429 errors (concurrent generations) shouldn't cancel generation, and now they don't, going for a delayed retry as they should  
-Single image generations incorrectly registered a lingering image generation into the according counter, causing it to display wrong numbers  
-Removed some error reporting popup calls that could soft lock the program, the console reports those issues instead for now  
-Guidance rescale should've had a fallback value of 0, and it wasn't consistently loaded either  
-Some hidden widget like the seed grid buttons could still be inadvertently activated, adjusted the hide_widgets function further  
-Once again improved the behavior and performance of message printing to keep the application responsive even under a flood of messages  
-ScrollInputs failed to properly apply the provided rounding value, leading to cases where floating point inaccuracies still reared their ugly heads  
-For debugging purposes build() is no longer excused from using @handle_exceptions since even there some crashes can be silent...  
-Console colors now actively change too, but that only works properly when all console colors remain distinct  
-Fixed an issue that could cause steps/scale to not be shown on cluster collages  
-Very quick production of cluster collages could possibly cause uncaught issues due to parallel access to font files, those are now properly cached  

### Known Issues
-Selecting any part of text also visually affects the token counter, this bug is seemingly purely visual  
-Windows currently always starts CVF at native resolution, and Kivy's window size handling implementation is simply lacking, once Kivy 3.0.0 is a thing this will be re-visited  
-Likewise font fallback will likely be added with Kivy 3.0.0 so we'll wait for that  
-The console can sometimes blackout, this is an issue with the Label class and may also be fixed with Kivy 3.0.0 so this will be ignored for now too    
-\ in evaluated parts of prompts don't work properly, this is a Python issue that should be fixed in 3.12 (which Torch doesn't support anytime soon), until then a BS constant is available  
-Although video generation has been improved, There's a semi-random failure affecting video generation at times, and video generation is still plain inadequate  
-Stopping a paused generation pops out one last generation instead of instantly stopping  
-Many samplers may lead to too long filenames, causing cluster collages to fail saving  
-If the number of samplers isn't properly divisible by the sampler cutoff, some images will likely not show up on the cluster collage, I won't fix this but add warnings in the future  

## NovelAI's Terms of Service
This UI is compliant with NAI's ToS (https://novelai.net/terms), and the devs are well aware of this UI.  
But you may want to be aware of 9.1.6 in their terms specifically, which disallows using automated systems to put excessive strain on their services. Just as using an autoclicker on their web UI may get you limited and banned so might using CVF as a glorified autoclicker get you banned. As a general rule of thumb, generate in a sane manner you might manually, do not generate all day... you know, the obvious, don't take the free Opus generations and go on a rampage. CVF's purpose is to generate insightful high quality data and to make your generations count, not to dig for raw quantity.
