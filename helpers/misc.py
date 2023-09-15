from __future__ import annotations

import os
import re
import shutil
import itertools
from pathlib import Path
from logging import Logger
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Optional, Iterable
import traceback
import contextlib

import helpers.corefile as hcf
from langs import *
from configs import *
from utils import *

import ssd_checker


__all__ = [
    'wrapTrackBack',
    'toEnabledList',
    'cmpCRC4CoreFiles',
    'printUsage',
    'printCheckerEnding',
    'filterOutCDsScans',
    'isSSD',
    'getCRC32MultiProc',
    'filterVxFilePaths',
    'guessVolNumsFromPaths',
    'handleResourceSrc',
    ]




def wrapTrackBack(func: Callable[[list[Path]], None], args: list[str]):
    try:
        func([Path(p) for p in args])
    except:
        traceback.print_exc()
        print(RUN_INTO_ERROR_0)
    input(ENTER_TO_EXIT_0)




def toEnabledList(values: Iterable[str]) -> list[bool]:
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




def cmpCRC4CoreFiles(
    cfs: Iterable[hcf.CF],
    expected_crc32s: Iterable[str],
    logger: Optional[Logger] = None,
    pass_not_recorded: bool = False
    ) -> bool:

    cfs = list(cfs)
    expected_crc32s = list(expected_crc32s)

    if not cfs or not expected_crc32s:
        if logger: logger.error(CRC32_MISSING_INPUT_0)
        return False

    if len(cfs) != len(expected_crc32s):
        if logger: logger.warning(CRC32_INPUT_LEN_MISMATCH_0)
        #! but we still accept such input and continue

    ok = True
    cf_paths, cf_crc32s = (cf.src for cf in cfs), (cf.crc32 for cf in cfs)
    for cf_path, cf_crc32, exp_crc32 in itertools.zip_longest(cf_paths, cf_crc32s, expected_crc32s, fillvalue=''):
        if not cf_path:
            if logger: logger.info(CRC32_REACHING_END_0)
            return ok  #! exit at the end of actual files
        if not cf_crc32:
            if logger: logger.error(CRC32_CF_MISSING_SRC_1.format(cf_path))
            ok = False
            continue
        if not exp_crc32:
            if logger: logger.warning(CRC32_NO_RECORD_2.format(cf_path, cf_crc32))
            if not pass_not_recorded: ok = False
            continue
        if not re.match(CRC32_STRICT_REGEX, exp_crc32):
            if logger: logger.error(CRC32_MALFORMED_RECORD_1.format(exp_crc32))
            ok = False
            continue
        if cf_crc32.lower() != exp_crc32.lower():
            if logger: logger.error(CRC32_MISMATCHED_3.format(cf_crc32, exp_crc32,cf_path))
            ok = False
    return ok




def printUsage(usage_txt: str, input_paths: list|tuple):
    print(usage_txt)
    print()
    print(PLZ_CHK_YOUR_INPUT_0)
    w = len(str(len(input_paths)))
    for i, path in enumerate(input_paths, start=1):
        print(f'{i:0>{w}}: "{path}"')




def printCheckerEnding(log_path: str|Path, logger: Optional[Logger] = None):
    log_path = Path(log_path).as_posix()
    printer = logger.info if logger else print
    printer(CHECKER_COMMON_ENDING_1.format(log_path))




def filterOutCDsScans(src_paths: list[Path]):
    '''Remove paths that are inside a CD or Scans dir.'''
    std_cds_dirname = STD_CDS_DIRNAME.lower()
    std_bks_dirname = STD_BKS_DIRNAME.lower()
    ret = []
    for src_path in src_paths:
        for part in src_path.parts:
            if part.lower() in std_cds_dirname:
                break
            if part.lower() in std_bks_dirname:
                break
        else:
            ret.append(src_path)
    return ret




def isSSD(path: Path, logger: Logger|None = None) -> bool:
    try:
        ret = ssd_checker.is_ssd(path.resolve().as_posix())
        if logger: logger.debug(FOUND_SSD_1.format(path) if ret else FOUND_HDD_1.format(path))
        return ret
    except KeyError:
        if logger: logger.debug(SSD_CHECKER_KEY_ERROR_1.format(path))
        # this happens when the input path is an SCSI device which is not listed as system physical drives
        return ENABLE_MULTI_PROC_IF_UNSURE
    except Exception as e:
        if logger: logger.debug(SSD_CHECKER_UNK_ERROR_2.format(e, path))
        return ENABLE_MULTI_PROC_IF_UNSURE




def getCRC32MultiProc(paths: Path|list[Path], logger: Logger|None = None) -> int:
    if isinstance(paths, Path): paths = [paths]
    futures = []
    with ProcessPoolExecutor(NUM_IO_JOBS) as exe:
        for path in paths:
            futures.append(exe.submit(isSSD, path, logger=logger))
    is_ssd_list = [f.result() for f in futures]
    if logger: logger.debug(CRC32_MP_GOT_N_OF_N_ON_SSD_2.format(sum(is_ssd_list), len(is_ssd_list)))
    if all(is_ssd_list):
        return NUM_IO_JOBS
    else:
        return 1




def filterVxFilePaths(src_path: Path, logger: Optional[Logger] = None) -> list[Path]:

    if logger: logger.info(VP_LOCATING_0)

    all_paths = filterOutCDsScans(listFile(src_path))
    vx_paths = filterOutCDsScans(listFile(src_path, ext=VX_ALL_EXTS))
    for path in (diffs := set(all_paths).difference(vx_paths)):
        if logger: logger.info(DISALLOWED_FILE_1.format(path))

    if DEBUG:
        for path in vx_paths:
            if logger: logger.debug(GOT_1.format(path))

    return vx_paths




def guessVolNumsFromPaths(paths: list[Path], parent: Optional[Path] = None,
                            logger: Optional[Logger] = None) -> list[str]:
    '''
    If all inputs are from the same dir, it will first use `parent` as the common parent instead of the most common prefix.
    This prevents
    '''

    fullnames = [path.as_posix() for path in paths]
    most_common_prefix = Path(os.path.commonprefix(fullnames))

    if all(path.is_relative_to(most_common_prefix) for path in paths):  # itself or its parent
        if most_common_prefix.is_file():
            most_common_prefix = most_common_prefix.parent
        # if the input is a list of identical inexisting files, we will fail here
    else:  # this means we get a common parent with some filename stems
        most_common_prefix = most_common_prefix.parent

    if parent and not Path(most_common_prefix).is_relative_to(parent):
        parent = None  # this means the input parent is invalid

    if parent and len(set(path.parent for path in paths)) == 1:
        most_common_prefix = parent

    rel_paths_strs = [path.parent.relative_to(most_common_prefix).as_posix() for path in paths]
    rel_paths_parts = [rel_path_str.split('/') for rel_path_str in rel_paths_strs]
    rel_paths_depths = [len(rel_path_parts) for rel_path_parts in rel_paths_parts]

    if logger:
        if len(set(rel_paths_depths)) != 1:
            logger.warning(INACCURETE_VOL_NUM_GUESS_1)

    is_processeds = [False] * len(paths)
    assumed_vols: list[str] = [''] * len(paths)

    for filenames in itertools.zip_longest(*rel_paths_parts, fillvalue=''):
        matches = [re.match(BDMV_DIRNAME_REGEX, filename) for filename in filenames]
        for i, path, match, processed_bool in zip(itertools.count(), paths, matches, is_processeds):
            if not match or processed_bool:
                continue
            assumed_vols[i] = str(int(match.group('idx')))  # remove prefixed zeros
            is_processeds[i] = True
        if all(is_processeds): break

    return assumed_vols




def handleResourceSrc(src: Path, tmp: Path, logger: Optional[Logger] = None) -> Path|None:
    '''
    Check the availability of `src` dir and return it.
    Decompress `src` to `tmp` if it is an archive file, and return `tmp`.
    '''
    if src.resolve().as_posix().lower() == tmp.resolve().as_posix().lower():
        if logger: logger.error(CANT_EXTRACT_TO_SRC_1.format(src))
        return

    # TODO: can we decompress archives inside the archive?
    if src.is_file():
        if src.suffix.lower().endswith(AD_ARC_EXTS):
            if logger: logger.info(DECOMPRESSING_2.format(src, tmp))
            try:
                assert not tmp.is_file()
                tmp.mkdir(parents=True, exist_ok=True)
                if extractArcWithPwdPrompt(src, tmp) != None:
                    return tmp
            except:
                if logger: logger.error(DECOMPRESS_FAILED_2.format(src, tmp))
                shutil.rmtree(tmp, ignore_errors=True)
                return
        else:
            if logger: logger.error(GOT_UNSUPP_INPUT_1.format(src))
            return
    elif src.is_dir():
        return src
    else:
        if logger: logger.error(CANT_LOCATE_DIR_1.format(src))
        return
