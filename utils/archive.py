import time
import shutil
import zipfile
from pathlib import Path

from configs.user import TEMP_DIR_DECOMPRESS
from configs.time import TIMESTAMP
from utils.environment import addPath

import py7zr
import rarfile

addPath()


__all__ = [ 'decompressArchives', 'tstDecompressArchives']




def decompressArchives(*paths:Path, out:Path|None=TEMP_DIR_DECOMPRESS) -> Path|None:
    '''
    Decompresses the given archive files to the given output dir.
    Return the output dir if succeeded, otherwise None.
    '''

    if not out or out.is_file():
        return None

    try:
        out.mkdir(parents=True, exist_ok=True)
        (outdir := out.joinpath(f'{TIMESTAMP}')).mkdir(parents=True, exist_ok=True)
    except:
        return None

    try:
        for i, path in enumerate(paths):
            if path.suffix.lower() == '.7z':
                with py7zr.SevenZipFile(path, 'r') as archive:
                    archive.extractall(outdir.joinpath(str(i)))
            elif path.suffix.lower() == '.rar':
                with rarfile.RarFile(path, 'r') as archive:
                    archive.extractall(outdir.joinpath(str(i)))
            elif path.suffix.lower() == '.zip':
                with zipfile.ZipFile(path, 'r') as archive:
                    archive.extractall(outdir.joinpath(str(i)))
            else:
                raise ValueError
        return outdir
    except Exception as e:
        try:
            if outdir.is_dir():
                time.sleep(1) # pause 1 second hoping IO lock to be released
                shutil.rmtree(outdir)
        except:
            pass
        return None




def tstDecompressArchives(*paths:Path, out:Path|None=TEMP_DIR_DECOMPRESS) -> bool:

    ret = decompressArchives(*paths, out=out)
    if ret is None:
        return False
    else:
        try:
            time.sleep(1)
            shutil.rmtree(ret)
        except:
            pass
        return True
