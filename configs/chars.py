import string

# these are the character whitelists used to filter the user input in VND.csv
VALID_BASE_CHARS = string.ascii_letters + string.digits
VALID_LANGTAG_CHARS = string.ascii_letters + '&'
VALID_GRPNAME_CHARS = VALID_BASE_CHARS + '&. -'
VALID_FILENAME_CHARS = VALID_BASE_CHARS + "`^!#$%&',;._+-=~@()[]{} ？＜＞"
# ？꞉⁄‹›＜＞

INVALID_FILENAME_CHARS = '<>:"/\\|?*'

FLEXIBLE_PUNCTUATIONS = (
    '‹›<>＜＞《》〈〉〔〕〘〙【】〖〗〚〛｢｣「」『』[]［］{}｛｝()（）'
    '!！?？⁄/／\\＼|｜*＊:꞉："＂\'＇〝〞〟'
    '@＠#＃$＄%％&＆+＋,，-－.．;；=＝^＾_＿`｀~～'
    )
