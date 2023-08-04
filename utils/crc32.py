
import re
import zlib
from pathlib import Path
from functools import partial
from multiprocessing import Pool

from configs.regex import CRC32_IN_FILENAME_PATTERN


__all__ = ['getCRC32', 'getCRC32List', 'findCRC32InFilename', 'findCRC32InFilenames']




def getCRC32(path:Path|str, prefix:str='', read_size:int=16*2**20) -> str:
    '''
    path:Path: the Path to the file

    prefix:str: append to the front of the hash string

    readsize:int: the read size limit in bytes in each CRC32 update
    default is 16 MiB, using <=0 means full read without blocks
    a higher value may reduce the total time consumption as it reduces the IO times
    but when using a multi-processing reader, too large read size may cause OOM

    return:str: the hash string

    typical speed: 500-1000MB/s on NVMe SSD
    '''
    hash = 0
    with Path(path).open('rb') as fo:
        while (b := fo.read(read_size)):
            hash = zlib.crc32(b, hash)
    return f'{prefix}{hash:08x}'




def getCRC32List(paths:list[Path], mp:int=1, prefix:str='', read_size:int=16*2**20) -> list[str]:
    mp = int(mp)
    if mp > 1:
        crc32s = list(Pool().map(partial(getCRC32, prefix=prefix, read_size=read_size), paths))
    else:
        crc32s = list(map(partial(getCRC32, prefix=prefix, read_size=read_size), paths))
    return crc32s




def findCRC32InFilename(inp:str|Path) -> str:
    name = inp.name if isinstance(inp, Path) else inp
    if m := re.findall(CRC32_IN_FILENAME_PATTERN, name):
        return m[-1]
    return ''




def findCRC32InFilenames(inp:list[Path]|list[str]) -> list[str]:
    return [findCRC32InFilename(p) for p in inp]



# def cmpCRC32(paths:list[Path], actual_crc32s:list[str], logger:logging.Logger):
#     for (path, actual_crc32) in zip(paths, actual_crc32s):
#         if matches := re.findall(BASIC_CRC32_PATTERN, path.as_posix()):
#             # NOTE using the last found crc32, which should be the correct one
#             assumed_crc32_in_filename = matches[-1]
#             if actual_crc32.lower() != assumed_crc32_in_filename.lower():
#                 logger.error(f'CRC32 mismatched (actual 0x{actual_crc32} ≠ 0x{assumed_crc32_in_filename} in "{path}".')
#         else:
#             logger.warning(f'CRC32 not found in "{path}".')
