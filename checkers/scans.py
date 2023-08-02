import os
import random
import logging
import difflib
import itertools
from pathlib import Path
from multiprocessing import Pool

from utils import *
from helpers import *
from configs import *
from .image import *

import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm


__all__ = ['chkScansNaming', 'chkScansFiles']




def chkScansNaming(scans_dir:Path, logger:logging.Logger):
    '''
    Check the naming of the scans folder.

    The input dir is considered as a standard "Scans" folder.
    The checking is done in each subdirs of the input dir.
    '''

    if scans_dir.name != STD_BKS_DIRNAME:
        logger.error(f'The dirname "{scans_dir.name}" is not "{STD_BKS_DIRNAME}".')

    # TODO add a depth check

    for img_dir in listDir(scans_dir):

        # **************************************************************************************************************
        files = listFile(img_dir, ext=ALL_EXTS_IN_SCANS, rglob=False)

        ext_upper_cased_files = [f for f in files if any((c in string.ascii_uppercase) for c in f.suffix)]
        for f in ext_upper_cased_files:
            logger.warning(f'The file extension is not lowercase: "{f}".')

        file_groups_by_ext : dict[str, list[Path]] = {}
        for f in files:
            key = f.suffix.lower()
            if file_groups_by_ext.get(key):
                file_groups_by_ext[key].append(f)
            else:
                file_groups_by_ext[key] = [f]

        if len(set(f.stem.lower() for f in files)) != len(files):
            logger.warning(f'Found different file types have the same filename under "{img_dir}". '
                            'This should be avoided.')

        for k, v in file_groups_by_ext.items():

            stems, lower_stems = [f.stem for f in v], [f.stem.lower() for f in v]
            lower_common_stem = os.path.commonprefix(lower_stems) if len(lower_stems) > 1 else ''

            if lower_common_stem:

                if not lower_common_stem.isdigit():
                    logger.warning(f'Possibly unnecessary prefix "{lower_common_stem}" for "{v[0].parent}{os.sep}{lower_common_stem}*{k}".')
                else:
                    # TODO: can we use a more accurate common prefix warning?
                    # current implementation can rarely raise a false detection
                    # e.g. a folder with WEBPs files have only 2 JPG files: 'BK 01.jpg' and 'BK 02.jpg'
                    pass
            else:
                # give this notice when the filenames are not purely number
                if not all(stem.isdigit() for stem in lower_stems):
                    logger.info(f'Note non-number named files: "{img_dir}/[{"|".join(stems)}]{k}".')

            # TODO: is there any other situation in each group to check?
            # however, there are too many possible naming style for files so we can hardly do a 100% trusty check
            # if anything happens in production, add here


        # TODO: do we need to check the file indexing is correct?
        # generally, wrong number (incl. not starting from 01) are all considered normal and acceptable
        # they are the normal behavior by the scanner


        #***************************************************************************************************************
        dirs = listDir(img_dir, rglob=False)

        lower_dirnames_map : dict[str, str] = {}
        lower_dirnames : list[str] = []
        for dir in dirs:
            lower_dirnames.append(dir.name.lower())
            lower_dirnames_map[dir.name.lower()] = dir.name

        groups : list[set] = []
        for i, lower_dirname in enumerate(lower_dirnames):
            # using [i:] make the matching return a list at least containing itself
            # using a cutoff 0.5 to make matches such as '01' vs '02'
            matches = difflib.get_close_matches(lower_dirname, lower_dirnames[i:], n=len(lower_dirnames[i:]), cutoff=0.5)
            added = False
            for group in groups:
                if any((match in group) for match in matches):
                    group.update(matches)
                    added = True
                    break
            if not added:
                groups.append(set(matches))

        if DEBUG:
            for g1, g2 in itertools.combinations(groups, 2):
                assert not g1.intersection(g2)

        if len(groups) >= 2:
            logger.info(f'Note that the dirs have multiple ({len(groups)}) naming styles under "{img_dir}".')

        for group in groups:
            lower_names = sorted(name for name in group)
            mc_name = os.path.commonprefix(lower_names) if len(lower_names) > 1 else ''

            if mc_name:
                logger.info(f'Note a common dirname prefix "{img_dir}{os.sep}{mc_name}*".')

                n = len(mc_name)
                cased_mc_names = [lower_dirnames_map[lc_name][:n] for lc_name in lower_names]
                cased_diff_names = [lower_dirnames_map[lc_name][n:] for lc_name in lower_names]

                if any(m1 != m2 for m1, m2 in itertools.combinations(cased_mc_names, 2)):
                    logger.warning(f'Inconsistent dirname capitalization under "{img_dir}".')

                if all(n.isdigit() for n in cased_diff_names):
                    ints = sorted(int(n) for n in cased_diff_names)
                    if len(set(ints)) != len(ints):
                        logger.error(f'Duplicated dirname index: "{img_dir}{os.sep}{mc_name}*".')
                    if min(ints) != 1:
                        logger.warning(f'Dirname is indexed from {min(ints)}: "{img_dir}{os.sep}{mc_name}*".')
                    if ints != list(range(min(ints), max(ints)+1)):
                        logger.warning(f'Improperly incremented index: "{img_dir}{os.sep}{mc_name}*".')
                else:
                    logger.warning(f'Inconsistent dirname suffix part: "{img_dir}{os.sep}{mc_name}[{"|".join(cased_diff_names)}]".')


        #***************************************************************************************************************
        match len(dirs) and len(files):
            case 0, 0: # empty folder doesn't matter in torrent making, so just give a notice
                logger.info(f'Note an empty dir: "{img_dir}".')
            case 0, 1:
                logger.info(f'Note a 1-file dir: "{img_dir}".')
            case 1, 0:
                logger.warning(f'Possibly unnecessary dir with only 1 subdir and 0 subfile: "{dirs[0]}".')
            case _:
                pass

    return




def chkScansFiles(files:list[Path], temp_dir:Path|None, logger:logging.Logger):

    if DEBUG: assert all(file.is_file() for file in files)

    with logging_redirect_tqdm([logger]):
        pbar = tqdm.tqdm(total=len(files), desc='Checking', unit='file', unit_scale=False, ascii=True, dynamic_ncols=True)
        for file in files:
            chkScansImage(FI(file), temp_dir, logger=logger, decode=True)
            pbar.update(1)
        pbar.close()
