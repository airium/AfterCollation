import re
from re import compile as rc



BASIC_CRC32_PATTERN = rc(r'^(?P<crc32>[0-9a-f]{8})$', re.IGNORECASE)
CRC32_IN_FILENAME_PATTERN = rc(r'\[(?P<crc32>[0-9a-f]{8})\]', re.IGNORECASE)
CRC32_CSV_PATTERN = rc(r'^(0x)?(?P<crc32>[0-9a-f]{8})$', re.IGNORECASE)




GENERIC_FILENAME = rc(r'^(?P<m2ts_idx>[0-9]{5})?(?P<stem>.*[^]])(\[(?P<crc32>[0-9a-f]{8})\])?\.(mkv|mka|mp4|flac|png|ass|7z|zip|rar)$', re.IGNORECASE)
EXPECTED_SIMPLE_NAME = rc(r'^(?P<typename>[^0-9]*)[ -]*(?P<idx>[0-9]*(\.[1-9])?)[ -]*(?P<note>.*)$')

MEDIAINFO_CHAPTER_PATTERN = rc(r'(?P<h>[0-9]{2})_(?P<m>[0-9]{2})_(?P<ms>[0-9]{5})')
VGMDB_CATALOG_PATTERN = rc(r'^(?P<prefix>.+-)(?P<start>[0-9]{1,5})~(?P<end>[0-9]{1,4})$')
VGMDB_DATE_FORMAT = rc(r'(?P<year>(19[5-9]|20[0-2])[0-9])-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})')
VNA_CONFS_FILENAME_PATTERN = rc(r'^VNA-[0-9]{6}-[0-9]{6}\.(csv|json|yaml)$')
VND_TABLE_FILENAME_PATTERN = rc(r'^VND-[0-9]{6}-[0-9]{6}\.csv$')
VNR_TABLE_FILENAME_PATTERN = rc(r'^VNR-[0-9]{6}-[0-9]{6}\.csv$')


# TODO [^0-9[\]] is not robust for misclabel
VCBS_SERIES_ROOT_DIRNAME_PATTERN = rc(r'^\[(?P<grptag>.*(VCB-Studio|VCB-S).*)\] (?P<title>[^\[\]]+)( \[(?P<misclabel>[^0-9[\]])\])?$')
VCBS_SEASON_ROOT_DIRNAME_PATTERN = rc(r'^\[(?P<grptag>.*(VCB-Studio|VCB-S).*)\] (?P<title>[^\[\]]+) \[(?P<qlabel>[^\]]*[0-9]{3}p)\](\[(?P<misclabel>[^0-9[\]])\])?$')
VOLUME_NAME_PATTERN = rc(r'^(?P<pre>.*)(?P<idx>[0-9]{1,3})(?P<aft>[^0-9]*)$')
OKE_FILESTEM_PATTERN = rc(r'^(?P<idx1>[0-9]{5})[ -]*(?P<idx2>[0-9]*) *(\[(?P<crc32>[0-9a-zA-Z]{8})\])?$')
STD_CHAP_TXT_PATTERN = rc(r'((?P<lang>[a-z]{2}):)?(?P<text>Chapter (?P<idx>[0-9]{2,3}))')
CUSTOM_CHAP_PATTERN = rc(r'((?P<lang>[a-z]{2}):)?(?P<text>.*)')
BDMV_M2TS_NAME_PATTERN = rc(r'^[0-9]{5}\.(m2ts|M2TS)$')
UNAMED_OKE_STEM_PATTERN = rc(r'^(?P<stem>.+)(\[(?P<crc32>[0-9a-fA-F]{8})\])$')
ASS_SUFFIX_PATTERN = rc(r'\.(?P<lang>.*)')
VID_SUFFIX_PATTERN = rc(r'\[(?P<lang>.*)\]')
ASS_INLINE_FONTNAME_BASE_PATTERN = rc(r'\\fn([^\\}]+)')
ASS_INLINE_STYLENAME_BASE_PATTERN = rc(r'\\r([^\\}]+)')
ASS_FILENAME_EARLY_PATTERN = rc(r'^(?P<name>.*)(?P<idx>[0-9]{1,3}(\.[0-9])?)[.-]?(?P<lang>(chs|cht|sc|tc)(&(jp|jap|jpn))?)?\.ass', re.IGNORECASE)

# NOTE this is a bytes regex instead of str, since we don't need to decode stderr
DWEBP_STDERR_PARSE_PATTERN = rc(rb'can be decoded \(dimensions: (?P<width>[0-9]{1,5}) x (?P<height>[0-9]{1,5}) (?P<alpha> \(with alpha\))?. Format: (?P<mode>lossy|lossless)\).')
HIRES_PATTERN = rc(r'(?P<b>16|24|32)bit_(?P<fs>48|96|192|384)kHz')
POSSIBLE_CATALOG_PATTERN = rc(r'^[a-zA-z0-9][a-zA-z0-9\-_ ]+([0-9]~[0-9]{0,3})?$')
CATALOG_MULTIDISC_PATTERN = rc(r'(?P<catalog>.+[0-9])(~[0-9]{1,3}|-([1-9]|0[1-9])|[a-z])$')
# NOTE try to find both '012. XXXX.EXT' and '012.EXT' where the latter is not a rare mistake
FRONT_INDEXED_TRACKNAME_PATTERN = rc(r'(?P<idx>[0-9]{1,3})((?P<dot>\.)?(?P<space> )?(?P<trname>.*)|)\.(?P<ext>flac|mp3|m4a)')
FILENAME_IN_CUE_PATTERN = rc(r'(FILE "(?P<filename>.+\.flac)" WAVE)')

# some albums may lack yymmdd, the only general pattern is the format suffix
ALBUM_DIR_MIN_PATTERN = rc(r'^.+\((flac|aac|mp3)((\+[a-z0-9]{1,4})*)\)$')
# NOTE
# structure [eac][year+month+day>]pre｢mid｣aft／art+art_tr[edt盤]+edt_ts[hr]hr_ts(af+if+vf)
# <year/month/day> is not enforced
# <pre> may have leading/trailing space (need 1/1)
# <mid> may have leading/trailing space (need 0/0)
# <aft> may have leading/trailing space (need 1/0 if <mid> else 0/0)
# <art> will not eat the last character before [edition]/[hi_res]/(flac)
# <art_ts> therefore always capture it (i.e. use . instead of .?)
# <art_ts> should depends on <slash> to make a required space after '｣' is always captured by <aft>
# <ed> requires the '盤/版' to works, which is unstable
# TODO update \[[^[\]盤]+盤\] to negative lookahead
# NOTE remember to update the year in 2030
ALBUM_DIR_FULL_PATTERN = rc(
    r"^(\[(?P<eac>EAC|XLD)\])?( )*"
    r"(\[(?P<year>[0129][0-9])(?P<month>[0-9]{2})?(?P<day>[0-9]{2})?\])?"
    r"(?P<pre>[^｢｣／[\]()]*)?"
    r"(?P<quot>｢)?"
    r"(?P<mid>(?(quot)([^｣]+)|))(?(quot)｣|)"
    r"(?P<aft>(?(quot)[^／[\]()]*|))"
    r"(?P<slash>／)?"
    r"(?(slash)(?P<art>(.(?!\[[^\[\]盤版]+(盤|版)\]|\[(16|24|32)bit|\((flac|aac|mp3)))*)(?P<art_ts>.)|)"
    r"(?P<ed>\[(?P<edn>[^[\]盤版]+(盤|版))\])?(?P<ed_ts>(?(ed)( )*)|)"
    r"(?P<hr>\[((?P<bit>16|24|32)bit_(?P<freq>48|96|192|384)kHz)\])?(?P<hr_ts>(?(hr)( )*)|)"
    r"\("
    r"(?P<af>(flac\+aac\+mp3|flac\+mp3\+aac|flac\+aac|flac\+mp3|flac|aac|mp3))"
    r"(\+(?P<if>webp\+jpg|jpg\+webp|webp|jpg))?"
    r"(\+(?P<vf>mkv))?"
    r"\)$")

# don't leak the group name
del re, rc