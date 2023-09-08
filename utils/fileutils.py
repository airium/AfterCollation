import os
import re
import csv
import json
import random
import shutil
import platform
import itertools
from typing import Optional, Iterable
from .crc32 import getCRC32

from pathlib import Path
from configs import *

import yaml


__all__ = [
    'listFile',
    'listDir',
    'tstFileEncoding',
    'tstMkHardlink',
    'tstMkHardlinks',
    'tstMkHardlinkInDir',
    'tryHardlinkThenCopy',
    'tryHardlink',
    'tryMkDir',
    'tryCopy',
    'writeCSV',
    'readCSV',
    'findCommonParentDir',
    'listM2TS2CSV',
    'listM2TS2YAML',
    'listM2TS2JSON',
    'getTempDir4Hardlink',
    'condenseDirLayout',
    'getFileID',
    ]




def listFile(
    *paths, ext: Optional[str|Iterable[str]] = None, rglob: bool = True, reduce: bool = True, sort: bool = True
    ) -> list[Path]:
    paths = [Path(Path(p).as_posix()) for p in paths]
    ret: list[Path] = []
    for p in paths:
        if p.is_file():
            ret.append(p)
            continue
        if p.is_dir():
            ret += [f for f in p.rglob('*') if f.is_file()] if rglob else [f for f in p.glob('*') if f.is_file()]
    if ext:
        exts = (ext, ) if isinstance(ext, str) else tuple(ext)
        ret = [p for p in ret if p.suffix.lower().endswith(exts)]
    if reduce:
        ret = list(set(ret))
    if sort:
        ret = sorted(ret)
    return ret




def listDir(*inp_paths, rglob: bool = True, reduce: bool = True, sort: bool = True) -> list[Path]:
    inp_paths = list(Path(Path(p).as_posix()) for p in inp_paths)
    ret: list[Path] = []
    for p in inp_paths:
        if p.is_dir():
            ret += [p] + [f for f in p.rglob('*') if f.is_dir()] if rglob else [f for f in p.glob('*') if f.is_dir()]
    if reduce:
        ret = list(set(ret))
    if sort:
        ret = sorted(ret)
    return ret




def tstFileEncoding(path: Path, encoding: str = 'utf-8-sig') -> bool:
    '''Test if the given encoding can decode the path file without any problem.'''

    # TODO integrate with chardet to achieve a better result?

    try:
        path = Path(path)
        assert path.is_file()
        raw_data = path.read_bytes()
        match encoding.lower():
            case 'utf-8-sig'|'utf_8_sig':
                assert raw_data[:3] == b'\xef\xbb\xbf'
            case 'utf-16-le'|'utf_16_le':
                assert raw_data[:2] == b'\xff\xfe'
            case 'utf-16-be'|'utf_16_be':
                assert raw_data[:2] == b'\xfe\xff'
        path.read_text(encoding=encoding, errors='strict')
    except AssertionError:
        return False
    except UnicodeError:
        return False
    return True




def writeCSV(csv_path: Path, data: list[dict], encoding: str = 'utf-8-sig', newline: str = os.linesep) -> bool:

    try:
        csv_path = Path(csv_path)
        assert csv_path.suffix.lower() == '.csv'
        assert len(data) > 0 and all(isinstance(d, dict) for d in data)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_head = data[0].keys()
        with csv_path.open('w', encoding=encoding, newline='') as fo:
            w = csv.DictWriter(fo, csv_head, lineterminator=newline, delimiter=',')
            w.writeheader()
            w.writerows(data)
    except:
        return False
    return True




def readCSV(csv_path: Path, encoding: str = 'utf-8-sig', newline: str = os.linesep) -> tuple[bool, list[dict]]:

    if not (csv_path := Path(csv_path)).is_file():
        return False, []

    try:
        with csv_path.open('r', encoding=encoding, newline=newline) as fo:
            reader = csv.DictReader(fo)
            data = [info for info in reader]
    except:
        return False, []
    return True, data




def findCommonParentDir(*paths: str|Path) -> Path|None:

    ps = [Path(p).resolve() for p in paths]

    # NOTE this function may have a bug if some inputs are not existing
    assert all(p.exists() for p in ps), 'Some input paths do not exist.'

    if len(ps) == 1 and ps[0].is_file():
        return ps[0].parent
    if len(ps) == 1 and ps[0].is_dir():
        return ps[0]

    fullpaths = [p.as_posix() for p in ps]
    common_prefix = os.path.commonprefix(fullpaths)
    if not common_prefix:
        return None
    common_prefix = Path(common_prefix)
    if common_prefix.is_dir():
        return common_prefix
    return common_prefix.parent




# dont change the function name
def listM2TS2CSV(out_file, output_list):
    try:
        with open(out_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_list[0].keys())
            writer.writeheader()
            writer.writerows(output_list)
        return True
    except:
        return False




# dont change the function name
def listM2TS2YAML(out_file, output_list):
    try:
        with open(out_file, 'w', encoding='utf-8-sig') as f:
            yaml.safe_dump(output_list, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True
    except:
        return False




# dont change the function name
def listM2TS2JSON(out_file, output_list) -> bool:
    try:
        with open(out_file, 'w', encoding='utf-8-sig') as f:
            json.dump(output_list, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False




def tryMkDir(path: str|Path) -> bool:
    path = Path(path)
    if path.is_file():
        return False
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except:
        return False




def tryCopy(src: str|Path, dst: str|Path) -> bool:
    src = Path(src)
    dst = Path(dst)
    remove_dst = not dst.is_file()

    if not src.is_file():
        raise FileNotFoundError(f'The source location "{src}" does not exist.')
    if dst.is_file():
        raise FileExistsError(f'The target location "{dst}" already exists as a file.')
    if dst.is_dir():
        raise IsADirectoryError(f'The target location "{dst}" already exists as a dir.')

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except:
        if remove_dst: dst.unlink(missing_ok=True)
        return False




def getFileID(path: str|Path) -> int|str:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'The input "{path}" is not a file.')
    try:
        if inode := path.stat().st_ino:
            return inode
    finally:
        return getCRC32(path)




def tryHardlinkThenCopy(src: str|Path, dst: str|Path) -> bool:
    src = Path(src)
    dst = Path(dst)
    remove_dst = not dst.is_file()

    if not src.is_file():
        raise FileNotFoundError(f'The source location "{src}" does not exist.')
    if dst.is_file():
        raise FileExistsError(f'The target location "{dst}" already exists as a file.')
    if dst.is_dir():
        raise IsADirectoryError(f'The target location "{dst}" already exists as a dir.')

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not tryHardlink(src, dst):
            shutil.copy2(src, dst)
        return True
    except:
        if remove_dst: dst.unlink(missing_ok=True)
        return False




def tryHardlink(existing: str|Path, proposed: str|Path) -> bool:
    '''Similar to `tstMkHardlink` but will keep the artifacts.'''

    existing = Path(existing)
    proposed = Path(proposed)

    if not existing.is_file():
        raise FileNotFoundError(f'The source location "{existing}" does not exist.')
    if proposed.is_file():
        raise FileExistsError(f'The target location "{proposed}" already exists as a file.')
    if proposed.is_dir():
        raise IsADirectoryError(f'The target location "{proposed}" already exists as a dir.')

    try:
        proposed.parent.mkdir(parents=True, exist_ok=True)
        proposed.hardlink_to(existing)
        return True
    except:
        proposed.unlink(missing_ok=True)
        return False




def tstMkHardlink(existing: str|Path, proposed: str|Path) -> bool:
    '''
    Test if we can proposed.hardlink_to(existing) successfully.
    if proposed is a dir, it will try hardlink to a randomly created file under it.
    '''

    if not (existing := Path(existing)).is_file():
        # NOTE raise Error instead of returning False
        # input not a file means the user is unconscious, warn it
        raise FileNotFoundError

    if (proposed := Path(proposed)).is_file():
        return False

    try:
        if proposed.is_dir():
            # randomly sample a un-suffixed number as the filename
            # hopefully there is no such file in the dir
            for _ in range(10):
                proposed = proposed.joinpath(str(random.sample(range(999999), 1)[0]))
                if not proposed.exists():
                    proposed.hardlink_to(existing)
                    proposed.unlink()
                    return True
            return False
        else:
            proposed.parent.mkdir(parents=True, exist_ok=True)
            proposed.hardlink_to(existing)
            proposed.unlink()
            return True
    except:
        # since we already return False if the file exists
        # this means the file is created by us
        if proposed.is_file(): proposed.unlink(missing_ok=True)
        return False




def tstMkHardlinks(existings: list[Path], proposed: Path, use_st_dev: bool = True) -> bool:
    src_dev = None
    for existing in existings:
        if not existing.is_file():
            raise FileNotFoundError
        if use_st_dev and (new_src_dev := existing.stat().st_dev) != src_dev:
            src_dev = new_src_dev
            if not tstMkHardlink(existing, proposed):
                return False
        else:
            if not tstMkHardlink(existing, proposed):
                return False
    return True




def tstMkHardlinkInDir(dir_path: str|Path) -> bool:
    '''
    This function test if the file system supports hardlink with touching it.
    '''

    dir_path = Path(dir_path)
    # NOTE this is because we are lazy to check at which level the input's parent exists
    # i.e. if we makedir(parents=True), we also need to later rmdir() all the tree we created
    if not dir_path.is_dir():
        raise NotADirectoryError

    f1: Path|None = None
    f2: Path|None = None
    try:
        for _ in range(10):  # do 10 attempts, seems enough?
            k1, k2 = random.sample(range(999999), 2)
            f1 = dir_path.joinpath(f'{k1:6d}')
            f2 = dir_path.joinpath(f'{k2:6d}')
            if f1.exists() or f2.exists():
                continue
            else:
                f1.touch()
                f2.hardlink_to(f1)
                f2.unlink()
                f1.unlink()
                return True
        return False
    except Exception:
        if f1 and f1.exists(): f1.unlink(missing_ok=True)
        if f2 and f2.exists(): f2.unlink(missing_ok=True)
        return False




def getTempDir4Hardlink(input_path: Path|None = None) -> Path|None:
    '''
    Return a default config dir which *should* be usable to hardlink from files in `input_path`.
    Note that the function will create the dir if success.
    Return None if failed.

    If you propose to use a specific dir, use `tstHardlink` to test it.
    '''

    if not input_path: return None
    input_path = input_path.resolve()

    proposed: Path|None = None
    try:
        match platform.system():
            case 'Windows':
                # NOTE Windows also has relative mount point
                proposed = Path(input_path.anchor).joinpath(TEMP_DIR_HARDLINK)
                proposed.mkdir(parents=True, exist_ok=True)
                if proposed.stat().st_dev != input_path.stat().st_dev:
                    proposed = None
            case 'Linux':
                # TODO finding better temp_dir under linux/osx
                proposed = Path('/tmp').joinpath(TEMP_DIR_HARDLINK)
                proposed.mkdir(parents=True, exist_ok=True)
                if proposed.stat().st_dev != input_path.stat().st_dev:
                    proposed = None
            case 'Darwin':
                proposed = Path('/tmp').joinpath(TEMP_DIR_HARDLINK)
                proposed.mkdir(parents=True, exist_ok=True)
                if proposed.stat().st_dev != input_path.stat().st_dev:
                    proposed = None
        if proposed and tstMkHardlinkInDir(proposed):
            return proposed
    except:
        if proposed and proposed.is_dir() and not list(proposed.iterdir()):
            try:
                proposed.rmdir()
            except:
                pass
    return None




def condenseDirLayout(root: Path):
    '''
    Remove all dirs with no files recursively.
    Will also remove any intermediate dirs level with no files.
    Will not remove the input dir if empty.
    '''
    if not root.is_dir():
        raise NotADirectoryError(f'The input "{root}" is not a dir.')
    for dir_path in listDir(root):
        files = listFile(dir_path, rglob=False)
        dirs = listDir(dir_path, rglob=False)
        match len(files), len(dirs):
            case 0, 0:
                if root != dir_path:
                    dir_path.rmdir()
                    return condenseDirLayout(root)
            case 0, 1:
                subfiles = listFile(dir_path)
                if not subfiles and root != dir_path:
                    shutil.rmtree(dir_path, ignore_errors=False)
                    return condenseDirLayout(root)
                for subfile in subfiles:
                    rel1 = dir_path.relative_to(root).parts
                    rel2 = subfile.relative_to(dir_path).parts[1:]
                    new_path = root.joinpath(*rel1, *rel2)
                    if new_path.exists():
                        raise FileExistsError(f'The new path "{new_path}" already exists.')
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    subfile.rename(new_path)
                    if DEBUG: print(f'Moved "{subfile}" -> "{new_path}".')
                return condenseDirLayout(root)
            case _:
                continue
    return
