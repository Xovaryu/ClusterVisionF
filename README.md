# ClusterVisionF

## Prerequisites
- Image sequences, standard videos made from the former, and cluster collages require a functional Python 3 installation and the following packages easily installable via PIP: requests, pillow, numpy, imageio, imageio[pyav], fontTools, kivy, transformers

## Usage
You can either subscribe to my Patreon page (5$) to get a .zip with a single executable file (plus the necessary fonts folder) or run this repo manually. Both versions are functionally the same. Currently this UI also needs an active NovelAI subscription. A full local Stable Diffusion integration is planned, and other APIs may be added as well.
If you opt to run this repo yourself, set up python and the dependencies as mentioned above. I strongly recommend Python 3.10. Other version may or may not work.
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

## Support me?
This tool is and will remain completely free to use, but if you could spare a bit of support that would be appreciated: https://www.patreon.com/Xovaryu (mild NSFW/18+ warning)  
I also have a discord server where I organize all my AI image generation endeavors including using this and other tools to try and gain a deeper understanding for certain characteristics of NAID, where we can share our results and so on: https://discord.gg/xJTwDVBa5b

## Change Log
### Version 5
#### Additions/Features
-Seed fields can now be randomized/cleared individually by pressing `r`/`c` in the desired field  
-Seed fields can now also be filled with the last two seeds that were used to generate images, using `l` for the last seed and `p` for the previous one  
-Introduced a new variable `s` for cluster collages, which is an index of all the provided seeds  
-All fields that support f-strings now allow placing the special f-string braces around the cursor when pressing CTRL+SHIFT+F  
-ScrollInput fields now can adjust any contained selected number even if there's text, and will automatically search the first number if needed  
-NAI Diffusion Anime V2 is now selectable as a model  
-NovelAI's Undesired Content Strength is now available in the UI  

#### Changes
-WARNING: NovelAI has released a new model and changed the naming of resolutions, so delete "2.NAID_Constants.py"  
-WARNING: Themes have gotten a slightly overhauled format, the old "3.Theme.py" file is hence outdated, rewrite or simply delete it  
-The default resolution is now 1024x1024 in line with the newest bigger free resolution  
-NovelAI has made permanent API tokens available under User Settings→Account→Get Persistent API Token, they can be inserted in the UI as before  
-The console now also supports color coded warnings  
-More refactoring, moved the kivy widgets into their own file and created the according manifest  
-The scale/steps fields are now using their f-string version by default  
-Streamlined StateFButton and its use, as well as PREVIEW_QUEUE (which is probably to be nuked some other update)  
-Stripped away a number of functions in image_generator.py in favor of in-place lambda bindings  
-Deprecated and removed the debriefing function  

#### Bug Fixes
-Failure to copy strings with certain symbols (This was a Kivy fault, has been reported by me and has a fix pending made by someone else)  
-There was another oversight leading to a memory leak when making cluster sequences but not videos  
-Video processing is now cancelled gracefully  
-The persisting image generation loop now works properly and can be cancelled properly  
-If a setting can't be imported from a previous image it was left as it is, which can cause problems in some cases, so far 2 needed fallbacks were added  
-Made it so that if the decrisper/dynamic thresholding is disabled, the according variables are set to None, which shouldn't be necessary, but was in a fringe case  
-Added traceback to the image loop since it would only report that it's retrying, but not the error that caused it, which is okay for connection issues, but not when I messed up  
-Image sequences actually didn't even appropriately try to evaluate f-strings for the decrisper, fixed  

### Known Issues
-Although video generation has been improved, options, especially for quality, still have to be properly integrated  
-Selecting any part of text also visually affects the token counter, this bug is seemingly purely visual  
-Windows currently always starts CVF at native resolution and ignores the resolution set in build(), which is almost certainly a Kivy issue  
-Backspaces in evaluated parts of prompts do not work properly, this is an issue with Python that will be fixed in 3.12, until then a BS constant is available  
-The spacing in the config Window is all mucked up  
