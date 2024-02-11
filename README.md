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
Once you have the folder set up with the files, run main.py, and set your token in the settings window (small gear icon in the upper left corner). To do that, fetch your authorization string from the NovelAI website (example process in Firefox would be "F12 → Storage → Local Storage → https://novelai.net → session → right-click on the field on the right and copy"), then put the entire string into the field and click "Set Token".
GenerationZone.py is in need of an update for now, and will likely have you run into trouble running it.  
This is the UI you can expect:
![Image](https://cdn.discordapp.com/attachments/1074334168378519622/1088219244803666052/image.png)
(There will be support for changing themes directly in the program later. After running the file once you can also edit "3.Theme.py" to your liking.)
## Example Outputs
Video:
[![Video](https://img.youtube.com/vi/XZLiKBt1J_I/maxresdefault.jpg)](https://www.youtube.com/watch?v=XZLiKBt1J_I)
Cluster Collage:
![Image](https://cdn.discordapp.com/attachments/1074334168378519622/1088222376023556197/MultiMonsterGirlDemonstration_CollageClusterk_dpmpp_2m_smea.jpg)

## Prerequisites
- Python 3.10 (other versions may or may not work)  
- The following packages (installable via PIP): requests, pillow, numpy, imageio, imageio[pyav], fontTools, kivy, transformers  

## Support me?
This tool is and will remain completely free to use, but if you could spare a bit of support that would be appreciated: https://www.patreon.com/Xovaryu (mild NSFW/18+ warning)  
I also have a discord server where I organize all my AI image generation endeavors including using this and other tools to try and gain a deeper understanding for certain characteristics of NAID, where we can share our results and so on: https://discord.gg/xJTwDVBa5b

## Change Log
### Version 5.2
#### Additions/Features
-Added support for NAI's new Guidance Rescale feature  
-Added support for NAI's new metadata format  
-Themes are now properly supported from within the GUI, there are a couple default themes to pick from, and there are a few more options for coloring  

#### Changes
-Set V3 as the default model  
-Renamed Scale into Guidance, as NAI did, though deliberately only partially  
-Adjusted the config popup size slightly to allow clicking outside to close it  
-Implemented better error messages and a small popup when trying to set the token  
-Migrated settings and themes into a new folder to prevent clutter now that themes are supported  
-Substantially streamlined and futureproofed the once frankly clumsy and ugly way of applying themes  
-Migrated all the file loading into its own module since it's now at over 300 lines of code, also improved file loading a lot  
-Improved configuration handling a lot  
-Optimized ScrollDropDownButton code to be smarter and a lot more capable to enable the theme color dropdown to scroll too  

#### Bug Fixes
-Images made via inpainting are now also correctly detected as coming from V3  
-Name and folder name fields now accept a sane number range from -100000 to 100000  
-I borked the token test function when introducing new variables, it should work again  
-Fixed int scrolling inputs getting stuck in an invalid float state when applying increments with division  

### Known Issues
-The negative prompt strength field does currently not work for cluster collages and f-strings, and there might be other hard to reproduce issues  
-Selecting any part of text also visually affects the token counter, this bug is seemingly purely visual  
-Windows currently always starts CVF at native resolution  
-\ in evaluated parts of prompts don't work properly, this is a Python issue that should be fixed in 3.12 (which Torch doesn't support anytime soon), until then a BS constant is available  
-Although video generation has been improved, There's a semi-random failure affecting video generation at times, and video generation is still plain inadequate  

## NovelAI's Terms of Service
This UI is compliant with NAI's ToS (https://novelai.net/terms), and the devs are well aware of this UI.  
But you may want to be aware of 9.1.6 in their terms specifically, which disallows using automated systems to put excessive strain on their services. Just as using an autoclicker on their web UI may get you limited and banned so might using CVF as a glorified autoclicker get you banned. As a general rule of thumb, generate in a sane manner you might manually, do not generate all day... you know, the obvious, don't take the free Opus generations and go on a rampage. CVF's purpose is to generate insightful high quality data and to make your generations count, not to dig for raw quantity.
