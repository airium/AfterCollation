import shutil
import logging
import itertools
from pathlib import Path
from functools import partial
from multiprocessing import Pool

from configs import *
from utils import *
from .misc import *
from .naming import *
from .season import Season
from .corefile import *
from .formatter import *

import tqdm
import ssd_checker


__all__ = [
    'cleanNamingDicts',
    # 'chkNamingDicts', #! in checkers/naming.py
    'applyNamingDicts',
    'tstIO4VNE',
    'toCoreFileObjs',
    'doNaming',
    'doAutoIndexing',
    'stageClassificationName',
    'unstageClassificationName',
    ]




def cleanNamingDicts(default_dict:dict[str, str], naming_dicts:list[dict[str, str]], logger:logging.Logger):
    '''
    Dedicated used in VNE to clean the naming fields (in place) from the user input (VDN.csv).
    Unacceptable characters are silently removed, so the program and the use wont be bothered handling them.
    '''

    logger.debug('PreClean: ' + ('|'.join(default_dict.values())))
    default_dict[FULLPATH_VAR] = normInputPath(default_dict[FULLPATH_VAR])
    default_dict[GRPTAG_VAR] = normFullGroupTag(default_dict[GRPTAG_VAR])
    default_dict[TITLE_VAR] = normTitle(default_dict[TITLE_VAR])
    default_dict[SUFFIX_VAR] = normFullSuffix(default_dict[SUFFIX_VAR])
    logger.debug('AftClean: ' + ('|'.join(default_dict.values())))

    for naming_dict in naming_dicts:

        logger.debug('PreClean: ' + ('|'.join(naming_dict.values())))
        naming_dict[FULLPATH_VAR] = normInputPath(naming_dict[FULLPATH_VAR])
        naming_dict[CRC32_VAR] = rmInvalidChars(naming_dict[CRC32_VAR])
        naming_dict[GRPTAG_VAR] = normFullGroupTag(naming_dict[GRPTAG_VAR])
        naming_dict[TITLE_VAR] = normTitle(naming_dict[TITLE_VAR])
        naming_dict[LOCATION_VAR] = normFullLocation(naming_dict[LOCATION_VAR])
        naming_dict[CLASSIFY_VAR] = normClassification(naming_dict[CLASSIFY_VAR])
        naming_dict[IDX1_VAR] = normDecimal(naming_dict[IDX1_VAR])
        naming_dict[IDX2_VAR] = normDecimal(naming_dict[IDX2_VAR])
        naming_dict[SUPPLEMENT_VAR] = normDescription(naming_dict[SUPPLEMENT_VAR])
        naming_dict[CUSTOM_VAR] = normDescription(naming_dict[CUSTOM_VAR])
        naming_dict[SUFFIX_VAR] = normFullSuffix(naming_dict[SUFFIX_VAR])
        logger.debug('AftClean: ' + ('|'.join(naming_dict.values())))




def applyNamingDicts(
    season: Season,
    default_dict: dict[str, str],
    naming_dicts: list[dict[str, str]],
    logger: logging.Logger
    ):
    '''
    Do a plain copy from the user input (VND.csv) to our internal data structure (Season).
    However, we will fill some empty fields with default values if not specified.

    #! Before calling this function, you should better call `cleanNamingDicts()` and `chkNamingDicts()` first.
    '''

    cfs = season.cfs
    if DEBUG: assert len(cfs) == len(naming_dicts)

    logger.info('Applying naming plan ...')

    if default_dict[GRPTAG_VAR]:
        season.g = default_dict[GRPTAG_VAR]
    else:
        grptags = [naming_dict[GRPTAG_VAR] for naming_dict in naming_dicts]
        if all(grptags):
            season.g = max(set(grptags), key=grptags.count)
            logger.info('Found empty base/default group tag but this is filled for each file. '
                        f'The program assumed the most common "{season.g}" as the title for the root dir. '
                        'You should better recheck this.')
        else:
            season.g = STD_GRPTAG
            logger.info(f'Found empty base/default group tag. The program filled it with the standard "{STD_GRPTAG}".')

    if default_dict[TITLE_VAR]:
        season.t = default_dict[TITLE_VAR]
    else:
        titles = [naming_dict[TITLE_VAR] for naming_dict in naming_dicts]
        if any(titles):
            season.t = max(set(titles), key=titles.count)
            logger.info('Found empty base/default show name but this is filled for each file. '
                        f'The program assumed the most common "{season.t}" as the show name for the root dir. '
                        'You should better recheck this.')
        else:
            season.t = FALLBACK_TITLE
            logger.info('Found empty base/default show name everywhere. '
                        'The program cannot guess this for you, so filled it with a mystery value.')

    season.x = default_dict[SUFFIX_VAR]
    # season.dst = default_dict[FULLPATH_VAR]

    for i, cf, naming_dict in zip(itertools.count(), cfs, naming_dicts):
        logger.info(f'Applying naming plan for "{cf.crc}" ...')

        cf.g = naming_dict[GRPTAG_VAR] if naming_dict[GRPTAG_VAR] else season.g
        if cf.g != season.g:
            logger.warning('Using non-default group tag.')

        cf.t = naming_dict[TITLE_VAR] if naming_dict[TITLE_VAR] else season.t
        if cf.t != season.t:
            logger.warning('Using non-default title.')

        if naming_dict[CUSTOM_VAR]:
            if m := re.match(CRC32_CSV_PATTERN, naming_dict[CUSTOM_VAR]):
                crc32 = m.group('crc32').lower()
                for ref_cf in (cfs[:i] + cfs[i+1:]):
                    if ref_cf.crc32.lower() == crc32:
                        cf.depends = ref_cf
                        logger.info(f'Set file 0x{cf.crc32} to copy/link the naming of file 0x{ref_cf.crc32}.')
                        break
                if not cf.depends:
                    logger.error(f'Failed to find the appointed file 0x{crc32} to copy/link the naming from.')
            else:
                if any((naming_dict[CLASSIFY_VAR],
                        naming_dict[IDX1_VAR],
                        naming_dict[IDX2_VAR],
                        naming_dict[SUPPLEMENT_VAR])):
                    logger.warning('Found using customised description. '
                                   'Will clear classification, main/sub index and supplement fields.')
                cf.f = naming_dict[CUSTOM_VAR]
        else:
            cf.c = naming_dict[CLASSIFY_VAR]
            cf.i1 = naming_dict[IDX1_VAR]
            cf.i2 = naming_dict[IDX2_VAR]
            cf.s = naming_dict[SUPPLEMENT_VAR]

        cf.l = STD_SPS_DIRNAME if (cf.c and not naming_dict[LOCATION_VAR]) else ''

        # possible suffix cases:
        # 1. root has no suffix or a non-lang-suffix like [Lite]:
        # if (not default_dict[SUFFIX_VAR]) or (default_dict[SUFFIX_VAR] not in AVAIL_SUB_LANG_TAGS):
        #     pass # dont touch any file suffix, as the files are free to use any suffix is this case (at least here)
        # 2. root has a language suffix like [CHS], files should have the same suffix
        if season.x and (season.x in AVAIL_SEASON_LANG_SUFFIXES):
            cf.x = season.x
            if naming_dict[SUFFIX_VAR]:
                logger.warning(f'Overridden suffix with the base/default language suffix "{default_dict[SUFFIX_VAR]}".')
        # #! there is a missing case above: root is missing language tag, but videos have language tags
        # #! since the default_dict will be disposed after this function and wont get checked afterwards
        # #! we need to catch it now
        # if cf.e in VNx_WITH_AUD_EXTS and not default_dict[SUFFIX_VAR]:
        #     logger.warning('Found video with language tag, but the root/default dir is missing language tag.')




def tstIO4VNE(src_files:list[str]|list[Path], dst_dir:str|Path, logger:logging.Logger) -> bool:
    '''This is a boring check to test if we can read/write the dst dir, and if we can hardlink from src to dst.'''

    logger.info(f'Testing input files and the output dir "{dst_dir}"...')

    src : list[Path] = [Path(path) for path in src_files]
    dst : Path = Path(dst_dir)

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
            logger.error(f'Failed to test reading the input file "{path}" due to an unexpected error {e}. Please Report.')
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




def toCoreFileObjs(paths:list[str]|list[Path], logger:logging.Logger, init_crc32:bool=True, mp:int=1) -> list[CF]:

    logger.info(f'Loading files with {mp} workers ...')
    paths = [Path(path) for path in paths]

    pbar = tqdm.tqdm(total=len(paths), desc='Loading', unit='file', ascii=True, dynamic_ncols=True)
    if mp > 1:
        ret = []
        with Pool(mp) as pool:
            for path in paths:
                ret.append(pool.apply_async(getCoreFile, kwds={'path':path, 'init_crc32':init_crc32}, callback=lambda _: pbar.update(1)))
            pool.close()
            pool.join()
        cfs = [r.get() for r in ret]
    else:
        cfs = []
        for path in paths:
            cfs.append(CF(path, init_crc32=init_crc32))
            pbar.update(1)
    pbar.close()

    return cfs




def doAutoIndexing(season:Season, logger:logging.Logger):

    cfs = season.cfs

    # we have the following kinds of files:
    # auto_cfs: to be automatically indexed
    # dep_cfs: dependent files, which need to copy the naming from another file by crc32 lookup
    # named_cfs: naming already specified in cf.c, no need to do anything

    auto_cfs : list[CF] = [info for info in cfs if not info.f]
    dep_cfs  : list[CF] = [info for info in cfs if (info.f and re.match(BASIC_CRC32_PATTERN, info.f))]
    named_cfs : list[CF] = [info for info in cfs if (info.f and not re.match(BASIC_CRC32_PATTERN, info.f))]

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




def stageClassificationName(season: Season, logger:logging.Logger):
    '''
    This function merge seperated typename/index1/2/note fields to the customization fields.

    Once merged, typename/index/1/2/note will be disposed and no longer usable.
    Use `splitContentName()` to re-gain access to these seperated fields.
    #! There is no guarantee the fields that the same seperated fields can be recovered.

    Once merged, all files are ready to accept the final naming conflict check, and then be layouted onto disk.
    '''

    cfs = season.cfs

    max_index = {}
    for cf in [info for info in cfs if not info.f]:
        l, t, i1, i2 = cf.l, cf.c, cf.i1, cf.i2
        if i2:
            key = f'{l}//{t}//{i1}'
            max_index[key] = max(max_index.get(key, -99999), float(i2))
        if i1:
            key = f'{l}//{t}'
            max_index[key] = max(max_index.get(key, -99999), float(i1))

    for i, cf in enumerate(cfs):
        if not cf.f:
            l, t, i1, i2, n = cf.l, cf.c, cf.i1, cf.i2, cf.s

            if i2:
                m2 = max(1, len(str(max_index[f'{l}//{t}//{i1}']).split('.')[0]))
                if float(i2) == int(i2): # integer
                    i2 = ('{:' + f'0{m2}.0f' + '}').format(float(i2))
                else: # float
                    n2 = len(str(max_index[f'{l}//{t}//{i1}']).split('.')[-1])
                    i2 = ('{:' + f'0{m2+n2+1}.{n2}f' + '}').format(float(i2))
            else:
                i2 = ''

            if i1:
                m1 = max(2, len(str(max_index[f'{l}//{t}']).split('.')[0]))
                if float(i1) == int(i1): # integer
                    i1 = ('{:' + f'0{m1}.0f' + '}').format(float(i1))
                else: # float
                    n1 = len(str(max_index[f'{l}//{t}']).split('.')[-1])
                    i1 = ('{:' + f'0{m1+n1+1}.{n1}f' + '}').format(float(i1))
            else:
                i1 = ''

            spaced = True if ((' ' in t) or (' ' in n)) else False
            if spaced:
                temp = '{tn}' + (' ' if t else '') + '{i1}' + ('-' if i2 else '') + '{i2}'
                temp +=  (' ' if n else '') + '{nt}'
            else:
                temp = '{tn}' + '{i1}' + ('_' if i2 else '') + '{i2}'
                temp +=  (('' if n.startswith('(') else '_') if n else '') + '{nt}'

            cf.c, cf.i1, cf.i2, cf.s, cf.f = '', '', '', '', temp.format(tn=t, i1=i1, i2=i2, nt=n)




def unstageClassificationName(season: Season, logger:logging.Logger):
    pass




def doNaming(season:Season, hardlink:bool, logger:logging.Logger) -> bool:
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
    logging.info(f'Created the season root dir "{season.dst}".')

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
