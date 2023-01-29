#Your authorization token goes here and will need replacing once a month.
#To get it, visit the NAI website, login and fetch your session authorization token, depending on your browser.
auth={"auth_token":"XXX","encryption_key":"XXX"}

#Video settings
BASE_FPS=7
#If Flowframes is used and the path is different it has to go here.
FLOWFRAMES_PATH='C:/Users/Administrator/AppData/Local/Flowframes/Flowframes.exe'
FF_FACTOR=4
FF_OUTPUT_MODE=2

#Settings for cluster collages
CREATOR_NAME=''
CC_SEEDS_FONT=['fonts/Roboto-Regular.ttf',29]
#If needed you can specify a custom font list that will be loaded before the provided fonts
CUSTOM_FONT_LIST_PREPEND=[]#Add fonts to be prioritized over the default
CUSTOM_FONT_LIST_APPEND=[]#Add fonts that will be used as a fallback if all others fail
FONT_SIZE=32

#Additional waiting time between generations, set higher when still using NAI yourself in parallel to avoid getting limited
WAIT_TIME=1

PROMPT_STABBER_DEFAULT_SEEDS=[
[4246521898,3725954486,916033042],
[4132094759,2830623800,88736211],
[2823232049,3881402690,808994933]]

PROMPT_STABBER_4_4=[
[3076815738, 1990129682, 3655402003, 3572297602],
[439438776, 688831479, 1391759257, 2062017751],
[396332814, 341256431, 4087186989, 3204503906],
[251242884, 1287923751, 2025346986, 3668458118]]