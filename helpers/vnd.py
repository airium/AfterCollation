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
    ]




def toVNDNamingDicts(cfs:list[CF], logger:logging.Logger) -> list[dict[str, str]]:
    ret = []

    for cf in cfs:
        d : dict[str, str] = dict()

        for k, v in VND_ALL_DICT.items():
            d[k] = ''

        d[FULLPATH_CN] = cf.path.resolve().as_posix()
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
        default_dict : dict[str, str] = {}
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
            naming_dict : dict[str, str] = {}
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



def guessAssNamingFields(cf:CF, logger:logging.Logger):
    '''We should be able to guess the eposide index and the language suffix if lucky.'''

    #* firstly let's try to get the info from filename

    lang, idx = '', ''
    if match := re.match(ASS_FILENAME_EARLY_PATTERN, cf.path.name):
        lang, idx = match.group('lang'), match.group('idx')
    lang_in_filename = lang if lang else ''
    idx_in_filename = idx if idx else ''
    langs_in_filename = toUniformLangSuffixes(lang_in_filename)
    if not langs_in_filename:
        langs_in_filename = toUniformLangSuffixes(cf.path.parent.name)
        if langs_in_filename:
            lang_in_filename = cf.path.parent.name

    #* eposide naming can be done now

    if idx_in_filename:
        setattr(cf, IDX1_VAR, float(idx_in_filename) if '.' in idx_in_filename else int(idx_in_filename))

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
    lang_detected = toUniformLangSuffix(lang_detected)
    # NOTE dont copy the langs_in_file
    if lang_detected:
        if langs_in_filename and not (lang_detected in langs_in_filename):
            # NOTE this means the detected lang differs from the one in filename, so don't fill it
            logger.warning(f'The detected language tag "{lang_detected}" differs from that in filename "{lang_in_filename}". '
                           f'The naming guesser wont fill in the info for you.')
        else:
            # NOTE use un-normalized `lang_in_filename` as this may be the expectation of the fansub groups
            # TODO normalize the field so the user wont get an error message in VNE
            # if the fansub groups used a language tag not meeting our naming standard
            setattr(cf, SUFFIX_VAR, lang_in_filename if lang_in_filename else lang_detected)




def doEarlyNamingGuess(cfs:list[CF], logger:logging.Logger):
    '''We can actually guess very few fields at VND, but try it.'''

    for i, cf in enumerate(cfs):

        match cf.ext:
            case 'ass': # we can guess ass lang suffix at VND
                guessAssNamingFields(cf, logger)
            case '7z'|'zip'|'rar':
                pass # TODO
            case 'mka':
                pass # TODO
            case 'flac':
                pass # TODO
