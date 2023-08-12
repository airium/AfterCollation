import json
import logging
import itertools
from pathlib import Path

from configs import *
from utils import *
from helpers.corefile import CoreFile
from helpers.misc import guessVolNumsFromPaths

import yaml


__all__ = [
    'readConf4VNA',
    'toVNAFullDict',
    'readVNANamingFile',
    'copyFileNamingFromVNA',
    ]




def readConf4VNA(script_path: str|Path, *paths: str|Path) -> dict:
    '''
    Read the configuration file (YAML/JSON) for VNA.

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
                    print(f'Failed to read the config file. Using VNA default.')
                    return VNA_DEFAULT_CONFIG
    return VNA_DEFAULT_CONFIG




def toVNAFullDict(m2ts_path: Path, assumed_vol: str, input_dir: Path) -> dict[str, str]:
    cf: CoreFile = CoreFile(m2ts_path, init_crc32=False, init_audio_samples=ENABLE_AUDIO_SAMPLES_IN_VNA)
    vna_full_dict = dict(zip(VNA_FULL_DICT.keys(), itertools.repeat('')))
    vna_full_dict[VNA_PATH_CN] = m2ts_path.relative_to(input_dir).as_posix()
    vna_full_dict[VNA_M2TS_VOL_CN] = assumed_vol
    vna_full_dict[VNA_M2TS_IDX_CN] = m2ts_path.stem
    vna_full_dict[DURATION_CN] = cf.fmtGeneralDuration()
    vna_full_dict[TR_COMP_CN] = cf.fmtTrackTypeCounts()
    vna_full_dict[VNA_VID_FPS_CN] = cf.fmtFpsInfo()
    vna_full_dict[VNA_AUDIO_SAMPLES_CN] = cf.audio_samples
    return vna_full_dict




def readVNANamingFile(vna_file: Path|None, logger: logging.Logger) -> tuple[dict, list[dict]]:
    '''
    Read the instructed naming fields ever filled in VNA.
    '''

    if not vna_file or not vna_file.is_file():
        return {}, []

    try:
        match vna_file.suffix.lower():
            case '.csv':
                success, data_dicts = readCSV(vna_file)
                data_dicts: list[dict[str, str]] = unquotFields4CSV(data_dicts)
                if not success: raise Exception
            case '.yaml'|'.yml':
                with vna_file.open('r', encoding='utf-8-sig') as fo:
                    data_dicts: list[dict[str, str]] = yaml.safe_load(fo)
            case '.json':
                data_dicts: list[dict[str, str]] = json.loads(vna_file.read_text(encoding='utf-8-sig'))
            case _:
                raise ValueError
        assert isinstance(data_dicts, list) and all(isinstance(d, dict) for d in data_dicts)
    except:
        logger.error(f'Failed to read "{vna_file}".')
        return {}, []

    try:
        base_naming_dict: dict[str, str] = {var: '' for var in VNA_FULL_DICT.values()}
        file_naming_dicts: list[dict[str, str]] = []
        for data_dict in data_dicts:
            if any(v == BASE_LINE_LABEL for v in data_dict.values()):
                #* default dict --------------------------------------------------------------------
                base_naming_dict.update({v: data_dict.get(k, '') for k, v in VNA_BASE_LINE_USER_DICT.items()})
            else:
                #* per file dict -------------------------------------------------------------------
                file_naming_dict: dict[str, str] = {}
                file_naming_dict.update({var: '' for var in VNA_FULL_DICT.values()})
                #! it's safe to use get() as we wont overwrite anything
                file_naming_dict.update({v: data_dict.get(k, '') for k, v in VNA_FULL_DICT.items()})
                file_naming_dicts.append(file_naming_dict)
    except:
        logger.error(f'Failed to load data from "{vna_file}".')
        return {}, []

    logger.info(f'Loaded data from "{vna_file}".')
    return base_naming_dict, file_naming_dicts




def copyFileNamingFromVNA(cfs: list[CoreFile], file_naming_dicts: list[dict[str, str]], logger: logging.Logger):

    if not file_naming_dicts: return

    logger.debug(f'Matching files to VNA instruction ...')

    cf_vol_nums = guessVolNumsFromPaths([cf.path for cf in cfs], logger=logger)
    file_naming_used_bools = [False] * len(file_naming_dicts)

    for cf in cfs:

        #* match by audio sample -------------------------------------------------------------------
        audio_samples_matched = False
        if ENABLE_AUDIO_SAMPLES_IN_VNA:
            for i, file_naming_dict in enumerate(file_naming_dicts):
                if file_naming_used_bools[i]: continue
                #! dont init cf.audio_samples if file_naming_dict has no audio_samples recorded
                if recorded_audio_samples := file_naming_dict.get(VNA_AUDIO_SAMPLES_VAR):
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
            vna_vol_idx = file_naming_dict.get(VNA_M2TS_VOL_VAR)
            vna_m2ts_idx = file_naming_dict.get(VNA_M2TS_IDX_VAR)
            cf_vol_num = cf_vol_num
            cf_m2ts_idx = m.group('m2ts_idx') if (m := re.match(STRICT_TRANSCODED_FILESTEM_REGEX, cf.path.stem)) else None
            if cf_vol_num and cf_m2ts_idx and vna_vol_idx and vna_m2ts_idx:
                if (int(cf_vol_num) == int(vna_vol_idx)) and (int(cf_m2ts_idx) == int(vna_m2ts_idx)):
                    cf.updateFromNamingDict(file_naming_dict)
                    file_naming_used_bools[i] = True
                    vol_idx_matched = True
                    break
        if vol_idx_matched:
            continue

        #* missing a match -------------------------------------------------------------------------
        logger.warning(f'"{cf.path}" cannot match a VNA config.')

    for used_bool, file_naming_dict in zip(file_naming_used_bools, file_naming_dicts):
        if not used_bool:
            logger.warning(f'Unused VNA config "{file_naming_dict}".')
