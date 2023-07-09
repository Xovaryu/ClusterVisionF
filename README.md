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
### Version 4
#### Added Features/Changes
-Cluster sequences/videos are now possible, allowing for even more complex tasks and visualizations  
-Status reports are now time gate to improve performance and prevent hanging when quick reports otherwise would overwhelm the console (primarily when skipping many generated images)  
-Switched video generation to imageio for a couple of reasons, and made it so that videos are processed immediately and in parallel to image generation  
-Retired GenerationZone.py in favor of the GUI approach  
-Settings have been added to:  
--Switch the evaluation behavior from guarded mode without globals to raw eval(), use at your own peril  
--Pasting the last error that happened into the clipboard  
-Though some smaller improvements are still planned, a major refactoring has been performed to make the program more stable and easier to develop in the future:  
--All subfunctions are decorated to prevent halting the program when issues arise, and issues are reported better, so the program should be much harder to break and easier to debug now  
--The program has been split into more modules  
--All wildcard imports were removed  
--A beginning has been made to give each file a detailed manifest of its contents and purpose  
--A global state class has been introduced to facilitate communication between different parts more efficiently and clearly  
--Comments have been put liberally into all files to briefly describe all functions  
--Renamed the program to ClusterVisionF so it actually has a sensical name more in line with what it does and what it's for  
--Improved checking of settings for critical missing information  

#### Bug Fixes
-The widget hiding function has been adjusted so it can't accidentally permanently disable any elements anymore  
-Fixed an issue when generating subcollages that have only one image  
-Fixed the console markup issue  
-Text with special symbols (at least confirmed under Windows) would fail to copy, the fix is a hacky overwrite of a Kivy class method however because the bug is in Kivy, it has been reported accordingly  

### Known Issues
-Cancelling a running queue doesn't end video generation gracefully, and doesn't reset the visual state of the play/pause button (should be cosmetic issues only)  
-Although video generation has been improved, options, especially for quality, still have to be properly integrated  
-Selecting any part of text also visually affects the token counter, this bug is seemingly purely visual  
-Windows currently always start native resolution and ignore the resolution set in build(), which is almost certainly a Kivy issue  
-Prompt injecting doesn't work as intended for f-string prompts  
-Backspaces in evaluated parts of prompts do not work properly, this is an issue with Python that will be fixed in 3.12, until then a BS constant is available  
