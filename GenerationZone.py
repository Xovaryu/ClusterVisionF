from ImageGenerator import *
from NAID_Tokens import *

###
# Examples&Tutorial
###

#---Image sequences and videos---

#In order to generate picture sequences and videos you'll be writing dicts with all the needed settings contained inside. That dict is passed to a function.
#Name is naturally part of how the pictures will be named.
#Most of the values here are self-explanatory, but a few of them can be addressed differently as variables in picture sequences/animation.
#Scale and Steps can either be written as a static number, or as a list with two entries like in this example.
#If so, the first entry in the list has to be the starting value and the second entry is the increment.
#Quantity is the number of pictures that will be generated, for that a range has to be used.
"""
settings={
'name':'ExampleKitsuneScale&Steps',
'folder_name':'',
'enumerator_plus':'',
'model':MODELS['Furry'],
'seed':1337,
'scale':[1.1,1],
'steps':[1,1],
'sampler':'k_euler_ancestral',
'img_mode':IMAGE_MODES['SquareNormal'],
'QT':'',
'prompt':'''kitsune monster girl,lady,lolita fashion,smile,sitting on couch''',
'UCp':'FurryNone',
'UC':'''nsfw,worst quality,low quality,what has science done,what,nightmare fuel,eldritch horror,where is your god now,why,''',
'quantity':range(28)
}
"""
#range(28) will give us 28 pictures. Ranges start with 0 and omit the last number, so this one goes from 0-27.
#The function you'll want to call with settings like these is render_loop(settings).

#The prompt and UC can be addressed differently too, but for them the usage is a little more complicated.
#A list of lists can be passed instead of a string, and the first entry in each sublist has to be a statement that can be evaluated, and returns a string.

#WARNING: Making use of eval() like this allows for a high degree of flexibility and convenience, but also means you NEED to be able to trust the string.
#By default the used eval() method doesn't have access to builtin functions and is heavily restricted. Imports aren't supported, nor are functions like str.
#As such making a concise and actually harmful string should be difficult or next to impossible. Nevertheless, don't run suspicious settings.
#Do not attempt to make image sequences with settings provided by other people unless you at least roughly understand what they do.
#Do not expose this functionality to something like a discord bot that could be used by untrusted users either, even aside from issues with NAI's ToS.
#In 99.9% of cases you will want to see nothing except for simple math in f-strings to be evaluated. Something simple like f'prompt:{1-0.01*n}',
#and most certainly not anything like __import__ or shenanigans like that. If it looks suspicious, do not copy and run it. You've been warned.
#Should you need access to builtin functions for whatever, and you really know what you're doing, you can run render_loop(settings,eval_guard=False).

#These lists are processed in order and added one by one to create the final prompt.
#Values after the first in a list can be passed and used in the eval statement in the form of prompt_list[1], prompt_list[2]... or respectively UC_list[1]...
#In order to work with the number of the current image simply use n.
#This example shows simple promptmixing, gradually replacing the "couch" with "bed".
"""
settings={
'name':'ExampleKitsunePromptMixing',
'folder_name':'',
'enumerator_plus':'',
'model':MODELS['Furry'],
'seed':1337,
'scale':11,
'steps':28,
'sampler':'k_euler_ancestral',
'img_mode':IMAGE_MODES['SquareNormal'],
'QT':'',
'prompt':[
['''f"kitsune monster girl,refined lady,gothic lolita fashion,smile,sitting on couch:{prompt_list[1]-0.01*n}"''',1],
['''f"|kitsune monster girl,refined lady,gothic lolita fashion,smile,sitting on bed:{prompt_list[1]+0.01*n}"''',0],
],
'UCp':'FurryNone',
'UC':'''nsfw,worst quality,low quality,what has science done,what,nightmare fuel,eldritch horror,where is your god now,why,''',
'quantity':range(101)
}
"""
#The range is 101, since that range goes from 0-100, so that it really starts on a value of 0 for the 1st and 1 for the 2nd prompt, ending with the inverse.

#And here's an example of adding a symbol sequence in the UC
"""
settings={
'name':'ExampleKitsuneUCSymbolSequence',
'folder_name':'',
'enumerator_plus':'',
'model':MODELS['Furry'],
'seed':1337,
'scale':11,
'steps':28,
'sampler':'k_euler_ancestral',
'img_mode':IMAGE_MODES['SquareNormal'],
'QT':'',
'prompt':'''kitsune monster girl,refined lady,gothic lolita fashion,smile,sitting on couch''',
'UCp':'FurryNone',
'UC':[
['''f"nsfw,worst quality,low quality,what has science done,what,nightmare fuel,eldritch horror,where is your god now,why,{UC_list[1]*n}"''','#']
],
'quantity':range(196)
}
"""
#f-strings and all of the operators do still work on both numbers and strings without builtin functions, and should be sufficient to get most things working.
#When an image sequence is finished you can generate videos out of it with OpenCV/Flowframes, for that look at the bottom of this file.

#---Prompt stabbing---

#Having and testing a given prompt&setting combination in the UI is nice and all, but sometimes you might want more data, and comparable at that.
#This is where prompt stabbing comes in. You can create large cluster collages with multiple generations and compare them directly.
#You can also use them to search for a better starting point to finetune a given generation.
#The settings for prompt stabbing aren't much different, but of course there are some things that work differently.
#Whereas for image sequences the seed is static, prompt stabbing is usually done across a list of seeds.
#A default list of 9 seeds exist, randomization is possible, or you can manually pass a list of seeds.
#To use the default seed list simply use: 'default'
#If you want to change the default seed list, adjust PROMPT_STABBER_DEFAULT_SEEDS in NAID_config.py
#To use randomized seeds, use a list formatted like this: ['random',[2,2]].
#The first number determines the amount of rows, the second the amount of columns.
#If you want to use different specific list, pass a list of lists, where the sublists make up the rows.
#A square setup with 9 seeds would look like this:
#[[1,2,3],
#[4,5,6],
#[7,8,9]]
#And a rectangle with 8 seeds could look like this:
#[[1,2,3,4],
#[5,6,7,8]]
#Instead of quantity, cluster collages need a collage_width variable. Each subcollage needs such a width which also doubles as it's height.
#This collage_width determines the amount of pictures per seed and gives collage_width^2 pictures. So that'd be 4 pictures at width 2, and 9 with width 3.
#While of course the prompt and UC will be static, scale and steps can be variable.
#Unlike in sequences where you give a starting point and an increment, for prompt stabbing you specify a start and an end.
#So assuming you have a collage_width of 2, so 4 pictures per seed, and set scale to [2,8], then the 4 pictures will have scales 2, 4, 6 and 8.
"""
settings={
'name':'ExampleKitsunePromptStab',
'folder_name':'',
'enumerator_plus':'',
'model':MODELS['Furry'],
'seed':'default',
'scale':[2,18],
'steps':[2,28],
'sampler':'k_euler_ancestral',
'img_mode':IMAGE_MODES['SquareNormal'],
'QT':'',
'prompt':'''kitsune monster girl,lady,lolita fashion,smile,sitting on couch''',
'UCp':'FurryNone',
'UC':'''nsfw,worst quality,low quality,what has science done,what,nightmare fuel,eldritch horror,where is your god now,why,''',
'collage_width':3
}
"""
#There is a different function for promptstabbing, prompt_stabber(settings).

#Stay safe, have some fun and generate some greatness.

###
#Execution area
###
start=time.time()

#Variables: Everything that determines your output belongs here, and will be saved along with the generations

settings={
'name':'ExampleKitsuneScale&Steps',
'folder_name':'',
'enumerator_plus':'',
'model':MODELS['Furry'],
'seed':1337,
'scale':[1.1,1],
'steps':[1,1],
'sampler':'k_euler_ancestral',
'img_mode':IMAGE_MODES['SquareNormal'],
'QT':'',
'prompt':'''kitsune monster girl,lady,lolita fashion,smile,sitting on couch''',
'UCp':'FurryNone',
'UC':'''nsfw,worst quality,low quality,what has science done,what,nightmare fuel,eldritch horror,where is your god now,why,''',
'quantity':range(28)
}
render_loop(settings)
#prompt_stabber(settings)

#Assuming you have OpenCV/Flowframes installed you can uncomment the following lines to turn creations into videos after they're finished.
#Keep in mind that you may have to switch between name/folder_name depending on your settings
#make_vid(settings['name'],fps=7)
#interpolate_vid(settings['name'],factor=4,output_mode=2)
#make_interpolated_vid(settings['name'])

debriefing()
print(f'Total Execution Time: {round(time.time()-start,3)}s')
print(f'Total Execution Time: {round((time.time()-start)/60,3)}m')
print(f'Total Execution Time: {round((time.time()-start)/3600,3)}h')