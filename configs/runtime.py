'''
The file contains internal variables used in AfterCollation.
Dont touch these variables unless you know what you are doing.
'''
from .time import TIMESTAMP, YYMMDD, HHMMSS

VA_LOG_FILENAME = f'VA-{TIMESTAMP}.log'
VP_LOG_FILENAME = f'VP-{TIMESTAMP}.log'
VR_LOG_FILENAME = f'VR-{TIMESTAMP}.log'

SD_LOG_FILENAME = f'SD-{TIMESTAMP}.log'
SP_LOG_FILENAME = f'SP-{TIMESTAMP}.log'
SR_LOG_FILENAME = f'SR-{TIMESTAMP}.log'

AD_LOG_FILENAME = f'AD-{TIMESTAMP}.log'
AP_LOG_FILENAME = f'AP-{TIMESTAMP}.log'
AR_LOG_FILENAME = f'AR-{TIMESTAMP}.log'

VP_CSV_FILENAME = f'VP-{TIMESTAMP}.csv'
VR_CSV_FILENAME = f'VR-{TIMESTAMP}.csv'
SP_CSV_FILENAME = f'SP-{TIMESTAMP}.csv'
AP_CSV_FILENAME = f'AP-{TIMESTAMP}.csv'

SD_DIRNAME_3 = 'SD-{}-{}-{}'
AD_DIRNAME_3 = 'AD-{}-{}-{}'

SD_TMP_DIRNAME = f'SD-{HHMMSS}'
AD_TMP_DIRNAME = f'AD-{HHMMSS}'

#* CSV fields exchange table -------------------------------------------------------------------------------------------
# these fields define the variable names saved internally

#! VA/VD/VP recognise the base/default line of naming config by any fields with this text in it
BASE_LINE_LABEL = '此格不填'

# general csv titles and internal variable names for VA/VD/VP/VR
FULLPATH_CN,      FULLPATH_VAR = '完整路径', 'vx_fullpath'
CRC32_CN,            CRC32_VAR = 'CRC32', 'vx_crc32'
DURATION_CN,      DURATION_VAR = '时长', 'vx_duration'
FILESIZE_CN,      FILESIZE_VAR = '大小', 'vx_filesize'
EXTENSION_CN,    EXTENSION_VAR = '文件后缀', 'vx_fileext'
FORMAT_CN,          FORMAT_VAR = '实际格式', 'vx_container'
TR_COMP_CN,        TR_COMP_VAR = '轨道组成', 'vx_trackcomp'
TR_VIDEO_CN,      TR_VIDEO_VAR = '视频轨道', 'vx_video_tracks'
TR_AUDIO_CN,      TR_AUDIO_VAR = '音频轨道', 'vx_audio_tracks'
TR_TEXT_CN,        TR_TEXT_VAR = '图形字幕', 'vx_text_tracks'
TR_MENU_CN,        TR_MENU_VAR = '章节菜单', 'vx_menu_tracks'
GRPTAG_CN,          GRPTAG_VAR = '组名', 'vx_grptag'
TITLE_CN,            TITLE_VAR = '片名', 'vx_title'
LOCATION_CN,      LOCATION_VAR = '位置', 'vx_location'
CLASSIFY_CN,      CLASSIFY_VAR = '内容类型', 'vx_classification'
IDX1_CN,              IDX1_VAR = '主序号', 'vx_idx1'
IDX2_CN,              IDX2_VAR = '副序号', 'vx_idx2'
SUPPLEMENT_CN,  SUPPLEMENT_VAR = '补充说明', 'vx_supplement'
FULLDESP_CN,      FULLDESP_VAR = '自定义名称', 'vx_fulldesp'
SUFFIX_CN,          SUFFIX_VAR = '后缀', 'vx_suffix'
ENABLE_CN,          ENABLE_VAR = '启用?', 'vx_enabled'
QLABEL_CN,          QLABEL_VAR = '画质标签', 'vx_qlabel'
TLABEL_CN,          TLABEL_VAR = '轨道标签', 'vx_tlabel'

# dedicated used between VA/VD
VA_PATH_CN,                    VA_PATH_VAR = 'M2TS路径', 'va_m2ts_path'
VA_M2TS_VOL_CN,            VA_M2TS_VOL_VAR = 'M2TS卷号', 'va_volume_idx'
VA_M2TS_IDX_CN,            VA_M2TS_IDX_VAR = 'M2TS序号', 'va_m2ts_idx'
VA_SCRIPT_CN,                VA_SCRIPT_VAR = '使用脚本', 'va_script'
VA_COMMENT_CN,              VA_COMMENT_VAR = '其它备注', 'va_comment'
VA_AUDIO_SAMPLES_CN,  VA_AUDIO_SAMPLES_VAR = '音频摘要', 'va_audio_samples'
VA_VID_FPS_CN,              VA_VID_FPS_VAR = '视频帧率', 'va_video_fps'

# dedicated used in VR
VR_GRP_IDX_CN,       VR_GRP_IDX_VAR = '主分组', 'vr_main_grouping'
VR_SUBGRP_IDX_CN, VR_SUBGRP_IDX_VAR = '子分组', 'vr_sub_grouping'

#* CSV fields the their order ------------------------------------------------------------------------------------------
# these are the field order to be shown in CSV files

#! dont change the order unless you know what you are doing
VA_FULL_DICT = {
    VA_PATH_CN:            VA_PATH_VAR,
    VA_M2TS_VOL_CN:        VA_M2TS_VOL_VAR,
    VA_M2TS_IDX_CN:        VA_M2TS_IDX_VAR,
    DURATION_CN:            DURATION_VAR,
    TR_COMP_CN:             TR_COMP_VAR,
    VA_VID_FPS_CN:         VA_VID_FPS_VAR,
    VA_SCRIPT_CN:          VA_SCRIPT_VAR,
    VA_COMMENT_CN:         VA_COMMENT_VAR,
    CLASSIFY_CN:            CLASSIFY_VAR,
    IDX1_CN:                IDX1_VAR,
    IDX2_CN:                IDX2_VAR,
    FULLDESP_CN:            FULLDESP_VAR,
    GRPTAG_CN:              GRPTAG_VAR,
    TITLE_CN:               TITLE_VAR,
    VA_AUDIO_SAMPLES_CN:   VA_AUDIO_SAMPLES_VAR,
}

#! dont change the order unless you know what you are doing
VD_FULL_DICT = {
    # VNX_CSV_PERSISTENT_KEY_DICT: these fields are always saved in CSV
    FULLPATH_CN:            FULLPATH_VAR,
    CRC32_CN:               CRC32_VAR,
    # VNX_USER_FIELDS_NAMING_DICT: these fields are to be input from the user
    GRPTAG_CN:              GRPTAG_VAR,
    TITLE_CN:               TITLE_VAR,
    LOCATION_CN:            LOCATION_VAR,
    CLASSIFY_CN:            CLASSIFY_VAR,
    IDX1_CN:                IDX1_VAR,
    IDX2_CN:                IDX2_VAR,
    SUPPLEMENT_CN:          SUPPLEMENT_VAR,
    FULLDESP_CN:            FULLDESP_VAR,
    SUFFIX_CN:              SUFFIX_VAR,
    ENABLE_CN:              ENABLE_VAR,
    # the following fields are just for presenting mediainfo
    # they have no usage in later stages
    DURATION_CN:            DURATION_VAR,
    FILESIZE_CN:            FILESIZE_VAR,
    EXTENSION_CN:           EXTENSION_VAR,
    FORMAT_CN:              FORMAT_VAR,
    TR_COMP_CN:             TR_COMP_VAR,
    TR_VIDEO_CN:            TR_VIDEO_VAR,
    TR_AUDIO_CN:            TR_AUDIO_VAR,
    TR_TEXT_CN:             TR_TEXT_VAR,
    TR_MENU_CN:             TR_MENU_VAR,
    QLABEL_CN:              QLABEL_VAR,
    TLABEL_CN:              TLABEL_VAR,
}

#! dont change the order unless you know what you are doing
#! if change, also change the order in `read/writeCSV4VR()`
VR_FULL_DICT = {
    VR_GRP_IDX_CN:         VR_GRP_IDX_VAR,
    VR_SUBGRP_IDX_CN:      VR_SUBGRP_IDX_VAR,
    ENABLE_CN:              ENABLE_VAR,
    FULLPATH_CN:            FULLPATH_VAR,
}

#* sub fields ----------------------------------------------------------------------------------------------------------
# NOTE dont change the order unless you know what you are doing

VA_BASE_LINE_USER_DICT = {
    GRPTAG_CN:              GRPTAG_VAR,
    TITLE_CN:               TITLE_VAR,
}
# 'presistent' means they are automatically in VA but to be used in VD
VA_PERSISTENT_DICT = {
    VA_M2TS_VOL_CN:        VA_M2TS_VOL_VAR,
    VA_M2TS_IDX_CN:        VA_M2TS_IDX_VAR,
    VA_AUDIO_SAMPLES_CN:   VA_AUDIO_SAMPLES_VAR,
}
VA_USER_DICT = {
    CLASSIFY_CN:            CLASSIFY_VAR,
    IDX1_CN:                IDX1_VAR,
    IDX2_CN:                IDX2_VAR,
    FULLDESP_CN:            FULLDESP_VAR,
    GRPTAG_CN:              GRPTAG_VAR,
    TITLE_CN:               TITLE_VAR,
}

VD_BASE_LINE_USER_DICT = {
    FULLPATH_CN:            FULLPATH_VAR,
    GRPTAG_CN:              GRPTAG_VAR,
    TITLE_CN:               TITLE_VAR,
    SUFFIX_CN:              SUFFIX_VAR,
}
# 'presistent' means they are automatically created in VD but to be used in VP
VD_PERSISTENT_DICT = {
    FULLPATH_CN:            FULLPATH_VAR,
    CRC32_CN:               CRC32_VAR,
}
VD_USER_DICT = {
    GRPTAG_CN:              GRPTAG_VAR,
    TITLE_CN:               TITLE_VAR,
    LOCATION_CN:            LOCATION_VAR,
    CLASSIFY_CN:            CLASSIFY_VAR,
    IDX1_CN:                IDX1_VAR,
    IDX2_CN:                IDX2_VAR,
    SUPPLEMENT_CN:          SUPPLEMENT_VAR,
    FULLDESP_CN:            FULLDESP_VAR,
    SUFFIX_CN:              SUFFIX_VAR,
    ENABLE_CN:              ENABLE_VAR,
}

COREFILE_DICT = {
    GRPTAG_CN:              GRPTAG_VAR,
    TITLE_CN:               TITLE_VAR,
    LOCATION_CN:            LOCATION_VAR,
    CLASSIFY_CN:            CLASSIFY_VAR,
    IDX1_CN:                IDX1_VAR,
    IDX2_CN:                IDX2_VAR,
    SUPPLEMENT_CN:          SUPPLEMENT_VAR,
    FULLDESP_CN:            FULLDESP_VAR,
    SUFFIX_CN:              SUFFIX_VAR,
    ENABLE_CN:              ENABLE_VAR,
}


#TODO add relation assert here to ensure vnx dicts are consistent

#* file extension vs expected format -----------------------------------------------------------------------------------
# these are the format string in libmediainfo

#! the values should be all lowercase to temporarily solve the mediainfo detection issue on UTF-8-BOM encoded ASS
#! details: libmediainfo wont recognise BOM-leading .ass file as ASS format, as a imperfect solution
#! details: we use make CoreFile.format to generate a lowercased format fallback from its extension
#! details: then the format will get matched
EXTS2FORMATS = {
    'mkv' : 'matroska',
    'mka' : 'matroska',
    'mp4' : 'mpeg-4',
    'm4a' : 'mpeg-4',

    'flac': 'flac',
    'aac' : 'aac',
    'ac3' : 'ac-3',
    'dts' : 'dts',

    'wav' : 'wave',
    'wav64': 'wave',

    'tak' : 'tak',
    'ape' : "monkey's audio",
    'wv'  : 'wavpack',
    'tak' : 'tak',
    'mp3' : 'mpeg audio',

    'webp': 'webp',
    'jpg' : 'jpeg',
    'jpeg': 'jpeg',
    'png' : 'png',
    'bmp' : 'bmp',
    'tif' : 'tiff',
    'tiff': 'tiff',
    'jxl' : 'jpeg xl',
    'heif': 'heif',

    'zip' : 'zip',
    '7z'  : '7-zip',
    'rar' : 'rar',

    # NOTE libmediainfo wont detect ass file as an SSA media track if the file has BOM for UTF-8 encoding
    # remember to specially handle this in VNx tools
    'ass' : 'ass',
}

#* the following defines the capability of VNx tools -------------------------------------------------------------------

# only the listed extensions will be processed by VNx tools
# which = the specification
VX_VID_EXTS     = ('mkv', 'mp4')            # video
VX_EXT_AUD_EXTS = ('mka', )                 # external audio
VX_STA_AUD_EXTS = ('flac', )                # standalone audio
VX_IMG_EXTS     = ('png',)                  # images, in SPs PNG is the only allowed image format
VX_SUB_EXTS     = ('ass',)                  # subtitle
VX_ARC_EXTS     = ('zip', '7z', 'rar')      # archives

# NOTE if updated, remember to update the corresponding checkers
VX_WITH_AUD_EXTS = VX_VID_EXTS + VX_EXT_AUD_EXTS + VX_STA_AUD_EXTS              # used to filter files in checkers/audio.py
VX_MAIN_EXTS = VX_VID_EXTS + VX_EXT_AUD_EXTS + VX_STA_AUD_EXTS + VX_IMG_EXTS   # used to filter files in VR matching
VX_ALL_EXTS = VX_MAIN_EXTS + VX_SUB_EXTS + VX_ARC_EXTS                          # used everywhere
VX_DEP_EXTS = VX_EXT_AUD_EXTS + VX_SUB_EXTS                                      # dependent exts i.e. the naming of the item depends on another file
VX_IDP_EXTS = VX_VID_EXTS + VX_STA_AUD_EXTS + VX_IMG_EXTS + VX_ARC_EXTS        # independent extensions

#* the following defines the capability of Sx tools --------------------------------------------------------------------

# ScansDrafter acceptable file extensions
SD_INFO_CSV_FILENAME : str = 'sd.csv'
SD_IMG_EXTS = tuple('png bmp tif tiff jpg jpeg webp'.split())
SD_ARC_EXTS = tuple('zip 7z rar'.split())
SD_ORIG_PATH_CN, SD_ORIG_PATH_VAR = '原始路径', 'sm_orig_path'
SD_PROC_PATH_CN, SD_PROC_PATH_VAR = '处理路径', 'sm_proc_path'
SD_CSV_DICT = {
    CRC32_CN: CRC32_VAR,
    SD_ORIG_PATH_CN: SD_ORIG_PATH_VAR,
    SD_PROC_PATH_CN: SD_PROC_PATH_VAR,
    }



SP_SRC_PATH_CN,     SP_SRC_DIR_PATH_VAR = '源目录', 'sp_src_path'
SP_DIRNAME_CN,           SP_DIRNAME_VAR = '目录命名', 'sp_dirname'
SP_VOLNUM_CN,             SP_VOLNUM_VAR = '卷号', 'sp_volnum'
SP_COMPLEMENT_CN,     SP_COMPLEMENT_VAR = '后缀说明', 'sp_complementry'
SP_CUSTOM_NAME_CN,   SP_CUSTOM_NAME_VAR = '自订名称', 'sp_custom_name'
SP_CSV_DICT = {
    SP_SRC_PATH_CN: SP_SRC_DIR_PATH_VAR,
    SP_DIRNAME_CN: SP_DIRNAME_VAR,
    SP_VOLNUM_CN: SP_VOLNUM_VAR,
    SP_COMPLEMENT_CN: SP_COMPLEMENT_VAR,
    SP_CUSTOM_NAME_CN: SP_CUSTOM_NAME_VAR,
    }

#* the following defines the capability of Mx tools --------------------------------------------------------------------

AD_INFO_CSV_FILENAME : str = 'ad.csv'
AD_ARC_EXTS = tuple('zip 7z rar'.split())
AD_AUD_EXTS = tuple('wav wav64 flac tak ape wv mp3 m4a'.split())
AD_EAC_EXTS = tuple('cue log'.split())
AD_VID_EXTS = ('mkv', )
AD_IMG_EXTS = SD_IMG_EXTS
AD_SRC_EXTS = AD_AUD_EXTS + AD_EAC_EXTS + AD_VID_EXTS + AD_IMG_EXTS

AD_ORIG_PATH_CN, AD_ORIG_PATH_VAR = '原始路径', 'sm_orig_path'
AD_PROC_PATH_CN, AD_PROC_PATH_VAR = '处理路径', 'sm_proc_path'
AD_FILE_TYPE_CN, AD_FILE_TYPE_VAR = '文件归类', 'sm_file_type'

AD_CSV_DICT = {
    CRC32_CN: CRC32_VAR,
    AD_ORIG_PATH_CN: AD_ORIG_PATH_VAR,
    AD_PROC_PATH_CN: AD_PROC_PATH_VAR,
    }

AD_FILE_TYPE_CD_0 = 'Album'
AD_FILE_TYPE_BK_0 = 'BK'
AD_FILE_TYPE_MV_0 = 'MV'





AP_SRC_PATH_CN,       AP_SRC_PATH_VAR = '源目录', 'ap_src_path'
AP_DIR_TYPE_CN,      AP_DIR_TYPE_VAR = '目录类型', 'ap_src_dir_type'
AP_ALBUM_DATE_CN,    AP_ALBUM_DATE_VAR = '年月日', 'ap_yymmdd'
AP_ALBUM_PRENAME_CN, AP_ALBUM_PRENAME_VAR = '专辑类型', 'ap_album_prename'
AP_ALBUM_NAME_CN,    AP_ALBUM_NAME_VAR = '专辑名称', 'ap_album_name'
AP_ALBUM_AFTNAME_CN, AP_ALBUM_AFTNAME_VAR = '专辑后缀', 'ap_album_aftname'
AP_ALBUM_ARTISTS_CN, AP_ALBUM_ARTISTS_VAR = '专辑艺术家', 'ap_album_artists'
AP_ALBUM_EDITION_CN, AP_ALBUM_EDITION_VAR = '专辑版本', 'ap_album_edition'
AP_CATALOG_CN,           AP_CATALOG_VAR = 'CATALOG', 'ap_catalog'
AP_VGMDB_UID_CN,     AP_VGMDB_UID_VAR = 'VGMDB UID', 'ap_vgmdb_uid'

AP_DIR_TYPE_DSK_CN = '音频'
AP_DIR_TYPE_BKS_CN = '扫图'
AP_DIR_TYPE_SPS_CN = '视频'

AP_CSV_DICT = {
    AP_SRC_PATH_CN: AP_SRC_PATH_VAR,
    AP_DIR_TYPE_CN: AP_DIR_TYPE_VAR,
    AP_ALBUM_DATE_CN: AP_ALBUM_DATE_VAR,
    AP_ALBUM_PRENAME_CN: AP_ALBUM_PRENAME_VAR,
    AP_ALBUM_NAME_CN: AP_ALBUM_NAME_VAR,
    AP_ALBUM_AFTNAME_CN: AP_ALBUM_AFTNAME_VAR,
    AP_ALBUM_ARTISTS_CN: AP_ALBUM_ARTISTS_VAR,
    AP_CATALOG_CN: AP_CATALOG_VAR,
    AP_VGMDB_UID_CN: AP_VGMDB_UID_VAR,
    }




#* other variables -----------------------------------------------------------------------------------------------------
# the following is customisable, but they should not be exposed to the user configuration file

# the all possible output formats of VA
VA_OUTPUT_EXTS : list[str] = ['csv', 'yaml', 'json']

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
