import random
import difflib
import itertools
from pathlib import Path
from multiprocessing import Pool

from utils import *
from helpers import *
from configs import *

import tqdm




def chkScansNaming(input_dirs:list[Path], logger):

    for input_dir in input_dirs:

        if DEBUG: assert input_dir.is_dir()

        # ******************************************************************************************
        files = listFile(input_dir, ext=ALL_EXTS_IN_SCANS, rglob=False)

        ext_upper_cased_files = [f for f in files if any((c in string.ascii_uppercase) for c in f.suffix)]
        for f in ext_upper_cased_files:
            logger.warning(f'"{f}" has upper-cased letter in file extension.')

        file_groups_by_ext : dict[str, list[Path]] = {}
        for f in files:
            key = f.suffix.lower()
            if file_groups_by_ext.get(key):
                file_groups_by_ext[key].append(f)
            else:
                file_groups_by_ext[key] = [f]

        for k, v in file_groups_by_ext.items():
            filestems = [f.stem.lower() for f in v]
            mc_stem = os.path.commonprefix(filestems) if len(filestems) > 1 else ''
            if mc_stem:
                if not mc_stem.isdigit():
                    logger.warning(f'Found possibly unnecessary prefix "{mc_stem}" for "{v[0].parent}/{mc_stem}*{k}".')
                else:
                    # TODO: can we use a more accurate common prefix warning?
                    # current implementation can rarely raise a false detection
                    # e.g. a folder with WEBPs files have only 2 JPG files: 'BK 01.jpg' and 'BK 02.jpg'
                    pass
            else:
                # give this warm notice when the filename is not purely number
                if not all(stem.isdigit() for stem in filestems):
                    logger.info(f'Note non-number named files: "{input_dir}/[{"|".join(filestems)}]{k}".')

                # TODO: is there any other situation to check?
                # there are too many possible naming style for files so we can hardly do a 100% trusty check
                # if anything happens in production, add here

        if len(set(f.stem.lower() for f in files)) != len(files):
            logger.warning(f'Found different file types have the same filename under "{input_dir}". '
                            'This should be avoided.')

        # TODO: do we need to check the file indexing is correct?
        # generally, wrong number (incl. not starting from 01) are all considered normal and acceptable
        # they are the normal behavior by the scanner

        #*******************************************************************************************
        dirs = listDir(input_dir, rglob=False)

        lcased_dirnames_map : dict[str, str] = {}
        lcased_dirnamed : list[str] = []
        for dir in dirs:
            lcased_dirnamed.append(dir.name.lower())
            lcased_dirnames_map[dir.name.lower()] = dir.name

        groups : list[set] = []
        for i, lc_dirname in enumerate(lcased_dirnamed):
            # using a cutoff 0.5 to make matches such as '01' vs '02'
            matches = difflib.get_close_matches(lc_dirname, lcased_dirnamed[i+1:],
                                                n=max(1, len(lcased_dirnamed[i+1:])), cutoff=0.5)
            matches.append(lc_dirname)
            added = False
            for group in groups:
                if any((match in group) for match in matches):
                    for match in matches:
                        group.add(match)
                    added = True
                    break
            if not added:
                groups.append(set(matches))

        if DEBUG:
            for g1, g2 in itertools.combinations(groups, 2):
                assert not g1.intersection(g2)

        if len(groups) >= 2:
            logger.info(f'Take care that the folders under "{input_dir}" '
                           f'have multiple ({len(groups)}) naming styles.')

        for group in groups:
            lcased_names = sorted(name for name in group)
            mc_name = os.path.commonprefix(lcased_names) if len(lcased_names) > 1 else ''

            if mc_name:
                logger.info(f'Found a common dirname prefix "{mc_name}" under "{input_dir}".')

                n = len(mc_name)
                cased_mc_names = [lcased_dirnames_map[lc_name][:n] for lc_name in lcased_names]
                cased_diff_names = [lcased_dirnames_map[lc_name][n:] for lc_name in lcased_names]

                if any(m1 != m2 for m1, m2 in itertools.combinations(cased_mc_names, 2)):
                    logger.warning(f'The dirname case style under "{input_dir}" looks inconsistent.')

                if all(n.isdigit() for n in cased_diff_names):
                    ints = sorted(int(n) for n in cased_diff_names)
                    if len(set(ints)) != len(ints):
                        logger.warning(f'The index in dirname "{input_dir}" contains duplication.')
                    if min(ints) != 1:
                        logger.warning(f'The index at "{input_dir}/{mc_name}*" not starts at 1.')
                    if ints != list(range(min(ints), max(ints)+1)):
                        logger.warning(f'The index at "{input_dir}/{mc_name}*" looks improperly incremented.')
                else:
                    logger.warning(f'The dirs under "{input_dir}" prefixed with "{mc_name}" '
                                    'looks inconsistent for their uncommon parts.')

                # if mc_name.startswith('vol'):
                #     cased_mc_name = [dirname[:n] for dirname in lcased_dirnames_map]

        if (len(dirs) == 1) and (len(files) == 0):
            logger.warning(f'The folder "{input_dir}" looks unnecessary as it contains only 1 dir '
                            'and no needed file (i.e. WEBP/JPG).')

        # this is unneeded as empty folder doesn't matter in torrent making
        # if (len(dirs) == 0) and (len(files) == 0):
        #     logger.warning(f'The folder {dir} is empty.')




def chkScansFiles(files:list[Path], temp_dir:Path|None, logger) -> bool:

    if DEBUG:
        for file in files:
            assert file.is_file()

    ok = True

    #* check filesize ******************************************************************************

    for file in files:
        filesize = file.stat().st_size
        if filesize == 0:
            logger.error(f'Found empty file "{file}".')
            ok = False
        elif filesize < SMALL_IMAGE_FILE_SIZE:
            logger.warning(f'Found very small file "{file}".')

    if not ok:
        return False

    #* check format/extension consistency *********************************************************

    for file in files:

        minfo : MI = getMediaInfo(file)
        ginfo = minfo.general_tracks[0]
        ext = (ext.lower() if (ext := ginfo.file_extension) else '')

        if DEBUG: assert ext

        # extension vs container
        match ext:
            case 'webp':
                # NOTE libmediainfo can only detect it's WebP but cannot show any info
                expected_format = 'WebP'
            case 'jpg'|'jpeg':
                expected_format = 'JPEG'
            case _:
                raise ValueError(f'Got {ext} but {ALL_EXTS_IN_SCANS=}')

        if expected_format != ginfo.format:
            logger.error(f'The actual media format {ginfo.format} ≠ file ext {expected_format} for "{file}".')
            ok = False

    if not ok:
        return False

    #* check basic mediainfo **********************************************************************#
    pbar = tqdm.tqdm(total=len(files), desc='Format&Metadata', unit='', unit_scale=False, ascii=True, dynamic_ncols=True)
    for file in files:

        minfo : MI = getMediaInfo(file)
        ginfo = minfo.general_tracks[0]
        iinfo = minfo.image_tracks[0]
        ext = (ext.lower() if (ext := ginfo.file_extension) else '')
        if DEBUG: assert ext

        w, h, mode = 0, 0, ''
        if temp_dir:
            (work_file := temp_dir.joinpath(f'{time.time_ns()}-{file.name}')).hardlink_to(file)
        else:
            work_file = file
        match ext:
            case 'webp':
                ret = tstDwebp(f'{work_file.as_posix()}')
                # NOTE don't decode the raw ret['stderr'], it may contain unknown encoding difficult to determine
                # and actually our regex only need the ASCII part
                if m := re.search(DWEBP_STDERR_PARSE_PATTERN, ret['stderr']):
                    w, h, mode, alpha = m['width'], m['height'], m['mode'], m['alpha']
                    q = getWebpQuality(f'{work_file.as_posix()}')
                    if q and not ((ENFORCED_WEBP_QUALITY - 3) < q < (ENFORCED_WEBP_QUALITY + 3)):
                        logger.warning(f'The WEBP file "{file}" may have improper quality '
                                    f'(got {q} but expect {ENFORCED_WEBP_QUALITY}).')
                    if alpha:
                        logger.info(f'Note an alpha WEBP file "{file}".')
                else:
                    if b'cannot open input file' in ret['stderr']:
                        logger.error(f'Libwebp cannot parse the path "{file}". Consider using hardlink mode.')
                    else:
                        logger.error(f'Failed to parse "{file}".')
                    ok = False
            case 'jpg'|'jpeg':
                w, h, mode = iinfo.width, iinfo.height, iinfo.compression_mode
                if not any((w, h, mode)):
                    logger.error(f'Failed to parse necessary metadata from "{file}".')
                    ok = False
                if iinfo.chroma_subsampling and iinfo.chroma_subsampling == '4:4:4':
                    # rarely, yuv444 is abnormal, give an info record
                    logger.info(f'Note a YUV444 JPEG file "{file}".')
            case _:
                raise ValueError(f'Got {ext} but {ALL_EXTS_IN_SCANS=}')

        if temp_dir: work_file.unlink()

        w, h, mode = w if w else 0, h if h else 0, mode if mode else ''
        # general check applies to all formats
        if int(w) >= LARGE_SCANS_THRESHOLD or int(h) >= LARGE_SCANS_THRESHOLD:
            logger.info(f'"{file}" ({int(w)}x{int(h)}) may be 1200dpi or higher. Consider downsampling it.')
        if mode.lower() == 'lossless':
            logger.error(f'Detected lossless image "{file}". This is disallowed.')

        pbar.update(1)
    pbar.close()
    if not ok:
        return False

    #* full decoding test *************************************************************************#
    logger.info('Starting multi-processed file decoding test. This can take a while .............')

    p = Pool()
    results = []
    hardlink_files = []
    for file in files:


        if temp_dir:
            # randomly sleep 0-100ms to make the filename different
            # this is because multiprocessing dispatches all together (at the same ns)
            time.sleep(random.random()*0.01)
            (work_file := temp_dir.joinpath(f'{time.time_ns()}-{file.name}')).hardlink_to(file)
            hardlink_files.append(work_file)
        else:
            work_file = file

        ext = file.suffix.lower()
        match ext:
            case '.webp':
                kwds = {'func':dwebp,
                        'input_path': f'{work_file.as_posix()}',
                        'output_path':'-',
                        'option':'-mt',
                        'logging':''}
                # results.append(decode(**kwds))
                results.append(p.apply_async(decode, kwds=kwds))
            case '.jpg'|'.jpeg':
                kwds = {'func':cwebp,
                        'input_path': f'{work_file.as_posix()}',
                        'output_path':'-',
                        'option':'-m 0 -mt -crop 0 0 16 16',
                        'logging':''}
                # results.append(decode(**kwds))
                results.append(p.apply_async(decode, kwds=kwds))
            case _:
                raise ValueError(f'Got {ext} but {ALL_EXTS_IN_SCANS=}')

    n_completed = 0
    pbar = tqdm.tqdm(total=len(files), desc='Decoding', unit='', unit_scale=False, ascii=True, dynamic_ncols=True)
    while n_completed < len(files):
        n_ready = sum(r.ready() for r in results)
        if n_new := (n_ready - n_completed):
            pbar.update(n_new)
        n_completed = n_ready
        time.sleep(0.5)

    pbar.close()

    p.close()
    p.join()

    for hardlink_file in hardlink_files: hardlink_file.unlink()

    results = [r.get() for r in results]
    for result in results:
        if result['retcode'] != 0:
            if b'cannot open input file' in result['stderr']:
                logger.error(f"Libwebp cannot parse the path \"{result['input_path']}\". "
                              'Consider using hardlink mode.')
            else:
                logger.error(f"Failed to decode \"{result['input_path']}\".")
            ok = False

    if not ok:
        return False

    return True
