import shutil
from pathlib import Path
from logging import Logger

from configs import *
from utils import *
from .misc import *
from .naming import *
from .season import Season
from .corefile import *
from .formatter import *


__all__ = [
    'tstIO4VNE',
    'doFilePlacement',
    'doAutoIndexing',
    ]




def tstIO4VNE(src_files: list[str]|list[Path], dst_dir: str|Path, logger: Logger) -> bool:
    '''This is a boring check to test if we can read/write the dst dir, and if we can hardlink from src to dst.'''

    logger.info(f'Testing input files and the output dir "{dst_dir}"...')

    src: list[Path] = [Path(path) for path in src_files]
    dst: Path = Path(dst_dir)

    # empty src input is abnormal
    if not src:
        logger.error('No input files.')
        return False

    # test that every input file is readable
    for path in src:
        try:
            path.is_file()
            (fobj := path.open(mode='rb')).read(1)
            fobj.close()
        except FileNotFoundError:
            logger.error(f'Failed to locate the input file "{path}".')
            return False
        except OSError:
            logger.error(f'Failed to test reading the input file "{path}".')
            return False
        except Exception as e:
            logger.error(
                f'Failed to test reading the input file "{path}" due to an unexpected error {e}. Please Report.'
                )
            return False
    logger.debug('Read test completed.')

    # test dst parent exists as a dir
    try:
        if not dst.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        assert dst.is_dir()
    except OSError:
        logger.error(f'Failed to create to output parent.')
        return False
    except AssertionError:
        logger.error(f'Failed to verify to output parent.')
        return False
    except Exception as e:
        logger.error(f'Failed to test the output parent due to an unexpected error {e}. Please Report.')
        return False
    logger.debug('Dst is dir completed.')

    # test creating and delete files under the dst parent
    dst_testfile = dst.joinpath('1234567890'*23 + '.tt')
    try:
        dst_testfile.touch()
        dst_testfile.write_bytes(b'1234567890')
        assert dst_testfile.read_bytes() == b'1234567890'
        dst_testfile.unlink()
    except OSError:
        logger.error('Failed to read/write a test file of 233 chars filename. Available path length may be inadequate.')
        return False
    except AssertionError:
        logger.error('Failed to verify a test file at the output parent. Your OS/Disk may be corrupted.')
        return False
    except Exception as e:
        logger.error(f'Failed to test r/w under the output parent due to an unexpected error {e}. Please Report.')
        return False
    logger.debug('Dst writing completed.')

    return True




def doAutoIndexing(season:Season, logger:Logger):

    cfs = season.cfs

    # we have the following kinds of files:
    # auto_cfs: to be automatically indexed
    # dep_cfs: dependent files, which need to copy the naming from another file by crc32 lookup
    # named_cfs: naming already specified in cf.c, no need to do anything

    auto_cfs : list[CF] = [info for info in cfs if not info.f]
    dep_cfs  : list[CF] = [info for info in cfs if (info.f and re.match(CRC32_STRICT_REGEX, info.f))]
    named_cfs : list[CF] = [info for info in cfs if (info.f and not re.match(CRC32_STRICT_REGEX, info.f))]

    state : dict[str, int|float] = {}
    for i, acf in enumerate(auto_cfs):
        i1 = acf.i1 if acf.i1 else ''
        i2 = acf.i1 if acf.i2 else ''
        if i1 and i2:
            state[f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{acf.x}'] = float(i1)
            state[f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{i1}//{acf.x}'] = float(i2)
        elif i1 and not i2:
            state[f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{acf.x}'] = float(i1)
            # whether we need to update i2 depends on whether there is a same key
            key = f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{i1}//{acf.x}'
            if (v := state.get(key)):
                v = int(v + 1)
                acf.i2 = str(v)
                state[key] = v
                continue
            else: # we need to loop though the remaining to find the same key
                for j, cf in enumerate(auto_cfs[i+1:]):
                    j1 = '' if cf.i1 == None else cf.i1
                    j2 = '' if cf.i2 == None else cf.i2
                    jey = f'{cf.e}//{cf.g}//{cf.t}//{cf.l}//{cf.c}//{j1}//{cf.x}'
                    if key == jey:
                        acf.i2 = str(1)
                        state[key] = 1
                        break
        else: # if not i1
            key = f'{acf.e}//{acf.g}//{acf.t}//{acf.l}//{acf.c}//{acf.x}'
            if (v := state.get(key)):
                v = int(v + 1)
                acf.i1 = str(v)
                state[key] = v
                continue
            else: # we need to loop through the remaining to find the same key
                for j, cf in enumerate(auto_cfs[i+1:]):
                    j1 = cf.i1 if cf.i1 else ''
                    j2 = cf.i2 if cf.i2 else ''
                    jey = f'{cf.e}//{cf.g}//{cf.t}//{cf.l}//{cf.c}//{cf.x}'
                    if key == jey:
                        acf.i1 = str(1)
                        state[key] = 1
                        break

    for i, dcf in enumerate(dep_cfs):
        found = None
        for cf in (auto_cfs + named_cfs):
            if cf.crc == dcf.f: # TODO use regex for dcf.c
                found = cf
                break
        if found != None:
            dcf.copyNaming(found)
            logger.info(f'File "{dcf.crc}" copied naming from file "{found.crc}".')
        else:
            logger.error('Cannot find the file with the target CRC32 {} to copy the naming from.')
            raise ValueError('Trying to refer to the naming of an inexisting/disabled file.')
    return








def doFilePlacement(season:Season, hardlink:bool, logger:Logger) -> bool:
    '''
    Perform the naming plan onto disk.

    Arguments:
    dst_parent: Path : the output dir will be under this dir
    default: INFO : the base/default naming config
    infos: list[CF] : the naming config of each files
    hardlink: bool : whether to use hardlink or not
    logger: Logger

    Return:
    bool: whether the whole job is completed without error
    '''

    # the quality label for the root dir is determined by files at the root dir

    logger.info('Placing files ...')

    ok = True
    Path(season.dst).mkdir(parents=True, exist_ok=True)
    logger.info(f'Created the season root dir "{season.dst}".')

    # everything looks ok so far, now start creating the target
    for cf in season.cfs:
        try:
            src, dst = Path(cf.src), Path(cf.dst)
            if src.resolve() == dst.resolve():
                logger.error(f'The source and destination are the same (file 0x{cf.crc}).')
                ok = False
                continue
            parent = dst.parent
            if parent.is_file():
                logger.error(f'Failed to create "{dst}" (its parent is a file)')
            else:
                if not parent.exists():
                    parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f'Created dir "{parent}"')
                if dst.is_file():
                    dst.unlink()
                    logger.warning(f'Removed existing file "{dst}".')
                if hardlink:
                    dst.hardlink_to(src)
                    logger.info(f'Harlinked to "{dst}" (0x{cf.crc}).')
                else:
                    shutil.copy(src, dst)
                    logger.info(f'Copied to "{dst}" (0x{cf.crc}).')
        except Exception as e:
            logger.error(f'Unknown error {e} occurred during placing files. Stopping...')
            ok = False
            break
    if not ok:
        logger.error('Error occurred during placing files.')
    return ok
