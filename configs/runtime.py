'''
The file contains internal variables used in AfterCollation.
Dont touch these variables unless you know what you are doing.
'''

#* CSV fields exchange table -------------------------------------------------------------------------------------------
# these fields define the variable names saved internally

BASE_LINE_LABEL = '勿填此格'

# these fields are used in dedicated in VNA
VNA_PATH_CN,                    VNA_PATH_VAR = 'M2TS路径',   'vna_m2ts_path'
VNA_M2TS_VOL_CN,            VNA_M2TS_VOL_VAR = 'VOL卷号',    'vna_volume_idx'
VNA_M2TS_IDX_CN,            VNA_M2TS_IDX_VAR = 'M2TS序号',   'vna_m2ts_idx'
VNA_SCRIPT_CN,                VNA_SCRIPT_VAR = '使用脚本',   'vna_script'
VNA_COMMENT_CN,              VNA_COMMENT_VAR = '其它备注',   'vna_comment'
VNA_AUDIO_SAMPLES_CN,  VNA_AUDIO_SAMPLES_VAR = '音频摘要',   'vna_audio_samples'
VNA_VID_FPS_CN,              VNA_VID_FPS_VAR = '视频帧率',   'vna_video_fps'

# these fields are used in dedicated in VNR
VNR_GRP_IDX_CN,       VNR_GRP_IDX_VAR = '主分组', 'vnr_main_grouping'
VNR_SUBGRP_IDX_CN, VNR_SUBGRP_IDX_VAR = '子分组', 'vnr_sub_grouping'

# these fields are generally used in VNx scripts
FULLPATH_CN,   FULLPATH_VAR = '完整路径',   'vn_fullpath'
CRC32_CN,         CRC32_VAR = 'CRC32',      'vn_crc32'
DURATION_CN,   DURATION_VAR = '时长',       'vn_duration'
FILESIZE_CN,   FILESIZE_VAR = '大小',       'vn_filesize'
EXTENSION_CN, EXTENSION_VAR = '文件后缀',   'vn_fileext'
CONTAINER_CN, CONTAINER_VAR = '实际格式',   'vn_container'
TRACKCOMP_CN, TRACKCOMP_VAR = '轨道组成',   'vn_trackcomp'
TR_VIDEO_CN,   TR_VIDEO_VAR = '视频轨道',   'vn_video_tracks'
TR_AUDIO_CN,   TR_AUDIO_VAR = '音频轨道',   'vn_audio_tracks'
TR_TEXT_CN,     TR_TEXT_VAR = '图形字幕',   'vn_text_tracks'
TR_MENU_CN,     TR_MENU_VAR = '章节菜单',   'vn_menu_tracks'
GRPTAG_CN,       GRPTAG_VAR = '组名',       'vn_grptag'
SHOWNAME_CN,   SHOWNAME_VAR = '片名',       'vn_showname'
LOCATION_CN,   LOCATION_VAR = '位置',       'vn_location'
TYPENAME_CN,   TYPENAME_VAR = '内容类型',   'vn_typename'
IDX1_CN,           IDX1_VAR = '主序号',     'vn_idx1'
IDX2_CN,           IDX2_VAR = '副序号',     'vn_idx2'
NOTE_CN,           NOTE_VAR = '补充说明',   'vn_note'
CUSTOM_CN,       CUSTOM_VAR = '自定义名称', 'vn_custom'
SUFFIX_CN,       SUFFIX_VAR = '后缀',       'vn_suffix'
ENABLE_CN,       ENABLE_VAR = '启用?',      'vn_enabled'

#* CSV fields the their order ------------------------------------------------------------------------------------------
# these are the field order to be shown in CSV files
# NOTE dont change the order unless you know what you are doing

VNA_ALL_DICT = {
    VNA_PATH_CN: VNA_PATH_VAR,
    VNA_M2TS_VOL_CN: VNA_M2TS_VOL_VAR,
    VNA_M2TS_IDX_CN: VNA_M2TS_IDX_VAR,
    DURATION_CN: DURATION_VAR,
    TRACKCOMP_CN: TRACKCOMP_VAR,
    VNA_VID_FPS_CN: VNA_VID_FPS_VAR,
    VNA_SCRIPT_CN: VNA_SCRIPT_VAR,
    VNA_COMMENT_CN: VNA_COMMENT_VAR,
    TYPENAME_CN: TYPENAME_VAR,
    IDX1_CN: IDX1_VAR,
    IDX2_CN: IDX2_VAR,
    CUSTOM_CN: CUSTOM_VAR,
    GRPTAG_CN: GRPTAG_VAR,
    SHOWNAME_CN: SHOWNAME_VAR,
    VNA_AUDIO_SAMPLES_CN: VNA_AUDIO_SAMPLES_VAR,
}

VND_ALL_DICT = {
    # VNX_CSV_PERSISTENT_KEY_DICT: these fields are always saved in CSV

    FULLPATH_CN: FULLPATH_VAR,
    CRC32_CN: CRC32_VAR,
    # VNX_USER_FIELDS_NAMING_DICT: these fields are to be input from the user
    GRPTAG_CN: GRPTAG_VAR,
    SHOWNAME_CN: SHOWNAME_VAR,
    LOCATION_CN: LOCATION_VAR,
    TYPENAME_CN: TYPENAME_VAR,
    IDX1_CN: IDX1_VAR,
    IDX2_CN: IDX2_VAR,
    NOTE_CN: NOTE_VAR,
    CUSTOM_CN: CUSTOM_VAR,
    SUFFIX_CN: SUFFIX_VAR,
    ENABLE_CN: ENABLE_VAR,
    # the following fields are just for presenting mediainfo
    # they have no usage in later stages
    DURATION_CN: DURATION_VAR,
    FILESIZE_CN: FILESIZE_VAR,
    EXTENSION_CN: EXTENSION_VAR,
    CONTAINER_CN: CONTAINER_VAR,
    TRACKCOMP_CN: TRACKCOMP_VAR,
    TR_VIDEO_CN: TR_VIDEO_VAR,
    TR_AUDIO_CN: TR_AUDIO_VAR,
    TR_TEXT_CN: TR_TEXT_VAR,
    TR_MENU_CN: TR_MENU_VAR,
}

# if change, also change the order in `read/writeCSV4VNR()`
VNR_ALL_DICT = {
    VNR_GRP_IDX_CN: VNR_GRP_IDX_VAR,
    VNR_SUBGRP_IDX_CN: VNR_SUBGRP_IDX_VAR,
    ENABLE_CN: ENABLE_VAR,
    FULLPATH_CN: FULLPATH_VAR,
}

#* sub fields ----------------------------------------------------------------------------------------------------------
# NOTE dont change the order unless you know what you are doing

VNA_BASE_LINE_USER_DICT = {
    GRPTAG_CN: GRPTAG_VAR,
    SHOWNAME_CN: SHOWNAME_VAR,
}
# 'presistent' means they are automatically in VNA but to be used in VND
VNA_PERSISTENT_DICT = {
    VNA_M2TS_VOL_CN: VNA_M2TS_VOL_VAR,
    VNA_M2TS_IDX_CN: VNA_M2TS_IDX_VAR,
    VNA_AUDIO_SAMPLES_CN: VNA_AUDIO_SAMPLES_VAR,
}
VNA_USER_DICT = {
    TYPENAME_CN: TYPENAME_VAR,
    IDX1_CN: IDX1_VAR,
    IDX2_CN: IDX2_VAR,
    CUSTOM_CN: CUSTOM_VAR,
    GRPTAG_CN: GRPTAG_VAR,
    SHOWNAME_CN: SHOWNAME_VAR,
}

VND_BASE_LINE_USER_DICT = {
    FULLPATH_CN: FULLPATH_VAR,
    GRPTAG_CN: GRPTAG_VAR,
    SHOWNAME_CN: SHOWNAME_VAR,
    SUFFIX_CN: SUFFIX_VAR,
}
# 'presistent' means they are automatically created in VND but to be used in VNE
VND_PERSISTENT_DICT = {
    FULLPATH_CN: FULLPATH_VAR,
    CRC32_CN: CRC32_VAR,
}
VND_USER_DICT = {
    GRPTAG_CN: GRPTAG_VAR,
    SHOWNAME_CN: SHOWNAME_VAR,
    LOCATION_CN: LOCATION_VAR,
    TYPENAME_CN: TYPENAME_VAR,
    IDX1_CN: IDX1_VAR,
    IDX2_CN: IDX2_VAR,
    NOTE_CN: NOTE_VAR,
    CUSTOM_CN: CUSTOM_VAR,
    SUFFIX_CN: SUFFIX_VAR,
    ENABLE_CN: ENABLE_VAR,
}

#TODO add relation assert here to ensure vnx dicts are consistent

#* file extension vs expected format -----------------------------------------------------------------------------------
# these are the format string in libmediainfo

EXTS2FORMATS = {
    'mkv' : 'Matroska',
    'mka' : 'Matroska',
    'mp4' : 'MPEG-4',
    'm4a' : 'MPEG-4',

    'flac': 'FLAC',
    'aac' : 'AAC',
    'ac3' : 'AC-3',
    'dts' : 'DTS',

    'wav' : 'Wave',
    'wav64': 'Wave',

    'tak' : 'TAK',
    'ape' : 'Monkey\'s Audio',
    'wv'  : 'WavPack',
    'tak' : 'TAK',
    'mp3' : 'MPEG Audio',

    'webp': 'WebP',
    'jpg' : 'JPEG',
    'jpeg': 'JPEG',
    'png' : 'PNG',
    'bmp' : 'BMP',
    'tif' : 'TIFF',
    'tiff': 'TIFF',
    'jxl' : 'JPEG XL',
    'heif': 'HEIF',

    'zip' : 'ZIP',
    '7z'  : '7-Zip',
    'rar' : 'RAR',

    # NOTE libmediainfo wont detect ass file as an SSA media track if the file has BOM for UTF-8 encoding
    # remember to specially handle this in VNx tools
    'ass' : 'ASS',
}

#* the following defines the capability of VNx tools -------------------------------------------------------------------

# only the listed extensions will be processed by VNx tools
# which = the specification
VNx_VID_EXTS     = ('mkv', 'mp4')            # video
VNx_EXT_AUD_EXTS = ('mka', )                 # external audio
VNx_STA_AUD_EXTS = ('flac', )                # standalone audio
VNx_IMG_EXTS     = ('png',)                  # images, in SPs PNG is the only allowed image format
VNx_SUB_EXTS     = ('ass',)                  # subtitle
VNx_ARC_EXTS     = ('zip', '7z', 'rar')      # archives

# NOTE if updated, remember to update the corresponding checkers
VNx_WITH_AUD_EXTS = VNx_VID_EXTS + VNx_EXT_AUD_EXTS + VNx_STA_AUD_EXTS              # used to filter files in checkers/audio.py
VNx_MAIN_EXTS = VNx_VID_EXTS + VNx_EXT_AUD_EXTS + VNx_STA_AUD_EXTS + VNx_IMG_EXTS   # used to filter files in VNR matching
VNx_ALL_EXTS = VNx_MAIN_EXTS + VNx_SUB_EXTS + VNx_ARC_EXTS                          # used everywhere
VNx_DEP_EXTS = VNx_EXT_AUD_EXTS + VNx_SUB_EXTS                                      # dependent exts i.e. the naming of the item depends on another file
VNx_IDP_EXTS = VNx_VID_EXTS + VNx_STA_AUD_EXTS + VNx_IMG_EXTS + VNx_ARC_EXTS        # independent extensions

#* the following defines the capability of Sx tools --------------------------------------------------------------------

# ScansMaker acceptable file extensions
SM_ACCEPTABLE_EXTS = tuple('png bmp tif tiff jpg jpeg webp'.split())

#* the following defines the capability of Mx tools --------------------------------------------------------------------

MM_ACCEPTED_AUD_EXTS = tuple('wav wav64 flac tak ape wv mp3 m4a'.split())
MM_ACCEPTED_IMG_EXTS = SM_ACCEPTABLE_EXTS
MM_ACCEPTED_VID_EXTS = ('mkv', )
MM_ACCEPTABLE_EXTS = MM_ACCEPTED_AUD_EXTS + MM_ACCEPTED_IMG_EXTS + MM_ACCEPTED_VID_EXTS

#* other variables -----------------------------------------------------------------------------------------------------
# the following is customisable, but they should not be exposed to the user configuration file

# the all possible output formats of VNA
VNA_OUTPUT_EXTS : list[str] = ['csv', 'yaml', 'json']

# we used the following keywords from VGMDB note to detect bonus CD
VGMDB_BONUS_CD_KEYWORDS : list[str] = ['bonus', 'enclosed', 'enclosure']

# the maximal and minimal track types in each format
MAXIMAL_TRACK_TYPES_IN_EXT = {
    'mkv': ('Video', 'Audio', 'Text', 'Menu'),
    'mp4': ('Video', 'Audio', 'Menu'),
    'mka': ('Audio', ),
    'png': ('Image', ),
}

MINIMAL_TRACK_TYPES_IN_EXT = {
    'mkv': ('Video', ),
    'mp4': ('Video', 'Audio'),
    'mka': ('Audio', ),
    'png': ('Image', ),
}

# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6name.html
ENABLED_FONT_NAME_IDS = (
    1, # Font Family name
    # 2, # Font Subfamily name
    3, # Unique font identifier
    4, # Full font name
    # 5, # Version string
    6, # PostScript name
    # 7, # Trademark
    # 8, # Manufacturer Name
    # 9, # Designer
    # 10, # Description
    # 11, # URL Vendor
    # 12, # URL Designer
    # 13, # License Description
    # 14, # License Info URL
    16, # Preferred Family
    # 17, # Preferred Subfamily
    # 18, # Compatible Full (Macintosh only)
    # 19, # Sample text
    # 20, # PostScript CID findfont name
    # 21, # WWS Family Name
    # 22, # WWS Subfamily Name
    # 23, # Light Background Palette
    # 24, # Dark Background Palette
    # 25, # Variations PostScript Name Prefix
)

FONT_SUBFAMILY_NAME_IDS = (2, 17)

# these are used to convert the language suffix to a uniformed one
# so we can compare if different language suffixes are the same
LANG_SUFFIX_UNIFORMATION_DICT = {
    'chs': 'chs',
    'sc': 'chs',
    'cht': 'cht',
    'tc': 'cht',
    'jpn': 'jpn',
    'jp': 'jpn',
    'jap': 'jpn'
}
