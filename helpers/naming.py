from __future__ import annotations

import re
from logging import Logger
from pathlib import PurePath

from configs import *
from utils.chars import isDecimal
import helpers.corefile as hc
import helpers.season as hs


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
    'cleanNamingDicts',
    'composeFullDesp',
    'decomposeFullDesp',
    'cmpDstNaming',
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
    chars = chars.lstrip(INVALID_NAMING_LEADING_CHARS).rstrip(INVALID_NAMING_ENDING_CHARS)
    return chars




def normFullGroupTag(chars: str) -> str:
    '''Disassemble the group name and clean each part, then join them back.'''
    parts = [normSingleGroupTag(p) for p in chars.split(TAG_SPLITTER)]
    parts = [p for p in parts if p]
    chars = TAG_SPLITTER.join(parts)
    return chars.lstrip(INVALID_NAMING_LEADING_CHARS).rstrip(INVALID_NAMING_ENDING_CHARS)




def normTitle(chars: str) -> str:
    '''Whitelist-based title cleaner.'''
    chars = rmInvalidChars(chars)
    chars = ''.join([c for c in chars if c in VALID_T_CHARS]).strip()
    return chars.lstrip(INVALID_NAMING_LEADING_CHARS).rstrip(INVALID_NAMING_ENDING_CHARS)




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
    return chars.lstrip(INVALID_PATH_LEADING_CHARS).rstrip(INVALID_PATH_ENDING_CHARS)




def normClassification(chars: str) -> str:
    '''Whitelist-based classification cleaner.'''
    chars = rmInvalidChars(chars)
    chars = ''.join([c for c in chars if c in VALID_C_CHARS]).strip()
    return chars.lstrip(INVALID_NAMING_LEADING_CHARS).rstrip(INVALID_NAMING_ENDING_CHARS)




def normDescription(chars: str) -> str:
    '''Whitelist-based description cleaner.'''
    chars = rmInvalidChars(chars)
    chars = ''.join([c for c in chars if c in VALID_F_CHARS]).strip()
    return chars.lstrip(INVALID_NAMING_LEADING_CHARS).rstrip(INVALID_NAMING_ENDING_CHARS)




def normDecimal(chars: str) -> str:
    chars = rmInvalidChars(chars)
    if isDecimal(chars): return chars  # quick exit
    chars = ''.join([c for c in chars if c in '01234567890.'])
    parts = [p for p in chars.split('.') if p]
    chars = '.'.join(chars.split('.')[:2])
    return chars.lstrip(INVALID_NAMING_LEADING_CHARS).rstrip(INVALID_NAMING_ENDING_CHARS)




def normSingleSuffix(chars: str) -> str:
    chars = rmInvalidChars(chars)
    return ''.join([c for c in chars if c in VALID_X_CHARS]).strip()




def normFullSuffix(chars: str) -> str:
    '''Disassemble the suffix and clean each part, then join them back.'''
    parts = [normSingleSuffix(p) for p in chars.split(TAG_SPLITTER)]
    parts = [p for p in parts if p]
    chars = TAG_SPLITTER.join(parts).strip(string.whitespace + TAG_SPLITTER)
    return chars.lstrip(INVALID_NAMING_LEADING_CHARS).rstrip(INVALID_NAMING_ENDING_CHARS)




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




def cleanNamingDicts(default_dict: dict[str, str], naming_dicts: list[dict[str, str]], logger: Logger):
    '''
    Clean the naming fields (in place) from the user input.
    Unacceptable characters are silently removed, so the program and the use wont be bothered handling them.
    '''

    logger.debug('PreClean: ' + ('|'.join(default_dict.values())))
    default_dict[FULLPATH_VAR] = normInputPath(default_dict[FULLPATH_VAR])
    default_dict[GRPTAG_VAR] = normFullGroupTag(default_dict[GRPTAG_VAR])
    default_dict[TITLE_VAR] = normTitle(default_dict[TITLE_VAR])
    default_dict[SUFFIX_VAR] = normFullSuffix(default_dict[SUFFIX_VAR])
    logger.debug('AftClean: ' + ('|'.join(default_dict.values())))

    for naming_dict in naming_dicts:

        logger.debug('PreClean: ' + ('|'.join(naming_dict.values())))
        naming_dict[FULLPATH_VAR] = normInputPath(naming_dict[FULLPATH_VAR])
        naming_dict[CRC32_VAR] = rmInvalidChars(naming_dict[CRC32_VAR])
        naming_dict[GRPTAG_VAR] = normFullGroupTag(naming_dict[GRPTAG_VAR])
        naming_dict[TITLE_VAR] = normTitle(naming_dict[TITLE_VAR])
        naming_dict[LOCATION_VAR] = normFullLocation(naming_dict[LOCATION_VAR])
        naming_dict[CLASSIFY_VAR] = normClassification(naming_dict[CLASSIFY_VAR])
        naming_dict[IDX1_VAR] = normDecimal(naming_dict[IDX1_VAR])
        naming_dict[IDX2_VAR] = normDecimal(naming_dict[IDX2_VAR])
        naming_dict[SUPPLEMENT_VAR] = normDescription(naming_dict[SUPPLEMENT_VAR])
        naming_dict[FULLDESP_VAR] = normDescription(naming_dict[FULLDESP_VAR])
        naming_dict[SUFFIX_VAR] = normFullSuffix(naming_dict[SUFFIX_VAR])
        logger.debug('AftClean: ' + ('|'.join(naming_dict.values())))




def composeFullDesp(season: hs.Season, logger: Logger):
    '''
    This function merge seperated typename/index1/2/note fields to the customization fields.

    Once merged, typename/index/1/2/note will be disposed and no longer usable.
    Use `splitContentName()` to re-gain access to these seperated fields.
    #! There is no guarantee the fields that the same seperated fields can be recovered.

    Once merged, all files are ready to accept the final naming conflict check, and then be layouted onto disk.
    '''

    cfs = season.cfs

    max_index = {}
    for cf in [info for info in cfs if not info.f]:
        l, t, i1, i2 = cf.l, cf.c, cf.i1, cf.i2
        if i2:
            key = f'{l}//{t}//{i1}'
            max_index[key] = max(max_index.get(key, -99999), float(i2))
        if i1:
            key = f'{l}//{t}'
            max_index[key] = max(max_index.get(key, -99999), float(i1))

    for i, cf in enumerate(cfs):
        if not cf.f:
            l, t, i1, i2, n = cf.l, cf.c, cf.i1, cf.i2, cf.s

            if i2:
                m2 = max(1, len(str(max_index[f'{l}//{t}//{i1}']).split('.')[0]))
                if float(i2) == int(i2):  # integer
                    i2 = ('{:' + f'0{m2}.0f' + '}').format(float(i2))
                else:  # float
                    n2 = len(str(max_index[f'{l}//{t}//{i1}']).split('.')[-1])
                    i2 = ('{:' + f'0{m2+n2+1}.{n2}f' + '}').format(float(i2))
            else:
                i2 = ''

            if i1:
                m1 = max(2, len(str(max_index[f'{l}//{t}']).split('.')[0]))
                if float(i1) == int(i1):  # integer
                    i1 = ('{:' + f'0{m1}.0f' + '}').format(float(i1))
                else:  # float
                    n1 = len(str(max_index[f'{l}//{t}']).split('.')[-1])
                    i1 = ('{:' + f'0{m1+n1+1}.{n1}f' + '}').format(float(i1))
            else:
                i1 = ''

            spaced = True if ((' ' in t) or (' ' in n)) else False
            if spaced:
                temp = '{tn}' + (' ' if t else '') + '{i1}' + ('-' if i2 else '') + '{i2}'
                temp += (' ' if n else '') + '{nt}'
            else:
                temp = '{tn}' + '{i1}' + ('_' if i2 else '') + '{i2}'
                temp += (('' if n.startswith('(') else '_') if n else '') + '{nt}'

            cf.c, cf.i1, cf.i2, cf.s, cf.f = '', '', '', '', temp.format(tn=t, i1=i1, i2=i2, nt=n)




def decomposeFullDesp(season: hs.Season, logger: Logger):
    for cf in season.cfs:
        if cf.f:
            if m := re.match(FULL_DESP_REGEX, cf.f):
                cf.f = ''
                c = normClassification(c) if (c := m.group('c')) else ''
                i1 = normDecimal(m.group('i1')) if (i1 := m.group('i1')) else ''
                i2 = normDecimal(m.group('i2')) if (i2 := m.group('i2')) else ''
                s = normDescription(m.group('s')) if (s := m.group('s')) else ''
                cf.c, cf.i1, cf.i2, cf.s = c, i1, i2, s
                logger.debug(f'Decomposed "{cf.f}" -> "{cf.c}|{cf.i1}|{cf.i2}|{cf.s}"')
            else:
                logger.warning(f'Cannot decompose "{cf.f}".')




def cmpDstNaming(season: hs.Season, logger: Logger) -> bool:
    ok = True
    for cf in season.cfs:
        if cf.dstname != cf.srcname:
            logger.warning(f'The filename differs after reconstruction: "{cf.srcname}" -> "{cf.dstname}".')
            ok = False
    return ok
