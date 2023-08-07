import re
import logging
import traceback
from pathlib import Path

from utils import *
from configs import *
from helpers.error import NamingDraftError
from helpers.naming import *
from helpers.season import Season
from helpers.corefile import CoreFile
from helpers.subtitle import getAssTextLangDict
from helpers.language import *


__all__ = [
    'chkNamingDicts',
    'chkGrpTag',
    'chkTitle',
    'chkLocation',
    'chkClassification',
    'chkIndex',
    'chkSupplementDesp',
    'chkCustomisedDesp',
    'chkSuffix'
    ]




def chkNamingDicts(default_dict: dict[str, str], naming_dicts: list[dict[str, str]], logger: logging.Logger) -> bool:
    '''
    Checking if the user input (VDN.csv) satisfies the minimal input requirements.
    Better call `cleanNamingDicts()` before this function if your input is not trusted.

    Return: bool: whether the naming draft passes the minimal requirements to continue later steps.
    '''

    logger.info('Checking the csv content ...')

    try:
        paths = [default_dict[FULLPATH_VAR]] + [d[FULLPATH_VAR] for d in naming_dicts]

        #! 1. there must be at least one file specified
        if not naming_dicts:
            logger.warning('No file specified or enabled from the input.')
            raise NamingDraftError

        #! 2. all files should have a path specified (except the default)
        for i, path in enumerate(paths[1:], start=3):
            if not path:
                logger.error(f'Missing file path at possibly line {i}.')
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
        crc32s = [d[CRC32_VAR].lower() for d in naming_dicts if d[CRC32_VAR]]
        all_crc32_valid = True
        for crc32 in crc32s:
            if not re.match(BASIC_CRC32_PATTERN, crc32):
                logger.error(f'Invalid CRC32 string: "{crc32}".')
        if not all_crc32_valid:
            raise NamingDraftError

        #! 8. there should be no file with identical crc32
        if len(set(crc32s)) != len(crc32s):
            logger.error('Found files with identical CRC32.')
            raise NamingDraftError

        #! 9. if crc32-based name copying is used, ensure the file with the target crc32 exists
        all_customs = [d[CUSTOM_VAR] for d in naming_dicts if d[CUSTOM_VAR]]
        all_customs = [m.group('crc32').lower() for c in all_customs if (m := re.match(CRC32_CSV_PATTERN, c))]
        all_found = True
        for custom in all_customs:
            if custom not in crc32s:
                logger.error(f'Cannot find the target file with CRC32 "{custom}" for naming reference.')
                all_found = False
        if not all_found: raise NamingDraftError

        #! 10 there is a default title, or all files have their own title
        titles = [default_dict[TITLE_VAR]] + [d[TITLE_VAR] for d in naming_dicts]
        if not titles[0] and not all(titles[1:]):
            logger.error('Missing title. You should set a base/default title, or set each title for all files.')
            raise NamingDraftError

    except NamingDraftError:
        logger.error('Rejected the naming draft. Stopping ...')
        return False
    except Exception:
        traceback.print_exc()
        logger.error('Please report the unknown error above. Stopping ...')
        return False
    else:
        logger.debug('Accepted the naming draft.')
        return True




def chkGrpTag(fullname: str, logger: logging.Logger) -> bool:

    cleaned_fullname = normFullGroupTag(fullname)
    if not fullname or not cleaned_fullname:
        logger.error(f'The group tag is empty.')
        return False

    ok = True

    if cleaned_fullname != fullname:
        logger.error(f'The group tag "{fullname}" is dirty.')
        ok = False

    # we need to go deeper and tell the detailed reasons why the naming looks wrong

    groups = splitGroupTag(fullname, clean=False, remove_empty=False)

    for group in groups:
        cleaned_group = normSingleGroupTag(group)
        if not group or not cleaned_group:
            logger.error(f'Found empty section.')
            ok = False
            continue
        if group != cleaned_group:
            logger.error(f'Found dirty section "{group}".')
            ok = False
        if [c for c in cleaned_group if c in WARN_G_CHARS]:
            logger.info(f'Using rare chars in "{group}".')
        if [c for c in cleaned_group if c in USER_GROUP_NAME_CHARS]:
            logger.info(f'Using user-allowed char in "{group}".')

    groups = splitGroupTag(fullname, clean=True, remove_empty=True)

    if len(groups) != len(set(group.lower() for group in groups)):
        logger.error(f'The group tag "{fullname}" has duplicated section.')
        ok = False

    for group in groups:
        if group not in COMMON_GRP_NAMES:
            logger.warning(f'Uncommon group tag "{group}" (or wrong case).')

    if not fullname.isascii():
        logger.warning(f'The group tag contains non-ASCII characters.')

    if fullname.endswith(OLD_GRP_NAME):
        logger.warning(f'The group tag ends with the old-fashion "{OLD_GRP_NAME}".')

    elif not fullname.endswith(STD_GRPTAG):
        logger.warning(f'The group tag is NOT ended with "{STD_GRPTAG}".')

    return ok




def chkTitle(fullname: str, logger: logging.Logger) -> bool:

    cleaned_fullname = normTitle(fullname)
    if not fullname or not cleaned_fullname:
        logger.error(f'The title is empty.')
        return False

    ok = True

    if cleaned_fullname != fullname:
        logger.error(f'The title "{fullname}" is dirty.')
        ok = False

    if [c for c in cleaned_fullname if c in WARN_T_CHARS]:
        logger.info(f'Using rare chars in "{fullname}".')
    if [c for c in cleaned_fullname if c in USER_SHOW_TITLE_CHARS]:
        logger.info(f'Using user-allowed char in "{fullname}".')

    if not fullname.isascii():
        logger.warning(f'The title contains non-ascii character.')

    if chkLang(fullname) == 'en':
        logger.info(
            f'The title looks like an English spelling. '
            f'Make sure that using English instead of Romaji is intended.'
            )

    return ok




def chkLocation(location: str, logger: logging.Logger) -> bool:
    #! We no longer check its relation to typename in this function

    if not location: return True  # empty location is correct here

    ok = True
    cleaned_location = normFullLocation(location)
    if location != cleaned_location:
        logger.error(f'The location "{location}" is dirty.')
        ok = False

    if cleaned_location.startswith('/'): cleaned_location = location[1:]
    if cleaned_location not in COMMON_VIDEO_LOCATIONS:
        logger.warning(f'Using an uncommon location "{cleaned_location}".')

    if '/' in cleaned_location:
        logger.info(f'The location contains sub-dirs. Make sure that this is intended.')

    for part in cleaned_location.split('/'):
        if [c for c in part if c in WARN_L_CHARS]:
            logger.info(f'Using rare chars in "{part}".')
        if [c for c in part if c in USER_LOCATION_CHARS]:
            logger.info(f'Using user-allowed char in "{part}".')

    if not location.isascii():
        logger.warning(f'The location contains non-ascii character.')

    return ok




def chkClassification(classification: str, logger: logging.Logger) -> bool:

    if not classification: return True  # empty typename is correct here

    ok = True
    cleaned_classifi = normClassification(classification)

    if classification != cleaned_classifi:
        logger.error(f'The video classification is dirty.')
        ok = False

    if cleaned_classifi not in COMMON_TYPENAME:
        logger.warning(f'Found uncommon video classification "{cleaned_classifi}" (or wrong case).')

    if [c for c in cleaned_classifi if c in WARN_C_CHARS]:
        logger.info(f'Using rare chars in "{cleaned_classifi}".')
    if [c for c in cleaned_classifi if c in USER_CLASSIFICATION_CHARS]:
        logger.info(f'Using user-allowed chars in "{cleaned_classifi}".')

    if not classification.isascii():
        logger.warning(f'The typename "{classification}" contains non-ascii character.')

    return ok




def chkIndex(idx1: str, idx2: str, logger: logging.Logger) -> bool:

    if not idx1:
        if idx2: logger.warning(f'Will ignore the sub index "{idx2}" as the main index is empty.')
        return True  # empty index is correct here

    ok = True
    cleaned_idx1 = normDecimal(idx1)
    cleaned_idx2 = normDecimal(idx2)

    if idx1 != cleaned_idx1:
        logger.error(f'The main index "{idx1}" is malformed.')
        ok = False

    if idx2 != cleaned_idx2:
        logger.error(f'The sub index "{idx2}" is malformed.')
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




def chkSupplementDesp(cf: CoreFile, logger: logging.Logger) -> bool:

    s = cf.s
    cs = normDescription(s)

    if not s: return True  # empty location is correct

    ok = True

    if cs != cs:
        logger.error(f'The description is dirty.')
        ok = False

    return ok




def chkCustomisedDesp(cf: CoreFile, logger: logging.Logger) -> bool:

    d = cf.f
    cd = normDescription(d)

    if not cf: return True  # empty customised description is correct

    ok = True

    if d != cd:
        logger.error(f'The customised description "{d}" is dirty.')
        ok = False

    return ok




def chkSuffix(obj: Season|CoreFile, logger: logging.Logger) -> bool:

    if DEBUG: assert isinstance(obj, (Season, CoreFile))

    x = obj.x
    cx = normFullSuffix(obj.x)

    if not x: return True  # having no suffix is OK if only viewed from the file itself

    ok = True

    if x != cx:
        logger.error(f'The suffix "{x}" is dirty.')
        ok = False

    if not cx: return ok  # no need to check more

    # if isinstance(obj, Series):
    #     # TODO
    #     return ok

    if isinstance(obj, Season):
        if cx not in AVAIL_SEASON_LANG_SUFFIXES:
            logger.info(f'Possibly using a version suffix "{cx}" in file name. Take care.')
        return ok

    if isinstance(obj, CoreFile):

        #! only MKV/MP4/ASS can have lang suffix
        if obj.e not in (VNx_VID_EXTS + VNx_SUB_EXTS):
            logger.error(f'Found disallowed suffix "{cx}" for file 0x{obj.crc32}/{obj.e}.')
            return False

        #! and the lang suffix must be in correct form (whitelist)
        if cx.lower() not in AVAIL_FILE_LANG_SUFFIXES:
            logger.error(f'Found malformed suffix "{cx}".')
            return False

        #! check the spelling style is coherent
        styles: list[int] = []
        for part in cx.split(TAG_SPLITTER):
            if part not in AVAIL_LANG_SUFFIXES:
                logger.error(f'Found incorrect capitalization "{part}" in suffix "{cx}".')
                ok = False
            else:
                styles.append(AVAIL_LANG_SUFFIXES.index(part))
        styles = [style % 5 for style in styles]
        if len(set(styles)) != len(styles):
            logger.error(f'Found different capitalization styles in "{cx}".')
            ok = False

        if obj.e in VNx_VID_EXTS:
            logger.info(f'Found suffix "{cx}" for file 0x{obj.crc32} - plz recheck that this video is hard-subbed.')

        if obj.e in VNx_SUB_EXTS:
            langs = toUniformLangTags(cx)
            lang_detected = ''
            if ass_obj := toAssFileObj(obj.path, test=True):
                full_text = ' '.join(listEventTextsInAssFileObj(ass_obj))
                langs = getAssTextLangDict(full_text)
                has_chs = bool(langs.get('chs'))
                has_cht = bool(langs.get('cht'))
                has_jpn = bool(langs.get('jpn'))
                match has_chs, has_cht, has_jpn:
                    case True, False, _:
                        lang_detected = 'chs'
                    case False, True, _:
                        lang_detected = 'cht'
            lang_detected = toUniformLangTag(lang_detected)
            if lang_detected not in langs:
                logger.error(f'Cannot verify the lang suffix "{cx}" from the content in ASS 0x{obj.crc32}.')
                ok = False

    return ok
