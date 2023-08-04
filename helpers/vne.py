import shutil
import logging

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
    'fmtContentName'
    ]




def cleanNamingDicts(default_dict:dict[str, str], naming_dicts:list[dict[str, str]], logger:logging.Logger):
    '''
    Dedicated used in VNE to clean the naming fields (in place) from the user input (VDN.csv).
    Unacceptable characters are silently removed, so the program and the use wont be bothered handling them.
    '''

    logger.debug('PreClean: ' + ('|'.join(f'{k}={v}' for k, v in default_dict.items())))
    default_dict[FULLPATH_VAR] = cleanFullPath(default_dict[FULLPATH_VAR])
    default_dict[GRPTAG_VAR] = cleanFullGroupName(default_dict[GRPTAG_VAR])
    default_dict[SHOWNAME_VAR] = cleanGenericName(default_dict[SHOWNAME_VAR])
    default_dict[SUFFIX_VAR] = cleanFullSuffix(default_dict[SUFFIX_VAR])
    logger.debug('AftClean: ' + ('|'.join(f'{k}={v}' for k, v in default_dict.items())))

    for naming_dict in naming_dicts:

        logger.debug('PreClean: ' + ('|'.join(f'{k}={v}' for k, v in naming_dict.items())))
        naming_dict[FULLPATH_VAR] = cleanFullPath(naming_dict[FULLPATH_VAR])
        naming_dict[CRC32_VAR] = cleanString(naming_dict[CRC32_VAR])
        naming_dict[GRPTAG_VAR] = cleanFullGroupName(naming_dict[GRPTAG_VAR])
        naming_dict[SHOWNAME_VAR] = cleanGenericName(naming_dict[SHOWNAME_VAR])
        naming_dict[LOCATION_VAR] = cleanLocation(naming_dict[LOCATION_VAR])
        naming_dict[TYPENAME_VAR] = cleanGenericName(naming_dict[TYPENAME_VAR])
        naming_dict[IDX1_VAR] = cleanDecimal(naming_dict[IDX1_VAR])
        naming_dict[IDX2_VAR] = cleanDecimal(naming_dict[IDX2_VAR])
        naming_dict[NOTE_VAR] = cleanGenericName(naming_dict[NOTE_VAR])
        naming_dict[CUSTOM_VAR] = cleanGenericName(naming_dict[CUSTOM_VAR])
        naming_dict[SUFFIX_VAR] = cleanFullSuffix(naming_dict[SUFFIX_VAR])
        logger.debug('AftClean: ' + ('|'.join(f'{k}={v}' for k, v in naming_dict.items())))




def applyNamingDicts(season:Season, default_dict:dict[str, str], naming_dicts:list[dict[str, str]], logger:logging.Logger):
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
            logger.info(f'Found empty base/default group tag but this is filled for each file. '
                        f'The program assumed the most common "{season.g}" as the showname for the root dir. '
                        'You should better recheck this.')
        else:
            season.g = STD_GRP_NAME
            logger.info(f'Found empty base/default group tag. The program filled it with the standard "{STD_GRP_NAME}".')

    if default_dict[SHOWNAME_VAR]:
        season.s = default_dict[SHOWNAME_VAR]
    else:
        shownames = [naming_dict[SHOWNAME_VAR] for naming_dict in naming_dicts]
        if any(shownames):
            season.s = max(set(shownames), key=shownames.count)
            logger.info(f'Found empty base/default show name but this is filled for each file. '
                        f'The program assumed the most common "{season.s}" as the show name for the root dir. '
                        'You should better recheck this.')
        else:
            season.s = FALLBACK_SHOWNAME
            logger.info(f'Found empty base/default show name everywhere. The program cannot guess this for you, so filled it with a mystery value.')

    season.x = default_dict[SUFFIX_VAR]
    # season.dst = default_dict[FULLPATH_VAR]

    for cf, naming_dict in zip(cfs, naming_dicts):
        logger.info(f'Applying naming plan for "{cf.crc}" ...')

        cf.g = naming_dict[GRPTAG_VAR] if naming_dict[GRPTAG_VAR] else season.g
        if cf.g != season.g:
            logger.warning('Using non-default group name.')

        cf.s = naming_dict[SHOWNAME_VAR] if naming_dict[SHOWNAME_VAR] else season.s
        if cf.s != season.s:
            logger.warning('Using non-default show name.')

        if naming_dict[CUSTOM_VAR] and (
            any((naming_dict[TYPENAME_VAR], naming_dict[IDX1_VAR], naming_dict[IDX2_VAR], naming_dict[NOTE_VAR]))):
            logger.warning('Found using customised name. Will clear typename, main/sub index and note fields.')
        cf.c = naming_dict[CUSTOM_VAR] if naming_dict[CUSTOM_VAR] else ''
        cf.t = '' if cf.c else naming_dict[TYPENAME_VAR]
        cf.i1 = '' if cf.c else naming_dict[IDX1_VAR]
        cf.i2 = '' if cf.c else naming_dict[IDX2_VAR]
        cf.n = '' if cf.c else naming_dict[NOTE_VAR]

        cf.l = STD_SPS_DIRNAME if (cf.t and not naming_dict[LOCATION_VAR]) else ''

        # possible suffix cases:
        # 1. root has no suffix or a non-lang-suffix like [Lite]:
        # if (not default_dict[SUFFIX_VAR]) or (default_dict[SUFFIX_VAR] not in AVAIL_SUB_LANG_TAGS):
        #     pass # dont touch any file suffix, as the files are free to use any suffix is this case (at least here)
        # 2. root has a language suffix like [CHS], files should have the same suffix
        if season.x and (season.x in AVAIL_SUB_LANG_TAGS):
            cf.x = season.x
            if naming_dict[SUFFIX_VAR]:
                logger.warning(f'Overwrite file suffix with the base/default language suffix "{default_dict[SUFFIX_VAR]}".')
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

    auto_cfs : list[CF] = [info for info in cfs if not info.c]
    dep_cfs  : list[CF] = [info for info in cfs if (info.c and re.match(BASIC_CRC32_PATTERN, info.c))]
    named_cfs : list[CF] = [info for info in cfs if (info.c and not re.match(BASIC_CRC32_PATTERN, info.c))]

    state : dict[str, int|float] = {}
    for i, acf in enumerate(auto_cfs):
        i1 = acf.i1 if acf.i1 else ''
        i2 = acf.i1 if acf.i2 else ''
        if i1 and i2:
            state[f'{acf.e}//{acf.g}//{acf.s}//{acf.l}//{acf.t}//{acf.x}'] = float(i1)
            state[f'{acf.e}//{acf.g}//{acf.s}//{acf.l}//{acf.t}//{i1}//{acf.x}'] = float(i2)
        elif i1 and not i2:
            state[f'{acf.e}//{acf.g}//{acf.s}//{acf.l}//{acf.t}//{acf.x}'] = float(i1)
            # whether we need to update i2 depends on whether there is a same key
            key = f'{acf.e}//{acf.g}//{acf.s}//{acf.l}//{acf.t}//{i1}//{acf.x}'
            if (v := state.get(key)):
                v = int(v + 1)
                acf.i2 = str(v)
                state[key] = v
                continue
            else: # we need to loop though the remaining to find the same key
                for j, cf in enumerate(auto_cfs[i+1:]):
                    j1 = '' if cf.i1 == None else cf.i1
                    j2 = '' if cf.i2 == None else cf.i2
                    jey = f'{cf.e}//{cf.g}//{cf.s}//{cf.l}//{cf.t}//{j1}//{cf.x}'
                    if key == jey:
                        acf.i2 = str(1)
                        state[key] = 1
                        break
        else: # if not i1
            key = f'{acf.e}//{acf.g}//{acf.s}//{acf.l}//{acf.t}//{acf.x}'
            if (v := state.get(key)):
                v = int(v + 1)
                acf.i1 = str(v)
                state[key] = v
                continue
            else: # we need to loop through the remaining to find the same key
                for j, cf in enumerate(auto_cfs[i+1:]):
                    j1 = cf.i1 if cf.i1 else ''
                    j2 = cf.i2 if cf.i2 else ''
                    jey = f'{cf.e}//{cf.g}//{cf.s}//{cf.l}//{cf.t}//{cf.x}'
                    if key == jey:
                        acf.i1 = str(1)
                        state[key] = 1
                        break

    for i, dcf in enumerate(dep_cfs):
        found = None
        for cf in (auto_cfs + named_cfs):
            if cf.crc == dcf.c: # TODO use regex for dcf.c
                found = cf
                break
        if found != None:
            dcf.copyNaming(found)
            logger.info(f'File "{dcf.crc}" copied naming from file "{found.crc}".')
        else:
            logger.error('Cannot find the file with the target CRC32 {} to copy the naming from.')
            raise ValueError('Trying to refer to the naming of an inexisting/disabled file.')
    return




def fmtContentName(season: Season, logger:logging.Logger):
    '''This function push typename/index/note to the customise'''

    cfs = season.cfs

    max_index = {}
    for cf in [info for info in cfs if not info.c]:
        l, t, i1, i2 = cf.l, cf.t, cf.i1, cf.i2
        if i2:
            key = f'{l}//{t}//{i1}'
            max_index[key] = max(max_index.get(key, -99999), float(i2))
        if i1:
            key = f'{l}//{t}'
            max_index[key] = max(max_index.get(key, -99999), float(i1))

    for i, cf in enumerate(cfs):
        if not cf.c:
            l, t, i1, i2, n = cf.l, cf.t, cf.i1, cf.i2, cf.n

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

            cf.t, cf.i1, cf.i2, cf.n, cf.c = '', '', '', '', temp.format(tn=t, i1=i1, i2=i2, nt=n)




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

    logger.info('Executing the naming plan ......................................................')

    root_qlabel : str = ''
    qlabels : dict[str, int] = {} # candidate quality labels
    for cf in [cf for cf in season.cfs if (cf.l in ('', '/'))]:
        if cf.has_video:
            q = fmtQualityLabel(cf, logger)
            qlabels[q] = qlabels.get(q, 0) + 1
    if qlabels: root_qlabel = max(qlabels, key=qlabels.get)
    else: logger.warning('No video enabled/located at root dir. The output dirname will have no quality label.')

    # now create the root dir
    root_qlabel = (f'[{root_qlabel}]' if root_qlabel else '')
    root_suffix = (f'[{season.x}]' if season.x else '')
    dst_dir = Path(season.p).joinpath(f'[{season.g}] {season.s} {root_qlabel}{root_suffix}')
    dst_dir.mkdir(parents=True, exist_ok=True) # the possible trailing space seems not matter
    logging.info(f'Created base dir "{dst_dir}"')

    # then the files
    # we need to process independent files first
    # because the q/t-label for mkv/mp4 must be determined before mka/ass copying
    # TODO: save quality label and track label in `CF` before `doNaming()`

    dep_cfs = list(cf for cf in season.cfs if cf.e in VNx_DEP_EXTS)
    idp_cfs = list(cf for cf in season.cfs if cf.e not in VNx_DEP_EXTS)

    for i, idp_cf in enumerate(idp_cfs):
        g = idp_cf.g
        s = idp_cf.s
        c = f'[{c}]' if (c := idp_cf.c) else '' # some files may have no content name
        q = f'[{q}]' if (q := fmtQualityLabel(idp_cf, logger)) else ''
        t = f'[{t}]' if (t := fmtTrackLabel(idp_cf, logger)) else ''
        x = (f'.{idp_cf.x}' if (idp_cf.e in VNx_SUB_EXTS) else f'[{idp_cf.x}]') if idp_cf.x else ''
        e = idp_cf.e
        idp_cf.dst = dst_dir.joinpath(idp_cf.l, f'[{g}] {s} {c}{q}{t}{x}.{e}').as_posix()

    for i, dep_cf in enumerate(dep_cfs):
        g = dep_cf.g
        s = dep_cf.s
        c = f'[{c}]' if (c := dep_cf.c) else '' # some files may have no content name
        counterparts = [cf for cf in idp_cfs if all(cmpCoreFileNaming(cf, dep_cf)[:8])] # match any except suffix
        if counterparts:
            q = f'[{q}]' if (q := fmtQualityLabel(counterparts[0], logger)) else ''
            t = f'[{t}]' if (t := fmtTrackLabel(counterparts[0], logger)) else ''
            if counterparts[1:]:
                logger.warning(f'Found more than 1 counterpart videos for "{dep_cf.crc}" '
                               f'to copy quality/track label You config may be incorrect.')
        else:
            logger.error(f'Cannot find a counterpart video for "{dep_cf.crc}" to copy quality/track label.')
            q = '[x]'
            t = '[x]'
        x = (f'.{dep_cf.x}' if (dep_cf.e in VNx_SUB_EXTS) else f'[{dep_cf.x}]') if dep_cf.x else ''
        e = dep_cf.e
        dep_cf.dst = dst_dir.joinpath(dep_cf.l, f'[{g}] {s} {c}{q}{t}{x}.{e}').as_posix()

    # everything looks ok so far, now start creating the target
    for cf in (idp_cfs + dep_cfs):
        src, dst = Path(cf.src), Path(cf.dst)
        if src.resolve() == dst.resolve():
            logger.error('Source and destination are the same.')
            continue
        parent = dst.parent
        if parent.is_file():
            logger.error(f'Failed to create "{dst.relative_to(dst_dir)}" (its parent is a file)')
        else:
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
                logger.info(f'Created dir "{parent}"')
            if dst.is_file():
                dst.unlink()
                logger.warning(f'Removed existing file "{dst.relative_to(dst_dir)}"')
            if hardlink:
                dst.hardlink_to(src)
            else:
                shutil.copy(src, dst)
            logger.info(f'Created file "{dst.relative_to(dst_dir)}" ({cf.crc})')

    logger.info('VNE stopped because of a failure in creating output files.')

    return True