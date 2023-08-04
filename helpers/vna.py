import os
import json
import logging
import itertools
from pathlib import Path

from configs import *
from utils import *
from helpers.corefile import CF

import yaml


__all__ = [
    'readConf4VNA',
    'loadVNAInfo',
    'fillNamingFieldsFromVNA',
    'guessVolNumsFromPaths',
    ]




def readConf4VNA(script_path:str|Path, *paths:str|Path) -> dict:

    script_path = Path(script_path)
    other_paths = [Path(p) for p in paths]

    try:
        for path in [*other_paths, script_path]:
            for suffix in ['.yaml', '.yml', '.json']:
                if (config_path := path.with_suffix(suffix)).is_file():
                    with open(config_path, 'r', encoding='utf-8-sig') as f:
                        # NOTE yaml.safe_load() can also handle json
                        ret = yaml.safe_load(f)
                        print(f'Successfully Read configuration file from "{config_path}".')
                        return ret
        raise FileNotFoundError
    except FileNotFoundError:
        pass
    except:
        print(f'Failed to read the config file. Using VNA default.')
    return VNA_DEFAULT_CONFIG




def loadVNAInfo(vna_file:Path|None, logger:logging.Logger) -> tuple[dict, list[dict]]:

    if not vna_file or not vna_file.is_file():
        return {}, []

    try:
        match vna_file.suffix.lower():
            case '.csv':
                success, data_dicts = readCSV(vna_file)
                data_dicts = unquotEntries4CSV(data_dicts)
                if not success: raise Exception
            case '.yaml':
                with vna_file.open('r', encoding='utf-8-sig') as fo:
                    data_dicts = yaml.safe_load(fo)
            case '.json':
                data_dicts = json.loads(vna_file.read_text(encoding='utf-8-sig'))
            case _:
                raise ValueError
        assert isinstance(data_dicts, list) and all(isinstance(d, dict) for d in data_dicts)
    except:
        logger.error(f'Failed to read "{vna_file}".')
        return {}, []

    try:
        default_dict : dict[str, str] = {}
        naming_dicts : list[dict[str, str]] = []
        for data_dict in data_dicts:
            #* default dict ------------------------------------------
            is_base_dict = False
            for k, v in data_dict.items():
                if v == BASE_LINE_LABEL:
                    for kk, vv in VNA_BASE_LINE_USER_DICT.items():
                        default_dict[vv] = data_dict.get(kk, '')
                    is_base_dict = True
                    break
            if is_base_dict: continue
            #* per file dict -----------------------------------------
            naming_dict : dict[str, str] = {}
            for k, v in VNA_PERSISTENT_FIELDS_DICT.items():
                naming_dict[v] = data_dict.get(k, '')
            for k, v in VNA_USER_FIELDS_DICT.items():
                naming_dict[v] = data_dict.get(k, '')
            naming_dicts.append(naming_dict)
    except:
        logger.error(f'Failed to load data from "{vna_file}".')
        return {}, []

    logger.info(f'Loaded data from "{vna_file}".')
    return default_dict, naming_dicts




def fillNamingFieldsFromVNA(corefiles:list[CF], vna_configs:list[dict], logger:logging.Logger):

    if not vna_configs: return

    guessed_vol_nums = guessVolNumsFromPaths([fi.path for fi in corefiles])

    vna_config_used_bools = [False] * len(vna_configs)
    for fi, guessed_vol_num in zip(corefiles, guessed_vol_nums):
        audio_samples_matched = False
        if ENABLE_VNA_AUDIO_SAMPLES:
            for i, vna_config in enumerate(vna_configs):
                if cmpAudioSamples(fi.audio_samples, vna_config.get(VNA_AUDIO_SAMPLES_VAR, '')):
                    fi.updateFromVNA(vna_config)
                    audio_samples_matched = True
                    vna_config_used_bools[i] = True
                    break
        if audio_samples_matched: continue
        # start matching by volume number, much less reliable
        for i, vna_config in enumerate(vna_configs):
            if (vna_vol_num := vna_config.get(VNA_VOL_VAR, '')) and (m := re.match(OKE_FILESTEM_PATTERN, fi.path.stem)):
                if int(vna_vol_num) == int(m.group('idx1')):
                    fi.updateFromVNA(vna_config)
                    vna_config_used_bools[i] = True
                    break
        logger.warning(f'"{fi.path}" cannot match a VNA config.')
    for vna_config_used_bool, vna_config in zip(vna_config_used_bools, vna_configs):
        if not vna_config_used_bool:
            logger.warning(f'Unused VNA config "{vna_config}".')




def guessVolNumsFromPaths(paths:list[Path], parent:Path|None=None) -> list[str]:
    '''
    If all inputs are from the same directory, it will use `parent` as the common parent instead of the most common prefix.
    '''

    fullnames = [path.as_posix() for path in paths]
    most_common_prefix = Path(os.path.commonprefix(fullnames))

    if all(path.is_relative_to(most_common_prefix) for path in paths): # itself or its parent
        if most_common_prefix.is_file():
            most_common_prefix = most_common_prefix.parent
        # if the input is a list of identical inexisting files, we will fail here
    else: # this means we get a common parent with some filename stems
        most_common_prefix = most_common_prefix.parent

    if parent and not Path(most_common_prefix).is_relative_to(parent):
        parent = None # this means the input parent is invalid

    if parent and len(set(path.parent for path in paths)) == 1:
        most_common_prefix = parent

    rel_paths_strs = [path.parent.relative_to(most_common_prefix).as_posix() for path in paths]
    rel_paths_parts = [rel_path_str.split('/') for rel_path_str in rel_paths_strs]
    rel_paths_depths = [len(rel_path_parts) for rel_path_parts in rel_paths_parts]

    processed_bools = [False] * len(paths)
    assumed_vols : list[str] = [''] * len(paths)

    for filenames in itertools.zip_longest(*rel_paths_parts, fillvalue=''):
        matches = [re.match(VOLUME_NAME_PATTERN, filename) for filename in filenames]
        for i, path, match, processed_bool in zip(itertools.count(), paths, matches, processed_bools):
            if not match or processed_bool:
                continue
            assumed_vols[i] = str(int(match.group('idx'))) # remove prefixed zeros
            processed_bools[i] = True
        if all(processed_bools): break

    return assumed_vols
