# video files commons
COMMON_VIDEO_FORMATS = ('HEVC', 'AVC')
COMMON_VIDEO_PROFILES = ('Main 10', 'Main', 'Format Range', 'High 10', 'High', 'High 4:4:4 Predictive')
COMMON_VIDEO_HEIGHTS = (720, 1080, 2160)
COMMON_VIDEO_WIDTHS = (1280, 1920, 3840)
COMMON_VIDEO_FPS = ('23.976', '29.970', '59.940')
COMMON_VIDEO_DEPTH = (8, 10)
COMMON_AUDIO_FORMATS = ('FLAC', 'AAC', 'AC3')
COMMON_AUDIO_DEPTH = (16, 24)
COMMON_AUDIO_FREQ = (44100, 48000)
COMMON_AUDIO_CHANNEL = (2, 6)
COMMON_AUDIO_LANGS = ('ja', )
COMMON_TEXT_FORMATS = ('PGS', )
COMMON_SUBS_LANGS = ('ja', 'en')

# video naming commons
COMMON_GRP_NAMES = (
    # sorted by the number of occurrences in filenames
    'VCB-Studio',        # 41977
    'Nekomoe kissaten',  # 5989
    'Airota',            # 2631
    'DMG',               # 1971
    'SweetSub',          # 1471
    'UHA-WINGS',         # 1402
    'Kamigami',          # 1373
    'Liuyun',            # 874
    'FZSD',              # 807
    'KTXP',              # 718
    'BeanSub',           # 624
    'MakariHoshiyume',   # 603
    'VCB-S',             # 572
    'ANK-Raws',          # 502
    'MH',                # 448
    'Mabors',            # 397
    'Hakugetsu',         # 356
    'XKsub',             # 285
    'DHR',               # 283
    'SumiSora',          # 269
    'NEOQSW',            # 243
    'EnkanRec',          # 243
    'Pussub',            # 234
    'Nyamazing',         # 221
    'LoliHouse',         # 209
    'RATH',              # 203
    'FreeSub',           # 187
    'philosophy-raws',   # 146
    'YYDM',              # 146
    'AI-Raws',           # 135
    'YUI-7',             # 128
    'T.H.X',             # 126
    'LoveEcho',          # 112
    'MMZY-Sub',          # 92
    'YlbudSub',          # 68
    'FLsnow',            # 60
    'Shirokoi',          # 60
    'DMG-Sub',           # 58
    'TUcaptions',        # 53
    'Lemonade',          # 51
    'TSDM',              # 48
    'SBSUB',             # 48
    'Ylbud-Sub',         # 43
    'Makino House',      # 42
    'PCSUB',             # 40
    'Mabors-Sub',        # 21
    'MakiYuu',           # 21
    'Maho.sub',          # 18
    'Eupho',             # 15
    'NijigakuSub',       # 15
    # 'PLF',               # 14
    'MLSUB',             # 13
    # 'KNA-Subs',          # 12
    'FZsub',             # 9
    'KimiUsofans Sub',   # 9
    # 'LBS',               # 7
    # 'Nanjo-Sub',         # 1
    'Xeon-Raw',          # 1
    # 'ARM-Raw',           # 1
    # 'Nyasama',           # 1
    'mawen1250',
    )

COMMON_VIDEO_LOCATIONS : list[str] = ['', 'SPs']
COMMON_TYPENAME : list[str] = [
    '',
    'OVA', 'OAD',
    'Menu',
    'Preview', 'Web Preview',
    'CM', 'CM Collection',
    'BD CM', 'DVD CM', 'BD&DVD CM', 'BD & DVD CM',
    'Trailer', 'Teaser', 'Teaser PV', 'SPOT', 'Spot',
    'Promotion Video', 'PV', 'PV Collection', 'Character PV',
    'PV & CM Collection', 'PV&CM Collection', 'CM & PV Collection', 'CM&PV Collection',
    'Intro', 'Introduction',
    'NCOP', 'NCED', 'EP',
    'MV',
    'IV', 'Interview', 'Event', 'Live', 'Making', 'Stage', 'Talk', 'Drama',
    'SP', 'Extra', 'Special'
]

# this is used to detect the chapter language, especially used by JSUM
KNOWN_MENU_EN_TEXTS = (
    'avant', 'opening', 'ending', 'yokoku', 'preview', 'a part', 'b part', 'c part', 'd part')

COMMON_VIDEO_EXTS = (
    'mkv', 'webm', 'flv', 'vob', 'ogv', 'ogg', 'drc', 'gif', 'gifv', 'mng', 'avi', 'mov', 'qt', 'wmv', 'yuv', 'rm',
    'rmvb', 'viv', 'amv', 'mp4', 'm4p', 'm4v', 'mpg', 'mp2', 'mpeg', 'mpe', 'mpv', 'm2v', 'svi', '3gp', '3g2', 'mxf',
    'roq', 'nsv', 'f4v', 'f4p', 'f4a', 'f4b')
COMMON_AUDIO_EXTS = (
    'flac', 'mka', 'ogg', 'oga', 'mp3', 'wav', 'w64', 'wma', 'm4a', 'm4b', 'm4p', 'mpc', 'ape', 'opus',
    'tak', 'tta', 'wv', 'wvc', 'aiff', 'aif', 'aifc', 'aac', 'mp2', 'ac3', 'dts', 'dtsma', 'dtshr', 'dtshd', 'eac3',
    'thd', 'truehd', 'at3', 'oma', 'aa3', 'oma')
COMMON_IMAGE_EXTS = (
    'png', 'jpg', 'jpeg', 'jpe', 'jfif', 'bmp', 'dib', 'gif', 'tif', 'tiff', 'webp', 'tga', 'dds', 'heif', 'heic', 'bpg',
    'jxl', 'psd', 'psb', 'exr', 'hdr', 'pic', 'pct', 'pict', 'jp2', 'j2k', 'jpf', 'jpm', 'jpx', 'mj2', 'wdp', 'hdp', 'cur', 'ico')

COMMON_F_FONT_EXTS = ('ttf', 'otf')
COMMON_C_FONT_EXTS = ('ttc', 'otc')
COMMON_FONT_EXTS = COMMON_F_FONT_EXTS + COMMON_C_FONT_EXTS

COMMON_TEXT_SUB_EXTS = ('ass',)

COMMON_ARCHIVE_EXTS = ('rar', '7z', 'zip', 'tar.gz', 'tgz')
