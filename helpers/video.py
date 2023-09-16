from __future__ import annotations


__all__ = [
    'readConf4VideoAlpha',
    'toVideoAlphaInfoDict',
    'readVideoAlphaNamingFile',
    'copyVideoNamingFromVA',
    'recordBDMVInfo',
    'toVideoInfoDicts',
    'readVdCSV',
    'writeVideoInfo2CSV',
    'guessVideoNaming',
    'guessNamingFieldsFromSimpleFilename',
    'guessNamingFields4ASS',
    'guessNamingFields4ARC',
    'guessNamingFields4MKA',
    'collectVideoInfos',
    'tstIO4VP',
    'doVideoFilePlacement',
    'doAutoIndexing',
    'placeVideos',
    'readCSV4ComplexVideoCmp',
    'writeCSV4ComplexVideoCmp',
    'cmpVideoGroups',
    'doStdSoloVideoCheck',
    'findVideoMatchingBetweenDir',
    'cmpSimplyPairedVideos',
    'cmpComplexlyPairedVideos',
    ]

import json
import shutil
import logging
import itertools
from pathlib import Path
from logging import Logger
from typing import Optional, Iterable
from multiprocessing import Pool

from utils import *
from langs import *
from configs import *
from checkers import *
from loggers import initLogger
from .naming import *
from .misc import *
from .subtitle import getAssTextLangDict
from .language import *
from .formatter import *
from .summaries import *
from .dirgetter import proposeFilePath
import helpers.corefile as hcf
import helpers.season as hsn
import helpers.series as hsr

import yaml
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from pymediainfo import Track





class VideoFile:

    def __init__(
        self,
        path: Path|str,
        ):

        if not (path := Path(path).resolve()).is_file():
            raise FileNotFoundError(CANT_FIND_SRC_FOR_IMAGEFILE_1.format(path))
        self.__path: Path = path
        self.__mediainfo: MediaInfo = getMediaInfo(path)
        self.__ffprobe: dict|None = None
        self.__crc32: str|None = None

    #* built-in methods override ---------------------------------------------------------------------------------------

    def __getattr__(self, __name: str):
        return getattr(self.__mediainfo, __name)

    def __getstate__(self) -> dict:
        return self.__dict__

    def __setstate__(self, state: dict):
        self.__dict__.update(state)

    #* input -----------------------------------------------------------------------------------------------------------

    @property
    def path(self) -> Path:
        return self.__path

    @property  # NOTE no setter for read-only path
    def src(self) -> str:
        return self.__path.resolve().as_posix()

    @property
    def srcname(self) -> str:
        return self.__path.name

    #* crc32 -----------------------------------------------------------------------------------------------------------

    @property
    def crc32(self) -> str:
        if not self.__crc32: self.__crc32 = getCRC32(self.path, prefix='', pass_not_found=True)
        return self.__crc32

    @property
    def crc(self) -> str:
        return self.crc32

    #* basic file info -------------------------------------------------------------------------------------------------

    @property
    def size(self) -> int:
        return self.path.stat().st_size

    @property
    def suffix(self) -> str:
        return self.path.suffix

    @property
    def ext(self) -> str:
        return self.suffix.lower().lstrip('.')

    @property
    def format(self) -> str:
        return fmt.lower() if (fmt := self.gtr.format) else self.ext

    #* file type -------------------------------------------------------------------------------------------------------

    @property
    def gtr(self) -> Track:
        return self.__mediainfo.general_tracks[0]

    @property
    def vtr(self) -> Track:
        return self.__mediainfo.video_tracks[0]


    @property
    def has_video(self) -> bool:
        return bool(self.__mediainfo.video_tracks)

    @property
    def is_video(self) -> bool:
        return (self.ext in COMMON_VIDEO_EXTS) and self.has_video

    @property
    def is_valid(self) -> bool:
        if not self.is_video: return False
        if self.format != EXTS2FORMATS.get(self.ext): return False
        if not tstFFmpegDecode(self.path): return False
        return True

    @property
    def ffprobe(self) -> dict:
        if self.__ffprobe == None: self.__ffprobe = FFprobe(self.path)
        return self.__ffprobe





def readConf4VideoAlpha(script_path: str|Path, *paths: str|Path) -> dict:
    '''
    Read the configuration file (YAML/JSON) for VA.

    INPUT: A mandatory reference path and optional paths to other config files.
    The input paths are not required to be the config file.

    Will only use the first found config.
    '''

    script_path = Path(script_path)
    other_paths = [Path(p) for p in paths]

    for path in [*other_paths, script_path]:
        for suffix in ['.yaml', '.yml', '.json']:
            if (config_path := path.with_suffix(suffix)).is_file():
                try:
                    # NOTE: utf-8-sig wont be a problem if no BOM
                    with open(config_path, 'r', encoding='utf-8-sig') as fobj:
                        # NOTE: yaml.safe_load() can load json as well
                        ret = yaml.safe_load(fobj)
                        print(f'Read config "{config_path}".')
                        return ret
                except:
                    print(f'Failed to read the config file. Using VA default.')
                    return VA_DEFAULT_CONFIG
    return VA_DEFAULT_CONFIG




def toVideoAlphaInfoDict(
    m2ts_path: Path, assumed_vol: int|str, input_dir: Path, init_audio_samples: bool = ENABLE_AUDIO_SAMPLES_IN_VA
    ) -> dict[str, str]:
    cf: hcf.CoreFile = hcf.CoreFile(m2ts_path, init_crc32=False, init_audio_samples=init_audio_samples)
    info_dict = dict(zip(VA_FULL_DICT.keys(), itertools.repeat('')))
    info_dict[VA_PATH_CN] = m2ts_path.relative_to(input_dir).as_posix()
    info_dict[VA_M2TS_VOL_CN] = str(assumed_vol)
    info_dict[VA_M2TS_IDX_CN] = m2ts_path.stem
    info_dict[DURATION_CN] = cf.fmtGeneralDuration()
    info_dict[TR_COMP_CN] = cf.fmtTrackTypeCounts()
    info_dict[VA_VID_FPS_CN] = cf.fmtFpsInfo()
    info_dict[VA_AUDIO_SAMPLES_CN] = cf.audio_samples
    return info_dict




def readVideoAlphaNamingFile(va_file: Path|None, logger: Logger) -> tuple[dict, list[dict]]:
    '''
    Read the instructed naming fields ever filled in VA.
    '''

    if not va_file or not va_file.is_file():
        return {}, []

    try:
        match va_file.suffix.lower():
            case '.csv':
                success, data_dicts = readCSV(va_file)
                data_dicts: list[dict[str, str]] = unquotFields4CSV(data_dicts)
                if not success: raise Exception
            case '.yaml'|'.yml':
                with va_file.open('r', encoding='utf-8-sig') as fo:
                    data_dicts: list[dict[str, str]] = yaml.safe_load(fo)
            case '.json':
                data_dicts: list[dict[str, str]] = json.loads(va_file.read_text(encoding='utf-8-sig'))
            case _:
                raise ValueError
        assert isinstance(data_dicts, list) and all(isinstance(d, dict) for d in data_dicts)
    except:
        logger.error(f'Failed to read "{va_file}".')
        return {}, []

    try:
        base_naming_dict: dict[str, str] = {var: '' for var in VA_FULL_DICT.values()}
        file_naming_dicts: list[dict[str, str]] = []
        for data_dict in data_dicts:
            if any(v == BASE_LINE_LABEL for v in data_dict.values()):
                #* default dict --------------------------------------------------------------------
                base_naming_dict.update({v: data_dict.get(k, '') for k, v in VA_BASE_LINE_USER_DICT.items()})
            else:
                #* per file dict -------------------------------------------------------------------
                file_naming_dict: dict[str, str] = {}
                file_naming_dict.update({var: '' for var in VA_FULL_DICT.values()})
                #! it's safe to use get() as we wont overwrite anything
                file_naming_dict.update({v: data_dict.get(k, '') for k, v in VA_FULL_DICT.items()})
                file_naming_dicts.append(file_naming_dict)
    except:
        logger.error(f'Failed to load data from "{va_file}".')
        return {}, []

    logger.info(f'Loaded data from "{va_file}".')
    return base_naming_dict, file_naming_dicts




def copyVideoNamingFromVA(cfs: list[hcf.CoreFile], file_naming_dicts: list[dict[str, str]], logger: Logger):

    if not file_naming_dicts: return

    logger.debug(f'Matching files to VA instruction ...')

    cf_vol_nums = guessVolNumsFromPaths([cf.path for cf in cfs], logger=logger)
    file_naming_used_bools = [False] * len(file_naming_dicts)

    for cf in cfs:

        #* match by audio sample -------------------------------------------------------------------
        audio_samples_matched = False
        if ENABLE_AUDIO_SAMPLES_IN_VA:
            for i, file_naming_dict in enumerate(file_naming_dicts):
                if file_naming_used_bools[i]: continue
                #! dont init cf.audio_samples if file_naming_dict has no audio_samples recorded
                if recorded_audio_samples := file_naming_dict.get(VA_AUDIO_SAMPLES_VAR):
                    if cmpAudioSamples(recorded_audio_samples, cf.audio_samples):
                        cf.updateFromNamingDict(file_naming_dict)
                        file_naming_used_bools[i] = True
                        audio_samples_matched = True
                        break
        if audio_samples_matched:
            continue

        #* matching by volume number, should be less reliable --------------------------------------
        vol_idx_matched = False
        for i, cf_vol_num, file_naming_dict in zip(itertools.count(), cf_vol_nums, file_naming_dicts):
            if file_naming_used_bools[i]: continue
            va_vol_idx = file_naming_dict.get(VA_M2TS_VOL_VAR)
            va_m2ts_idx = file_naming_dict.get(VA_M2TS_IDX_VAR)
            cf_vol_num = cf_vol_num
            cf_m2ts_idx = m.group('m2ts_idx') if (m := STRICT_TRANSCODED_FILESTEM_REGEX.match(cf.path.stem)) else None
            if cf_vol_num and cf_m2ts_idx and va_vol_idx and va_m2ts_idx:
                if (int(cf_vol_num) == int(va_vol_idx)) and (int(cf_m2ts_idx) == int(va_m2ts_idx)):
                    cf.updateFromNamingDict(file_naming_dict)
                    file_naming_used_bools[i] = True
                    vol_idx_matched = True
                    break
        if vol_idx_matched:
            continue

        #* missing a match -------------------------------------------------------------------------
        logger.warning(f'"{cf.path}" cannot match a VA config.')

    for used_bool, file_naming_dict in zip(file_naming_used_bools, file_naming_dicts):
        if not used_bool:
            logger.warning(f'Unused VA config "{file_naming_dict}".')




def recordBDMVInfo(input_dir: Path):
    if DEBUG: assert input_dir.is_dir()

    logger = initLogger(input_dir.parent / VA_LOG_FILENAME)
    logger.info(USING_VA_1.format(AC_VERSION))
    logger.info(THE_INPUT_IS_1.format(input_dir))

    # TODO: better adding CLI interface in the future
    config: dict = readConf4VideoAlpha(__file__, input_dir)

    # TODO: support DVD in the future
    if not (m2ts_paths := listFile(input_dir, ext='m2ts')):
        logger.error(VA_NO_M2TS_FOUND_0)
        return

    assumed_vols = guessVolNumsFromPaths(m2ts_paths, input_dir, logger)
    if ENABLE_AUDIO_SAMPLES_IN_VA:
        logger.info(VA_WILL_READ_M2TS_0)

    mp = NUM_RAM_JOBS if ENABLE_AUDIO_SAMPLES_IN_VA else NUM_IO_JOBS
    logger.info(LOADING_WITH_N_WORKERS_1.format(mp))
    with logging_redirect_tqdm([logger]):
        pbar = tqdm(total=len(m2ts_paths), desc='Loading', dynamic_ncols=True, ascii=True, unit='file')

        def callback(result):
            pbar.update(1)
            logger.info(ADDED_1.format(result[VA_PATH_CN]))

        ret = []
        with Pool(mp) as pool:
            for m2ts_path, assumed_vol in zip(m2ts_paths, assumed_vols):
                ret.append(
                    pool.apply_async(toVideoAlphaInfoDict, args=(m2ts_path, assumed_vol, input_dir), callback=callback)
                    )
            pool.close()
            pool.join()
        pbar.close()
        va_info_dicts: list[dict[str, str]] = [r.get() for r in ret]

    va_base_info_dict = {k: BASE_LINE_LABEL for k in VA_FULL_DICT.keys()}
    va_base_info_dict.update({k: '' for k in VA_BASE_LINE_USER_DICT.keys()})
    va_info_dicts = [va_base_info_dict] + va_info_dicts

    for ext in VA_OUTPUT_EXTS:
        if config.get(ext, False):
            out_file = input_dir.parent.joinpath(f'VA-{TIMESTAMP}.{ext}')
            print(VA_GEN_OUTPUT_1.format(out_file))
            working_list = quotFields4CSV(va_info_dicts) if ext == 'csv' else va_info_dicts
            if not globals()[f'listM2TS2{ext.upper()}'](out_file, working_list):
                print(FAILED_TO_WRITE_1.format(out_file))

    logging.shutdown()




#*=====================================================================================================================




def toVideoInfoDicts(cfs: list[hcf.CF], logger: Logger) -> list[dict[str, str]]:
    ret = []

    for cf in cfs:

        d: dict[str, str] = {}
        d.update({k: '' for k in VD_FULL_DICT.keys()})
        d.update({k: getattr(cf, v) for (k, v) in VD_USER_DICT.items()})

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




def readVdCSV(vd_csv_path: Path, logger: Logger) -> tuple[dict[str, str], list[dict[str, str]]]:

    logger.debug(f'Loading "{vd_csv_path}" ...')

    if not vd_csv_path or not vd_csv_path.is_file():
        return {}, []

    success, csv_dicts = readCSV(vd_csv_path)
    if not success:
        logger.error(f'Failed to read "{vd_csv_path}".')
        return {}, []
    csv_dicts = unquotFields4CSV(csv_dicts)

    try:
        base_naming_dict: dict[str, str] = {var: '' for var in VD_FULL_DICT.values()}
        file_naming_dicts: list[dict[str, str]] = []
        for csv_dict in csv_dicts:
            if any(v == BASE_LINE_LABEL for v in csv_dict.values()):
                #* default dict --------------------------------------------------------------------
                #! dont use get() as we want to assert csv_dict has all VD_FULL_DICT.keys()
                base_naming_dict.update({v: csv_dict[k] for k, v in VD_FULL_DICT.items()})
            else:
                #* per file dict -------------------------------------------------------------------
                naming_dict: dict[str, str] = {}
                naming_dict.update({var: '' for var in VD_FULL_DICT.values()})
                #! dont use get() as we want to assert csv_dict has all VD_FULL_DICT.keys()
                naming_dict.update({v: csv_dict[k] for k, v in VD_FULL_DICT.items()})
                file_naming_dicts.append(naming_dict)
        enables = toEnabledList([naming_dict[ENABLE_VAR] for naming_dict in file_naming_dicts])
        enabled_naming_dicts = list(itertools.compress(file_naming_dicts, enables))
        if len(file_naming_dicts) != len(enabled_naming_dicts):
            logger.info(f'Loaded "{vd_csv_path}" with {len(enabled_naming_dicts)}/{len(file_naming_dicts)} files.')
        else:
            logger.info(f'Loaded "{vd_csv_path}".')
    except:
        logger.error(f'Failed to load data from "{vd_csv_path}".')
        return {}, []

    return base_naming_dict, enabled_naming_dicts




def writeVideoInfo2CSV(
    csv_path: Path, base_csv_dict: dict[str, str], file_csv_dicts: list[dict[str, str]], logger: Logger
    ) -> bool:

    logger.debug(WRITING_1.format(csv_path))
    csv_dicts = quotFields4CSV([base_csv_dict] + file_csv_dicts)
    if writeCSV(csv_path, csv_dicts):
        logger.info(SAVED_1.format(csv_path))
        return False
    else:
        logger.error(FAILED_TO_WRITE_INFO_CSV_1.format(csv_path))
        return True




def guessNamingFieldsFromSimpleFilename(cf: hcf.CF, logger: Logger):
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




def guessNamingFields4ASS(cf: hcf.CF, logger: Logger):
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
            logger.warning(GUESSED_ASS_NAMING_CONFLICT_3.format(lang_detected, cf.path.parent.name, cf.path.name))
        else:
            # NOTE use un-normalized `lang_in_filename` as this may be the expectation of the fansub groups
            # TODO normalize the field so the user wont get an error message in VP
            # if the fansub groups used a language tag not meeting our naming standard
            cf.x = filename_lang_tag if filename_lang_tag else lang_detected




def guessNamingFields4ARC(cf: hcf.CF, logger: Optional[Logger] = None):
    if not isArchive(cf.path):
        if logger: logger.error(INVALID_FILE_1.format(cf.path))
        return
    has_image, has_font = False, False
    for filename in getFileList(cf.path):
        if filename.lower().endswith(COMMON_IMAGE_EXTS): has_image = True
        if filename.lower().endswith(COMMON_FONT_EXTS): has_font = True
        if has_image and has_font: break  # early stopping
    match has_image, has_font:
        case True, False:
            cf.l = STD_SPS_DIRNAME  # archives of pure images are placed in SPs
        case False, True:
            cf.l = '/'
            cf.c = STD_FONT_NAME  # archives of pure fonts are placed in fonts
        case True, True:
            if logger: logger.warning(DIRTY_CONTENT_1.format(cf.path))
        case False, False:
            if logger: logger.warning(UNKNOWN_ARC_CONTENT_1.format(cf.path))




def guessNamingFields4MKA(mka: hcf.CF, cfs: list[hcf.CF], logger: Logger):

    candidates = [cf for cf in cfs if (cf.e == 'mkv' and matchTime(mka.duration, cf.duration))]
    #? how can we discriminate multiple mka if they have the same duration?
    if len(candidates) == 1:
        mka.f = candidates[0].crc32




def guessVideoNaming(cfs: list[hcf.CF], logger: Logger):
    '''Guess the naming of each CoreFile based on its current filename.'''
    for i, cf in enumerate(cfs):
        logger.debug(GUESSING_NAMING_1.format(cf.path))
        match cf.ext:
            case 'mkv'|'mp4':
                guessNamingFieldsFromSimpleFilename(cf, logger)
            case 'mka':
                guessNamingFieldsFromSimpleFilename(cf, logger)
                guessNamingFields4MKA(cf, cfs[:i] + cfs[i + 1:], logger)
            case 'flac':
                guessNamingFieldsFromSimpleFilename(cf, logger)
                cf.l = STD_SPS_DIRNAME
            case 'ass':  # we can guess ass lang suffix at VD
                guessNamingFields4ASS(cf, logger)
            case '7z'|'zip'|'rar':
                guessNamingFields4ARC(cf, logger)
            case _:
                logger.warning(GOT_BUT_EXPECT_ONE_OF_2.format(cf.ext, VX_ALL_EXTS))




def collectVideoInfos(*, src_dir: Path, va_file: Optional[Path] = None):

    if not src_dir.exists():
        print(CANT_FIND_1.format(src_dir))
        return

    logger = initLogger(src_dir.parent / VP_LOG_FILENAME)
    logger.info(USING_VP_1.format(AC_VERSION))

    if va_file:
        logger.info(THE_INPUT_IS_2.format(src_dir, va_file))
        va_base_naming_dict, va_file_naming_dicts = readVideoAlphaNamingFile(va_file, logger)
    else:
        logger.info(logger.info(THE_INPUT_IS_1.format(src_dir)))
        va_base_naming_dict, va_file_naming_dicts = {}, []

    vx_paths = filterVxFilePaths(src_dir, logger)
    cfs = hcf.toCoreFilesWithTqdm(vx_paths, logger, mp=getCRC32MultiProc(vx_paths, logger))
    cmpCRC4CoreFiles(cfs, findCRC32InFilenames(vx_paths), logger)
    if ENABLE_FILE_CHECKING_IN_VP: chkSeasonFiles(cfs, logger)

    # NOTE first guess naming and then fill each CF from VA
    # so the naming instruction in VA will not be overwritten
    # also, audio samples will not appear in file_naming_dicts to be sent to VP
    # so we cannot use file_naming_dicts for copyNamingFromVA()
    guessVideoNaming(cfs, logger)
    copyVideoNamingFromVA(cfs, va_file_naming_dicts, logger)
    file_csv_dicts = toVideoInfoDicts(cfs, logger)

    # don't forget to update the default dict from VA, which is not updated in fillFieldsFromVA()
    # NOTE leave useful fields as '' to notify the user that they can fill it
    base_csv_dict = {k: BASE_LINE_LABEL for k in VD_FULL_DICT.keys()}
    base_csv_dict.update({k: ' ' for k in VD_BASE_LINE_USER_DICT.keys()})
    base_csv_dict.update({k: va_base_naming_dict.get(v, ' ') for k, v in VA_BASE_LINE_USER_DICT.items()})

    writeVideoInfo2CSV(src_dir.parent / VP_CSV_FILENAME, base_csv_dict, file_csv_dicts, logger)




def tstIO4VP(src_files: list[str]|list[Path], dst_dir: str|Path, logger: Logger) -> bool:
    '''This is a boring check to test if we can read/write the dst dir, and if we can hardlink from src to dst.'''

    logger.info(f'Testing input files and the output dir "{dst_dir}"...')

    src: list[Path] = [Path(path) for path in src_files]
    dst: Path = Path(dst_dir)

    # empty src input is abnormal
    if not src:
        logger.error('No input files.')
        return False

    # test that every input file is readable
    for path in src:
        try:
            path.is_file()
            (fobj := path.open(mode='rb')).read(1)
            fobj.close()
        except FileNotFoundError:
            logger.error(f'Failed to locate the input file "{path}".')
            return False
        except OSError:
            logger.error(f'Failed to test reading the input file "{path}".')
            return False
        except Exception as e:
            logger.error(
                f'Failed to test reading the input file "{path}" due to an unexpected error {e}. Please Report.'
                )
            return False
    logger.debug('Read test completed.')

    # test dst parent exists as a dir
    try:
        if not dst.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        assert dst.is_dir()
    except OSError:
        logger.error(f'Failed to create to output parent.')
        return False
    except AssertionError:
        logger.error(f'Failed to verify to output parent.')
        return False
    except Exception as e:
        logger.error(f'Failed to test the output parent due to an unexpected error {e}. Please Report.')
        return False
    logger.debug('Dst is dir completed.')

    # test creating and delete files under the dst parent
    dst_testfile = dst.joinpath('1234567890'*23 + '.tt')
    try:
        dst_testfile.touch()
        dst_testfile.write_bytes(b'1234567890')
        assert dst_testfile.read_bytes() == b'1234567890'
        dst_testfile.unlink()
    except OSError:
        logger.error('Failed to read/write a test file of 233 chars filename. Available path length may be inadequate.')
        return False
    except AssertionError:
        logger.error('Failed to verify a test file at the output parent. Your OS/Disk may be corrupted.')
        return False
    except Exception as e:
        logger.error(f'Failed to test r/w under the output parent due to an unexpected error {e}. Please Report.')
        return False
    logger.debug('Dst writing completed.')

    return True




def doAutoIndexing(season: hsn.Season, logger: Logger):

    cfs = season.files

    # we have the following kinds of files:
    # auto_cfs: to be automatically indexed
    # dep_cfs: dependent files, which need to copy the naming from another file by crc32 lookup
    # named_cfs: naming already specified in cf.c, no need to do anything

    auto_cfs: list[hcf.CF] = [info for info in cfs if not info.f]
    dep_cfs: list[hcf.CF] = [info for info in cfs if (info.f and re.match(CRC32_STRICT_REGEX, info.f))]
    named_cfs: list[hcf.CF] = [info for info in cfs if (info.f and not re.match(CRC32_STRICT_REGEX, info.f))]

    state: dict[str, int|float] = {}
    for i, acf in enumerate(auto_cfs):
        i1 = acf.i1 if acf.i1 else ''
        i2 = acf.i1 if acf.i2 else ''
        if i1 and i2:
            state[f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{acf.x}'] = float(i1)
            state[f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{i1}//{acf.x}'] = float(i2)
        elif i1 and not i2:
            state[f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{acf.x}'] = float(i1)
            # whether we need to update i2 depends on whether there is a same key
            key = f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{i1}//{acf.x}'
            if (v := state.get(key)):
                v = int(v + 1)
                acf.i2 = str(v)
                state[key] = v
                continue
            else:  # we need to loop though the remaining to find the same key
                for j, cf in enumerate(auto_cfs[i + 1:]):
                    j1 = '' if cf.i1 == None else cf.i1
                    j2 = '' if cf.i2 == None else cf.i2
                    jey = f'{cf.e}//{cf.g}//{cf.t}//{cf.l}//{cf.c}//{j1}//{cf.x}'
                    if key == jey:
                        acf.i2 = str(1)
                        state[key] = 1
                        break
        else:  # if not i1
            key = f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{acf.x}'
            if (v := state.get(key)):
                v = int(v + 1)
                acf.i1 = str(v)
                state[key] = v
                continue
            else:  # we need to loop through the remaining to find the same key
                for j, cf in enumerate(auto_cfs[i + 1:]):
                    j1 = cf.i1 if cf.i1 else ''
                    j2 = cf.i2 if cf.i2 else ''
                    jey = f'{cf.e}//{cf.g}//{cf.t}//{cf.l}//{cf.c}//{cf.x}'
                    if key == jey:
                        acf.i1 = str(1)
                        state[key] = 1
                        break

    for i, dcf in enumerate(dep_cfs):
        found = None
        for cf in (auto_cfs + named_cfs):
            if cf.crc == dcf.f:  # TODO use regex for dcf.c
                found = cf
                break
        if found != None:
            dcf.copyNaming(found)
            logger.info(f'File "{dcf.crc}" copied naming from file "{found.crc}".')
        else:
            logger.error('Cannot find the file with the target CRC32 {} to copy the naming from.')
            raise ValueError('Trying to refer to the naming of an inexisting/disabled file.')
    return




def doVideoFilePlacement(season: hsn.Season, hardlink: bool, logger: Logger) -> bool:
    '''
    Execute the naming plan of a Season onto disk.

    Arguments:
    season: Season: the source Season object

    dst_parent: Path : the output dir will be under this dir
    default: INFO : the base/default naming config
    infos: list[CF] : the naming config of each files
    hardlink: bool : whether to use hardlink or not
    logger: Logger

    Return:
    bool: whether the whole job is completed without error
    '''

    # the quality label for the root dir is determined by files at the root dir

    logger.info('Placing files ...')

    ok = True
    Path(season.dst).mkdir(parents=True, exist_ok=True)
    logger.info(f'Created the season root dir "{season.dst}".')

    # everything looks ok so far, now start creating the target
    for cf in season.files:
        try:
            src, dst = Path(cf.src), Path(cf.dst)
            if src.resolve() == dst.resolve():
                logger.error(f'The source and destination are the same (file 0x{cf.crc}).')
                ok = False
                continue
            parent = dst.parent
            if parent.is_file():
                logger.error(f'Failed to create "{dst}" (its parent is a file)')
            else:
                if not parent.exists():
                    parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f'Created dir "{parent}"')
                if dst.is_file():
                    dst.unlink()
                    logger.warning(f'Removed existing file "{dst}".')
                if hardlink:
                    dst.hardlink_to(src)
                    logger.info(f'Harlinked to "{dst}" (0x{cf.crc}).')
                else:
                    shutil.copy(src, dst)
                    logger.info(f'Copied to "{dst}" (0x{cf.crc}).')
        except Exception as e:
            logger.error(f'Unknown error {e} occurred during placing files. Stopping...')
            ok = False
            break
    if not ok:
        logger.error('Error occurred during placing files.')
    return ok




def placeVideos(*, csv_path: Path):

    logger = initLogger(log_path := csv_path.parent.joinpath(VP_LOG_FILENAME))
    logger.info(USING_VP_1.format(AC_VERSION))

    base_naming_dict, file_naming_dicts = readVdCSV(csv_path, logger)
    cleanNamingDicts(base_naming_dict, file_naming_dicts, logger)
    if not chkNamingDicts(base_naming_dict, file_naming_dicts, logger): return

    dst_parent_dir = Path(p) if (p := base_naming_dict[FULLPATH_VAR]) else csv_path.parent
    src_file_paths = [Path(d[FULLPATH_VAR]) for d in file_naming_dicts]
    if not tstIO4VP(src_file_paths, dst_parent_dir, logger): return

    (season := hsn.Season()).dst_parent = dst_parent_dir.as_posix()
    season.add(hcf.toCoreFilesWithTqdm(src_file_paths, logger, mp=getCRC32MultiProc(src_file_paths, logger)))
    cmpCRC4CoreFiles(season.files, [naming_info[CRC32_VAR] for naming_info in file_naming_dicts], logger)
    hsn.applyNamingDicts(season, base_naming_dict, file_naming_dicts, logger)
    doAutoIndexing(season, logger)
    chkSeasonNaming(season, logger)
    composeFullDesp(season, logger)
    chkNamingDependency(season, logger)
    if ENABLE_FILE_CHECKING_IN_VP:
        if not chkSeasonFiles(season, logger): return
    if not chkFinalNamingConflict(season, logger): return
    logNamingSummary(base_naming_dict, file_naming_dicts, season, logger)
    if not doVideoFilePlacement(season, tstMkHardlinks(src_file_paths, dst_parent_dir), logger): return




#*=====================================================================================================================




def readCSV4ComplexVideoCmp(input_path: Path) -> tuple[bool, dict[str, list[tuple[str, str, str]]]]:

    if not input_path or not (input_path := Path(input_path)).is_file():
        return False, {}

    # vr_csv_dicts : list[dict[str, str]]
    success, vr_csv_dicts = readCSV(input_path)
    if not success:
        return False, {}
    vr_csv_dicts = unquotFields4CSV(vr_csv_dicts)

    grouping_dicts: dict[str, list[tuple[str, str, str]]] = {}

    for vr_csv_dict in vr_csv_dicts:
        k = vr_csv_dict[VR_GRP_IDX_CN]
        if k in grouping_dicts.keys():
            grouping_dicts[k].append((vr_csv_dict[VR_SUBGRP_IDX_CN], vr_csv_dict[ENABLE_CN], vr_csv_dict[FULLPATH_CN]))
        else:
            grouping_dicts[k] = [(vr_csv_dict[VR_SUBGRP_IDX_CN], vr_csv_dict[ENABLE_CN], vr_csv_dict[FULLPATH_CN])]

    return True, grouping_dicts




def writeCSV4ComplexVideoCmp(ouput_path: Path, grouping_dict: dict[str, list[tuple[str, str, str]]]) -> bool:

    if not ouput_path or (output_path := Path(ouput_path)).exists():
        return False

    vr_csv_dicts: list[dict] = []
    for group_idx, group_list in grouping_dict.items():
        for group in group_list:
            vr_csv_dict = dict(zip(VR_FULL_DICT.keys(), (group_idx, *group)))
            vr_csv_dicts.append(vr_csv_dict)

    return writeCSV(output_path, quotFields4CSV(vr_csv_dicts))




def cmpVideoGroups(*groups: list[Path], grpname: str = '0', subgrps_names: list[str] = [], logger: Logger):

    if len(groups) < 2:
        logger.error('At least 2 groups are required.')

    if subgrps_names and (len(subgrps_names) != len(groups) or len(set(subgrps_names)) != len(subgrps_names)):
        logger.warning('The supplied names do not match the number of groups. Falling back to default names.')
        subgrps_names = [str(i) for i in range(len(groups))]
    elif not subgrps_names:
        subgrps_names = [str(i) for i in range(len(groups))]

    for (n1, n2), (g1, g2) in zip(itertools.combinations(subgrps_names, 2), itertools.combinations(groups, 2)):

        l1, l2 = len(g1), len(g2)
        if l1 == 0 or l2 == 0:
            logger.error(f'Cannot compare empty group.')
            continue

        g1 = [hcf.CF(f) for f in g1]
        g2 = [hcf.CF(f) for f in g2]

        if any(cf.has_video for cf in g1 + g2):
            logger.info('Comparing video...')
            cmpVideoContent(g1, g2, logger)

        if any(cf.has_audio for cf in g1 + g2):
            logger.info('Comparing audio...')
            diff_audios = cmpCfAudContent(g1, g2, logger)
            for k, diff_audio, freq in diff_audios:
                filename = f'VR-{TIMESTAMP}-DiffAudio-{grpname if grpname else 0}-{n1}vs{n2}-a{k}.log'
                img_path = proposeFilePath([cf.path for cf in (g1 + g2)], filename)
                logger.debug(f'Proposed spectrogram img path: {img_path}')
                if mkSpectrogram(img_path, diff_audio, freq):
                    logger.info(SAVED_SPECTROGRAM_1.format(img_path))
                else:
                    logger.error(FAILED_TO_WRITE_1.format(img_path))

        if any(cf.has_menu for cf in g1 + g2):
            logger.info('Comparing menu...')
            cmpCfMenuContent(g1, g2, logger)

        if any(cf.has_image for cf in g1 + g2):
            logger.info('Comparing menu...')
            cmpImageContent(g1, g2, logger)

        if any(cf.has_text for cf in g1 + g2):
            logger.info('Comparing text...')
            cmpTextContent(g1, g2, logger)

        # cmpNaming(g1, g2, logger)




def doStdSoloVideoCheck(input_dir: Path):

    if not input_dir.is_dir(): return

    logger = initLogger(log_path := input_dir.parent.joinpath(VR_LOG_FILENAME))
    logger.info(USING_VR_1.format(AC_VERSION))
    logger.info(VR_MODE_STD_SOLO_CHK_0)

    dirs = listDir(input_dir, rglob=False)
    files = listFile(input_dir, rglob=False)
    match len(dirs), len(files):
        case 0, 0:
            logger.error(GOT_EMPTY_DIR_1.format(input_dir))
        case _, 0:
            logger.info(VR_GOT_SERIES_DIR_0)
            # if series := fromSeriesDir(input_dir, logger): chkSeries(series, logger)
            # else: logger.error(f'Not a valid series dir "{input_dir}".')
        case _, _:
            if season := hsn.fromSeasonDir(input_dir, logger):
                chkSeason(season, logger)
                composeFullDesp(season, logger)
                cmpDstNaming(season, logger)
            else:
                logger.error(VR_NOT_A_VALID_SEASON_DIR.format(input_dir))

    printCheckerEnding(log_path.as_posix(), logger)




def findVideoMatchingBetweenDir(input1_dir: Path, input2_dir: Path):

    if not input1_dir.is_dir() or not input2_dir.is_dir(): return

    logger = initLogger(log_path := proposeFilePath([input1_dir, input2_dir], VR_LOG_FILENAME))
    logger.info(USING_VR_1.format(AC_VERSION))
    logger.info(VR_MODE_FIND_MATCHING_0)

    input1_fs_all: list[Path] = listFile(input1_dir, ext=VX_MAIN_EXTS)
    input2_fs_all: list[Path] = listFile(input2_dir, ext=VX_MAIN_EXTS)
    input1_fs = filterOutCDsScans(input1_fs_all)
    input2_fs = filterOutCDsScans(input2_fs_all)
    # if len(input1_fs) != len(input1_fs_all):
    #     logger.info(f'Removed some FLAC in {STD_CDS_DIRNAME} from the input dir "{input1_dir}".')
    # if len(input2_fs) != len(input2_fs_all):
    #     logger.info(f'Removed some FLAC in {STD_CDS_DIRNAME} from the input dir "{input2_dir}".')
    input1_cfs = [hcf.CoreFile(f) for f in input1_fs]
    input2_cfs = [hcf.CoreFile(f) for f in input2_fs]

    if (not input1_cfs) or (not input2_cfs):
        logger.info(VR_GOT_EMPTY_DIR_FINDING_MATCHING_0)
        groups: dict[str, list[tuple[str, str, str]]] = dict()
        #! only one of the two loops below will be executed
        for i, input1_cf in enumerate(input1_cfs):
            groups[str(i)] = [('', '', input1_cf.path.resolve().as_posix())]
        for i, input2_cf in enumerate(input2_cfs):
            groups[str(i)] = [('', '', input2_cf.path.resolve().as_posix())]
        csv_path = input1_dir.parent / VR_CSV_FILENAME if input1_cfs else input2_dir.parent / VR_CSV_FILENAME
        if writeCSV4ComplexVideoCmp(csv_path, groups):
            logger.info(SAVED_1.format(csv_path))
        else:
            logger.error(FAILED_TO_WRITE_1.format(csv_path))
        logging.shutdown()
        return

    groups: dict[str, list[tuple[str, str, str]]] = dict()
    idx = itertools.count(1)

    # now let's start matching, we do it in this order:
    # 1. match by menu timestamps, higher robust (may fail if videos rarely use identical menu)
    # 2. match by audio samples, higher robust (may fail especially in CM/Menu with identical audio)
    # 3. match by duration, mid robust (may fail in any videos having identical duration)

    #***********************************************************************************************
    # step 1: match by chapter timestamps

    for input1_cf in input1_cfs[:]:  # make a copy of the list, so we can call .remove() in the loop
        # NOTE we only match the first menu track, is this not robust enough?
        matches = [
            input2_fi for input2_fi in input2_cfs if (
                input1_cf.menu_tracks and input2_fi.menu_tracks
                and matchMenuTimeStamps(input1_cf.menu_timestamps[0], input2_fi.menu_timestamps[0])
                )
            ]
        if len(matches) == 1:
            groups[str(next(idx))] = [('1', '', input1_cf.path.resolve().as_posix()),
                                        ('2', '', matches[0].path.resolve().as_posix())]
            input1_cfs.remove(input1_cf)
            input2_cfs.remove(matches[0])
            logger.info(f'Matched by chapter timestamp: "{input1_cf.path}" <-> "{matches[0].path}"')
        elif len(matches) > 1:
            logger.warning(f'Cannot match "{input1_cf.path}" as multiple counterparts have the same chapter timestamp.')
        else:
            if input1_cf.menu_tracks:
                logger.warning(f'Cannot match "{input1_cf.path}" as NO counterpart has the same chapter timestamp.')

    #***********************************************************************************************
    # step 2: match by audio digest
    if ENABLE_AUDIO_SAMPLES_IN_VA:
        for input1_cf in input1_cfs[:]:  # make a copy of the list, so we can call .remove() in the loop
            matches = [
                input2_fi for input2_fi in input2_cfs
                if cmpAudioSamples(input1_cf.audio_samples, input2_fi.audio_samples)
                ]
            if len(matches) == 1:
                groups[str(next(idx))] = [('1', '', input1_cf.path.resolve().as_posix()),
                                            ('2', '', matches[0].path.resolve().as_posix())]
                input1_cfs.remove(input1_cf)
                input2_cfs.remove(matches[0])
                logger.info(f'Matched by audio digest: "{input1_cf.path}" <-> "{matches[0].path}"')
            elif len(matches) > 1:
                logger.warning(f'Cannot match "{input1_cf.path}" as multiple counterparts have the same audio digest.')
            else:
                if input1_cf.audio_samples:
                    logger.warning(f'Cannot match "{input1_cf.path}" as NO counterpart has the same audio digest.')

    #***********************************************************************************************
    # step 3: match by duration
    for input1_cf in input1_cfs[:]:  # make a copy of the list, so we can call .remove() in the loop
        matches = [
            input2_fi for input2_fi in input2_cfs if
            (input1_cf.has_duration and input2_fi.has_duration and matchTime(input1_cf.duration, input2_fi.duration))
            ]
        if len(matches) == 1:
            groups[str(next(idx))] = [('1', '', input1_cf.path.resolve().as_posix()),
                                        ('2', '', matches[0].path.resolve().as_posix())]
            input1_cfs.remove(input1_cf)
            input2_cfs.remove(matches[0])
            logger.info(f'Matched by duration: "{input1_cf.path}" <-> "{matches[0].path}"')
        elif len(matches) > 1:
            # TODO this implementation is dirty, fix it
            if all('menu' in cf.path.name.lower() for cf in (input1_cf, *matches)):
                subidx = itertools.count(1)
                group: list[tuple[str, str, str]] = []
                group.append((str(next(subidx)), '', input1_cf.path.resolve().as_posix()))
                for match in matches:
                    group.append((str(next(subidx)), '', match.path.resolve().as_posix()))
                    input2_cfs.remove(match)
                input1_cfs.remove(input1_cf)
                groups[str(next(idx))] = group
                logger.info(f'Matched by duration for menus: "{input1_cf.path}". (NOTE this is not robust)')
            else:
                logger.warning(f'Cannot match "{input1_cf.path}" as multiple counterparts have the same duration.')
        else:
            logger.warning(f'Cannot match "{input1_cf.path}" as NO counterpart has the same duration.')

    # we need to do this again for input2_cfs
    for input2_cf in input2_cfs[:]:  # make a copy of the list, so we can call .remove() in the loop
        matches = [
            input1_fi for input1_fi in input1_cfs if
            (input2_cf.has_duration and input1_fi.has_duration and matchTime(input2_cf.duration, input1_fi.duration))
            ]
        if len(matches) == 1:
            groups[str(next(idx))] = [('1', '', input2_cf.path.resolve().as_posix()),
                                        ('2', '', matches[0].path.resolve().as_posix())]
            input2_cfs.remove(input2_cf)
            input1_cfs.remove(matches[0])
            logger.info(f'Matched by duration: "{matches[0].path}" <-> "{input2_cf.path}"')
        elif len(matches) > 1:
            # TODO this implementation is dirty, fix it
            if all('menu' in cf.path.name.lower() for cf in (input2_cf, *matches)):
                subidx = itertools.count(1)
                group: list[tuple[str, str, str]] = []
                group.append((str(next(subidx)), '', input2_cf.path.resolve().as_posix()))
                for match in matches:
                    group.append((str(next(subidx)), '', match.path.resolve().as_posix()))
                    input1_cfs.remove(match)
                input2_cfs.remove(input2_cf)
                groups[str(next(idx))] = group
                logger.info(f'Matched by duration for menus: "{input2_cf.path}". (NOTE this is not robust)')
            else:
                logger.warning(f'Cannot match "{input2_cf.path}" as multiple counterparts have the same duration.')
        else:
            logger.warning(f'Cannot match "{input2_cf.path}" as NO counterpart has the same duration.')

    #***********************************************************************************************
    # slicing is common in videos, so we need to match the rest by filename

    for input1_cf in [input1_fi for input1_fi in input1_cfs if input1_fi.menu_tracks]:
        timestamps = input1_cf.menu_timestamps[0]
        if len(timestamps) < 2: continue  # this seems an incorrect menu
        distances = [(timestamps[i + 1] - timestamps[i]) for i in range(len(timestamps) - 1)]
        founds: list[hcf.CF] = []
        for i, distance in enumerate(distances):
            for input2_cf in input2_cfs:
                if input2_cf in founds: continue
                if matchTime(distance, input2_cf.duration):
                    founds.append(input2_cf)
                    break
        if len(founds) == len(distances):
            matched_group: list[tuple[str, str, str]] = []
            matched_group.append(('1', '', input1_cf.path.resolve().as_posix()))
            for found in founds:
                matched_group.append(('2', '', found.path.resolve().as_posix()))
                input2_cfs.remove(found)
            input1_cfs.remove(input1_cf)
            groups[str(next(idx))] = matched_group
            logger.info(f'Matched sliced videos: {input1_cf}')

    # we need to do this again for input2_cfs
    for input2_cf in [input2_fi for input2_fi in input2_cfs if input2_fi.menu_tracks]:
        timestamps = input2_cf.menu_timestamps[0]
        if len(timestamps) < 2: continue  # this seems an incorrect menu
        distances = [(timestamps[i + 1] - timestamps[i]) for i in range(len(timestamps) - 1)]
        founds: list[hcf.CF] = []
        for i, distance in enumerate(distances):
            for input1_cf in input1_cfs:
                if input1_cf in founds: continue
                if matchTime(distance, input1_cf.duration):
                    founds.append(input1_cf)
                    break
        if len(founds) == len(distances):
            matched_group: list[tuple[str, str, str]] = []
            # NOTE always place input1_cfs first
            for found in founds:
                matched_group.append(('1', '', found.path.resolve().as_posix()))
                input1_cfs.remove(found)
            input2_cfs.remove(input2_cf)
            matched_group.append(('2', '', input2_cf.path.resolve().as_posix()))
            groups[str(next(idx))] = matched_group
            logger.info(f'Matched sliced videos: {input2_cf}')

    #***********************************************************************************************
    # place all the rest into an unnamed group
    unmatched_group: list[tuple[str, str, str]] = []
    for input1_cf in input1_cfs:
        unmatched_group.append(('', '', input1_cf.path.resolve().as_posix()))
    for input2_cf in input2_cfs:
        unmatched_group.append(('', '', input2_cf.path.resolve().as_posix()))
    if unmatched_group:
        groups[''] = unmatched_group

    #***********************************************************************************************
    # write the result to a CSV

    csv_parent = findCommonParentDir([input1_dir, input2_dir])
    if not csv_parent: csv_path = input1_dir.parent.joinpath(f'VR-{TIMESTAMP}.csv')
    else: csv_path = csv_parent.joinpath(f'VR-{TIMESTAMP}.csv')
    if writeCSV4ComplexVideoCmp(csv_path, groups):
        logger.info(f'Successfully written to "{csv_path}".')
        logger.info('')
        logger.info('NEXT:')
        logger.info('Please check again the matching result.')
        logger.info('And then drop the CSV to VR again to start the comparison.')
        logger.info('')
    else:
        logger.error(f'Failed to write to "{csv_path}".')




def cmpSimplyPairedVideos(paths: Iterable[Path]):

    paths = [Path(p) for p in paths]
    assert len(paths) % 2 == 0
    group1 = paths[:len(paths) // 2]
    group2 = paths[len(paths) // 2:]

    logger = initLogger(log_path := proposeFilePath(paths, VR_LOG_FILENAME))
    logger.info(USING_VR_1.format(AC_VERSION))
    logger.info(VR_MODE_SIMP_PAIRED_CMP_0)

    total = len(group1)
    for i, (path1, path2) in enumerate(zip(group1, group2)):
        logger.info(VR_COMPARING_GRP_4.format(i + 1, total, path1, path2))
        cmpVideoGroups([path1], [path2], logger=logger)




def cmpComplexlyPairedVideos(input_csv_path: Path):

    logger = initLogger(input_csv_path.parent / VR_LOG_FILENAME)
    logger.info(USING_VR_1.format(AC_VERSION))
    logger.info(VR_MODE_COMPLEX_PAIRED_CMP_0)

    succ, groups = readCSV4ComplexVideoCmp(input_csv_path)
    if not succ:
        logger.error(FAILED_TO_READ_INFO_CSV_1.format(input_csv_path))
        logging.shutdown()
        return

    for group_id, group_items in groups.items():

        if not group_id:
            continue

        logger.info('')
        logger.info(VR_COMPARING_GRP_1.format(group_id))

        subgrps, enableds, fullpaths = zip(*group_items)
        enableds = toEnabledList(enableds)
        for sub_grp, enabled, fullpath in zip(subgrps, enableds, fullpaths):
            logger.info(VR_COMPARING_ITEM_1.format(sub_grp, ('E' if enabled else 'D'), fullpath))

        if sum(enableds) < 2:
            logger.error(VR_CANT_CHK_GRP_LT2_0)
            continue

        subgrps = [sub_grp for (sub_grp, enabled) in zip(subgrps, enableds) if enabled]
        fullpaths = [full_path for (full_path, enabled) in zip(fullpaths, enableds) if enabled]
        subgrp_tags = list(set(subgrps))
        assert subgrp_tags  # this should never happen

        fullpaths = [Path(fullpath) for fullpath in fullpaths]
        all_files_exist = True
        for fullpath in fullpaths:
            if not fullpath.is_file():
                logger.error(f'File "{fullpath}" is missing.')
                all_files_exist = False
        if not all_files_exist:
            logger.error('Some files are missing. Please check again.')
            continue

        # NOTE this is no longer considered as unsupported
        # if len(valid_subgrps) > 2:
        #     logger.error(f'>2 subgroups defined in group "{grouping_id}". It will be converted to 2 subgroups.')
        #     valid_subgrps = valid_subgrps[:2]
        #     subgrps = [(valid_subgrps[-1] if (sub_grp not in valid_subgrps) else sub_grp) for sub_grp in subgrps]
        #     logger.info(f'Converted subgrouping:')
        #     for sub_grp, fullpath in zip(subgrps, fullpaths):
        #         logger.info(f'{sub_grp:s}: "{fullpath}"')

        if len(subgrp_tags) == 1:
            subgrps = ['1', '2']
            if len(fullpaths) > 2:
                logger.warning('>2 items defined in a single subgroup. Plz note auto subgrouping is not accurate.')
                base_parent = fullpaths[0].parent
                for i, fullpath in zip(itertools.count(), fullpaths):
                    subgrps[i] = '1' if fullpath.is_relative_to(base_parent) else '2'
                logger.info(f'Auto subgrouping:')
                for sub_grp, fullpath in zip(subgrps, fullpaths):
                    logger.info(f'{sub_grp:s}: "{fullpath}"')

        src = [fullpath for (sub_grp, fullpath) in zip(subgrps, fullpaths) if sub_grp == subgrp_tags[0]]
        refs = []
        for subgrp_tag in subgrp_tags[1:]:
            refs.append([fullpath for (sub_grp, fullpath) in zip(subgrps, fullpaths) if sub_grp == subgrp_tag])

        cmpVideoGroups(src, *refs, grpname=group_id, subgrps_names=subgrp_tags, logger=logger)
