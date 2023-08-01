import json
import logging
from pathlib import Path

from configs import *
from utils import *

import yaml



__all__ = ['readConf4VNA', 'loadVNAInfo', 'fillFieldsFromVNA']




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
                succ, data_dicts = readCSV(vna_file)
                data_dicts = unquotEntries4CSV(data_dicts)
                if not succ: raise Exception
            case '.yaml':
                with vna_file.open('r', encoding='utf-8-sig') as fo:
                    data_dicts = yaml.safe_load(fo)
            case '.json':
                data_dicts = json.loads(vna_file.read_text(encoding='utf-8-sig'))
            case _:
                raise ValueError
        assert isinstance(data_dicts, list) and all(isinstance(d, dict) for d in data_dicts)
    except:
        logger.error(f'Failed to read the pre-encoding instruction from VNA output "{vna_file}".')
        return {}, []

    try:
        base : dict[str, str]= {}
        configs : list[dict[str, str]] = []
        for data_dict in data_dicts:
            is_base_dict = False
            for k, v in data_dict.items():
                if v == BASE_LINE_LABEL:
                    is_base_dict = True
                    for kk, vv in VNA_BASE_LINE_EDITABLE_DICT.items():
                        base[vv] = data_dict.get(kk, '')
                    break
            if is_base_dict: continue
            conf = {}
            # NOTE we read all keys from the csv (VNA_ALL_FIELDS_DICT)
            # but later we only fill `VNA_FIELDS_DICT_FOR_VND` to FI
            # so it won't matter
            for k, v in VNA_ALL_FIELDS_DICT.items():
                conf[v] = data_dict.get(k, '')
            configs.append(conf)
    except:
        logger.error(f'Failed to pick data from the pre-encoding instruction from VNA output "{vna_file}".')
        return {}, []

    logger.info(f'Successfully read the pre-encoding instruction from VNA output "{vna_file}".')
    return base, configs




def fillFieldsFromVNA(fileinfos:list[FI], vna_configs:list[dict], logger:logging.Logger):

    if not vna_configs: return

    guessed_vol_nums = guessVolNumByPath([fi.path for fi in fileinfos])

    vna_config_used_bools = [False] * len(vna_configs)
    for fi, guessed_vol_num in zip(fileinfos, guessed_vol_nums):
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
