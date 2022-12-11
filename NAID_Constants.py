#The URL to which the requests are sent
URL='https://api.novelai.net/ai/generate-image'

#This is a list reflecting the online UI UC presets
UNDESIRED_CONTENT_LISTS={
'AnimeLQBA':[0,'''nsfw,lowres,bad anatomy,bad hands,text,error,missing fingers,
extra digit,fewer digits,cropped,worst quality,low quality,normal quality,
jpeg artifacts,signature,watermark,username,blurry,'''],
'AnimeLQ':[1,'nsfw,lowres,text,cropped,worst quality,low quality,normal quality,jpeg artifacts,signature,watermark,username,blurry'],
'AnimeNone':[2,''],
'FurryLQ-Deprecated':[0,'nsfw,{worst quality},{bad quality},text,signature,watermark,'],
'FurryLQ':[0,'nsfw,worst quality,low quality,what has science done,what,nightmare fuel,eldritch horror,where is your god now,why,'],
'FurryNone':[1,''],}

#NAID uses these two vectors as standard quality tags
STANDARD_QT='masterpiece,best quality,'

#These are the names used to address certain models
MODELS={'Curated':'safe-diffusion','Full':'nai-diffusion','Furry':'nai-diffusion-furry'}

#These are the image modes as used on the website
IMAGE_MODES={
'PortraitNormal':
{'width': 512, 'height': 768},
'LandscapeNormal':
{'width': 768, 'height': 512},
'SquareNormal':	
{'width': 640, 'height': 640,},
'PortraitLarge':
{'width': 512, 'height': 1024},
'LandscapeLarge':
{'width': 1024,'height': 512},
'SquareLarge':
{'width': 1024,'height': 1024},}