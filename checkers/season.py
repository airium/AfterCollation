import logging
from pathlib import Path

from utils import FI
from configs.runtime import *

from .tracks import *
from .video import *
from .audio import *
from .image import *
from .text import *
from .menu import *
from .archive import *
from .fonts import *

import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm


__all__ = ['chkFile', 'chkFiles', 'chkSeasonNaming']




def chkFile(fi:FI, logger:logging.Logger):

    logger.info(f'Checking "{fi.path}" ...')
    if not chkContainer(fi, logger):
        return
    match fi.ext:
        case 'mkv'|'mp4':
            chkTracks(fi, logger)
            chkVideoTracks(fi, logger)
            chkAudioTracks(fi, logger)
            chkMenuTracks(fi, logger)
            chkTextTracks(fi, logger)
        case 'mka':
            chkTracks(fi, logger)
            chkAudioTracks(fi, logger)
        case 'flac':
            chkTracks(fi, logger)
            chkAudioTracks(fi, logger)
        case 'png':
            chkTracks(fi, logger)
            chkImageTracks(fi, logger)
        case 'ass':
            chkAssFile(fi, logger)
        case '7z'|'zip'|'rar':
            chkImageArcFile(fi, logger)
            chkFontArcFile(fi, logger)
        case _:
            logger.error(f'Got "{fi.ext}" but {VNx_ALL_EXTS=}.')




def chkFiles(fis:list[FI], logger:logging.Logger):

    with logging_redirect_tqdm([logger]):
        pbar = tqdm.tqdm(total=len(fis), desc='Checking', unit='file', unit_scale=False, ascii=True, dynamic_ncols=True)
        for fi in fis:
            if fi.ext in VNx_ALL_EXTS:
                chkFile(fi, logger=logger)
            else:
                logger.error(f'"{fi.ext}" is not a valid extension to check.')
            pbar.update(1)
        pbar.close()




def chkSeasonNaming(input_dir:Path, logger:logging.Logger):
    pass
