import re
import logging
import itertools
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

from .corefile import CF
from utils.mediautils import *
from utils.fileutils import *
from configs.specification import STD_BKS_DIRNAME, STD_CDS_DIRNAME
from configs.user import ENABLE_MULTI_PROC_IF_UNSURE, NUM_IO_JOBS
from configs.runtime import VNx_ALL_EXTS
from configs.debug import DEBUG
from configs.regex import BASIC_CRC32_PATTERN

import ssd_checker


__all__ = [
    'toEnabledList',
    'cmpCfCRC32',
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




def cmpCfCRC32(cfs:CF|list[CF], expects:str|list[str], logger:logging.Logger, pass_not_recorded:bool=False) -> bool:

    if isinstance(cfs, CF): cfs = [cfs]
    if isinstance(expects, str): expects = [expects]

    if not cfs or not expects:
        logger.warning('Missing input for CRC32 comparison.')
        return False

    if len(cfs) != len(expects):
        logger.warning('The input files and expected CRC32s have different length.')

    ok = True
    cf_paths, cf_crc32s = (cf.src for cf in cfs), (cf.crc32 for cf in cfs)
    for cf_path, cf_crc32, exp_crc32 in itertools.zip_longest(cf_paths, cf_crc32s, expects, fillvalue=''):
        if not cf_path:
            logger.info(f'Reaching the end of actual files.')
            return ok #! exit at the end of actual files
        if not cf_crc32:
            logger.error(f'The source file "{cf_path}" used to instantiate CoreFile is missing now.')
            ok = False
            continue
        if not exp_crc32:
            logger.warning(f'No recorded CRC32 to verify "{cf_path}" (0x{cf_crc32}).')
            if not pass_not_recorded: ok = False
            continue
        if not re.match(BASIC_CRC32_PATTERN, exp_crc32):
            logger.error(f'The recorded CRC32 "{exp_crc32}" is malformed.')
            ok = False
            continue
        if cf_crc32.lower() != exp_crc32.lower():
            logger.error(f'Mismatched CRC32 - actual 0x{cf_crc32} but recorded 0x{exp_crc32} for "{cf_path}".')
            ok = False
    return ok




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
