import os
import shutil
import logging
import difflib
import platform
import traceback
import itertools
from pathlib import Path
from logging import Logger
from operator import attrgetter
from typing import Callable, Iterable, Optional
from multiprocessing import Pool

from langs import *
from utils import *
from configs import *
from checkers.scans import *
from utils.fileutils import listFile, listDir
from loggers import initLogger
from .summaries import logScansSummary
from .image import ImageFile
from .misc import handleResourceSrc
from .dirgetter import *
from .naming import *

import yaml


__all__ = [
    'getScansDirs',
    'filterScansFiles',
    'cleanScansFilenames',
    'ScansConfig',
    'getScansConfig',
    'procScanSrc',
    'collectScansDirs',
    'placeScans',
    'chkScans',
    'procScanSrcList',
    ]




def _runJob(job: tuple[Callable, tuple]) -> bool:
    return job[0](*job[1])




def filterScansFiles(src_path: Path, logger: Optional[Logger] = None) -> list[Path]:

    all_paths = listFile(src_path)
    scans_files = listFile(src_path, ext=ALL_EXTS_IN_SCANS)
    for path in set(all_paths).difference(scans_files):
        if logger: logger.error(DISALLOWED_FILE_1.format(path))
    return scans_files




def cleanScansFilenames(scans_dir: Path, logger: Logger):
    if not scans_dir.is_dir():
        raise NotADirectoryError(f'The input "{scans_dir}" is not a dir.')
    for dir_path in listDir(scans_dir):

        files = listFile(dir_path, rglob=False, ext=ALL_EXTS_IN_SCANS)
        for file in files:
            file.rename(file.with_suffix(file.suffix.lower()))

        files = listFile(dir_path, rglob=False, ext=ALL_EXTS_IN_SCANS)
        file_groups_by_ext: dict[str, list[Path]] = {}
        for f in files:
            key = f.suffix
            if file_groups_by_ext.get(key):
                file_groups_by_ext[key].append(f)
            else:
                file_groups_by_ext[key] = [f]

        for suffix, files in file_groups_by_ext.items():

            lower_filenames: list[str] = []
            lower2orig_filename_mapping: dict[str, str] = {}
            for file in files:
                lower_filenames.append(file.name.lower())
                lower2orig_filename_mapping[file.name.lower()] = file.name

            groups: list[set[str]] = []
            for i, lower_filename in enumerate(lower_filenames):
                # using [i:] make the matching return a list at least containing itself
                # using a cutoff 0.5 to make matches such as '01' vs '02'
                matches = difflib.get_close_matches(
                    lower_filename, lower_filenames[i:], n=len(lower_filenames[i:]), cutoff=0.5
                    )
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

            for group in groups:

                lower_names = sorted(name for name in group)
                lower_common_prefix = os.path.commonprefix(lower_names) if len(lower_names) > 1 else ''

                lower_stems, exts = zip(*[os.path.splitext(name) for name in lower_names])
                reverse_lower_stems = [stem[::-1] for stem in lower_stems]
                lower_common_suffix = os.path.commonprefix(reverse_lower_stems) if len(lower_names) > 1 else ''

                if lower_common_prefix or lower_common_suffix:
                    prewidth = len(lower_common_prefix)
                    endwidth = len(lower_common_suffix)
                    for lower_name, ext in zip(lower_names, exts):
                        old_path = dir_path / (old_name := lower2orig_filename_mapping[lower_name])
                        new_path = dir_path / (new_name := old_name[prewidth:len(old_name) - len(ext) - endwidth] + ext)
                        old_path.rename(new_path)
                        logger.info(f'Renamed "{old_path}" -> "{new_path.name}".')




class ScansConfig:
    pass




def getScansConfig(possible_paths: list[str|Path], logger: Logger|None = None) -> ScansConfig:

    conf = ScansConfig()
    paths = [Path(p) for p in possible_paths]

    data = None
    for path in paths:
        if path.is_file():
            try:
                data = yaml.safe_load(path.read_text(encoding='utf-8-sig'))
                break
            except:
                if logger: logger.debug(f'Failed to read config file "{path}".')
                continue

    if (not data) or (not isinstance(data, dict)): return conf

    # TODO: update conf




def procScanSrc(src_path: Path, dst_dir: Path, logger: Logger):

    if DEBUG: logger.debug(PROCESSING_2.format(src_path, dst_dir))
    else: logger.info(PROCESSING_1.format(src_path))

    #* check output availability ---------------------------------------------------------------------------------------

    try:
        assert not dst_dir.is_file()
        dst_dir.mkdir(parents=True, exist_ok=False)
        (dst_scans_dir := dst_dir / STD_BKS_DIRNAME).mkdir(parents=True, exist_ok=False)
        (info_csv_path := dst_dir / SD_INFO_CSV_FILENAME).touch(exist_ok=False)
    except:
        logger.error(DEST_DIR_NOT_AVAIL_1.format(dst_dir))
        shutil.rmtree(dst_dir, ignore_errors=True)
        return

    #* check input, decompress if required -----------------------------------------------------------------------------

    tmp_dir = TEMP_DIR_DECOMPRESS / SD_TMP_DIRNAME
    if ret := handleResourceSrc(src_path, tmp_dir, logger):
        remove_src: bool = (ret == tmp_dir)
        src_path = ret
    else:
        logger.error(CANT_HANDLE_SRC_1.format(src_path))
        shutil.rmtree(dst_dir, ignore_errors=True)
        return

    #* validate input files  -------------------------------------------------------------------------------------------

    pool = Pool(NUM_CPU_JOBS)

    ifs = [ImageFile(path) for path in listFile(src_path, ext=SD_IMG_EXTS)]
    vals = pool.map(attrgetter('is_valid'), ifs)
    val_ifs = [file for (valid, file) in zip(vals, ifs) if valid]

    for file in set(ifs).difference(val_ifs):
        logger.error(INVALID_FILE_1.format(file.path))
    if not all(vals):
        logger.error(SRC_NO_IMG_FILE_1.format(src_path.name))
        shutil.rmtree(dst_dir, ignore_errors=True)
        if remove_src: shutil.rmtree(src_path, ignore_errors=True)
        return
    if not val_ifs:
        logger.warning(SKIP_EMPTY_SOURCE_0)
        shutil.rmtree(dst_dir, ignore_errors=True)
        if remove_src: shutil.rmtree(src_path, ignore_errors=True)
        return

    #* transcode/move files --------------------------------------------------------------------------------------------

    dsts: list[Path] = []
    jobs: list[tuple[Callable, tuple]] = []
    for img in val_ifs:
        match img.ext:
            case 'jpg'|'jpeg':
                dst = (dst_scans_dir / img.path.relative_to(src_path)).with_suffix('.jpg')
                jobs.append((tryHardlinkThenCopy, (img.path, dst)))
            case 'webp':
                dst = (dst_scans_dir / img.path.relative_to(src_path)).with_suffix('.webp')
                jobs.append((tryHardlinkThenCopy, (img.path, dst)))
            case 'png'|'bmp'|'tif'|'tiff':
                dst = dst_scans_dir / img.path.relative_to(src_path).with_suffix('.webp')
                jobs.append((toWebp, (img.path, dst)))
            case _:  #! we still copy the file since the user thinks the extension is of scans through `SD_IMG_EXTS`
                dst = dst_scans_dir / img.path.relative_to(src_path)
                jobs.append((tryHardlinkThenCopy, (img.path, dst)))
                if DEBUG: logger.debug(GOT_BUT_EXPECT_ONE_OF_2.format(img.ext, SD_IMG_EXTS))
                logger.info(GOT_UNSUPP_FILE_1.format(img.path))
        dsts.append(dst)

    succs = pool.map(_runJob, jobs)
    if DEBUG: assert len(succs) == len(val_ifs) == len(dsts)
    crc32_to_orig_path: dict[str, Path] = {getCRC32(dst): img.path for (img, dst, s) in zip(val_ifs, dsts, succs) if s}

    for img in (img for (img, succ) in zip(val_ifs, succs) if not succ):
        logger.error(FAILED_TO_HANDLE_FILE_1.format(img.path.relative_to(src_path)))
    if not all(succs):
        logger.warning(FAILED_TO_PROC_SOME_SCANS_0.format(src_path))

    #* clean dirs/filenames paths --------------------------------------------------------------------------------------

    try:
        condenseDirLayout(dst_scans_dir)
        cleanScansFilenames(dst_scans_dir, logger)
    except Exception as e:
        if DEBUG: traceback.print_exc()
        logger.error(UNEXP_ERR_IN_TIDYING_UP_2.format(dst_scans_dir, e))
        logger.warning(SD_SCANS_WILL_BE_REMOVED_0)
        if remove_src: shutil.rmtree(src_path, ignore_errors=True)
        shutil.rmtree(dst_scans_dir, ignore_errors=True)
        return

    #* record files to meta --------------------------------------------------------------------------------------------

    info_dicts: list[dict] = []
    for path in listFile(dst_scans_dir):
        crc32 = getCRC32(path)
        info_dicts.append({
            CRC32_CN: crc32,
            SD_ORIG_PATH_CN: crc32_to_orig_path[crc32].relative_to(src_path.parent),
            SD_PROC_PATH_CN: path.relative_to(dst_scans_dir),
            })
    # TODO: update it to orig:orig_crc32:dst:dst_crc32:custom

    csv_dicts = quotFields4CSV(info_dicts)
    if not writeCSV(info_csv_path, csv_dicts):
        logger.error(FAILED_TO_WRITE_INFO_CSV_1.format(info_csv_path))
    if remove_src: shutil.rmtree(src_path, ignore_errors=True)
    logger.info(PROCESSED_TO_1.format(dst_dir))




def procScanSrcList(src_paths: list[Path]):
    if DEBUG: assert src_paths, GOT_NO_INPUT_0
    dst_parent = initScansDraftDstParentDir(input_paths=src_paths, script_path=Path(__file__).parent.parent)
    if DEBUG: assert dst_parent.is_dir(), CANT_INIT_OUTPUT_DIR_0
    logger = initLogger(dst_parent / SD_LOG_FILENAME)
    logger.info(USING_SD_1.format(AC_VERSION))
    w = len(str(len(src_paths)))
    for i, src_path in enumerate(src_paths, start=1):
        dst_dir = dst_parent / SD_DIRNAME_3.format(TIMESTAMP, f'{i:0>{w}}', src_path.name)
        procScanSrc(src_path, dst_dir, logger)
        logger.info('')




def collectScansDirs(src_paths: Iterable[Path]):

    src_paths = list(src_paths)
    assert src_paths, GOT_NO_INPUT_0

    sp_csv_path = proposePath(src_paths, SP_CSV_FILENAME)
    try:
        sp_csv_path.parent.mkdir(parents=True, exist_ok=True)
        sp_csv_path.write_bytes(b'')
    except:
        print(CANT_CREATE_CSV_1.format(sp_csv_path))
        return

    sp_dicts: list[dict] = []
    for src_path in src_paths:

        print()
        print(PROCESSING_1.format(src_path))

        img_paths = listFile(src_path, ext=ALL_EXTS_IN_SCANS)
        if not img_paths:
            print(SP_SKIP_NO_IMG_DIR.format(src_path))
            continue

        sp_dicts.append({
            SP_DIRNAME_CN: '',
            SP_VOLNUM_CN: '',
            SP_COMPLEMENT_CN: '',
            SP_CUSTOM_NAME_CN: '',
            SP_SRC_PATH_CN: src_path.resolve().as_posix(),
            })

    sp_dicts = quotFields4CSV(sp_dicts)
    writeCSV(sp_csv_path, sp_dicts)




def placeScans(csv_path: Path):

    s, sp_dicts = readCSV(csv_path)
    if not s:
        print(CANT_CREATE_CSV_1.format(csv_path))
        return
    sp_dicts = unquotFields4CSV(sp_dicts)

    dst_root = csv_path.with_name(STD_BKS_DIRNAME)
    if dst_root.exists():
        print(DIR_EXISTS_DEL_FIRST_1.format(dst_root))
        return
    dst_root.mkdir(parents=True, exist_ok=True)

    for i, sp_dict in enumerate(sp_dicts, start=1):

        #* src_sd_dir ------------------------------------------------------------------------------

        src_sd_dir = Path(sp_dict[SP_SRC_PATH_CN])
        print(PROCESSING_1.format(src_sd_dir))

        #* dst_dirname -----------------------------------------------------------------------------

        dirname = normClassification(sp_dict.get(SP_DIRNAME_CN, ''))
        volnum = normDecimal(sp_dict.get(SP_VOLNUM_CN, ''))
        complement = normDesp(sp_dict.get(SP_COMPLEMENT_CN, ''))
        custom_name = rmInvalidChars(sp_dict.get(SP_CUSTOM_NAME_CN, ''))

        if DEBUG: print(f'SP-CSV-INPUT: {dirname=}, {volnum=}, {complement=}, {custom_name=}')

        if custom_name:
            dst_dirname = custom_name
        else:
            dst_dirname = ''
            dst_dirname += f'{dirname} ' if dirname else ''
            dst_dirname += f'Vol.{volnum} ' if volnum else ''
            dst_dirname += f'{complement}' if complement else ''
            dst_dirname = dst_dirname.strip()
        if not dst_dirname:
            print(SP_MISSING_DIRNAME_1.format(i))
            dst_dirname = f'Unknown {i}'

        #* sd_img_dir_path -------------------------------------------------------------------------

        if (src_sd_dir / STD_BKS_DIRNAME).is_dir():
            sd_img_dir_path = src_sd_dir / STD_BKS_DIRNAME
        else:
            sd_img_dir_path = src_sd_dir
        if not sd_img_dir_path.is_dir():
            print(SP_CANT_LOCATE_DIR_1.format(sd_img_dir_path))
            continue

        #* src_img_paths ---------------------------------------------------------------------------
        src_img_paths = listFile(sd_img_dir_path, ext=ALL_EXTS_IN_SCANS)
        if not src_img_paths:
            print(SP_CANT_FIND_IMG_1.format(sd_img_dir_path))
            continue

        #* crc2path_mapping ------------------------------------------------------------------------

        # crc2path: dict[str, Path] = {}
        # sd_info_csv_path = src_sd_dir / SD_INFO_CSV_FILENAME
        # if sd_info_csv_path.is_file():
        #     s, sd_dicts = readCSV(sd_info_csv_path)

        #     if not s: print(SP_CANT_READ_SD_CSV_1.format(sd_info_csv_path))
        #     sd_dicts = unquotFields4CSV(sd_dicts)

        #     for sd_dict in sd_dicts:
        #         crc32 = sd_dict.get(CRC32_CN, '')
        #         relpath = normFullLocation(sd_dict.get(SD_PROC_PATH_CN, '')).lstrip('/' + string.whitespace)
        #         if CRC32_BASIC_REGEX.fullmatch(crc32):
        #             crc2path[crc32] = sd_img_dir_path / relpath
        #     else:
        #         print(SP_WORK_WO_SD_0)

        #* -----------------------------------------------------------------------------------------

        # for img_path in src_img_paths:
        #     crc32 = getCRC32(img_path)
        #     if rel_path := crc2path.get(crc32):
        #         dst_img_path = dst_root / dst_dirname / rel_path
        #     else:
        #         dst_img_path = dst_root / dst_dirname / img_path.relative_to(sd_img_dir_path)
        #     if not tryHardlinkThenCopy(img_path, dst_img_path):
        #         print(SP_CANT_PLACE_IMG_2.format(img_path, dst_img_path))

        for img_path in src_img_paths:
            dst_img_path = dst_root / dst_dirname / img_path.relative_to(sd_img_dir_path)
            if not tryHardlinkThenCopy(img_path, dst_img_path):
                print(SP_CANT_PLACE_IMG_2.format(img_path, dst_img_path))




def getScansDirs(root: Path, logger: Logger) -> list[Path]:

    scans_dirs = [d for d in listDir(root) if d.name.lower() == STD_BKS_DIRNAME.lower()]
    if not scans_dirs:
        logger.warning(SR_FOUND_NO_BK_NAMED_DIR_2.format(STD_BKS_DIRNAME, root))
        scans_dirs = [root]

    ret = []
    for scans_dir in scans_dirs:
        if scans_dir == root:
            ret.append(scans_dir)
            break
        # avoid duplicated processing of scans dir under scans dir
        parent_has_scans = False
        for p in scans_dir.parent.relative_to(root).parts:
            if p.lower() == STD_BKS_DIRNAME.lower():
                parent_has_scans = True
                break
        if parent_has_scans: continue
        ret.append(scans_dir)
    return ret




def chkScans(root):

    logger = initLogger(log_path := root.parent.joinpath(SR_LOG_FILENAME))
    logger.info(USING_SR_1.format(AC_VERSION))
    logger.info(THE_INPUT_IS_1.format(root))

    if platform.system() == 'Windows':
        temp_dir = getTempDir4Hardlink(root)
        if temp_dir: logger.info(SR_ENABLED_HARDLINK_AND_TEMP_DIR_1.format(temp_dir))
        else: logger.info(SR_DISABLED_HARDLINK_0)
    else:
        temp_dir = None

    for scans_dir in getScansDirs(root, logger=logger):
        logger.info('')
        logger.info(CHECKING_1.format(scans_dir))
        logger.info(LISTING_FILES_0)
        files = filterScansFiles(scans_dir, logger=logger)
        logger.info(CHECKING_FILENAMES_0)
        chkScansNaming(scans_dir, logger=logger)
        logger.info(CHECKING_FILECONTENT_0)
        chkScansFiles(files, temp_dir, logger=logger)
        logger.info(SR_LOG_SCANS_SUMMARY_0)
        logScansSummary(scans_dir, files, logger=logger)
        logger.info('')

    logger.info(SR_ENDING_NOTE_1.format(log_path))

    try:
        if temp_dir and not list(temp_dir.iterdir()):
            temp_dir.rmdir()
            logger.info(REMOVED_TEMP_DIR_1.format(temp_dir))
    except OSError:
        pass

    logging.shutdown()
    return
