import shutil
import logging
from pathlib import Path

from configs import *
from langs import *
from utils import *
from .image import chkCfImage
from helpers.corefile import CF


__all__ = [
    'chkArcFile',
    'chkFontArcDir',
    'chkImageArcDir',
    ]




def chkArcFile(cf: CF, logger: logging.Logger, decompress: bool = True) -> bool:

    if cf.ext not in COMMON_ARCHIVE_EXTS:
        logger.error(GOT_UNKNOWN_ARC_EXT_1.format(cf.ext))
        return False
    if cf.ext not in VX_ARC_EXTS:
        logger.warning(UNSUPPORTED_EXT_TO_CHECK_1.format(cf.ext))
        return False
    if not tstArchive(cf.path):
        logger.warning(INVALID_FILE_1.format(cf.path))
        return False

    filenames = getFileList(cf.path)
    has_png, has_font = False, False
    for filename in filenames:
        if filename.lower().endswith(VX_IMG_EXTS): has_png = True
        if filename.lower().endswith(COMMON_FONT_EXTS): has_font = True
        if has_png and has_font: break

    ok = True

    if has_png and has_font:
        logger.error('The file contains both PNG and FONT files.')
        ok = False
    if not has_png and not has_font:
        logger.error('The file contains neither PNG nor FONT files.')
        ok = False

    if decompress and (has_png or has_font):
        temp_dir = TEMP_DIR_DECOMPRESS.joinpath(cf.path.name + TIMESTAMP)
        if not extractARC(cf.path, temp_dir):
            logger.error(FAILED_TO_DECOMPRESS_1.format(cf.path))
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False
        if has_png: ok = ok if chkImageArcDir(temp_dir, logger) else False
        if has_font: ok = ok if chkFontArcDir(temp_dir, logger) else False
        shutil.rmtree(temp_dir, ignore_errors=True)

    return ok




def chkFontArcDir(path: Path, logger: logging.Logger) -> bool:

    if not path.is_dir():
        return False

    ok = True
    all_files = listFile(path)
    all_font_files = listFile(path, ext=COMMON_FONT_EXTS)
    valid_font_files = getValidFontPaths(*all_font_files)

    if len(all_files) != len(all_font_files):
        logger.error('The archive file contains non-FONT files.')
        ok = False
    if len(all_font_files) != len(valid_font_files):
        logger.error('Some font files in the archive are NOT valid.')
        ok = False

    return ok




def chkImageArcDir(path: Path, logger: logging.Logger) -> bool:

    if not path.is_dir():
        return False

    ok = True
    all_files = listFile(path)
    all_image_files = listFile(path, ext=VX_IMG_EXTS)

    if len(all_files) != len(all_image_files):
        logger.error('The archive file contains non-PNG files.')
        ok = False
    for image_file in all_image_files:
        ok = ok if chkCfImage(CF(image_file), logger) else False

    return ok
