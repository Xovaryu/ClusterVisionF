SPACE_NONE=[" ",""]
#The first entry in these lists is the symbol, the second is the token cost in repetitive sequences.

ALT30_LIST=[
["☺",1],
["☻",2],
["♥",1/4],
["♦",1],
["♣",2],
["♠",2],
["•",1/8],
["◘",2],
["○",2],
["◙",2],
["♂",2],
["♀",2],
["♪",1],
["♫",1],
["☼",2],
["►",1],
["◄",2],
["↕",2],
["‼",1],
["¶",2],
["▬",1/2],
["↨",2],
["↑",2],
["↓",2],
["→",2],
["←",2],
["∟",2],
["↔",2],
["▲",2],
["▼",2],
]

KEYBOARD_SYMBOL_LIST=[
["§",2],
["'",2],
["`",1],
["´",1],
["@",1],
["€",1],
["\\",1],
["#",1],
["°",1],
["%",1],
["&",1],
["^",1/2],
['"',1/2],
["$",1/2],
["<",1/2],
["(",1/2],
[",",1/2],
[";",1/2],
[":",1/2],
["+",1/2],
["/",1/4],
[")",1/4],
["~",1/4],
[">",1/8],
["*",1/8],
["=",1/8],
["?",1/8],
[".",1/16],
["_",1/16],
["!",1/16],
["-",1/16],
]

OTHER_LIST=[
["⑨",3],
["⟁",3],
["µ",2],
["✩",2],
["¥",2],
["¼",2],
["«",2],
["ω",2],
["δ",2],
["×",2],
["±",2],
["∞",2],
["ƒ",2],
["ǂ",2],
["ˆ",2],
["ˇ",2],
["⑊",2],
["⏎",2],
["⌘",2],
["⊹",2],
["☄",2],
["æ",1],
]

HEARTS=[#♥❤♡❣❥❦❧
["♥",1/4],#Black Heart Suit
["❤",1/4],#Heavy Black Heart
["♡",1/2],#White Heart Suit
["❣",1],#Heavy Heart Exclamation Mark Ornament
["❥",2],#Rotated Heavy Black Heart Bullet
["❦",2],#Floral Heart
["❧",2],#Rotated Floral Heart Bullet
]

HEART_EMOJIS=[#💔💗💖💕♥️💓💟💝💘💞❣️🫀
["💔",1/2],#Broken Heart
["💗",1/2],#Growing Heart
["💖",1/2],#Sparkling Heart
["💕",1/2],#Two Hearts
["♥️",1/2],#Heart Suit
["💓",1],#Beating Heart
["💟",1],#Heart Decoration
["💝",1],#Heart with Ribbon
["💘",1],#Heart with Arrow
["💞",1],#Revolving Hearts
["❣️",2],#Heavy Heart Exclamation Mark Ornament Emoji
["🫀",3],#Anatomical Heart
]

COLORED_HEART_EMOJIS=[#❤️💙💚💜💛🧡🖤🤍🤎
["❤️",1/4],#Red Heart
["💙",1/2],#Blue Heart
["💚",1/2],#Green Heart
["💜",1/2],#Purple Heart
["💛",1/2],#Yellow Heart
["🧡",1],#Orange Heart
["🖤",1],#Black Heart
["🤍",2],#White Heart
["🤎",2],#Brown Heart
]

VAR_SEL_16=["️",1],#Variation Selector-16

EMPTY_CHARS=[
[" ‎",1],
["‎",1],
["͏",2],#Combining Grapheme Joiner
["‭",2],#Left-To-Right Override
["‮",2],#Right-To-Left Override
["‬",2],#Pop Directional Formatting
["‪",2],#Left-To-Right Embedding
["‫",2],#Right-To-Left Embedding
["​",1],#Zero Width Space
["‌",2],#Zero Width Non-Joiner
["‍",1],#Zero Width Joiner
["‎",2],#Left-To-Right Mark
["‏",2],#Right-To-Left Mark
]

EMOJI_LIST=[
["😻",0.5],
]