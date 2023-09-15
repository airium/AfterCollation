import re
import zlib
from pathlib import Path
from functools import partial
from multiprocessing import Pool
from configs.regex import CRC32_IN_FILENAME_REGEX, CRC32_STRICT_REGEX


__all__ = [
    'getFileID',
    'getCRC32',
    'getCRC32List',
    'findCRC32InFilename',
    'findCRC32InFilenames',
    ]




def getFileID(path: str|Path) -> int|str:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'The input "{path}" is not a file.')
    try:
        if inode := path.stat().st_ino:
            return inode
    finally:
        return getCRC32(path)


def getCRC32(path: Path|str, prefix: str = '', read_size: int = 16 * 2**20, pass_not_found: bool = False) -> str:
    '''
    path:Path: the Path to the file

    prefix:str: append to the front of the hash string

    readsize:int: the read size limit in bytes in each CRC32 update
    default is 16 MiB, using <=0 means full read without blocks
    a higher value may reduce the total time consumption as it reduces the IO times
    but when using a multi-processing reader, too large read size may cause OOM

    return:str: the hash string

    typical speed: 500-1500MB/s on NVMe SSD per thread
    '''

    try:
        hash = 0
        with Path(path).open('rb') as fo:
            while (b := fo.read(read_size)):
                hash = zlib.crc32(b, hash)
        return f'{prefix}{hash:08x}'
    except FileNotFoundError as e:
        if pass_not_found: return ''
        raise e
    except Exception as e:
        raise e




def getCRC32List(paths: list[Path], mp: int = 1, prefix: str = '', read_size: int = 16 * 2**20) -> list[str]:
    mp = int(mp)
    if mp > 1:
        crc32s = list(Pool().map(partial(getCRC32, prefix=prefix, read_size=read_size), paths))
    else:
        crc32s = list(map(partial(getCRC32, prefix=prefix, read_size=read_size), paths))
    return crc32s




def findCRC32InFilename(inp: str|Path) -> str:
    name = inp.name if isinstance(inp, Path) else inp
    if m := re.findall(CRC32_IN_FILENAME_REGEX, name):
        return m[-1]
    return ''




def findCRC32InFilenames(inp: list[Path]|list[str]) -> list[str]:
    return [findCRC32InFilename(p) for p in inp]




def cmpCRC32(*, actuals: str|list[str], expects: str|list[str]) -> bool|list[bool]:

    is_str = False
    if isinstance(actuals, str):
        actuals = [actuals]
        is_str = True
    if isinstance(expects, str):
        expects = [expects]
        is_str = True
    if len(actuals) != len(expects):
        raise ValueError('The actual and expected CRC32s have different length.')

    ret: list[bool] = []
    for (actual, expects) in zip(actuals, expects):
        if not actual or not re.match(CRC32_STRICT_REGEX, actual):
            ret.append(False)
        elif not expects or not re.match(CRC32_STRICT_REGEX, expects):
            ret.append(False)
        else:
            ret.append(actual.lower() == expects.lower())
    return ret[0] if is_str else ret
