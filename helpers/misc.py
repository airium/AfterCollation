import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

from .corefile import CF
from utils.mediautils import *
from utils.fileutils import *
from configs.specification import STD_BKS_DIRNAME, STD_CDS_DIRNAME
from configs.user import ENABLE_MULTI_PROC_IF_UNSURE, NUM_IO_JOBS
from configs.runtime import VNx_ALL_EXTS
from configs.debug import DEBUG

import ssd_checker


__all__ = [
    'toEnabledList',
    'cmpCRC32VND',
    'cmpCRC32VNE',
    'printCliNotice',
    'filterOutCDsScans',
    'isSSD',
    'getCRC32MultiProc',
    'listVNxFilePaths',
    ]




def toEnabledList(values:list[str]|tuple[str]) -> list[bool]:
    '''
    all None = enable all
    partial yes = enable these yes
    partial no = enable remaining
    yes and no both exists = only enable these yes (excluding these None)
    '''
    ret = []
    for v in values:
        if v == '':
            ret.append(None)
        elif v.lower() in ('n', 'no', 'not', 'negative', 'f', 'false', '0'):
            ret.append(False)
        else:
            ret.append(True)
    if all(r is None for r in ret):
        return [True] * len(ret)
    elif any(r is True for r in ret):
        return [(False if r is None else True) for r in ret]
    else:
        return [(True if r is None else False) for r in ret]




def cmpCRC32VND(fis:CF|list[CF], expected_crc32s:str|list[str], logger:logging.Logger):

    if isinstance(fis, CF): fis = [fis]
    if isinstance(expected_crc32s, str): expected_crc32s = [expected_crc32s]

    if len(fis) != len(expected_crc32s):
        logger.error('The input files and expected CRC32s have different length.')

    # do a shortest loop, though the length mismatches
    for fi, expected_crc32 in zip(fis, expected_crc32s):
        if not expected_crc32:
            logger.warning(f'No CRC32 found in filename "{fi.path}".')
            continue
        if fi.crc32.lower() != expected_crc32.lower():
            logger.error(f'CRC32 mismatches, actual 0x{fi.crc32} ≠ 0x{expected_crc32} for "{fi.path}".')




def cmpCRC32VNE(fis:CF|list[CF], expected_crc32s:str|list[str], logger:logging.Logger):

    if isinstance(fis, CF): fis = [fis]
    if isinstance(expected_crc32s, str): expected_crc32s = [expected_crc32s]

    if len(fis) != len(expected_crc32s):
        logger.error('The input files and expected CRC32s have different length.')

    # do a shortest loop, though the length mismatches
    for fi, expected_crc32 in zip(fis, expected_crc32s):
        if not expected_crc32:
            logger.warning(f'No CRC32 recorded for "{fi.path}".')
            continue
        if fi.crc32.lower() != expected_crc32.lower():
            logger.error(f'CRC32 mismatches, actual 0x{fi.crc32} ≠ 0x{expected_crc32} for "{fi.path}".')




def printCliNotice(usage_txt:str, paths:list|tuple):
        print(usage_txt)
        print()
        print('Please check your input:')
        for i, path in enumerate(paths):
            print(f'{i+1:03d}: "{path}"')




def filterOutCDsScans(inp:list[Path]):
    ret = []
    for p in inp:
        if any(part in (STD_BKS_DIRNAME, STD_CDS_DIRNAME) for part in p.as_posix().split('/')):
            continue
        else:
            ret.append(p)
    return ret




def isSSD(path:Path, logger:logging.Logger|None=None) -> bool:
    try:
        ret = ssd_checker.is_ssd(path.resolve().as_posix())
        if logger: logger.debug(f'Found SSD "{path}"' if ret else f'Found HDD "{path}"')
        return ret
    except KeyError:
        if logger: logger.debug(f'KeyError when checking "{path}".')
        # this happens when the input path is an SCSI device which is not listed as system physical drives
        return ENABLE_MULTI_PROC_IF_UNSURE
    except Exception as e:
        if logger: logger.debug(f'Unknown error {e} when checking "{path}".')
        return ENABLE_MULTI_PROC_IF_UNSURE




def getCRC32MultiProc(paths:Path|list[Path], logger:logging.Logger|None=None) -> int:
    if isinstance(paths, Path): paths = [paths]
    futures = []
    with ProcessPoolExecutor(NUM_IO_JOBS) as exe:
        for path in paths:
            futures.append(exe.submit(isSSD, path, logger=logger))
    is_ssd_list = [f.result() for f in futures]
    if logger: logger.debug(f'CRC32 MultiProc gets {sum(is_ssd_list)}/{len(is_ssd_list)} paths on SSDs.')
    if all(is_ssd_list):
        return NUM_IO_JOBS
    else:
        return 1



def listVNxFilePaths(path:Path, logger:logging.Logger) -> list[Path]:

    logger.info(f'Locating all required media files ...')

    all_files = filterOutCDsScans(listFile(path))
    vnx_files = filterOutCDsScans(listFile(path, ext=VNx_ALL_EXTS))
    if (diffs := set(all_files).difference(set(vnx_files))):
        for diff in diffs:
            logger.error(f'Disallowed file "{diff}".')

    if DEBUG:
        for file in vnx_files:
            logger.debug(f'Got: "{file}"')

    return vnx_files
