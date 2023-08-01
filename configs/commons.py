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
    'VCB-Studio','Airota', 'SweetSub', 'Nekomoe kissaten', 'DMG', 'SumiSora', 'UHA-WINGS', 'BeanSub',
    'XKsub', 'MakiYuu', 'EnkanRec', 'SBSUB', 'MakariHoshiyume', 'Kamigami', 'Liuyun', 'FZSD', 'Pussub',
    'Mabors-Sub', 'KTXP', 'philosophy-raws', 'mawen1250')
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