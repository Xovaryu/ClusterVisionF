# ClusterVisionF

## Prerequisites
- Python 3.10 (other versions may or may not work)  
- The following packages (installable via PIP): requests, pillow, numpy, imageio, imageio[pyav], fontTools, kivy, transformers  

## Usage
Currently this UI also needs an active NovelAI subscription, so keep that in mind (there is a hint about NAI's ToS at the end of this README).  
A full local Stable Diffusion integration is planned, and other APIs may be added as well.
You can either subscribe to my Patreon page (5$) to get a .zip with a single executable file (plus the necessary fonts folder) or run this repo manually. Both versions are functionally the same.
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
### Version 5.1
#### Additions/Features
-Support for V3 (delete 2.NAID_Constants.py before running the new version)  

#### Changes
-Upgraded Name and Folder Name fields to ScrollInputs  
-The collage dimension fields are now labeled for better immediate understanding  
-Lambda functions have now also been aggressively wrapped with exception handling to fight silent crashes further  
-The ucPreset variable hasn't been used and the API doesn't demand it so it has been removed  
-process_queue has been streamlined just a bit  
-Failure to set a model now has CVF default to V3  

#### Bug Fixes
-The negative prompt strength field should now work as intended  
-I smartly left in temporary test settings for video generation, so the frame rate was always set to 10, ignoring user input, fixed that...  

### Known Issues
-The negative prompt strength field does currently not work for cluster collages and f-strings  
-Although video generation has been improved, options, especially for quality, still have to be properly integrated  
-Selecting any part of text also visually affects the token counter, this bug is seemingly purely visual  
-Windows currently always starts CVF at native resolution and ignores the resolution set in build(), which is almost certainly a Kivy issue  
-Backspaces in evaluated parts of prompts do not work properly, this is an issue with Python that will be fixed in 3.12, until then a BS constant is available  
-The spacing in the config Window is all mucked up  
-There's a semi-random failure affecting video generation at times  

## NovelAI's Terms of Service
This UI is compliant with NAI's ToS (https://novelai.net/terms), and the devs are well aware of this UI.  
But you may want to be aware of 9.1.6 in their terms specifically, which disallows using automated systems to put excessive strain on their services. Just as using an autoclicker on their web UI may get you limited and banned so might using CVF as a glorified autoclicker get you banned. As a general rule of thumb, do not generate more than one picture at once for more than a sparse parallel images, do not generate all day... you know, the obvious, don't take the free Opus generations and go on a rampage. CVF's purpose is to generate insightful high quality data and to make your generations count, not to dig for raw quantity.
