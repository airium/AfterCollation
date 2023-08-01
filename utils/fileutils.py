import os
import re
import csv
import json
import random
import platform
import itertools

from pathlib import Path
from configs import *

import yaml


__all__ = ['listFile',
           'listDir',
           'tstFileEncoding',
           'tstHardlinkInDir',
           'tstHardlink',
           'writeCSV',
           'readCSV',
           'guessVolNumByPath',
           'findCommonParentDir',
           'listM2TS2CSV',
           'listM2TS2YAML',
           'listM2TS2JSON',
           'getTempDir4Hardlink'
           ]




def listFile(*paths, ext:str|tuple|list[str]|None=None, rglob:bool=True, reduce:bool=True, sort:bool=True) -> list[Path]:
    paths = list(Path(Path(p).as_posix()) for p in paths)
    ret_paths = []
    for p in paths:
        if p.is_file():
            ret_paths.append(p)
            continue
        if p.is_dir():
            ret_paths += [f for f in p.rglob('*') if f.is_file()] if rglob else [f for f in p.glob('*') if f.is_file()]
    if ext:
        exts = (ext,) if isinstance(ext, str) else tuple(ext)
        ret_paths = [p for p in ret_paths if p.suffix.lower().endswith(exts)]
    if reduce:
        ret_paths = list(set(ret_paths))
    if sort:
        ret_paths = sorted(ret_paths)
    return ret_paths




def listDir(*inp_paths, rglob:bool=True, reduce:bool=True, sort:bool=True) -> list[Path]:
    inp_paths = list(Path(Path(p).as_posix()) for p in inp_paths)
    ret_paths = []
    for p in inp_paths:
        if p.is_dir():
            ret_paths += [p] + [f for f in p.rglob('*') if f.is_dir()] if rglob else [f for f in p.glob('*') if f.is_dir()]
    if reduce:
        ret_paths = list(set(ret_paths))
    if sort:
        ret_paths = sorted(ret_paths)
    return ret_paths




def tstFileEncoding(path:Path, encoding:str='utf-8-sig') -> bool:
    '''Test if the given encoding can decode the path file without any problem.'''

    # TODO integrate with chardet to achieve a better result?

    try:
        path = Path(path)
        assert path.is_file()
        data = path.read_text(encoding=encoding)
        if data[:3] and data[:3] == '\xef\xbb\xbf':
            return False
    except AssertionError:
        return False
    except UnicodeError:
        return False
    return True












def writeCSV(csv_path:Path, data:list[dict], encoding:str='utf-8-sig', newline:str=os.linesep) -> bool:

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




def readCSV(csv_path:Path, encoding:str='utf-8-sig', newline:str=os.linesep) -> tuple[bool, list[dict]]:

    try:
        with csv_path.open('r', encoding=encoding, newline=newline) as fo:
            reader = csv.DictReader(fo)
            data = [info for info in reader]
    except:
        return False, []
    return True, data




def guessVolNumByPath(paths:list[Path]) -> list[int|str]:

    fullnames = [path.as_posix() for path in paths]
    common_parent = Path(os.path.commonprefix(fullnames))

    if not common_parent.exists() or common_parent.is_file():
        common_parent = common_parent.parent
    assert common_parent.is_dir()

    rel_paths_strs = [path.parent.relative_to(common_parent).as_posix() for path in paths]
    rel_paths_parts = [rel_path_str.split('/') for rel_path_str in rel_paths_strs]
    rel_paths_depths = [len(rel_path_parts) for rel_path_parts in rel_paths_parts]

    processed_bools = [False] * len(paths)
    assumed_vols : list[int|str] = [''] * len(paths)

    for filenames in itertools.zip_longest(*rel_paths_parts, fillvalue=''):
        matches = [re.match(VOLUME_NAME_PATTERN, filename) for filename in filenames]
        for i, path, match, processed_bool in zip(itertools.count(), paths, matches, processed_bools):
            if not match or processed_bool:
                continue
            assumed_vols[i] = int(match.group('idx'))
            processed_bools[i] = True
        if all(processed_bools): break

    return assumed_vols




def findCommonParentDir(*paths:str|Path) -> Path|None:

    ps = [Path(p).resolve() for p in paths]

    # NOTE this function may have a bug if some inputs are not existing
    assert all(p.exists() for p in ps)

    if len(ps) == 1 and ps[0].is_file():
        return ps[0].parent
    if len(ps) == 1 and ps[0].is_dir():
        return ps[0]

    fullpaths = [p.as_posix() for p in ps]
    common_prefix = os.path.commonprefix(fullpaths)
    if not common_prefix:
        return None
    common_prefix = Path(common_prefix)
    if common_prefix.is_file():
        return common_prefix.parent
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




def tstHardlink(old:Path, new:Path) -> bool:
    '''
    Test if we can new.hardlink_to(old) successfully.
    if new is a dir, it will try hardlink to a randomly created file in the dir.
    '''

    if not (old := Path(old)).is_file():
        # NOTE raise Error instead of returning False
        # input not a file means the user is unconscious, warn it
        raise FileNotFoundError

    if (new := Path(new)).is_file():
        return False

    try:
        if new.is_dir():
            # randomly sample a un-suffixed number as the filename
            # hopefully there is no such file in the dir
            for _ in range(10):
                new = new.joinpath(str(random.sample(range(999999), 1)[0]))
                if not new.exists():
                    new.hardlink_to(old)
                    new.unlink()
                    return True
            return False
        else:
            new.hardlink_to(old)
            new.unlink()
            return True
    except:
        # since we already return False if the file exists
        # this means the file is created by us
        if new.is_file(): new.unlink(missing_ok=True)
        return False




def tstHardlinkInDir(dir_path:str|Path) -> bool:
    '''
    This function is used to test if the hardlink functionality is usable inside it.
    '''

    dir_path = Path(dir_path)
    # NOTE this is because we are lazy to check at which level the input's parent exists
    # i.e. if we makedir(parents=True), we also need to later rmdir() all the tree we created
    if not dir_path.is_dir():
        raise NotADirectoryError

    f1 : Path|None = None
    f2 : Path|None = None
    try:
        for _ in range(10): # do 10 attempts, seems enough?
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




def getTempDir4Hardlink(input_path:Path|None=None) -> Path|None:
    '''
    Return a default config dir which *should* be usable to hardlink from files in `input_path`.
    Note that the function will create the dir if success.
    Return None if failed.

    If you propose to use a specific dir, use `tstHardlink` to test it.
    '''

    if not input_path: return None
    input_path = input_path.resolve()

    proposed : Path|None = None
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
        if proposed and tstHardlinkInDir(proposed):
            return proposed
    except:
        if proposed and proposed.is_dir() and not list(proposed.iterdir()):
            try: proposed.rmdir()
            except: pass
    return None
