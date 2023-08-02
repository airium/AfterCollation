import logging
from pathlib import Path

from utils.fileinfo import FI
from utils.mediautils import *
from utils.fileutils import *
from configs.specification import STD_BKS_DIRNAME, STD_CDS_DIRNAME


__all__ = ['toEnabledList', 'cmpCRC32FI', 'printCliNotice', 'filterOutCDsScans']




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




def cmpCRC32FI(fileinfos:FI|list[FI], expected_crc32s:str|list[str], logger:logging.Logger):

    if isinstance(fileinfos, FI): fileinfos = [fileinfos]
    if isinstance(expected_crc32s, str): expected_crc32s = [expected_crc32s]

    if len(fileinfos) != len(expected_crc32s):
        logger.error('Input fileinfos and expected CRC32s have different length.')
        return

    for fi, expected_crc32 in zip(fileinfos, expected_crc32s):
        if not expected_crc32:
            logger.warning(f'No CRC32 found in filename "{fi.path}".')
        else:
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
