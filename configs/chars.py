import string

TAG_SPLITTER = '&'


# these are the set of characters considered safe in each naming part
#! though they are not 100% safe
SAFE_G_CHARS = ' -.7ABCDEFGHIKLMNOPQRSTUVWXYZabcdefghijklmnoprstuvwyz'
SAFE_T_CHARS = string.ascii_letters + string.digits + ' ,.-~？!@'
SAFE_L_CHARS = string.ascii_letters +                 ' '
SAFE_C_CHARS = string.ascii_letters +                 ' _&'
SAFE_F_CHARS = string.ascii_letters + string.digits + ' ,.-~？!@()&\''
SAFE_X_CHARS = string.ascii_letters

# these characters are rarely used in naming but allowed, so give a warning
# WARN_CHARS = "`^!#$%&',;._+-=~@()[]{} ？＜＞"
WARN_G_CHARS = 'Jqx012345689'
WARN_T_CHARS = '\';_+='
WARN_L_CHARS = '()' + string.digits
WARN_C_CHARS = '()' + string.digits
WARN_F_CHARS = '`^#$%&;_+={}＜＞'
WARN_X_CHARS = string.digits

# allowed in naming fields, but should not be placed at the starting or ending of the field
INVALID_LEADING_CHARS, INVALID_ENDING_CHARS = ' .-&', ' -&'

from .user import (
    USER_GROUP_NAME_CHARS,
    USER_SHOW_TITLE_CHARS,
    USER_LOCATION_CHARS,
    USER_CLASSIFICATION_CHARS,
    USER_DESCRIPTION_CHARS,
    USER_SUFFIX_CHARS,
)

VALID_G_CHARS = SAFE_G_CHARS + WARN_G_CHARS + USER_GROUP_NAME_CHARS
VALID_T_CHARS = SAFE_T_CHARS + WARN_T_CHARS + USER_SHOW_TITLE_CHARS
VALID_L_CHARS = SAFE_L_CHARS + WARN_L_CHARS + USER_LOCATION_CHARS
VALID_C_CHARS = SAFE_C_CHARS + WARN_C_CHARS + USER_CLASSIFICATION_CHARS
VALID_F_CHARS = SAFE_F_CHARS + WARN_F_CHARS + USER_DESCRIPTION_CHARS
VALID_X_CHARS = SAFE_X_CHARS + WARN_X_CHARS + USER_SUFFIX_CHARS

# user fields containing the following character will be filtered out from the input
#! the program will automatically split any path/location before applying the filter to each part
#! so dont remove '/\\' from the definition
INVALID_CHARS = '<>:"/\\|?*' + '\t\n\r\v\f'
# the path to source files will be instead filtered as below
#! to accept Linux/MacOS path input, dont filter any input part part with `INVALID_CHARS`
INVALID_PATH_STARTING_CHARS = INVALID_CHARS + ' .'
INVALID_PATH_ENDING_CHARS = INVALID_CHARS + ' '

FLEXIBLE_PUNCTUATIONS = (
    '‹›<>＜＞《》〈〉〔〕〘〙【】〖〗〚〛｢｣「」『』[]［］{}｛｝()（）'
    '!！?？⁄/／\\＼|｜*＊:꞉："＂\'＇〝〞〟'
    '@＠#＃$＄%％&＆+＋,，-－.．;；=＝^＾_＿`｀~～'
    )
