import itertools
from pathlib import Path
from logging import Logger

from configs import *
from utils import *
from .misc import *
from .subtitle import getAssTextLangDict
from .language import *
from helpers.corefile import CF


__all__ = [
    'toVNDTableDicts',
    'readVndCSV',
    'writeVNDTable',
    'doEarlyNamingGuess',
    'guessNamingFieldsFromSimpleFilename',
    'guessNamingFields4ASS',
    'guessNamingFields4ARC',
    'guessNamingFields4MKA',
    ]




def toVNDTableDicts(cfs: list[CF], logger: Logger) -> list[dict[str, str]]:
    ret = []

    for cf in cfs:

        d: dict[str, str] = {}
        d.update({k: '' for k in VND_FULL_DICT.keys()})
        d.update({k: getattr(cf, v) for k, v in VND_USER_DICT.items()})

        d[FULLPATH_CN] = cf.src
        d[CRC32_CN] = cf.crc32
        d[QLABEL_CN] = cf.qlabel
        d[TLABEL_CN] = cf.tlabel

        # the following keys are just for presenting mediainfo in CSV, having no usage in later stages
        d[DURATION_CN] = cf.fmtGeneralDuration()
        d[FILESIZE_CN] = cf.fmtFileSize()
        d[EXTENSION_CN] = cf.ext
        d[FORMAT_CN] = cf.format
        d[TR_COMP_CN] = cf.fmtTrackTypeCountsWithOrder()
        d[TR_VIDEO_CN] = '／'.join(cf.digestVideoTracksInfo())
        d[TR_AUDIO_CN] = '／'.join(cf.digestAudioTracksInfo())
        d[TR_TEXT_CN] = '／'.join(cf.digestTextTracksInfo())
        d[TR_MENU_CN] = '／'.join(cf.digestMenuTracksInfo())

        logger.debug(f'Added: {"|".join(d.values())}.')

        ret.append(d)

    return ret




def readVndCSV(vnd_csv_path: Path, logger: Logger) -> tuple[dict[str, str], list[dict[str, str]]]:

    logger.debug(f'Loading "{vnd_csv_path}" ...')

    if not vnd_csv_path or not vnd_csv_path.is_file():
        return {}, []

    success, csv_dicts = readCSV(vnd_csv_path)
    if not success:
        logger.error(f'Failed to read "{vnd_csv_path}".')
        return {}, []
    csv_dicts = unquotFields4CSV(csv_dicts)

    try:
        base_naming_dict: dict[str, str] = {var: '' for var in VND_FULL_DICT.values()}
        file_naming_dicts: list[dict[str, str]] = []
        for csv_dict in csv_dicts:
            if any(v == BASE_LINE_LABEL for v in csv_dict.values()):
                #* default dict --------------------------------------------------------------------
                #! dont use get() as we want to assert csv_dict has all VND_FULL_DICT.keys()
                base_naming_dict.update({v: csv_dict[k] for k, v in VND_FULL_DICT.items()})
            else:
                #* per file dict -------------------------------------------------------------------
                naming_dict: dict[str, str] = {}
                naming_dict.update({var: '' for var in VND_FULL_DICT.values()})
                #! dont use get() as we want to assert csv_dict has all VND_FULL_DICT.keys()
                naming_dict.update({v: csv_dict[k] for k, v in VND_FULL_DICT.items()})
                file_naming_dicts.append(naming_dict)
        enables = toEnabledList([naming_dict[ENABLE_VAR] for naming_dict in file_naming_dicts])
        enabled_naming_dicts = list(itertools.compress(file_naming_dicts, enables))
        if len(file_naming_dicts) != len(enabled_naming_dicts):
            logger.info(f'Loaded "{vnd_csv_path}" with {len(enabled_naming_dicts)}/{len(file_naming_dicts)} files.')
        else:
            logger.info(f'Loaded "{vnd_csv_path}".')
    except:
        logger.error(f'Failed to load data from "{vnd_csv_path}".')
        return {}, []

    return base_naming_dict, enabled_naming_dicts




def writeVNDTable(
    csv_path: Path, base_csv_dict: dict[str, str], file_csv_dicts: list[dict[str, str]], logger: Logger
    ) -> bool:

    logger.debug(f'Writing VND csv ...')
    csv_dicts = quotFields4CSV([base_csv_dict] + file_csv_dicts)
    if not writeCSV(csv_path, csv_dicts):
        logger.error(f'Failed to save "{csv_path}".')
        return False
    else:
        logger.info(f'Saved to "{csv_path}".')
        return True




def guessNamingFieldsFromSimpleFilename(cf: CF, logger: Logger):
    '''Sometimes the video may be already simply named. Let's try our luck.

    It should now be able to process something like:
    "(01234)?(-012)? (NAMING)? ([01abcdef])?.(mkv|mka|mp4|flac|png|ass|7z|zip|rar)"
    where (01234) is optionally the m2ts index and [01abcdef] is optionally crc32
    where NAMING should be like: abcd 012.45 abcd1234 e.g. NCOP 02 EP03
    Allowed spacing includes: space, dash, underscore
    '''

    effective_stem = m.group('stem') if (m := re.match(UNNAMED_TRANSCODED_FILENAME_REGEX, cf.path.name)) else ''
    if not effective_stem:
        logger.debug(f'Failed to match.')
        return
    effective_stem = effective_stem.strip(string.whitespace + '.-_')

    # TODO use VideoNamingCopier API to handle this
    if any(c in effective_stem for c in '[]()'):
        logger.debug(f'Complex filename.')
        return

    if match := re.match(EXPECTED_SIMPLE_FILESTEM_REGEX, effective_stem):
        c, i1, s = match.group('c'), match.group('i1'), match.group('s')
        logger.debug(f'Guessed: "{c=}|{i1=}|{s=}".')

        if c: cf.c = c.strip(string.whitespace + '.-_')
        if i1: cf.i1 = i1  # i1 is clean from the regex
        if s: cf.s = s.strip(string.whitespace + '.-_')

    else:
        logger.debug('BUG: Failed to match the stem pattern in guessing.')




def guessNamingFields4ASS(cf: CF, logger: Logger):
    '''We should be able to guess the eposide index and the language suffix if lucky.'''

    #* firstly let's try to get the info from filename

    if match := re.match(ASS_FILENAME_EARLY_PATTERN, cf.path.name):
        filename_lang_tag, filename_ep_idx = match.group('lang'), match.group('idx')
    else:
        filename_lang_tag, filename_ep_idx = '', ''
    filename_lang_tag = filename_lang_tag if filename_lang_tag else ''
    filename_ep_idx = filename_ep_idx if filename_ep_idx else ''
    langs = toUniformLangTags(filename_lang_tag)
    if not langs:  # if got no valid language tag from filename, then try its parent dirname
        langs = toUniformLangTags(cf.path.parent.name)
        if langs:
            filename_lang_tag = cf.path.parent.name  # overwrite the one found in filename

    #* eposide naming can be done now

    if filename_ep_idx:
        cf.i1 = filename_ep_idx

    #* then detect the language from ASS content

    lang_detected = ''
    if ass_obj := toAssFileObj(cf.path, test=True):
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
    # NOTE dont copy the langs_in_file
    if lang_detected:
        if langs and not (lang_detected in langs):
            #! this means the detected lang differs from the one in filename - dont fill anything
            logger.warning(
                f'The detected language "{lang_detected}" differs from that in filename '
                f'{cf.path.parent.name}/{cf.path.name}". '
                f'The naming guesser wont fill in the language suffix for you.'
                )
        else:
            # NOTE use un-normalized `lang_in_filename` as this may be the expectation of the fansub groups
            # TODO normalize the field so the user wont get an error message in VNE
            # if the fansub groups used a language tag not meeting our naming standard
            cf.x = filename_lang_tag if filename_lang_tag else lang_detected




def guessNamingFields4ARC(cf: CF, logger: Logger):
    filenames = getArchiveFilelist(cf.path)
    has_png, has_font = False, False
    for filename in filenames:
        if filename.lower().endswith(VNX_IMG_EXTS): has_png = True
        if filename.lower().endswith(COMMON_FONT_EXTS): has_font = True
        if has_png and has_font: break
    if has_png and not has_font:
        cf.l = STD_SPS_DIRNAME
    if not has_png and has_font:
        cf.c = STD_FONT_NAME




def guessNamingFields4MKA(mka: CF, cfs: list[CF], logger: Logger):

    candidates = [cf for cf in cfs if (cf.e == 'mkv' and matchTime(mka.duration, cf.duration))]
    #? how can we discriminate multiple mka if they have the same duration?
    if len(candidates) == 1:
        mka.f = candidates[0].crc32




def doEarlyNamingGuess(cfs: list[CF], logger: Logger):
    '''We can actually guess very few fields at VND, but try it.'''

    for i, cf in enumerate(cfs):
        logger.debug(f'Guessing naming fields for "{cf.path}" ...')
        match cf.ext:
            case 'mkv'|'mp4':
                guessNamingFieldsFromSimpleFilename(cf, logger)
            case 'mka':
                guessNamingFieldsFromSimpleFilename(cf, logger)
                guessNamingFields4MKA(cf, cfs[:i] + cfs[i + 1:], logger)
            case 'flac':
                guessNamingFieldsFromSimpleFilename(cf, logger)
                cf.l = STD_SPS_DIRNAME
            case 'ass':  # we can guess ass lang suffix at VND
                guessNamingFields4ASS(cf, logger)
            case '7z'|'zip'|'rar':
                guessNamingFields4ARC(cf, logger)
            case _:
                logger.error(f'Got "{cf.ext}" but "{VNX_ALL_EXTS=}".')
