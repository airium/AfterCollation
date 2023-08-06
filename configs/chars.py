import string

# these are the minimum set of characters considered safe in each naming part
#! though they are not 100% safe
SAFE_G_CHARS = string.ascii_letters + string.digits + ' .-'
SAFE_T_CHARS = string.ascii_letters + string.digits + ' .-' + ',~？!@'
SAFE_F_CHARS = string.ascii_letters + string.digits + ' ,.-~？!@' + '()&'''
SAFE_X_CHARS = string.ascii_letters

# these characters are rarely used in naming but allowed, so give a warning
WARN_G_CHARS = ''
WARN_T_CHARS = '`^!#$%&\'",;._+-=~@[]{} ？＜＞'
WARN_F_CHARS = '`^!#$%&\'",;._+-=~@[]{} ？＜＞'
WARN_X_CHARS = string.digits
WARN_CHARS = "`^!#$%&',;._+-=~@()[]{} ？＜＞"

from .user import (
    USER_GROUP_NAME_CHARS,
    USER_SHOW_TITLE_CHARS,
    USER_DESCRIPTION_CHARS,
    USER_SUFFIX_CHARS,
)

VALID_G_CHARS = SAFE_G_CHARS + WARN_G_CHARS + USER_GROUP_NAME_CHARS
VALID_T_CHARS = SAFE_T_CHARS + WARN_T_CHARS + USER_SHOW_TITLE_CHARS
VALID_F_CHARS = SAFE_F_CHARS + WARN_F_CHARS + USER_DESCRIPTION_CHARS
VALID_X_CHARS = SAFE_X_CHARS + WARN_X_CHARS + USER_SUFFIX_CHARS

# path input containing the following character will be rejected
# user fields containing the following character will be filtered
INVALID_CHARS = '<>:"/\\|?*'
INVALID_PATH_STARTING_CHARS = string.whitespace + './\\'
INVALID_PATH_ENDING_CHARS = string.whitespace + '/\\'

FLEXIBLE_PUNCTUATIONS = (
    '‹›<>＜＞《》〈〉〔〕〘〙【】〖〗〚〛｢｣「」『』[]［］{}｛｝()（）'
    '!！?？⁄/／\\＼|｜*＊:꞉："＂\'＇〝〞〟'
    '@＠#＃$＄%％&＆+＋,，-－.．;；=＝^＾_＿`｀~～'
    )
