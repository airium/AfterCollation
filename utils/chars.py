__all__ = [
    'isDecimal',
    'quotChars',
    'unquotChars',
    'quotFields4CSV',
    'unquotFields4CSV',
    'suppressPunctuation',
    'getPrintLen',
    ]

import string
from typing import Optional
from configs.chars import FLEXIBLE_PUNCTUATIONS

try:
    from configs.chars import CSV_QUOT_CHAR
except ImportError:
    CSV_QUOT_CHAR = '"'




def isDecimal(chars: str) -> bool:
    return chars.replace('.', '', 1).isdigit()




def unquotChars(chars: str, quot: Optional[str] = None) -> str:

    if not chars: return ''
    quot = CSV_QUOT_CHAR if quot == None else quot

    try:
        chars = str(chars)
    except:
        return ''
    while chars.startswith(quot) and chars.endswith(quot):
        chars = chars[1:-1]

    return chars




def quotChars(chars: str, quot: Optional[str] = None) -> str:

    if not chars: return ''
    quot = CSV_QUOT_CHAR if quot == None else quot

    return f'{quot}{unquotChars(chars, quot)}{quot}'




def quotFields4CSV(entries: list[dict], quot: Optional[str] = None, sep: Optional[str] = None) -> list[dict]:
    '''Return a copy of the input list of dict, with all chars quoted.'''

    if not entries: return []
    quot = CSV_QUOT_CHAR if quot == None else quot
    sep = ',' if sep == None else sep

    ret: list[dict] = []
    for entry in entries:
        d = {}
        for k, v in entry.items():
            if isinstance(v, str) and v and all(c in string.hexdigits for c in v):
                v = quotChars(v, quot)
            elif isinstance(v, str) and v and (sep in v):
                v = quotChars(v, quot)
            elif not isinstance(v, str):
                v = quotChars(v, quot)
            d[k] = v
        ret.append(d)

    return ret




def unquotFields4CSV(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    ret = []
    for entry in entries:
        d = {}
        for k, v in entry.items():
            d[k] = unquotChars(v)
        ret.append(d)
    return ret




def suppressPunctuation(chars: str, underscore: bool = True) -> str:
    '''
    Fuzzy matching two filenames is not that easy, partially due to the flexible choice of punctuations.
    This function is a cheap solution by converting flexible punctuations to underscores or removing them.

    If `underscore` == True, then flexible punctuations will be converted to underscores.
    If not, then punctuations along with whitespaces will be all removed.
    i.e. `underscore` means the filename should still have used some punctuations, though the choice is different.
    '''
    if not chars: return ''
    char = '_' if underscore else ''

    for c in FLEXIBLE_PUNCTUATIONS:
        chars = chars.replace(c, char)
    for c in string.whitespace:
        chars = chars.replace(c, '')
    return chars




def getPrintLen(chars: str) -> int:
    chars = chars.replace('｢', ' ')
    chars = chars.replace('｣', ' ')
    len_unispace = len([c for c in chars if c in string.printable])
    # NOTE we don't know the font used by the terminal
    # so we assume the width of an non-ascii char is 2
    # which maximizes the UE with fonts such as Sarasa Unispaces
    len_doublespace = (len(chars) - len_unispace) * 2
    return len_unispace + len_doublespace
