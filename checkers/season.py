import logging
from pathlib import Path

from utils import FI

from .video import *
from .audio import *
from .image import *
from .text import *
from .menu import *
from .archive import *
from .fonts import *




def chkSeasonFiles(fis:list[FI], logger:logging.Logger):
    '''Check whether the media files meet the restriction in the standard.'''

    [chkVideoFI(fi, logger) for fi in fis if fi.has_video]
    [chkAudioFI(fi, logger) for fi in fis if fi.has_audio]
    [chkTextFI(fi, logger) for fi in fis if fi.has_text]
    [chkImage(fi, logger) for fi in fis if fi.has_image]
    [chkMenu(fi, logger) for fi in fis if fi.has_menu]
    [chkFontArcFile(fi, logger) for fi in fis if fi.ext in VNx_ARC_EXTS]
    [chkImageArcFile(fi, logger) for fi in fis if fi.ext in VNx_ARC_EXTS]
    [chkAssFile(fi, logger) for fi in fis if fi.ext in VNx_SUB_EXTS]




def chkSeasonNaming(input_dir:Path, logger:logging.Logger):
    pass