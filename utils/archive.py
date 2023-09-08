import shutil
from pathlib import Path

from langs import *
from configs.time import TIMESTAMP

import pyzipper
import py7zr
import rarfile


__all__ = [
    'isArchive',
    'extract7Z',
    'extractRAR',
    'extractZIP',
    'extractARC',
    'extractWithPwdPrompt',
    'extractMultiple',
    'tstArchive',
    'getFileList',
    ]




def isArchive(path: Path) -> bool:
    if not path.is_file(): return False
    try:
        match path.suffix.lower():
            case '.7z':
                return py7zr.is_7zfile(path)
            case '.rar':
                return rarfile.is_rarfile(path)
            case '.zip':
                return pyzipper.is_zipfile(path)
            case _:
                print(UNSUPPORTED_ARC_TYPE_1.format(path.suffix))
                return False
    except:
        return False




def extract7Z(src_path: Path, dst_dir: Path, password: str|None = None) -> bool:
    if not src_path.is_file(): return False
    if not dst_dir.is_dir(): return False
    if not isArchive(src_path): return False
    try:
        with py7zr.SevenZipFile(src_path) as archive:
            if not archive.needs_password():
                archive.extractall(dst_dir)
                return True
        if not password: return False
        with py7zr.SevenZipFile(src_path, password=password) as archive:
            archive.extractall(dst_dir)
            return True
    except:
        return False




def extractRAR(src_path: Path, dst_dir: Path, password: str|None = None) -> bool:
    if not src_path.is_file(): return False
    if not dst_dir.is_dir(): return False
    if not isArchive(src_path): return False
    try:
        with rarfile.RarFile(src_path, 'r') as archive:
            if archive.needs_password():
                if not password: return False
                archive.setpassword(password)
                archive.extractall(dst_dir, pwd=password)
            else:
                archive.extractall(dst_dir)
            return True
    except Exception as e:
        return False




def _isEncryptedZIP(src_path: Path) -> bool:
    if not src_path.is_file(): return False
    zf = pyzipper.ZipFile(src_path)
    for zinfo in zf.infolist():
        is_encrypted = zinfo.flag_bits & 0x1
        if is_encrypted: return True
    return False




def extractZIP(src_path: Path, dst_dir: Path, password: str|None = None) -> bool:
    if not src_path.is_file(): return False
    if not dst_dir.is_dir(): return False
    if not isArchive(src_path): return False
    need_password = _isEncryptedZIP(src_path)
    try:
        if need_password and not password: return False
        with pyzipper.AESZipFile(src_path, 'r') as archive:
            if need_password and password:
                archive.setpassword(password.encode('utf-8'))
            archive.extractall(dst_dir)
            return True
    except:
        try:
            with pyzipper.ZipFile(src_path, 'r') as archive:
                if need_password and password:
                    archive.setpassword(password.encode('utf-8'))
                archive.extractall(dst_dir)
                return True
        except:
            pass
    return False




def extractARC(src_path: Path, dst_dir: Path, passwords: str|list[str]|None = None) -> bool:

    if not src_path.is_file(): return False
    if not dst_dir.is_dir(): return False
    if not isArchive(src_path): return False
    if passwords == None:
        pwds = [None]
    elif isinstance(passwords, str):
        pwds = [None, passwords]
    else:
        pwds = [None] + passwords

    match src_path.suffix.lower():
        case '.7z':
            decompressor = extract7Z
        case '.rar':
            decompressor = extractRAR
        case '.zip':
            decompressor = extractZIP
        case _:
            return False

    try:
        for pwd in pwds:
            if decompressor(src_path, dst_dir, password=pwd):
                return True
    except:
        return False
    else:
        return False




def extractWithPwdPrompt(src_path: Path, dst_dir: Path, passwords: str|list[str]|None = None) -> str|None:

    if not src_path.is_file(): return None
    if not dst_dir.is_dir(): return None
    if not isArchive(src_path): return None
    if passwords == None:
        pwds = [None]
    elif isinstance(passwords, str):
        pwds = [None, passwords]
    else:
        pwds = [None] + passwords

    match src_path.suffix.lower():
        case '.7z':
            decompressor = extract7Z
        case '.rar':
            decompressor = extractRAR
        case '.zip':
            decompressor = extractZIP
        case _:
            return None

    ok = False
    try:
        for pwd in pwds:
            ok = decompressor(src_path, dst_dir, password=pwd)
            if ok: return pwd if pwd else ''
        while not ok:
            try:
                print(FOUND_PWD_PROTECTED_1.format(src_path))
                password = input(PROMPT_PWD_0)
                ok = decompressor(src_path, dst_dir, password=password)
                if not ok: print(INCORRECT_PWD_1.format(password))
                else: return password
            except KeyboardInterrupt:
                return None
    except:
        return None




def extractMultiple(src_paths: list[Path], dst_parent_dir: Path,
                    passwords: str|list[str]|None = None) -> list[Path|None]:
    '''
    Decompresses a batch of archive files to the given output dir.
    Return each sub output dir if succeeded, otherwise None.
    '''

    if not dst_parent_dir or dst_parent_dir.is_file():
        return [None] * len(src_paths)

    try:
        dst_parent_dir.mkdir(parents=True, exist_ok=True)
        (outdir := dst_parent_dir.joinpath(f'{TIMESTAMP}')).mkdir(parents=True, exist_ok=True)
    except:
        return [None] * len(src_paths)

    ret: list[Path|None] = [None] * len(src_paths)
    for i, src_path in enumerate(src_paths):
        dst_dir = outdir.joinpath(src_path.name)
        try:
            dst_dir.mkdir(parents=True, exist_ok=True)
            if not isArchive(src_path): continue
            if extractARC(src_path, outdir, passwords=passwords):
                ret[i] = dst_dir
        except:
            shutil.rmtree(outdir, ignore_errors=True)
            pass
    return ret




def tstArchive(path: Path) -> bool:
    '''Decompress the files one by one to memory without temporarily saving to disk.'''
    if not path.is_file(): return False
    if not isArchive(path): return False
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
                with pyzipper.ZipFile(path, 'r') as archive:
                    if archive.testzip():
                        return False
            case _:
                return False
    except:  # rarfile.BadRarFile
        return False
    return True




def getFileList(path: Path) -> list[str]:
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
            with pyzipper.ZipFile(path, 'r') as archive:
                return archive.namelist()
        case _:
            return []
