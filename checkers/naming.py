import re
import logging
import traceback
from pathlib import Path

from configs import *
from utils import *
from helpers import *
from helpers.error import NamingDraftError


__all__ = [
    'chkNamingDicts',
    'chkGrpTag',
    'chkTitle',
    'chkLocation',
    'chkTypeName',
    'chkIndex',
    'chkNote',
    'chkCustom',
    'chkSuffix'
    ]


def chkNamingDicts(default_dict:dict[str, str], naming_dicts:list[dict[str, str]], logger:logging.Logger) -> bool:
    '''Checking if the user input (VDN.csv) satisfies the minimal input requirements.
    Better call `cleanNamingDicts()` before this function if your input is not trusted.

    Return: bool: whether the naming draft passes the minimal requirements to continue later steps.
    '''

    logger.info('Checking the csv content ...')

    try:
        paths = [default_dict[FULLPATH_VAR]] + [d[FULLPATH_VAR] for d in naming_dicts]

        #! 1. there must be at least one file specified
        if not naming_dicts:
            logger.warning('No file specified or enabled from the input.')
            logger.error('Rejected the naming draft. Stopping ...')
            raise NamingDraftError

        #! 2. all files should have a path specified (except the default)
        for i, path in enumerate(paths[1:], start=3):
            if not path:
                logger.error(f'Missing file path at possibly line {i}.')
                logger.error('Rejected the naming draft. Stopping ...')
                raise NamingDraftError

        # #! 3. no invalid characters should exist in the path
        # all_path_chars_valid = True
        # for path in paths:
        #     if any((c in path) for c in INVALID_FILENAME_CHARS):
        #         logger.error(f'Invalid characters in "{path}".')
        #         all_path_chars_valid = False
        # if not all_path_chars_valid:
        #     logger.error('Rejected the naming draft. Stopping ...')
        #     raise NamingDraftError

        #! 4. all files should be valid and exist
        all_files_exists = True
        for path in paths[1:]:
            try:
                if not Path(path).is_file():
                    logger.error(f'File not found: "{path}".')
                    all_files_exists = False
            except:
                all_files_exists = False
                logger.error(f'Error in locating "{path}".')
        if not all_files_exists:
            logger.error('Rejected the naming draft. Stopping ...')
            raise NamingDraftError

        #! 5. the default path should be an existing file
        if Path(paths[0]).is_file():
            logger.error('The default output dir exists as a file.')
            raise NamingDraftError

        #! 6. there is no identical path
        all_paths = [Path(p).resolve().as_posix() for p in paths]
        if len(set(all_paths)) != len(all_paths):
            logger.error('Found identical paths.')
            raise NamingDraftError

        #! 7. crc32, if specified, should be in a valid format ([0-9a-fA-F]{8})
        crc32s = [d[CRC32_VAR] for d in naming_dicts if d[CRC32_VAR]]
        all_crc32_valid = True
        for crc32 in crc32s:
            if not re.match(BASIC_CRC32_PATTERN, crc32):
                logger.error(f'Invalid CRC32 string: "{crc32}".')
        if not all_crc32_valid:
            logger.error('Rejected the naming draft. Stopping ...')
            raise NamingDraftError

        #! 8. there should be no file with identical crc32
        if len(set(crc32s)) != len(crc32s):
            logger.error('Found files with identical CRC32.')
            raise NamingDraftError

        #! 9. if crc32-based name copying is used, ensure the file with the target crc32 exists

        #! 10 there is a default showname, or all files have their own showname
        shownames = [default_dict[TITLE_VAR]] + [d[TITLE_VAR] for d in naming_dicts]
        if not shownames[0] and not all(shownames[1:]):
            logger.error('Missing showname. You should set a base/default showname, or set each showname for all files.')
            raise NamingDraftError

    except NamingDraftError:
        logger.error('Rejected the naming draft. Stopping ...')
        return False
    except Exception:
        traceback.print_exc()
        logger.error('Rejected the naming draft. Stopping ...')
        return False
    else:
        logger.debug('Accepted the naming draft.')
        return True










def chkGrpTag(fullname:str, logger:logging.Logger) -> bool:

    cleaned_fullname = cleanFullGroupName(fullname)
    if not fullname or not cleaned_fullname:
        logger.error(f'The group tag is empty.')
        return False

    ok = True

    if cleaned_fullname != fullname:
        logger.error(f'The group tag contains disallowed characters or incorrect spacing.')
        ok = False

    groups = splitGroupTags(fullname, clean=False, remove_empty=False)
    for group in groups:
        cleaned_group = clean1GrpName(group)
        if not group or not cleaned_group:
            logger.error(f'Found empty section in group name.')
            ok = False

    groups = splitGroupTags(fullname, clean=True, remove_empty=True)
    if len(groups) != len(set(group.lower() for group in groups)):
        logger.error(f'Found duplicated section in group name.')
        ok = False
    for group in groups:
        if group not in COMMON_GRP_NAMES:
            logger.error(f'Unseen group tag "{group}" (or wrong case).')
            ok = False

    if not fullname.isascii():
        logger.warning(f'The group tag contains non-ASCII characters.')
    if fullname.endswith(OLD_GRP_NAME):
        logger.warning(f'The group tag ends with the old-fashion "{OLD_GRP_NAME}".')
    elif not fullname.endswith(STD_GRPTAG):
        logger.warning(f'The group tag is NOT ended with "{STD_GRPTAG}".')

    return ok




def chkTitle(fullname:str, logger:logging.Logger) -> bool:

    cleaned_fullname = cleanGenericName(fullname)
    if not fullname or not cleaned_fullname:
        logger.error(f'The show name is empty.')
        return False

    ok = True

    if cleaned_fullname != fullname:
        logger.error(f'The showname contains disallowed characters or incorrect spacing.')
        ok = False

    if not fullname.isascii():
        logger.warning(f'The showname contains non-ascii character.')
    if chkLang(fullname) == 'en':
        logger.info(f'The showname looks like an English spelling. '
                    f'Make sure that using English instead of Romaji is intended.')

    return ok








# __all__ = [
#     'cleanString',
#     'cleanFullPath',
#     'cleanFullName',
#     'cleanLocation',
#     'cleanDecimal',
#     'clean1GrpName',
#     'cleanFullGrpName',
#     'clean1Suffix',
#     'cleanFullSuffix',
#     'splitGroupTags']



# THIS IS aut ofilling
# def chkLocation(location:str, typename:str, logger:logging.Logger) -> str:

#     if location:
#         if location.startswith('/'): # a leading '/' may be preserved to indicate the season root dir
#             location = location[1:]
#         if location not in COMMON_VIDEO_LOCATIONS:
#             logger.warning(f'Using an uncommon location "{location}".')
#     else:
#         if typename: location = 'SPs'

#     assert not location.startswith('/'), 'doNaming() enforces that location not started with /.'
#     return location

def chkLocation(location:str, logger:logging.Logger) -> bool:
    #! We no longer check its relation to typename in this function

    if not location: return True # empty location is correct here

    ok = True
    cleaned_location = cleanLocation(location)
    if location != cleaned_location:
        logger.error(f'The location contains disallowed characters or incorrect spacing.')
        ok = False

    if cleaned_location.startswith('/'): cleaned_location = location[1:]
    if cleaned_location not in COMMON_VIDEO_LOCATIONS:
        logger.warning(f'Using an uncommon location "{cleaned_location}".')
    if '/' in cleaned_location:
        logger.info(f'The location contains sub-dirs. Make sure that this is intended.')

    if not location.isascii():
        logger.warning(f'The location contains non-ascii character.')

    return ok


def chkTypeName(typename:str, logger:logging.Logger) -> bool:

    if not typename: return True # empty typename is correct here

    ok = True
    cleaned_typename = cleanGenericName(typename)
    if typename != cleaned_typename:
        logger.error(f'The typename contains disallowed characters or incorrect spacing.')
        ok = False

    if cleaned_typename not in COMMON_TYPENAME:
        logger.warning(f'The typename "{cleaned_typename}" is uncommon (or wrong case).')
    if any((p in cleaned_typename) for p in string.digits):
        logger.warning(f'The typename "{typename}" contains numbers, which may be incorrect.')

    if not typename.isascii():
        logger.warning(f'The typename "{typename}" contains non-ascii character.')

    return ok


# def chkIndex(idx1:str, idx2:str, logger:logging.Logger) -> tuple[int|float|None, int|float|None]:

#     ret_idx1 : int|float|None = None
#     ret_idx2 : int|float|None = None

#     if idx1:
#         if not isDecimal(idx1):
#             logger.warning(f'The main index "{idx1}" will be ignored as not a decimal number.')
#         elif not idx1.isdigit():
#             logger.warning(f'The main index "{idx1}" is not an integer.')
#             ret_idx1 = float(idx1)
#         else:
#             ret_idx1 = int(idx1)

#     if ret_idx1 == None:
#         ret_idx2 = None
#         if idx2: logger.warning(f'The sub index "{idx2}" will be ignored as the main index is empty or invalid.')
#     elif idx2:
#         if not isDecimal(idx2):
#             logger.warning(f'The sub index "{idx2}" will be ignored as not a decimal number.')
#         elif not idx2.isdigit():
#             logger.warning(f'The main index "{idx2}" is not an integer.')
#             ret_idx2 = float(idx2)
#         else:
#             ret_idx2 = int(idx2)

#     return ret_idx1, ret_idx2

def chkIndex(idx1:str, idx2:str, logger:logging.Logger) -> bool:

    if not idx1:
        if idx2: logger.warning(f'The sub index "{idx2}" will be ignored as the main index is empty.')
        return True # empty index is correct here

    ok = True
    cleaned_idx1 = cleanDecimal(idx1)
    cleaned_idx2 = cleanDecimal(idx2)

    if idx1 != cleaned_idx1:
        logger.error(f'The main index is malformed.')
        ok = False
    if idx2 != cleaned_idx2:
        logger.error(f'The sub index is malformed.')
        ok = False
    # look deeper to tell the user what's wrong
    if cleaned_idx1:
        if not isDecimal(idx1):
            logger.error(f'The main index "{idx1}" is not a decimal number.')
        elif not idx1.isdigit():
            logger.warning(f'The main index "{idx1}" is not an integer.')
    if cleaned_idx2:
        if not isDecimal(idx2):
            logger.error(f'The sub index "{idx2}" is not a decimal number.')
        elif not idx2.isdigit():
            logger.warning(f'The sub index "{idx2}" is not an integer.')

    return ok




def chkNote(fullnote:str, logger:logging.Logger) -> bool:

    if not fullnote: return True # empty location is correct here

    ok = True

    cleaned_fullnote = cleanGenericName(fullnote)
    if fullnote != cleaned_fullnote:
        logger.error(f'The location contains disallowed characters or incorrect spacing.')
        ok = False

    if fullnote and (not fullnote.isascii()):
        logger.warning(f'The extra note "{fullnote}" contains non-ascii character.')

    return ok




def chkCustom(cname:str, logger:logging.Logger) -> bool:

    if not cname: return True

    ok = True

    cleaned_cname = cleanGenericName(cname)
    if cname != cleaned_cname:
        logger.error(f'The customized name contains disallowed characters or incorrect spacing.')
        ok = False

    if not cname.isascii():
        logger.warning(f'The customized name contains non-ascii character.')

    # if re.match(CRC32_CSV_PATTERN, cname):
    #     logger.info(f'Using naming reference to "{cname}".')
    #     if ext not in VNx_DEP_EXTS:
    #         # warn that files except mka/ass should not use reference naming
    #         logger.warning(f'The file type {ext.upper()} should better NOT use name reference.')
    # else: # if not re.match(CRC32_CSV_PATTERN, cname)
    #     if ext in VNx_DEP_EXTS:
    #         # warn that mka/ass should better use reference naming
    #         logger.warning(f'This file type {ext.upper()} should better use name reference. Auto/Manual indexing may be inaccurate.')
    #     logger.warning(f'Using a customized name "{cname}". '
    #                     'Auto location and indexing will be DISABLED for this file.')

    return ok




def chkSuffix(suffix:str, logger:logging.Logger)-> bool:

    if not suffix: return True

    ok = True

    cleaned_suffix = cleanFullSuffix(suffix)
    if suffix != cleaned_suffix:
        logger.error(f'The suffix name contains disallowed characters or incorrect spacing.')
        ok = False

    if not cleaned_suffix: return ok

    return ok



# def chkSuffix(suffix:str, default:str, fullpath:str, logger:logging.Logger)-> str:

#     # TODO check again if default suffix should be applied to files

#     if not suffix:
#         # suffix default only applies when it's a language tag and only for video files
#         if (default in AVAIL_SUB_LANG_TAGS) and (fullpath.lower().endswith(VNx_VID_EXTS)):
#             return default
#         else:
#             return ''

#     # if suffix:

#     if fullpath == BASE_LINE_LABEL:
#         if suffix not in AVAIL_SUB_LANG_TAGS:
#             logger.warning(f'Using a non-language suffix for base. It will be only applied to the root dirname.')
#         return suffix

#     # if suffix and fullpath != DEFAULT_LABEL:

#     if fullpath.lower().endswith(VNx_VID_EXTS):

#         # TODO: can we check if the video images contain any hard subs?
#         logger.warning(f'Found "{suffix=}" - plz recheck that this video is hard-subbed.')

#         valid_part = ''
#         for part in suffix.split('&'):
#             if valid_part:
#                 logger.warning('Ignoring more than 1 valid language tag.')
#                 break
#             if part in AVAIL_SUB_LANG_TAGS:
#                 valid_part = part
#             else:
#                 logger.warning(f'Ignoring disallowed language tag "{part}" in suffix.')
#         suffix = valid_part

#     elif fullpath.lower().endswith(VNx_SUB_EXTS):

#         valid_count, valid_parts = 0, []
#         for part in suffix.split('&'):
#             if valid_count == 2:
#                 logger.warning('Ignoring more than 2 valid language tags.')
#                 break
#             if part in AVAIL_SUB_LANG_TAGS:
#                 valid_parts.append(part)
#                 valid_count += 1
#             else:
#                 logger.warning(f'Ignoring disallowed language tag "{part}" in suffix.')

#         cn_lang = ''

#         if valid_count == 1:
#             lang = valid_parts[0]
#             if lang in AVAIL_JPN_LANG_TAGS:
#                 logger.warning('Single language tag should not be Japanese.')
#             else:
#                 cn_lang = lang

#         elif valid_count == 2:
#             lang1, lang2 = valid_parts[0], valid_parts[1]
#             a1, b1 = divmod(AVAIL_SUB_LANG_TAGS.index(lang1), 5)
#             a2, b2 = divmod(AVAIL_SUB_LANG_TAGS.index(lang2), 5)
#             if b1 != b2:
#                 logger.warning('Used CN/JP format mismatched in suffix.')
#             if ((a1 * a2) != 0) or ((a1 + a2) == 0) or ((a1 + a2) > 2):
#                 logger.warning('The language tag does not contain only one CN and only one JP.')
#             elif a1 > 0:
#                 cn_lang = AVAIL_SUB_LANG_TAGS[a1 * 5 + b1]
#             else: # a2 > 0
#                 cn_lang = AVAIL_SUB_LANG_TAGS[a2 * 5 + b2]

#         else:
#             raise ValueError('VNE bug inside `chkSuffix()`. Please report.')

#         if cn_lang:
#             tagged_cht = True if (cn_lang in AVAIL_CHT_LANG_TAGS) else False
#             try:
#                 ass_text = Path(fullpath).read_text('utf-8-sig')
#                 detected_cht = False
#                 for tc in CHT_SAMPLE_CHARS:
#                     if tc in ass_text:
#                         detected_cht = True
#                         break
#                 if tagged_cht != detected_cht:
#                     if detected_cht:
#                         logger.warning(f'The ASS file seems to be Traditional Chinese, but tagged as {cn_lang}.')
#                     else:
#                         logger.warning(f'The ASS file seems to be Simplified Chinese, but tagged as {cn_lang}.')
#             except UnicodeDecodeError:
#                 logger.warning('The encoding of the ASS file is not UTF-8-BOM.')
#             except Exception as e:
#                 logger.warning(f'Failed to detect ASS language from its content due to unexpected error: "{e}". Please report.')

#         suffix = '&'.join(valid_parts)

#     elif fullpath.endswith(('mka', )):
#         pass # to be checked in correlated naming check

#     else:

#         logger.warning(f'Found "{suffix=}" - but this file should not have suffix.')

#     if default and (suffix != default):
#         logger.warning(f'Using a non-default suffix "{suffix}".')

#     return suffix




# def chkNamingInfos(infos:list[dict], default:INFO, logger:logging.Logger) -> list[INFO]:

#     ret : list[INFO] = []

#     for i, info in enumerate(infos):


#         if not (gname := procSeasonGroupTag(gname, default.g, logger)):
#             logger.error(f'Got an empty groupname.')
#             return []
#         if not (sname := chkShowName(sname, default.s, logger)):
#             logger.error(f'Got an empty showname.')
#             return []

#         if (cname := chkCustom(cname, ext, logger)):
#             tname, idx1, idx2, note = '', None, None, ''
#         else:
#             tname = chkTypeName(tname, logger)
#             idx1, idx2 = chkIndex(idx1, idx2, logger)
#             note = chkNote(note, logger)

#         loc = chkLocation(loc, tname, logger)
#         suffix = chkSuffix(suffix, default.x, srcpath, logger)

#         if DEBUG: logger.info(f'Checked: "{gname}|{sname}|{loc}|{tname}|{idx1}|{idx2}|{note}|{cname}|{suffix}"')

#         # looks good, now save the processed key:value for later usage
#         # this dict layout is re-used in all subsequent functions
#         info=INFO(crc=crc32, src=srcpath, dst='', g=gname, s=sname, l=loc, t=tname, i1=idx1, i2=idx2,
#                   n=note, c=cname, x=suffix, e=ext)
#         ret.append(info)

#     return ret


# def chkNamingInfos(infos:list[dict], default:INFO, logger:logging.Logger) -> list[INFO]:

#     ret : list[INFO] = []

#     for i, info in enumerate(infos):

#         crc32 : str = info[CRC32_VAR]
#         srcpath : str = info[FULLPATH_VAR]
#         gname : str = info[GRPTAG_VAR]
#         sname : str = info[SHOWNAME_VAR]
#         loc : str = info[LOCATION_VAR]
#         tname : str = info[TYPENAME_VAR]
#         idx1 : str = info[IDX1_VAR]
#         idx2 : str = info[IDX2_VAR]
#         note : str = info[NOTE_VAR]
#         cname : str = info[CUSTOM_VAR]
#         suffix : str = info[SUFFIX_VAR]
#         ext : str = srcpath.lower().split('.')[-1]

#         logger.info(f'Checking the file with CRC32 "{crc32}"...')

#         if DEBUG: logger.info(f'User Input: "{gname}|{sname}|{loc}|{tname}|{idx1}|{idx2}|{note}|{cname}|{suffix}"')

#         gname : str = cleanGroupName(gname)
#         sname : str = cleanFullName(sname)
#         loc : str = cleanLocation(loc)
#         tname : str = cleanFullName(tname)
#         idx1 : str = cleanDecimal(idx1)
#         idx2 : str = cleanDecimal(idx2)
#         note : str = cleanFullName(note)
#         cname : str = cleanFullName(cname)
#         suffix : str = cleanFullSuffix(suffix)

#         if DEBUG: logger.info(f'Cleaned: "{gname}|{sname}|{loc}|{tname}|{idx1}|{idx2}|{note}|{cname}|{suffix}"')

#         if not (gname := procSeasonGroupTag(gname, default.g, logger)):
#             logger.error(f'Got an empty groupname.')
#             return []
#         if not (sname := chkShowName(sname, default.s, logger)):
#             logger.error(f'Got an empty showname.')
#             return []

#         if (cname := chkCustom(cname, ext, logger)):
#             tname, idx1, idx2, note = '', None, None, ''
#         else:
#             tname = procTypeName(tname, logger)
#             idx1, idx2 = procIndex(idx1, idx2, logger)
#             note = chkNote(note, logger)

#         loc = chkLocation(loc, tname, logger)
#         suffix = chkSuffix(suffix, default.x, srcpath, logger)

#         if DEBUG: logger.info(f'Checked: "{gname}|{sname}|{loc}|{tname}|{idx1}|{idx2}|{note}|{cname}|{suffix}"')

#         # looks good, now save the processed key:value for later usage
#         # this dict layout is re-used in all subsequent functions
#         info=INFO(crc=crc32, src=srcpath, dst='', g=gname, s=sname, l=loc, t=tname, i1=idx1, i2=idx2,
#                   n=note, c=cname, x=suffix, e=ext)
#         ret.append(info)

#     return ret
