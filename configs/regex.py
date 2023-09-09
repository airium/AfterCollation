import re as _re
from re import compile as _rc

CRC32_BASIC_REGEX = _rc(r'(0x)?(?P<crc32>[0-9a-f]{8})', _re.I)
CRC32_STRICT_REGEX = _rc(r'^(?P<crc32>[0-9a-f]{8})$', _re.I)
CRC32_IN_FILENAME_REGEX = _rc(r'\[(?P<crc32>[0-9a-f]{8})\]', _re.I)
CRC32_CSV_FIELD_REGEX = _rc(r'^(0x)?(?P<crc32>[0-9a-f]{8})$', _re.I)

# used to match simple filename after encoding i.e. OKE
UNNAMED_TRANSCODED_FILENAME_REGEX = _rc(
    r'^'
    r'(?P<m2ts_idx>[0-9]{5}([-_](?P<sub_idx>[0-9]{1,3}))?)?'
    r'(?P<stem>(.(?!(\[[0-9a-f]{8}\])?\.(mkv|mka|mp4|flac|png|ass|7z|zip|rar)))*.)'
    r'(\[(?P<crc32>[0-9a-f]{8})\])?\.(mkv|mka|mp4|flac|png|ass|7z|zip|rar)'
    r'$', _re.I)
# used together with the above, try to get 'c' and 'i1' but if failed, push everything to 's'
EXPECTED_SIMPLE_FILESTEM_REGEX = _rc(
    r'^'
    r'(?P<c>[^0-9]*)[ -_]*'  #! the produced 'c' can be very dirty
    r'(?P<i1>[0-9]{1,3}(\.([0-9][1-9]|[1-9]))?)?' #! [0-9][1-9] must be placed in the front
    r'(?P<s>.*)'  #! this make the regex always match, and the produced 's' can be very dirty
    r'$', _re.I)
# this is similar to `UNNAMED_TRANSCODED_FILENAME_REGEX` but we forced the existence of `m2ts_idx`
# it is used in VD to find the possible `m2ts_idx` and `sub_idx` for the user to fill
STRICT_TRANSCODED_FILESTEM_REGEX = _rc(r'^(?P<m2ts_idx>[0-9]{5})(|[^0-9].*)$')

# this is used to exclude the ending crc32 if it exists
TRANSCODED_FILESTEM_REGEX = _rc(r'^(?P<stem>(.(?!\[[a-f0-9]{8}\]))*.)(\[(?P<crc32>[0-9a-f]{8})\])?$', _re.I)




LIBMEDIAINFO_CHAPTER_REGEX = _rc(r'(?P<h>[0-9]{2})_(?P<m>[0-9]{2})_(?P<ms>[0-9]{5})')

VA_OUT_FILENAME_REGEX = _rc(r'^VA-[0-9]{6}-[0-9]{6}\.(csv|json|yaml)$')
VP_CSV_FILENAME_REGEX = _rc(r'^VP-[0-9]{6}-[0-9]{6}\.csv$', _re.I)
VR_OUT_FILENAME_REGEX = _rc(r'^VR-[0-9]{6}-[0-9]{6}\.csv$', _re.I)
SP_CSV_FILENAME_REGEX = _rc(r'^SP-[0-9]{6}-[0-9]{6}\.csv$', _re.I)

VCBS_SERIES_ROOT_DIRNAME_PATTERN = _rc(
    r'^'
    r'\[(?P<g>[^]]+)\]'
    r'(?P<t>[^[]+)'
    r'$'
    , _re.I)

VCBS_SEASON_ROOT_DIRNAME_PATTERN = _rc(
    r'^'
    r'\[(?P<g>[^]]+)\]'
    r'(?P<t>[^[]+)'
    r'\[(?P<qlabel>[^]]*[0-9]{3}p)\]'
    r'(\[(?P<x>[^0-9][^]]*)\])?'
    r'$'
    , _re.I)

VCBS_COREFILE_FILENAME_PATTERN = _rc(
    r'^'
    r'\[(?P<g>[^]]+)\]'
    r'((?P<b1>\[)?(?P<t>[^[\]]+)(?(b1)\]|))'
    r'( )*(\[(BD|DVD|Web)Rip\])?( )*'
    #! 'f' may be missing or be filled with arbitrary characters, there is no easy method to match it 100% correctly
    #! we assume all characters before the qlabel are part of it
    #! if there is no qlabel, then 'f' will eat up all remaining, only backtracked for 'e'
    r'(?P<f>(.(?!(BD|DVD|Web)Rip\]|(((Ma|Hi|YUV)(10|444|422)[^\]_]+|BDRemux)_)?([1-9][0-9]{2,3}p|4K)(_HDR)?\]))*)'
    # this is used to match very old release
    r'( )*(\[(BD|DVD|Web)Rip\])?( )*'
    #! qlabel and tlabel are bundled together
    # YUV/422/BDRemux are used to match very old release
    r'(\[(?P<qlabel>(((Ma|Hi|YUV)(10|444|422)[^\]_]+|BDRemux)_)?([1-9][0-9]{2,3}p|4K)(_HDR)?)\]'
    # this is used to match very old release
    r'( )*(\[(BD|DVD|Web)Rip\])?( )*(\[BDRemux\])?( )*'
    # h264/BDRemux are used to match very old release
    r'\[(?P<tlabel>([2-9]?x26[45]|h264|BDRemux)(_(1[0-9]|[2-9])?(flac|aac|ac3|dts))*)\])?'
    # this is used to match very old release
    r'( )*(\[(BD|DVD|Web)Rip\])?( )*'
    # the additional ']' is used to match existing human errors
    r'((?P<b2>\[)?(\.)?(?P<x>[^]]*)(?(b2)\]|)(?=\]?\.(mkv|mka|mp4|flac|png|ass|7z|zip|rar)))'
    # this is used to match very old release
    r'( )*(\[(BD|DVD|Web)Rip\])?( )*\]?'
    r'\.(?P<e>mkv|mka|mp4|flac|png|ass|7z|zip|rar)'
    r'$'
    , _re.I)

FULL_DESP_REGEX = _rc(
    r'^'
    r'((?P<c>[^0-9]*)?(v[2-9])?)'
    r'[ _]*'
    r'((?P<i1>[0-9]{0,3})(v[2-9])?)'
    r'[ _]*'
    r'((?P<i2>[0-9]{0,2})(v[2-9])?)'
    r'[ _]*'
    r'(?P<s>.*)'
    r'$'
    , _re.I)






VGMDB_CATALOG_PATTERN = _rc(r'^(?P<prefix>.+-)(?P<start>[0-9]{1,5})~(?P<end>[0-9]{1,4})$')
VGMDB_DATE_FORMAT = _rc(r'(?P<year>(19[5-9]|20[0-2])[0-9])-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})')


BDMV_DIRNAME_REGEX = _rc(r'^(?P<pre>.*)(?P<idx>[0-9]{1,3})(?P<aft>[^0-9]*)$')
BDMV_M2TS_FILENAME_REGEX = _rc(r'^[0-9]{5}\.m2ts$', _re.I)

MENU_TEXT_STD_REGEX = _rc(r'((?P<lang>[a-z]{2}):)?(?P<text>Chapter (?P<idx>[0-9]{2,3}))')
MENU_TEXT_CUSTOM_REGEX = _rc(r'((?P<lang>[a-z]{2}):)?(?P<text>.*)')


ASS_SUFFIX_PATTERN = _rc(r'\.(?P<lang>.*)')
VID_SUFFIX_PATTERN = _rc(r'\[(?P<lang>.*)\]')
ASS_INLINE_FONTNAME_BASE_PATTERN = _rc(r'\\fn([^\\}]+)')
ASS_INLINE_STYLENAME_BASE_PATTERN = _rc(r'\\r([^\\}]+)')
ASS_FILENAME_EARLY_PATTERN = _rc(r'^(?P<name>.*)(?P<idx>[0-9]{1,3}(\.[1-9]{1,2})?)[.-]?(?P<lang>(chs|cht|sc|tc)(&(jp|jap|jpn))?)?\.ass', _re.IGNORECASE)

# NOTE this is a bytes regex instead of str, since we don't need to decode stderr
DWEBP_STDERR_PARSE_REGEX = _rc(rb'can be decoded \(dimensions: (?P<width>[0-9]{1,5}) x (?P<height>[0-9]{1,5}) (?P<alpha> \(with alpha\))?. Format: (?P<mode>lossy|lossless)\).')
ALBUM_HIRES_REGEX = _rc(r'(?P<b>16|24|32)bit_(?P<fs>48|96|192|384)kHz')
POSSIBLE_CATALOG_REGEX = _rc(r'^[a-zA-z0-9][a-zA-z0-9\-_ ]+([0-9]~[0-9]{0,3})?$')
CATALOG_MULTIDISC_REGEX = _rc(r'(?P<catalog>.+[0-9])(~[0-9]{1,3}|-([1-9]|0[1-9])|[a-z])$')

# NOTE try to find both '012. XXXX.EXT' and '012.EXT' where the latter is not a rare mistake
FRONT_INDEXED_TRACKNAME_PATTERN = _rc(r'(?P<idx>[0-9]{1,3})((?P<dot>\.)?(?P<space> )?(?P<trname>.*)|)\.(?P<ext>flac|mp3|m4a)')
CUE_FILENAME_LINE_REGEX = _rc(r'(FILE "(?P<filename>.+\.flac)" WAVE)')



# some albums may lack yymmdd, the only general pattern is the format suffix
ALBUM_DIR_MIN_PATTERN = _rc(r'^.+\((flac|wv|aac|mp3)((\+[a-z0-9]{1,4})*)\)$')



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
#! remember to update the year in 2030
ALBUM_DIR_FULL_PATTERN = _rc(
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




COVER_ART_FILENAME_PATTERN = _rc(r'^(cover|front)[0-9]{0,3}\.(jpg|jpeg|png|bmp|webp)$', _re.I)

# don't leak the group name
del _re, _rc