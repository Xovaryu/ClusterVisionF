"""
documentation.py
This module contains the text CVF uses to explain itself
"""
TOOLTIPS = {
	'F-Input':
'''This is a text field that interprets its contents as a F-string, the F in ClusterVisionF. You can read up on how they work in more detail here: [u][ref=https://docs.python.org/3/reference/lexical_analysis.html#f-strings]Python docs - F-strings[/ref][/u]
The short explanation is that you can let parts of the strings in these fields be evaluated, allowing you to make sequences and collages with just about any conditions you can think of.
Within this program the evaluated parts of your string aren't enclosed in {curly}, but rather ⁅quilled⁆ braces, which are then re-interpreted. This is so that curly braces can still be used in NAI for strengthening with no hassle.
So for instance if you write "2*4" here, the final text CVF will use is just "2*4", however "⁅2*4⁆" will pass through as the calculated value "8".
Most operations you might want to do are fairly simple, you could make an image sequence with 10 different scale values, then you could write "⁅10+1*n⁆" in the scale input. But if you want to use a logistic function? You can.
Maybe you want to dynamically adjust the prompt? "⁅['fox','cat','dog'][n]⁆ monster girl" will give you the three prompts "fox/cat/dog monster girl" respectively.
By default the following variables will be usable: n for number, c for column, r for row, cc for cluster collage and s for seed. Do note that these values are integers starting at 0.
n is available in all modes, when making image sequences this is simply the number of the image/frame, in cluster collages/sequences n is the number of the image within its cluster going left to right, top to bottom
c is available in both cluster modes, and enumerates images according to the column they are in, or going along the x-axis, to the right
r is available in both cluster modes, and enumerates images according to the row they are in, or going along the y-axis, downwards
s is available in both cluster modes, and enumerates the seed clusters, in case you want to each seed cluster evaluated differently
cc is exclusive to cluster sequences and is the number of each individual cluster collage, which means that for cluster sequences cc acts like n does for image sequences
By default strings are evaluated without __builtins__ for your safety, this means that pretty much only the most basic expressions will work such as addition or multiplication, and only extreme malicious code should be able to run.
You can enable __builtins__ per session in the settings if you really need to. Also you always have modules math and numpy (as np) available, so you could write something like "⁅np.exp(1)⁆". See: [u][ref=https://numpy.org/doc/stable/reference]Numpy Reference[/ref][/u]
Should you ever need a \ (backslash) in an F-Input field, use the provided BS constant like this "⁅BS⁆" = "\". This is an issue with python 3.10 and will only be addressed in 3.12.
Also a small warning, while you can use an arbitrary number of double quotes (""""⁅...⁆""") in the non-evaluated parts, three of them at once in the evaluated part (⁅"""⁆) will make evaluation fail.
CTRL+SHIFT+F: Last but not least, this key combination can be used in any F-Input field to give you the quilled braces''',
	'Scroll-Input':
"""This field supports hover scrolling to change it's values. Where applicable you are able to select text to scroll numbers only in your selection, and hybrid text inputs such as F-Inputs will search for the first scrollable number without selection.
Further you can hold down buttons on the keyboard to adjust the value by which you scroll numbers on the fly as follows:
CTRL: ×10
SHIFT: ×100
CTRL+SHIFT: ×1000
ALT: ÷10
ALT+CTRL: ÷100
ALT+SHIFT: ÷1000""",
	'Resolution Scroll-Input':
"""These specialized scroll input fields support hover scrolling to change their values, have an increment of 64 and control the output resolution of your image(s). They are set up to never allow any invalid values.
With NAID Opus the highest free resolution you can generate at is 1024×1024 or any other resolutions with less pixels total.""",
	'Steps':
"""Your image gets created from noise according to the settings you provide. Steps is the number of steps used for this process, and that also means that more steps will take longer, and in NAID they're capped at 50 and any steps past 28 disable free Opus generations.
Generally staying at 28 steps is fine, and there isn't much benefit to more. More steps should typically never break your image, may add more details, but with linearly scaling computation time/cost and heavily diminishing returns.""",
	'Prompt':
"""This here is the main way of telling the AI in text what to generate. Your text gets "digested" into tokens (think of them like AI words), which are then processed further by the model to figure out what to create from the starting point its given, typically noise.
Do yourself a favor, and don't get too caught up thinking of any AI models and the prompt in a too human way. Yes, your run-of-the-mill prompts like "1girl,sundress,forest" will generally work, and if what you have makes what you want, good.
Models don't think about your prompt like a human would. For one, everything is a vector, and typically models will understand a lot more than just the main datasets you might think about, for NAID Anime models that would be Danbooru, and for Furry e621, both NSFW.
Models may well understand symbols like ♥ for instance which at least for V1 was genuinely very useful, and still isn't useless. You can also separate your words with symbols and get sane results, like "1girl♥sundress♥forest", nothing is stopping you.
Also complex concepts that the AI is sort of able to understand, but not reliably so you may want to repeat instead of simply strengthening. "complex concept,complex concept,complex concept" may go a much longer way than just "{{complex concept}}" would.""",
	'Negative Prompt/Undesired Content':
"""Mostly what it says it is. It works like the prompt, just that instead of biasing the AI towards the text, it steers it away from it. A simple "nsfw" in the UC can go a long way to make SFW images, (less so in newer more horny models).
However do note that different models may still respond relatively speaking very differently to the UC. NAID Anime V2 responds incredibly well to the UC and can be driven almost entirely only with it, whereas V3 is affected much, much weaker by it and needs a good prompt.""",
	'CFG Scale/Scale/Guidance':
"""It's typically said that this parameter determines how much the AI follows your prompt, and on a very technical level, given how AI's with this parameter are built, this is true. But it's in practice a surprisingly unhelpful description, lacking some relevant nuance.
It's also in practical application due to the complexities of how AI's interpret your prompt often simply not true.
Changing the scale with settings locked may well show you a lot of different interpretations for a given prompt, and interpretations at the higher end, before breaking, and with very much trained tags and a normal prompt, may well be a lot worse than something in the middle.
Very low values will certainly cause your image to come out with a notable lack of definition and generally a softer look. Higher values give you sharper features, before eventually deepfrying your image. The sweet spot lies typically somewhere in the middle.
The values you can and should use can vary wildly between models and overall settings. In NAID Furry V1 in particular it was possible to get mostly sane images as high as 100, in the V3 models you will very rarely want to exceed 10.
When using img2img at very low strengths you also may be able and might even want to crank up this setting considerably.""",
	'Purge':
"""This button deletes all the entries of the linked list to free up memory. Needs two clicks within 3 seconds, to prevent accidental deletion of images.""",
	'Sampler Cutoff':
"""This tiny field determines the cutoff numbers for samplers on a cluster collage, that is how many samplers are displayed per row. 0 is for all, so a complete horizontal display, 1 would be all aligned vertically.
Be advised that you should pay attention to make your number of samplers cleanly divisible by the sampler cutoff, or you may run into issues with collage generation.""",
	'Seed':
"""This field used for the/a seed when generating. The seed is basically a predetermined random noise pattern from which the image is diffused. An empty field means that a new seed will be seed per image or task. Collages of course maintain picked seeds per cluster.
When your settings are otherwise good enough but the results are not satisfying, typically you would try again on new seeds. When making collages in particular it can be helpful to search for specific seeds to show special things, though be aware and honest about biases.
When making cluster collages seeds provide the variable s in case you want to address them individually.
Seed fields like these additionally support 4 quick operations via simple single button hotkeys:
R: Set a new random but fixed seed to the field
C: Clear the field for unfixed randomization again
L: Set the seed of the last image that has been generated, particularly useful if you use single generations in search of useful seeds for collages or sequences
P: Set the seed of the image before the last one that has been generated""",
	'History':
"""These are the images that you have generated in this session so far. In order to not litter your memory older generations are eventually deleted from the history, but not from your system.
You can transfer images into the loaded list where they will persist until deletion or closing the program.""",
	'Show Last Generation':
"""A simple boolean button that switches whether any new generations should be automatically displayed or not.""",
	'Loaded images':
"""These are imported or transferred images that will persist and are ready to be used for image2image and vibe transfer.""",
	'Image2image':
"""Uses a single image as a direct input to change it according to your other settings. Check the strength and noise fields for tooltips with more information.""",
	'Vibe Transfer':
"""Uses up to 16 images as indirect inputs, basically visual prompts. Check the strength and information extracted fields for tooltips with more information.""",
	'Truth Condition':
"""This is a CVF specific input field, a truth condition on wether to use this image for i2i/VT for any given image in your collage/sequence and will overwrite the boolean button if anything is set here.
For instance you could have 2 images you want to use in an alternating fashion for image2image purposes then you could give one the condition "⁅n==0⁆" and the other "⁅n==1⁆".
Not that only a single image for i2i is permitted to be used per generation, and for VT there's a maximum of 16. CVF will not pre-check all your conditions, but it will inform you if something goes wrong.""",
	'Image2image Strength':
"""This is a mostly easy to understand parameter. Strength decides how much the image gets changed, where 0 would be no change at all, and 1 would be completely disregarding the input image.
Good values for this can depend a lot on what exactly you want to accomplish. If you want to fix seams or minor errors you will probably just want low values, not even higher than 0.3.
If the goal is to refine an image or change some minor features you will want to experiment with medium values, a common one used is 0.7.
If you only really want your input image to be used as very vague guidance while still getting entirely new poses and maybe even very different characters, go close to 1.
Not that higher image2image strength means higher processing requirements, and so for NAID higher Anlas cost if outside of the parameters of free Opus generations.""",
	'Image2image Noise':
"""This parameter adds noise over your input image which is generally supposed to help with creating new details be weakening your input image.
It's not necessary in most cases, and if you use it you'll generally want to use low values, or the noise could survive the processing.""",
	'Vibe Transfer Strength':
"""This indicates how strongly the VT is taken into account, with 0 not affecting the output at all, and 1 being a very strong effect. Unlike i2i strength arbitrary and even negative values are possible. With negative values VTs act somewhat akin to, but not exactly like an UC.
Also note that this is an absolute value, two VT images at strength 1 will have a collective strength of 2 and as such if you add VT images you will eventually overwhelm the model and get corrupted outputs.
""",
	'Vibe Transfer Information Extracted':
"""One of the most complicated parameters to understand, and simple words won't remotely do it justice. The exact details and best descriptions of this are something not even the developers themselves could confidently give.
At a very general level it is of course true that less IE gives you less content from your input images, but the ways this exactly works has several highly peculiar nuances.
For one, VT digests images according to the model's understanding of what it sees. If you give it an image of a character that the model really knows, then it will understand that you want this particular character in a way similar as if you had used the tag for it.
This also applies to any other features. The more the model knows and understands features shown in the input image, the better it will be at following.
Putting in a very well known character you might be able to get that exact character at IE 0.01, yet if you have a fancy OC with unique characteristics then even at full strength and IE you may not even get close to that character, as such an OC would get broken down into parts.""",
	'Metadata Viewer':
"""CVF has an internal metadata viewer that can be displayed in place of the image preview. Images from the loaded list and history can be analyzed with the according buttons.
This metadata viewer will attempt to display both the EXIF and NAID Alpha information verbatim with no filtering at all, though should any fields contain too much information that gets truncated.""",
	'Overwrite Images':
"""A simple boolean button that determines whether images at the specified saving location are overwritten, or whether their generation is skipped. Skipping present images is useful to resume processing of interrupted tasks and to prevent accidental loss of images.""",
	'Wipe Queue':
"""Completely wipes any tasks from the queue without processing them and resets according internal settings.""",
	'Generate Image':
"""Generates a single image according to the settings. Any F variables such as n or cc will be evaluated with 0.""",
	'Queue Task':
"""Queues a task according to the current settings and will immediately save a .py and if necessary a .cvfimgs file to the according folder. Once a task is queued you may change the settings freely to make a new task.""",
	'Process Tasks':
"""Processes all tasks in the queue, working through the images one by one. Be advised that ClusterVisionF is not a glorified autoclicker and excessive use of free Opus generations can get you rate limited and at worst banned. This UI itself is terms compliant, so it's up to you.
As a general rule of thumb when using free generations, generate with CVF within limits of what you might be able to accomplish yourself. Don't generate 24/7, 1000 images is one thing, 10000 an entirely different thing. See 9.1.6 in the [u][ref=https://novelai.net/terms]NAI ToS[/ref][/u].
Note that this does not apply to any Anlas costing and hence paid generations, go wild with them it's your money.""",
	'Image Quantity':
"""This value determines how many images are generated for a task. For image sequences this value here also directly determines the range of n. Since n starts at 0, if you put in a quantity of 4 here, you get 4 images with associated n values of 0, 1, 2 and 3.
For cluster sequences this value instead determines the range of cc, and these numbers will be shown on the collage in the top left.""",
	'Cluster Columns':
"""The columns/rows settings allows you to get multiple images per seed and you can adjust the number and format of images as you want. This value determines the number of columns you get, x-axis, left and right. Directly translates to the c variable (starting at 0).""",
	'Cluster Rows':
"""The columns/rows settings allows you to get multiple images per seed and you can adjust the number and format of images as you want. This value determines the number of rows you get, y-axis, up and down. Directly translates to the r variable (starting at 0).""",
	'Cluster Collage':
"""CVFs main way of producing high quality insightful data are these cluster collages. Their name comes from them being collages in which you can organize nigh arbitrary clusters of images. Provides variables n, c, r and s.
Check the tooltip of any F-Input for more details on the variables.""",
	'Image Sequence':
"""Produces only simple images, but can do so in a sequence, which also can be turned into a video. Provides the variable n to use in F-strings.
Check the tooltip of any F-Input for more details on the variables.""",
	'Cluster Sequence':
"""See "Cluster Collage" and "Image Sequence" first. A cluster sequence is just the logical combination of both concepts, potentially allowing you to process hundreds of images into one single insightful video.
For this in particular when generating on an online service you will want to be aware of their terms of service. All variables are usable in this mode, with cc being the variable to use for each new collage, just like n for image sequences.
Check the tooltip of any F-Input for more details on the variables.""",
	'Image Deletion':
"""If clicked twice within 3 seconds this image will be deleted out of the program memory. It will not delete any images that were saved to or came in for first place from your system.""",
}# Left to implement: Settings, Themes, Sampler, Decrisper (partially deprecated in NAID tho), Model, Name, Folder Name, Wait Time
HELP_TEXT = """ClusterVisionF is a bit of a complicated and unusual UI, but most text fields and buttons have tooltips attached that will explain their function and possible hotkeys.
Rightclick any such elements to see if they have something to say about themselves.
Starting with CVF6 file imports work a little bit different, and CVF can handle a number of different files.
You should be able to see the background split into two colors with the same spacing as the metadata on the left, and console/image on the right, that's relevant positioning for image drops.
- When dropping single images (.png or .jpg) on the left, CVF will attempt to load metadata from the image according to which settings have import enabled
- When dropping single images on the right, or multiple images at once, CVF will load all of those for use with image2image/vibe transfer, and will allow you to look at the full metadata via the according viewer
- CVF will save any images and their exact settings used for i2i/VT as a .cvfimgs file, which can be imported by dropping them anywhere, completely restoring that state, no need to manually redo all of those settings
- You can drop CVF theme files (.py) to apply them instantly
- When dropping a single CVF task setting file (.py) it will always load the according metadata into the fields on the left
- When dropping multiple CVF task settings files their metadata will not be loaded and instead the tasks immediately get queued (which is mostly useful for tests, or if you externally adjusted these tasks)"""
