import math
import string
from configs.chars import FLEXIBLE_PUNCTUATIONS


__all__ = ['unquotChars', 'quotChars', 'quotEntries4CSV', 'unquotEntries4CSV',
           'suppressPunctuation', 'getPrintLen', 'isDecimal',
           'formatFileSize1', 'formatFileSize2', 'formatTimeLength']



def isDecimal(chars:str) -> bool:
    return chars.replace('.', '', 1).isdigit()



def unquotChars(chars:str) -> str:
    if not chars:
        return ''
    try:
        chars = str(chars)
    except:
        return ''
    return chars.strip(string.whitespace + '\'\"')




def quotChars(chars:str, quot:str='"') -> str:
    return f'{quot}{unquotChars(chars)}{quot}'




def quotEntries4CSV(entries:list[dict], quot:str='"') -> list[dict]:
    '''Return a copy of the input list of dict, with all chars quoted.'''
    ret = []
    for entry in entries:
        d = {}
        for k, v in entry.items():
            if isinstance(v, str) and v and all(c in string.hexdigits for c in v):
                v = quotChars(v, quot)
            elif isinstance(v, str) and v and (',' in v):
                v = quotChars(v, quot)
            elif not isinstance(v, str):
                v = quotChars(v, quot)
            d[k] = v
        ret.append(d)
    return ret




def unquotEntries4CSV(entries:list[dict[str, str]]) -> list[dict[str, str]]:
    ret = []
    for entry in entries:
        d = {}
        for k, v in entry.items():
            d[k] = unquotChars(v)
        ret.append(d)
    return ret




def suppressPunctuation(chars:str, underscore:bool=True) -> str:
    '''
    Fuzzy matching two filenames is not that easy, partially due to the flexible choice of punctuations.
    This function is a cheap solution by converting flexible punctuations to underscores or removing them.

    If `underscore` is True, then flexible punctuations will be converted to underscores.
    If not, then punctuations along with whitespaces will be all removed.
    i.e. `underscore` means the filename should still have used some punctuations, though the choice is different.
    '''
    if not chars:
        return ''
    try:
        chars = str(chars)
    except Exception:
        return ''
    char = '_' if underscore else ''
    for c in FLEXIBLE_PUNCTUATIONS: chars = chars.replace(c, char)
    for c in string.whitespace: chars = chars.replace(c, '')
    return chars




def getPrintLen(chars:str) -> int:
    chars = chars.replace('｢', ' ')
    chars = chars.replace('｣', ' ')
    len_unispace = len([c for c in chars if c in string.printable])
    # NOTE we don't know the font used by the terminal
    # so we assume the width of an non-ascii char is 2
    # which maximizes the UE with fonts such as Sarasa Unispaces
    len_doublespace = (len(chars) - len_unispace) * 2
    return len_unispace + len_doublespace



def formatFileSize1(number:int) -> str:
    units = ['B', 'K', 'M', 'G', 'T', 'P']
    if number:
        base = 1000
        magnitude = int(math.floor(math.log(number, 1000)))
        return f'{number/base**magnitude:.3f}{units[magnitude]}'
    else:
        return '0B'




def formatFileSize2(n:int) -> str:
    if n < 0:
        return ''
    if n == 0:
        return '0'
    else:
        g, n = divmod(n, 1000**3)
        m, n = divmod(n, 1000**2)
        k, n = divmod(n, 1000**1)
        ret = ''
        ret += (f'{g:2d}g' if g else  '   ')
        ret += (f'{m:3d}m' if m else '    ')
        ret += (f'{k:3d}k' if k else '    ')
        ret += (f'{n:3d}'  if n else  '   ')
        return ret




def formatTimeLength(n:int) -> str:
    '''The input `n` is in milliseconds.'''
    if n < 0:
        return ''
    if n == 0:
        return '0'
    else:
        h, n = divmod(n, 3600000)
        m, n = divmod(n,   60000)
        s, n = divmod(n,    1000)
        ret = ''
        ret += (f'{h:2d}h' if h else '   ')
        ret += (f'{m:2d}m' if m else '   ')
        ret += (f'{s:2d}s' if s else '   ')
        ret += (f'{n:3d}'  if n else '   ')
        return ret




