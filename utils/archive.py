import time
import shutil
import zipfile
from pathlib import Path

from configs.user import TEMP_DIR_DECOMPRESS
from configs.time import TIMESTAMP

import py7zr
import rarfile


__all__ = [
    'decompressArchives',
    'tstDecompressArchive',
    'getArchiveFilelist',
    ]




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




def tstDecompressArchive(path:Path) -> bool:
    '''Decompress the files one by one to memory without temporarily saving to disk.'''
    if not path.is_file(): return False
    try:
        match path.suffix.lower():
            case '.7z':
                with py7zr.SevenZipFile(path, 'r') as archive:
                    if archive.testzip():
                        return False
            case '.rar':
                with rarfile.RarFile(path, 'r') as archive:
                    archive.testrar()
            case '.zip':
                with zipfile.ZipFile(path, 'r') as archive:
                    if archive.testzip():
                        return False
            case _:
                return False
    except: # rarfile.BadRarFile
        return False
    return True




def getArchiveFilelist(path:Path) -> list[str]:
    '''Return the file list inside the given archive file.'''
    if not path.is_file(): return []
    match path.suffix.lower():
        case '.7z':
            with py7zr.SevenZipFile(path, 'r') as archive:
                return archive.getnames()
        case '.rar':
            with rarfile.RarFile(path, 'r') as archive:
                return archive.namelist()
        case '.zip':
            with zipfile.ZipFile(path, 'r') as archive:
                return archive.namelist()
        case _:
            return []
