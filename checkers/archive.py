import logging
from utils.archive import *
from utils.fileinfo import FI
from utils.fileutils import listFile
from utils.fontutils import getValidFontPaths
from configs import *

from .image import chkImage


__all__ = ['chkFontArcFile', 'chkImageArcFile']




def _chkArcFile(fi:FI, logger:logging.Logger, decode:bool=True) -> bool:

    if fi.ext not in COMMON_ARCHIVE_EXTS:
        logger.error('The file is not an archive file.')
        return False

    expected_format = EXTS2FORMATS.get(fi.ext)
    if not expected_format:
        logger.warning(f'Unhandled audio file extension "{fi.ext}".')
    if expected_format != fi.gtr.format:
        logger.error(f'The actual media format "{fi.gtr.format}" mismatched file ext "{fi.ext}".')
        return False

    if fi.ext not in VNx_ARC_EXTS:
        logger.warning(f'The checker is not designed to check the file type "{fi.ext}". Stopping archive check.')
        return False

    if not tstDecompressArchives(fi.path):
        logger.error('The archive file cannot be decompressed.')
        return False

    return True



def chkFontArcFile(fi:FI, logger:logging.Logger):

    if not _chkArcFile(fi, logger):
        return

    if not (path := decompressArchives(fi.path)):
        # NOTE this should be never reached as we checked it in _chkArcFile()
        logger.error('Failed to decompress the archive file.')
        return

    all_files = listFile(path)
    all_font_files = listFile(path, ext=COMMON_FONT_EXTS)
    if len(all_files) != len(all_font_files):
        logger.error('The archive file contains non-font files.')

    valid_font_files = getValidFontPaths(*all_font_files)
    if len(all_font_files) != len(valid_font_files):
        logger.error('Some font files in the archive are NOT valid.')




def chkImageArcFile(fi:FI, logger:logging.Logger):

    if not _chkArcFile(fi, logger):
        return

    if not (path := decompressArchives(fi.path)):
        # NOTE this should be never reached as we checked it in _chkArcFile()
        logger.error('Failed to decompress the archive file.')
        return

    all_files = listFile(path)
    all_image_files = listFile(path, ext=VNx_IMG_EXTS)
    if len(all_files) != len(all_image_files):
        logger.error('The archive file contains non-PNG files.')

    for image_file in all_image_files:
        chkImage(FI(image_file), logger)

