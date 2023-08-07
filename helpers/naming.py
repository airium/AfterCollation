from __future__ import annotations

from pathlib import Path, PurePath

from configs import *
from utils.chars import isDecimal
import helpers.corefile as hc


__all__ = [
    'stripString',
    'cleanFullPath',
    'clean1GrpName',
    'cleanFullGroupName',
    'cleanTitle',
    'clean1Location',
    'cleanFullLocation',
    'cleanClassification',
    'cleanDescription',
    'cleanDecimal',
    'clean1Suffix',
    'cleanFullSuffix',
    'splitGroupTags',
    'cmpCoreFileNaming',
    ]




def stripString(chars: str) -> str:
    '''We dont need this function in fact.'''
    return chars.strip()




def cleanFullPath(chars: str) -> str:
    '''
    Clean the input string for actual path.
    #! relative and uri path is not allowed
    #! this cleaner will make such path inaccessible so got caught by in chkNamingDicts()
    '''
    return chars.rstrip(INVALID_PATH_ENDING_CHARS).lstrip(INVALID_PATH_STARTING_CHARS)




def clean1GrpName(chars: str) -> str:
    '''Whitelist-based group name cleaner.'''
    return ''.join([c for c in chars if c in VALID_G_CHARS]).strip()




def cleanFullGroupName(chars: str) -> str:
    '''Disassemble the group name and clean each part, then join them back.'''
    parts = [clean1GrpName(p) for p in chars.split('&')]
    parts = [p for p in parts if p]
    # '&. -' is possible characters in group name, but they should not appear at start/end
    return '&'.join(parts).strip(' .-&')




def cleanTitle(chars: str) -> str:
    '''Whitelist-based title cleaner.'''
    return ''.join([c for c in chars if c in VALID_T_CHARS]).strip()




def clean1Location(chars: str) -> str:
    '''Whitelist-based location cleaner.'''
    return ''.join([c for c in chars if c in VALID_L_CHARS]).strip()




def cleanFullLocation(chars: str) -> str:
    #! use pure path to avoid raising error on invalid characters in path string
    chars = PurePath(chars.strip()).as_posix()  # as_posix() converts '\' to '/' and normalize the path
    parts = chars.split('/')  # split the path with '/' to parts
    for i, part in enumerate(parts):
        parts[i] = clean1Location(part)  # whitelist clean each part
    parts = [p for p in parts if p]  # only keep non-empty parts
    # NOTE need to keep the initial '/' if it exists, used to indicate the root
    return (('/' if chars[0] == '/' else '') + ('/'.join(parts)).lstrip('.'))




def cleanClassification(chars: str) -> str:
    '''Whitelist-based classification cleaner.'''
    return ''.join([c for c in chars if c in VALID_C_CHARS]).strip()




def cleanDescription(chars: str) -> str:
    '''Whitelist-based description cleaner.'''
    return ''.join([c for c in chars if c in VALID_F_CHARS]).strip()




def cleanDecimal(chars: str) -> str:
    chars = chars.strip()  # firstly, strip it
    if isDecimal(chars): return chars  # quick exit
    chars = ''.join([c for c in chars if c in '01234567890.'])
    parts = [p for p in chars.split('.') if p]
    return '.'.join(chars.split('.')[:2])




def clean1Suffix(chars: str) -> str:
    return ''.join([c for c in chars if c in VALID_X_CHARS]).strip()




def cleanFullSuffix(chars: str) -> str:
    '''Disassemble the suffix and clean each part, then join them back.'''
    parts = [clean1Suffix(p) for p in chars.split('&')]
    parts = [p for p in parts if p]
    return '&'.join(parts).strip(string.whitespace + '&')




def splitGroupTags(chars: str, clean: bool = True, remove_empty: bool = True) -> list[str]:
    if clean: parts = [clean1GrpName(p) for p in chars.split('&')]
    else: parts = [p for p in chars.split('&')]
    if remove_empty: parts = [p for p in parts if p]
    return parts




def cmpCoreFileNaming(a: hc.CF, b: hc.CF) -> list[bool]:
    ret = [False] * 10
    if a.g == b.g: ret[0] = True    # compare group name
    if a.t == b.t: ret[1] = True    # compare title
    if a.l == b.l: ret[2] = True    # compare location
    if a.c == b.c: ret[3] = True    # compare classification
    if a.i1 == b.i1: ret[4] = True  # compare main index
    if a.i2 == b.i2: ret[5] = True  # compare sub index
    if a.s == b.s: ret[6] = True    # compare note
    if a.f == b.f: ret[7] = True    # compare full description
    if a.x == b.x: ret[8] = True    # compare suffix
    if a.e == b.e: ret[9] = True    # compare extension
    return ret
