# NovelAIDiffusion-API

## Prerequisites
- Image sequences, standard videos made from the former, and cluster collages require a functional Python 3 installation and the following packages easily installable via PIP: requests, pillow, numpy, opencv-python, fonttools, kivy, transformers

## Usage
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
I also have a discord server where I organize all my AI image generation endeavors including using this and other tools to try and gain a deeper understanding for certain characteristics of NAID, where we can share our results and so on: https://discord.gg/xJTwDVBa5b (again, NSFW/18+ warning)

## Change Log
### Version 3
#### Added Features/Changes
-Addition of a Kivy GUI  
-f-string support in cluster collages  
-Support for multiple samplers in cluster collages  
-Improved fallback font writer for cluster collages  
-Unified handling of scales/steps for cluster collages and image sequences  
-Revamped configuration handling  
-Deprecated the old way of handling QT/UC in favor of prompt chunks  

#### Breaking Changes
-Image sequence quantity is now saved as a two int list instead of range to work with literal_eval  
-nai_smea and nai_smea_dyn are deprecated names for the accordingly adjusted k_euler_ancestral sampler with SMEA/Dyn (the API is addressed with two bools, but the script now uses _smea or _dyn as suffixes for all qualifying samplers)  
-f-string formatting has been substantially changed to make it work with the UI  
-Flowframes support is broken for the time being  

#### Known Issues
-GenerationZone.py is in disrepair for now and needs an update in the future  
-The way the console in the UI is proned causes markup error messages and may discolor the first messages  
-Backspaces in evaluated parts of prompts do not work properly, this is an issue with Python that will be fixed in 3.12, until then a BS constant is available  

### Version 3.0.1
#### Added Features/Changes
-Switched to NAI's new API, which means that sampler PLMS is not available anymore while adding some new ones. There's also a number of other related silent needed changes  
-Improved `SeedGrid`. Changed handling of grid size to use scrolling inputs and removed the according buttons. Added a clear button to wipe all fields so they will be randomized when adding a task into the queue  
-Added max variants of Square/Portrait/Landscape resolutions, specified in "1.User_Settings", delete the file or add the values manually if you want them available  

#### Breaking Changes
-IMPORTANT: "2.NAID_Constants.py" needs to be edited or deleted due to the updated sampler lists and a small issue with Wallpaper resolutions  

#### Bug Fixes
-Fixed import of files with sampler defined as nai_smea or nai_smea_dyn  
-Fixed some possibly malformed settings being queued (empty CC sampler field or prompt)  
-Fixed a bug that would reset resolution values to their min value when entering the text field and leaving it  
-Fixed an issue where not accepting steps/scale lists with single images might cause settings with two different steps/scale values to fail. Lists are now accepted even if only 1 value is needed  
-Fixed the Landscape/Portrait Wallpaper resolutions  
-Fixed Furry v1.3 not being correctly detected  
