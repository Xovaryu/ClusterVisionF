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
### Version 2
#### Added Features/Changes
-A proper task queue  
--Previously tasks from GenerationZone.py would be processed one by one as they come in, and metadata was a little lacking. Particularly when processing long lists of tasks and stopping midway this was an issue as those lists would've had to be manually adjusted. Nor was it clear how long the script might still be running. Now all tasks are first collected in a list (deque actually) and metadata about the queue is calculated. The script will then display the exact location of the current rendering image in the list (Current Task/Total Tasks | Current Task Image/Total Task Images | Current Total Image/Total Images). The function process_queue() now starts the actual processing, and accepts an integer with the number of tasks to skip. Finished rendering 10 tasks but got interrupted? process_queue(10) will get you right back on track.  
-Improved cluster collage headers  
--The previous state of cluster collage headers was barely workable, with the main issue being that many symbols wouldn't render properly. This has been fixed by implementing a rigorous system to render any written character with the first font of an arbitrarily long list. A number of standard fonts has been provided which should cover most emojis, unicode symbols as well as Asian languages. Should you require the ability to render any symbols that aren't covered by the provided fonts you can simply add your own, which can also overwrite the default fonts if desired. While there is no single "Everything Font" you can effectively build your own universally robust font by adding fallback fonts as needed. For languages I'd recommend a look at Google Noto, which is also used for providing emoji and CJK support.  
(Known issue: There's a couple outliers like the "Red Heart Emoji" `❤️` that may render incorrectly and show weird behavior... because it's actually a combined symbol. I probably could fix this issue too, but I didn't want to bother with Variation Selector-16 and its problems so far.)  
--The previous text wrapping functionality was barebones, and this has been addressed too. Now the header should always be cleanly readable, properly spaced, and just as big as it has to be. Some bugs may remain, and using a huge font wouldn't do you favors either.  
-Multithreading  
--Since the changes to the collage generation substantially increase the workload, the brunt of their creation, as well as the creation of videos which already was a little slower, will now be performed in separate threads so the image generation will proceed without interruption.  
#### Bug Fixes
-Switched settings encoding to UTF-16 to prevent corruption of characters like `🤎` which is the "Brown Heart Emoji".

### Version 2.1
#### Added Features/Changes
-Streamlined the fallback font writing system further  
-Added an experimental way to manually adjust cluster collage folder structure further  
-Changed the function definition order to place related functions closer together  
#### Bug Fixes
-Fixed a few cluster collage header bugs

### Version 2.2
#### Added Features/Changes
-Added detection for invalid access tokens  
-Improved formatting of saved settings to streamline their appearance and usability  
#### Bug Fixes
-Fixed an issue with superfluous information in saved settings  
-Fixed an issue with saved cluster collage settings, seeds wouldn't be replaced correctly, requiring manual adjustment  
-Fixed task counter for render loops  

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
