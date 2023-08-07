# the use this as the default webp quality
ENFORCED_WEBP_QUALITY : int = 90

OLD_GRP_NAME : str = 'VCB-S'
STD_GRPTAG : str = 'VCB-Studio'
STD_FONT_NAME : str = 'Fonts'
STD_SPS_DIRNAME : str = 'SPs'
STD_BKS_DIRNAME : str = 'Scans'   # standard BK root dirname
STD_CDS_DIRNAME : str = 'CDs'     # standard CD roor diranme
STD_COVER_FILENAME : str = 'Cover.jpg'
DEFAULT_TSDM_CREDIT : str = 'TSDM合购区'
STD_TSDM_CREDIT_TXT_FILENAME : str = '天使动漫自购转载声明.txt'
STD_TSDM_CREDIT_TEXT = '''天使动漫授权 VCB-Studio 转载声明
TSDM's authorization of redistribution for VCB-Studio

本音乐仅供 VCB-Studio 发布使用，请勿单独转载。本文件由放流者要求加入，转载时请原样保留。
The music files here are for VCB-Studio's release only. Please do not re-post them separately. The source provider requires this file to be included as is when re-posting the BDRip release.

动漫音乐微博，最新自购无损音乐更新情况：
TSDM's Weibo with latest information of self-purchased lossless music:
https://weibo.com/dmmusic
https://weibo.com/acgtsdm

天使动漫自购音乐区链接：
Link to TSDM's self-purchased music forum:
https://www.tsdm39.net/forum.php?mod=forumdisplay&fid=247

自购支援规则（无损音质 + BK 扫图，新老 CD 皆可）：
Rules of joining self-purchased music forum:
https://www.tsdm39.net/forum.php?mod=viewthread&tid=841501'''

# these are whitelisted
# NOTE don't adjust the orders in these LANG_TAGS
# it will change the function behavior in `chkSuffix()`
AVAIL_JPN_LANG_SUFFIXES : list[str] = ['jp', 'JP', 'jpn', 'JPN', 'Jpn']
AVAIL_CHS_LANG_SUFFIXES : list[str] = ['sc', 'SC', 'chs', 'CHS', 'Chs']
AVAIL_CHT_LANG_SUFFIXES : list[str] = ['tc', 'TC', 'cht', 'CHT', 'Cht']
AVAIL_LANG_SUFFIXES : list[str] = AVAIL_JPN_LANG_SUFFIXES + AVAIL_CHS_LANG_SUFFIXES + AVAIL_CHT_LANG_SUFFIXES
AVAIL_SEASON_LANG_SUFFIXES : list[str] = AVAIL_CHS_LANG_SUFFIXES + AVAIL_CHT_LANG_SUFFIXES
AVAIL_FILE_LANG_SUFFIXES : list[str] = ['sc', 'tc', 'chs', 'cht', 'sc&jp', 'tc&jp', 'chs&jpn', 'cht&jpn']

# allowed file extensions under 'Scans'
ALL_EXTS_IN_SCANS = tuple('jpg jpeg webp'.split())

# allowed file extensions under 'CDs'
MAIN_EXTS_IN_CDS = tuple('flac m4a mp3 cue log'.split())
AUD_EXTS_IN_CDS = tuple('flac m4a mp3'.split())
IMG_EXTS_IN_CDS = tuple('jpg jpeg webp'.split())
VID_EXTS_IN_CDS = ('mkv', )
TXT_EXTS_IN_CDS = ('txt', )
ALL_EXTS_IN_CDS = MAIN_EXTS_IN_CDS + IMG_EXTS_IN_CDS + VID_EXTS_IN_CDS + TXT_EXTS_IN_CDS

GRPTAG : str = 'full_group_tag'
TITLE : str = 'show_title'
QUALITY : str = 'quality_label'
SUFFIX: str = 'suffix'
EXT : str = 'extension'

SERIES_DIR_FMT = f'{{{GRPTAG}:s}} {{{TITLE}:s}} {{{SUFFIX}:s}}.'
SEASON_DIR_FMT = f'{{{GRPTAG}:s}} {{{TITLE}:s}} {{{QUALITY}:s}}{{{SUFFIX}:s}}.'
