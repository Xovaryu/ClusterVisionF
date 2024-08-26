# ClusterVisionF

## Features
The purpose of ClusterVisionF at its core is a little different than what you get with other UIs, it's not merely to produce images as if the generating AI models are well known and understood, but also to generate high-quality comparable data to understand them in the first place. It's meant to aid in research and learning how to properly generate in the first place. To this end CVF's inputs such as text inputs aren't merely "dumb" text inputs, but programmable. Say you have an image and want to see it in different scales? Make scale a variable and get an image sequence or collage. But well, this is something you can, to a point, also do with other UIs. CVF can create sequences and collages with nigh arbitrary conditions and complexity.
Want a collage of an image that's the same except a part of the prompt, such as a species term? A direct comparison of monster girls? Just write a little list.
Want to make an XY collage where one axis is the scale and another is a list such as above? No problem.
Want to compare multiple images with slightly or totally different prompts on the same seed and across different seeds at once? You can make a cluster collage like that with virtually no extra work.
Want to make a sequence/video of cluster collages with that level of complexity but then changing steps/scale/whatever you want over time? Sure. If you can think of the conditions and relations you wanna test, there is a pretty solid chance CVF can do it, and without you having to create a ton of images while adjusting the settings yourself all the time.
The limit isn't quite the sky, but rather Python's f-strings.
Also CVF now has internal tooltips for fields and buttons that allow the program to explain itself at run-time with little to no need for external documentation. These tooltips can be brought up with right clicking.

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
![Tooltips/Metadata UI](https://files.catbox.moe/bffgzq.png)
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
### Version 6
#### Additions/Features
-Image2image and vibe transfer are now fully supported, this includes them being shown as thumbnails on cluster collages too  
-CVF now has a generation history, and it's capped at a user specified number of saved images  
-CVF now has a list of loaded images that persist until deleted, these can be used for i2i/VT, generated images can be loaded into that list  
-The i2i/VT state is saved into it's very own file format along with, but separate from CVF settings, this means any i2i/VT state can instantly be restored in full with just a drag'n'drop  
-What .cvfimgs contains is on a technical level a maximally zlib compressed python dict with the full images in base 64  
-CVF now also has an internal metadata reader, both generated and loaded images can be parsed for their full EXIF/alpha metadata within the program  
-The wait time between generations can now be controlled with an according field  
-There are now buttons to enable/disable all import buttons simultaneously  
-CVF now has tooltips, that means various fields and buttons will explain themselves with just a simple right click on them  

#### Changes
-Some drag'n'drop operations are now location sensitive, images dropped on the right will be loaded, while on the left they will still be scanned for metadata  
-Optimized handling of the theme colors display which should also lead to a... microscopic performance increase  
-Split settings and theme configuration apart  
-There are new values for the new tooltips in the themes, either delete old files and let them regenerate, or adjust these tooltips to your liking  
-Improved the error reporting function  
-Disabled fields for undesired content strength, mimic scale and percentile as NAID now deliberately ignores these variables  
-Scale values can be anything except 0, so the base field restrictions have been adjusted  
-Properly put the token test into its own separate thread which doesn't halt the program anymore  

#### Bug Fixes
-The counter for skipped images didn't always get properly reset  
-Removed GS.futures since I didn't actually use it and it considerably leaked into the RAM for no benefit  
-Fixed the seed grid to not leak widgets when lowering the number of seeds, though the gain is tiny  
-There was a little dumb bug that could cause settings with absolutely no UC to fail loading  
-Stopping after a pause shouldn't produce a final image anymore  
-Fixed multiple issues with how sampler strings were handled  
-Due to a simple oversight pressing C to clear seed fields still cleared the field even if the user actually used CTRL+C which was... suboptimal  
-Updated the NAID alpha metadata importing code which also fixes a hard lock bug with images too small to have alpha metadata  
-Fixed a tiny and functionally irrelevant bug when video generation is cancelled immediately  
-Improved sampler string adding  
-Tasks could still be added into a running queue via bulk queueing, but those tasks wouldn't be processed, prevented such queueing now  
-The pause button could get desynched   

### Known Issues
-Selecting any part of text also visually affects the token counter, this bug is seemingly purely visual  
-Windows currently always starts CVF at native resolution, and Kivy's window size handling implementation is simply lacking, once Kivy 3.0.0 is a thing this will be re-visited  
-Likewise font fallback will likely be added with Kivy 3.0.0 so we'll wait for that  
-The console can sometimes blackout, this is an issue with the Label class and may also be fixed with Kivy 3.0.0 so this will be ignored for now too    
-\ in evaluated parts of prompts don't work properly, this is a Python issue that should be fixed in 3.12 (which Torch doesn't support anytime soon), until then a BS constant is available  
-Video generation is still plain inadequate  
-Many samplers may lead to too long filenames, causing cluster collages to fail saving  
-If the number of samplers isn't properly divisible by the sampler cutoff, some images will likely not show up on the cluster collage, I won't fix this but add warnings in the future  
-The new options for the user settings work, but can't yet be saved and automatically reloaded  

## NovelAI's Terms of Service
This UI is compliant with NAI's ToS (https://novelai.net/terms), and the devs are well aware of this UI.  
But you may want to be aware of 9.1.6 in their terms specifically, which disallows using automated systems to put excessive strain on their services. Just as using an autoclicker on their web UI may get you limited and banned so might using CVF as a glorified autoclicker get you banned. As a general rule of thumb, generate in a sane manner you might manually, do not generate all day... you know, the obvious, don't take the free Opus generations and go on a rampage. CVF's purpose is to generate insightful high quality data and to make your generations count, not to dig for raw quantity.
