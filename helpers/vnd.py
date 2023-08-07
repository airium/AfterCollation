import logging
import itertools
from pathlib import Path

from configs import *
from utils import *
from .misc import *
from .subtitle import getAssTextLangDict
from .language import *
from helpers.corefile import CF


__all__ = [
    'toVNDNamingDicts',
    'loadVNDNaming',
    'doEarlyNamingGuess',
    'guessNamingFieldsFromSimpleFilename',
    'guessNamingFields4ASS',
    'guessNamingFields4ARC',
    'guessNamingFields4MKA',
    ]




def toVNDNamingDicts(cfs:list[CF], logger:logging.Logger) -> list[dict[str, str]]:
    ret = []

    for cf in cfs:
        d : dict[str, str] = dict()

        for k, v in VND_ALL_DICT.items():
            d[k] = ''

        d[FULLPATH_CN] = cf.src
        d[CRC32_CN] = cf.crc32

        for k, v in VND_USER_DICT.items():  # user fields
            # these keys may be already filled from VNA
            d[k] = getattr(cf, v, '')

        # the following keys are just for presenting mediainfo
        # they have no usage in later stages
        d[DURATION_CN] = cf.fmtGeneralDuration()
        d[FILESIZE_CN] = cf.fmtFileSize()
        d[EXTENSION_CN] = cf.ext
        d[CONTAINER_CN] = cf.format
        d[TRACKCOMP_CN] = cf.fmtTrackTypeCountsWithOrder()
        d[TR_VIDEO_CN] = '／'.join(cf.digestVideoTracksInfo())
        d[TR_AUDIO_CN] = '／'.join(cf.digestAudioTracksInfo())
        d[TR_TEXT_CN] = '／'.join(cf.digestTextTracksInfo())
        d[TR_MENU_CN] = '／'.join(cf.digestMenuTracksInfo())

        ret.append(d)

    return ret




def loadVNDNaming(vnd_csv:Path, logger:logging.Logger) -> tuple[dict[str, str], list[dict[str, str]]]:

    logger.info(f'Loading "{vnd_csv}" ...')

    if not vnd_csv or not vnd_csv.is_file():
        return {}, []

    success, csv_dicts = readCSV(vnd_csv)
    if not success:
        logger.error(f'Failed to read "{vnd_csv}".')
        return {}, []
    csv_dicts = unquotFields4CSV(csv_dicts)

    try:
        default_dict : dict[str, str] = {var: '' for var in VND_ALL_DICT.values()}
        naming_dicts : list[dict[str, str]] = []
        for csv_dict in csv_dicts:
            #* default dict ------------------------------------------
            is_base_dict = False
            for k, v in csv_dict.items():
                if v == BASE_LINE_LABEL:
                    for kk, vv in VND_BASE_LINE_USER_DICT.items():
                        default_dict[vv] = csv_dict.get(kk, '')
                    is_base_dict = True
                    break
            if is_base_dict: continue
            #* per file dict -----------------------------------------
            naming_dict : dict[str, str] = {var: '' for var in VND_ALL_DICT.values()}
            for k, v in VND_PERSISTENT_DICT.items():
                naming_dict[v] = csv_dict.get(k, '')
            for k, v in VND_USER_DICT.items():
                naming_dict[v] = csv_dict.get(k, '')
            naming_dicts.append(naming_dict)

        enables = toEnabledList([naming_dict[ENABLE_VAR] for naming_dict in naming_dicts])
        enabled_naming_dicts = list(itertools.compress(naming_dicts, enables))
        if len(naming_dicts) != len(enabled_naming_dicts):
            logger.info(f'Enabled {len(enabled_naming_dicts)} out of {len(naming_dicts)} files in the naming plan.')
    except:
        logger.error(f'Failed to load data from "{vnd_csv}".')
        return {}, []

    logger.info(f'Loaded data from "{vnd_csv}".')
    return default_dict, enabled_naming_dicts




def guessNamingFieldsFromSimpleFilename(cf:CF, logger:logging.Logger):
    '''Sometimes the video may be already simply named. Let's try our luck.'''

    filename = m.group('stem') if (m := re.match(GENERIC_FILENAME, cf.path.name)) else ''
    if not filename:
        logger.debug(f'Got nothing from "{cf.path.name}".')
        return
    filename = filename.strip().strip('.-_').strip()

    # TODO use VideoNamingCopier API to handle this
    if any(c in filename for c in '[]()'):
        logger.debug(f'Complex named file detected "{cf.path.name}".')
        return

    if match := re.match(EXPECTED_SIMPLE_NAME, filename):
        typename, idx, note = match.group('typename'), match.group('idx'), match.group('note')
        if typename: cf.c = typename.strip().strip('.-_').strip()
        if idx: cf.i1 = idx.strip().strip('.-_').strip()
        if (typename or idx) and note: cf.s = note.strip().strip('.-_').strip()
        # NOTE there is no need to fill in the location fields
        # if a typename is detected, VNE will automatically place it under SPs if location is empty




def guessNamingFields4ASS(cf:CF, logger:logging.Logger):
    '''We should be able to guess the eposide index and the language suffix if lucky.'''

    #* firstly let's try to get the info from filename

    if match := re.match(ASS_FILENAME_EARLY_PATTERN, cf.path.name):
        filename_lang_tag, filename_ep_idx = match.group('lang'), match.group('idx')
    else:
        filename_lang_tag, filename_ep_idx = '', ''
    filename_lang_tag = filename_lang_tag if filename_lang_tag else ''
    filename_ep_idx = filename_ep_idx if filename_ep_idx else ''
    langs = toUniformLangTags(filename_lang_tag)
    if not langs: # if got no valid language tag from filename, then try its parent dirname
        langs = toUniformLangTags(cf.path.parent.name)
        if langs:
            filename_lang_tag = cf.path.parent.name # overwrite the one found in filename

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
            logger.warning(f'The detected language "{lang_detected}" differs from that in filename '
                           f'{cf.path.parent.name}/{cf.path.name}". '
                           f'The naming guesser wont fill in the language suffix for you.')
        else:
            # NOTE use un-normalized `lang_in_filename` as this may be the expectation of the fansub groups
            # TODO normalize the field so the user wont get an error message in VNE
            # if the fansub groups used a language tag not meeting our naming standard
            cf.x = filename_lang_tag if filename_lang_tag else lang_detected




def guessNamingFields4ARC(cf:CF, logger:logging.Logger):
    filenames = getArchiveFilelist(cf.path)
    has_png, has_font = False, False
    for filename in filenames:
        if filename.lower().endswith(VNx_IMG_EXTS): has_png = True
        if filename.lower().endswith(COMMON_FONT_EXTS): has_font = True
        if has_png and has_font: break
    if has_png and not has_font:
        cf.l = STD_SPS_DIRNAME
    if not has_png and has_font:
        cf.c = STD_FONT_NAME




def guessNamingFields4MKA(mka:CF, cfs:list[CF], logger:logging.Logger):

    candidates = [cf for cf in cfs if (cf.e == 'mkv' and matchTime(mka.duration, cf.duration))]
    if len(candidates) == 1:
        mka.f = candidates[0].crc32




def doEarlyNamingGuess(cfs:list[CF], logger:logging.Logger):
    '''We can actually guess very few fields at VND, but try it.'''

    for i, cf in enumerate(cfs):
        match cf.ext:
            case 'mkv'|'mp4':
                guessNamingFieldsFromSimpleFilename(cf, logger)
            case 'mka':
                guessNamingFieldsFromSimpleFilename(cf, logger)
                guessNamingFields4MKA(cf, cfs[:i] + cfs[i+1:], logger)
            case 'flac':
                guessNamingFieldsFromSimpleFilename(cf, logger)
                cf.l = STD_SPS_DIRNAME
            case 'ass': # we can guess ass lang suffix at VND
                guessNamingFields4ASS(cf, logger)
            case '7z'|'zip'|'rar':
                guessNamingFields4ARC(cf, logger)
            case _:
                logger.error(f'Got "{cf.ext}" but "{VNx_ALL_EXTS=}".')
