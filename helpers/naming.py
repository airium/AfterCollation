from __future__ import annotations

from pathlib import PurePath

from configs import *
from utils.chars import isDecimal
import helpers.corefile as hc


__all__ = [
    'rmInvalidChars',
    'normInputPath',
    'normSingleGroupTag',
    'normFullGroupTag',
    'normTitle',
    'normSingleLocation',
    'normFullLocation',
    'normClassification',
    'normDescription',
    'normDecimal',
    'normSingleSuffix',
    'normFullSuffix',
    'splitGroupTag',
    'cmpCoreFileNaming',
    ]




def rmInvalidChars(chars: str) -> str:
    '''Blacklist-based string cleaner that removes any invalid characters for path on Windows.'''
    return ''.join([c for c in chars if (c not in INVALID_CHARS)])




def normInputPath(chars: str) -> str:
    '''
    Clean the input string for actual path.
    #! relative path is not allowed
    #! this cleaner will make relative paths inaccessible so get them caught in chkNamingDicts()
    '''
    return chars.lstrip(INVALID_PATH_STARTING_CHARS).rstrip(INVALID_PATH_ENDING_CHARS)




def normSingleGroupTag(chars: str) -> str:
    '''Whitelist-based group name cleaner.'''
    chars = rmInvalidChars(chars)
    chars = ''.join([c for c in chars if c in VALID_G_CHARS])
    chars = chars.lstrip(INVALID_LEADING_CHARS).rstrip(INVALID_ENDING_CHARS)
    return chars




def normFullGroupTag(chars: str) -> str:
    '''Disassemble the group name and clean each part, then join them back.'''
    parts = [normSingleGroupTag(p) for p in chars.split(TAG_SPLITTER)]
    parts = [p for p in parts if p]
    chars = TAG_SPLITTER.join(parts)
    return chars.lstrip(INVALID_LEADING_CHARS).rstrip(INVALID_ENDING_CHARS)




def normTitle(chars: str) -> str:
    '''Whitelist-based title cleaner.'''
    chars = rmInvalidChars(chars)
    chars = ''.join([c for c in chars if c in VALID_T_CHARS]).strip()
    return chars.lstrip(INVALID_LEADING_CHARS).rstrip(INVALID_ENDING_CHARS)




def normSingleLocation(chars: str) -> str:
    '''Whitelist-based location cleaner.'''
    chars = rmInvalidChars(chars)
    chars = ''.join([c for c in chars if c in VALID_L_CHARS])
    chars = chars.lstrip('.' + string.whitespace).rstrip()
    return chars




def normFullLocation(chars: str) -> str:
    #! use pure path to avoid raising error on invalid characters in path string
    chars = PurePath(chars.strip()).as_posix()
    parts = chars.split('/')  # split the path with '/' to parts
    for i, part in enumerate(parts):
        parts[i] = normSingleLocation(part)
    parts = [p for p in parts if p]
    #! need to keep the initial '/' if it exists, used to enforce placing at the root
    chars = ('/' if chars[0] == '/' else '') + '/'.join(parts)
    return chars.lstrip(INVALID_LEADING_CHARS).rstrip(INVALID_ENDING_CHARS)




def normClassification(chars: str) -> str:
    '''Whitelist-based classification cleaner.'''
    chars = rmInvalidChars(chars)
    chars = ''.join([c for c in chars if c in VALID_C_CHARS]).strip()
    return chars.lstrip(INVALID_LEADING_CHARS).rstrip(INVALID_ENDING_CHARS)




def normDescription(chars: str) -> str:
    '''Whitelist-based description cleaner.'''
    chars = rmInvalidChars(chars)
    chars = ''.join([c for c in chars if c in VALID_F_CHARS]).strip()
    return chars.lstrip(INVALID_LEADING_CHARS).rstrip(INVALID_ENDING_CHARS)




def normDecimal(chars: str) -> str:
    chars = rmInvalidChars(chars)
    if isDecimal(chars): return chars  # quick exit
    chars = ''.join([c for c in chars if c in '01234567890.'])
    parts = [p for p in chars.split('.') if p]
    chars = '.'.join(chars.split('.')[:2])
    return chars.lstrip(INVALID_LEADING_CHARS).rstrip(INVALID_ENDING_CHARS)







def normSingleSuffix(chars: str) -> str:
    chars = rmInvalidChars(chars)
    return ''.join([c for c in chars if c in VALID_X_CHARS]).strip()




def normFullSuffix(chars: str) -> str:
    '''Disassemble the suffix and clean each part, then join them back.'''
    parts = [normSingleSuffix(p) for p in chars.split(TAG_SPLITTER)]
    parts = [p for p in parts if p]
    chars = TAG_SPLITTER.join(parts).strip(string.whitespace + TAG_SPLITTER)
    return chars.lstrip(INVALID_LEADING_CHARS).rstrip(INVALID_ENDING_CHARS)




def splitGroupTag(chars: str, clean: bool = True, remove_empty: bool = True) -> list[str]:
    if clean: parts = [normSingleGroupTag(p) for p in chars.split(TAG_SPLITTER)]
    else: parts = [p for p in chars.split(TAG_SPLITTER)]
    if remove_empty: parts = [p for p in parts if p]
    return parts




def cmpCoreFileNaming(a: hc.CF, b: hc.CF) -> list[bool]:
    ret = [False] * 10
    if a.g == b.g: ret[0] = True  # compare group name
    if a.t == b.t: ret[1] = True  # compare title
    if a.l == b.l: ret[2] = True  # compare location
    if a.c == b.c: ret[3] = True  # compare classification
    if a.i1 == b.i1: ret[4] = True  # compare main index
    if a.i2 == b.i2: ret[5] = True  # compare sub index
    if a.s == b.s: ret[6] = True  # compare note
    if a.f == b.f: ret[7] = True  # compare full description
    if a.x == b.x: ret[8] = True  # compare suffix
    if a.e == b.e: ret[9] = True  # compare extension
    return ret
