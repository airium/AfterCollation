import sys
import enum
import time
import locale
import difflib
import hashlib
import argparse
import multiprocessing as mp

from pathlib import Path
from operator import methodcaller
from itertools import repeat, starmap
from typing import Callable, Any, List
from difflib import get_close_matches as gcm

try:
    from ssd_checker import is_ssd as SSD_CHECKER
except ImportError:
    SSD_CHECKER = None


''' Use can modify '''

# You can hard-code dir paths here
NEW_DIR_PATH : None | Path = None
OLD_DIR_PATHS : None | List[Path] = None
# the hash function used for files
HASHER = hashlib.sha1
# Python SHA1 >800MB/thread, so 4 is adequate and should fit any PCIe 3.0 NVMe SSD
N_HASH_JOBS : int = 6
# Read size per HASHER().update() - seems not matter in most cases
IO_SIZE : int = 4 * 1024 * 1024
#
ENABLE_HARDLINK_DIFF : bool = True


''' User should NOT Modify '''

VERSION = '0.2.3.230228'
TRANSLATION = {
    'en': {
        'INSTALL_SSD_CHK': 'I: Please consider `python3 -m pip install ssd_checker` to enable SSD detection and multi-processing hashing.',
        'INSTALL_TQDM': 'I: Please consider `python3 -m pip install tqdm` to enable progress bar.',
        'ARG_PATHS': '2 or more paths to directory',
        'ARG_HASHER': 'Any hash function in hashlib',
        'ARG_JOBS': 'Max number of hashing processes',
        'ARG_IO_SIZE': 'The read size in a hashing thread in bytes',
        'CLI_HASHING': 'hashing files at',
        'CLI_COMPARING': 'comparing files',
        'CLI_EXIT': 'Press ENTER key to exit...',
        'CLI_DONE': 'done and the report is at',
        'NEW': 'NEW',
        'OLD': 'OLD',
        'FILE_STATE_0': 'Untouched Files',
        'FILE_STATE_1': 'Renamed-only Files',
        'FILE_STATE_2': 'Moved-only Files',
        'FILE_STATE_3': 'Renamed & Moved Files',
        'FILE_STATE_4': 'Content Modified Files',
        'FILE_STATE_5': 'Added New Files',
        'FILE_STATE_6': 'Deleted Old Files',
        'README': f'DiffRS: {VERSION}\n'
                   'Find the file change between old ver(s) to the new ver\n'
                   'Usage: drag-drop/cli/hard-code dir paths\n'
                   '       comparision is done between the first dir and all remaining dirs\n'
                   '       priority: cli (drag/drop) > hard-coded values',
        'CHANGES' : '0.1.0 First Release\n'
                    '0.2.0 Significant improvement and bug fixes\n'
                    '0.2.1 Fix duplication of addition/deletion and modification\n'
                    '0.2.2 Main function refactor - should fix all logical bugs\n'
                    '0.2.3 SSD checker exception on SCSI disks\n'
       },
    'zh': {
        'INSTALL_SSD_CHK': 'I: 请考虑 `python3 -m pip install ssd_checker` 来启用 SSD 检测和多进程 hash 计算。',
        'INSTALL_TQDM': 'I: 请考虑 `python3 -m pip install tqdm` 来启用进度条。',
        'ARG_PATHS': '2个或更多指向目录的路径',
        'ARG_HASHER': '任何 hashlib 中的 hash 函数',
        'ARG_JOBS': '并行的 hash 计算进程数量',
        'ARG_IO_SIZE': 'hash 计算进程每次读取的数据大小',
        'CLI_HASHING': '正在计算 hash 特征',
        'CLI_COMPARING': '正在对比文件',
        'CLI_DONE': '对比完成。对比报告位于',
        'CLI_EXIT': '按下 ENTER 键退出...',
        'NEW': '新版',
        'OLD': '旧版',
        'FILE_STATE_0': '无任何变动的文件',
        'FILE_STATE_1': '只被重命名了的文件',
        'FILE_STATE_2': '只被移动了的文件',
        'FILE_STATE_3': '被重命名且移动了的文件',
        'FILE_STATE_4': '内容被修改的文件',
        'FILE_STATE_5': '在新版中新增的文件',
        'FILE_STATE_6': '从旧版中移除的文件',
        'README': f'DiffRS: {VERSION}\n'
                   '找出新版和旧版文件目录间的改动\n'
                   '用法: GUI拖放目录 或 命令行输入目录 或 修改脚本内目录变量\n'
                   '      脚本视首个目录为新版本，其余均为旧版本，将新版本与每个旧版本逐一对比\n'
                   '      优先级: GUI拖放目录 = 命令行输入目录 > 修改脚本内目录变量',
        'CHANGES': ''
       }
    }

TIME = time.strftime('%y%m%d-%H%M%S')
LANG = l[:2] if (l := locale.getdefaultlocale()[0]) else 'en'
if LANG not in TRANSLATION.keys(): LANG = 'en'
PROMPT = TRANSLATION.get(LANG, TRANSLATION['en'])
if SSD_CHECKER is None: print(PROMPT['INSTALL_SSD_CHK'])


class FILE_STATE(enum.Enum):
    FILE_SAME = 0
    FILE_RENAMED = 1
    FILE_MOVED = 2
    FILE_RENAMED_MOVED = 3
    CONTENT_MODIFIED = 4
    NEW_FILE_ADDED = 5
    OLD_FILE_DELETED = 6

FILE_STAT_CODE = {
    FILE_STATE.FILE_SAME :          'U',
    FILE_STATE.FILE_RENAMED :       'R',
    FILE_STATE.FILE_MOVED :         'M',
    FILE_STATE.FILE_RENAMED_MOVED : 'RM',
    FILE_STATE.CONTENT_MODIFIED :   'C',
    FILE_STATE.NEW_FILE_ADDED :     'A',
    FILE_STATE.OLD_FILE_DELETED :   'D',
}

def hashFile(hasher: Callable, path: Path, io_size: int) -> str:
    '''Compute the hash digest of a file.'''
    assert path.is_file()  # sanity check
    h = hasher()
    with path.open('rb') as fo:
        while (b := fo.read(io_size)):
            h.update(b)
    return h.hexdigest()


def batchHash(hasher: Callable, path2files: list[Path], n_hash_jobs: int, io_size: int, common_path: Path, ssd_checker: Callable | None) -> dict[Path, str]:
    '''Hash a list of files with `hasher`

    Arguments:
    hasher:  any hashing class in hashlib.
    path2files:  list of `pathlib.Path` to be hash.
    n_hash_jobs:  max current jobs for hashing.
    io_size:  the max read size per `hasher().update()`
    common_file:  the path used to check if hash exists
    ssd_checker:  the function to check if `common_path` is SSD.

    Multi-threaded hashing is used only if `n_hash_jobs > 1` and `ssd_checker(commmon_path) == True`.

    Return:
    dict [ relative Path to common_path : hash str ]
    '''
    try: # RAMDISK or other SCSI device may cause ssd_checker failure
        use_mt_checker = ssd_checker(common_path) if ssd_checker else False
    except Exception as e:
        print('Error in activating ssd checker, falling back to single threaded hashing')
        use_mt_checker = False
    if (n_hash_jobs > 1) and use_mt_checker:
        digests = mp.Pool(n_hash_jobs).starmap(hashFile, zip(repeat(hasher), path2files, repeat(io_size)))
    else:
        digests = list(starmap(hashFile, zip(repeat(hasher), path2files, repeat(io_size))))
    return dict(zip([path.relative_to(common_path) for path in path2files], digests))


def writeReport(report_path: Path, new_path: Path, old_path: Path, logs: dict[int, list[list[str]]]) -> None:
    WAVY = '〰'
    with report_path.open('w', encoding='utf-8-sig') as fo:
        fo.write(f'DiffRS {VERSION} @{TIME}\n')
        fo.write(f'{WAVY*50}\n')
        fo.write(f'{PROMPT["OLD"]}-: "{old_path}"\n')
        fo.write(f'{PROMPT["NEW"]}+: "{new_path}"\n')
        fo.write(f'{WAVY*50}\n')

        for k, record in logs.items():
            for i, v in enumerate(FILE_STATE):
                if k == v:
                    description = PROMPT[f'FILE_STATE_{i}']
                    break
            else:
                raise ValueError()
            if record:
                fo.write(f'{description} {WAVY*((100-len(description)-1)//2)}\n')
            for j, (new, old) in enumerate(record, start=1):
                match v:
                    case FILE_STATE.FILE_SAME | FILE_STATE.CONTENT_MODIFIED | FILE_STATE.NEW_FILE_ADDED:
                        fo.write(f'{FILE_STAT_CODE[v]}{j:+>8d} {new}\n')
                    case FILE_STATE.OLD_FILE_DELETED:
                        fo.write(f'{FILE_STAT_CODE[v]}{j:->8d} {old}\n')
                    case FILE_STATE.FILE_RENAMED_MOVED:
                        fo.write(f'{FILE_STAT_CODE[v]}{j:->7d} {old}\n')
                        fo.write(f'{FILE_STAT_CODE[v]}{j:+>7d} {new}\n')
                    case FILE_STATE.FILE_RENAMED | FILE_STATE.FILE_MOVED:
                        fo.write(f'{FILE_STAT_CODE[v]}{j:->8d} {old}\n')
                        fo.write(f'{FILE_STAT_CODE[v]}{j:+>8d} {new}\n')


def main(args:argparse.Namespace):

    hasher = args.hasher if args.hasher else (HASHER if HASHER else hashlib.sha1)
    n_hash_jobs = args.max_num_hash_jobs if args.n_hash_jobs else (N_HASH_JOBS if N_HASH_JOBS else 1)
    io_size = args.io_size if args.io_size else (IO_SIZE if IO_SIZE else 4 * 1024 * 1024)
    ssd_checker = SSD_CHECKER if SSD_CHECKER else None
    new_dir_path = args.paths[0] if args.paths else (NEW_DIR_PATH if NEW_DIR_PATH else None)
    old_dir_paths = args.paths[1:] if args.paths else (OLD_DIR_PATHS if OLD_DIR_PATHS else [])

    assert isinstance(new_dir_path, Path) and new_dir_path.is_dir()
    for old_dir_path in old_dir_paths: assert isinstance(old_dir_path, Path) and old_dir_path.is_dir()

    logs = dict(zip(FILE_STATE, [list() for _ in range(len(FILE_STATE))]))

    print(f'I: {PROMPT["CLI_HASHING"]} "{new_dir_path}"')
    # new is marked as 0
    abs_paths_0_list = sorted(filter(methodcaller('is_file'), new_dir_path.rglob('*')))
    hashes_0_dict = batchHash(hasher, abs_paths_0_list, n_hash_jobs, io_size, new_dir_path, ssd_checker)

    for i, old_dir_path in enumerate(old_dir_paths, start=1):

        print(f'I: {PROMPT["CLI_HASHING"]} "{old_dir_path}"')
        # old is marked as i=1,2,3...
        abs_paths_i_list = sorted(filter(methodcaller('is_file'), old_dir_path.rglob('*')))
        hashes_i_dict = batchHash(hasher, abs_paths_i_list, n_hash_jobs, io_size, old_dir_path, ssd_checker)
        not_hash_matched_hashes_i_dict = dict(hashes_i_dict.items())

        print(f'I: {PROMPT["CLI_COMPARING"]}...')
        content_modified_paths = set()
        for path_0, hash_0 in hashes_0_dict.items():
            hash_matched_paths = []
            for path_i, hash_i in hashes_i_dict.items():
                if hash_0 == hash_i:
                    hash_matched_paths.append(path_i)
                if (hash_0 != hash_i) and (str(path_0) == str(path_i)):
                    content_modified_paths.add(path_0)
                    logs[FILE_STATE.CONTENT_MODIFIED].append((f'{path_0}', f'{path_i}'))
            if hash_matched_paths:
                matched_path = Path(hash_matched_paths[0]) if len(hash_matched_paths) == 1 else \
                               Path(gcm(str(path_0), [str(p) for p in hash_matched_paths], n=1, cutoff=0)[0])
                if matched_path in not_hash_matched_hashes_i_dict.keys(): not_hash_matched_hashes_i_dict.pop(matched_path)
                match [path_0 == matched_path, str(path_0) == str(matched_path)]:
                    case [True, True]:
                        logs[FILE_STATE.FILE_SAME].append((f'{path_0}', f'{matched_path}'))
                    case [True, False]:
                        logs[FILE_STATE.FILE_RENAMED].append((f'{path_0}', f'{matched_path}'))
                    case [False, True] | [False, False] :
                        match [path_0.parent == matched_path.parent, path_0.name == matched_path.name]:
                            case True, False:
                                logs[FILE_STATE.FILE_RENAMED].append((f'{path_0}', f'{matched_path}'))
                            case False, True:
                                logs[FILE_STATE.FILE_MOVED].append((f'{path_0}', f'{matched_path}'))
                            case False, False:
                                logs[FILE_STATE.FILE_RENAMED_MOVED].append((f'{path_0}', f'{matched_path}'))
                            case _:
                                raise ValueError()
                    case _:
                        raise ValueError()
            else:
                if path_0 not in content_modified_paths:
                    logs[FILE_STATE.NEW_FILE_ADDED].append((f'{path_0}', ''))
        for unmatched_path in not_hash_matched_hashes_i_dict.keys():
            if unmatched_path not in content_modified_paths:
                logs[FILE_STATE.OLD_FILE_DELETED].append(('', f'{unmatched_path}'))
        output_path = new_dir_path.with_suffix(f'.{TIME}.{i:02d}.txt')
        writeReport(output_path, new_dir_path, old_dir_path, logs)
        print(f'I: {PROMPT["CLI_DONE"]} "{output_path}"')
        input(PROMPT['CLI_EXIT'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='DiffRS', epilog=PROMPT['README'],
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('paths', metavar='path', type=Path, nargs='*',
                        help=PROMPT['ARG_PATHS'])
    parser.add_argument('--hasher', metavar='sha1', dest='hasher', choices=hashlib.__all__, default=None,
                        help=PROMPT['ARG_HASHER'])
    parser.add_argument('--jobs', metavar='4', dest='n_hash_jobs', type=int, default=None,
                        help=PROMPT['ARG_JOBS'])
    parser.add_argument('--io-size', metavar='4MiB', dest='io_size', type=int, default=None,
                        help=PROMPT['ARG_IO_SIZE'])
    parser.add_argument('--version', action='version', version=VERSION)

    if sys.argv[1:] or (NEW_DIR_PATH and OLD_DIR_PATHS):
        main(parser.parse_args())
    else:
        parser.print_help()
        input(PROMPT['CLI_EXIT'])
