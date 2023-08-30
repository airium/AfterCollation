import logging
import itertools
from pathlib import Path

from utils import *
from configs import *
from checkers import *
from helpers.corefile import CF


__all__ = ['readCSV4VNR', 'writeCSV4VNR', 'doComparison']




def readCSV4VNR(input_path:Path) -> tuple[bool, dict[str, list[tuple[str, str, str]]]]:

    if not input_path or not (input_path := Path(input_path)).is_file():
        return False, {}

    # vnr_csv_dicts : list[dict[str, str]]
    success, vnr_csv_dicts = readCSV(input_path)
    if not success:
        return False, {}
    vnr_csv_dicts = unquotFields4CSV(vnr_csv_dicts)

    grouping_dicts : dict[str, list[tuple[str, str, str]]] = {}

    for vnr_csv_dict in vnr_csv_dicts:
        k = vnr_csv_dict[VNR_GRP_IDX_CN]
        if k in grouping_dicts.keys():
            grouping_dicts[k].append(
                (vnr_csv_dict[VNR_SUBGRP_IDX_CN],
                 vnr_csv_dict[ENABLE_CN],
                 vnr_csv_dict[FULLPATH_CN]))
        else:
            grouping_dicts[k] = [
                (vnr_csv_dict[VNR_SUBGRP_IDX_CN],
                 vnr_csv_dict[ENABLE_CN],
                 vnr_csv_dict[FULLPATH_CN])]

    return True, grouping_dicts




def writeCSV4VNR(ouput_path:Path, grouping_dict:dict[str, list[tuple[str, str, str]]]) -> bool:

    if not ouput_path or (output_path := Path(ouput_path)).exists():
        return False

    vnr_csv_dicts : list[dict] = []
    for group_idx, group_list in grouping_dict.items():
        for group in group_list:
            vnr_csv_dict = dict(zip(VNR_ALL_DICT.keys(), (group_idx, *group)))
            vnr_csv_dicts.append(vnr_csv_dict)

    return writeCSV(output_path, quotFields4CSV(vnr_csv_dicts))




def doComparison(*groups:list[Path], grpname:str='0', subgrps_names:list[str]=[], logger:logging.Logger):

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

        g1 = [CF(f) for f in g1]
        g2 = [CF(f) for f in g2]

        if any(cf.has_video for cf in g1+g2):
            logger.info('Comparing video...')
            cmpVideoContent(g1, g2, logger)

        if any(cf.has_audio for cf in g1+g2):
            logger.info('Comparing audio...')
            diff_audios = cmpAudioContent(g1, g2, logger)
            for k, diff_audio, freq in diff_audios:
                img_path = findCommonParentDir(*[cf.path for cf in g1+g2])
                if not img_path:
                    print('!!! Cannot find a common parent dir of your input. '
                        'The spectrogram of audio difference will be written under the same dir as this script.')
                    img_path = Path(__file__).parent
                img_path = img_path.joinpath(f'VNR-{TIMESTAMP}-DiffAudio-{grpname if grpname else 0}-{n1}vs{n2}-a{k}.log')
                if mkSpectrogram(img_path, diff_audio, freq):
                    logger.info(f'Successfully written spectrogram to "{img_path}".')
                else:
                    logger.error(f'Failed to write spectrogram to "{img_path}".')

        if any(cf.has_menu for cf in g1+g2):
            logger.info('Comparing menu...')
            cmpMenuContent(g1, g2, logger)

        if any(cf.has_image for cf in g1+g2):
            logger.info('Comparing menu...')
            cmpImageContent(g1, g2, logger)

        if any(cf.has_text for cf in g1+g2):
            logger.info('Comparing text...')
            cmpTextContent(g1, g2, logger)

        # cmpNaming(g1, g2, logger)
