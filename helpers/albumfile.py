from __future__ import annotations

from pathlib import Path

import shutil
import itertools
import traceback
from pathlib import Path
from logging import Logger
from typing import Iterable, Callable, Optional, Any
from operator import attrgetter
from multiprocessing import Pool

from langs import *
from utils import *
from configs import *
import configs.runtime as cr
from .misc import handleResourceSrc
from .image import ImageFile
from .scans import cleanScansFilenames
from .naming import *
from .dirgetter import proposeFilePath

import helpers.album as ha
import helpers.albuminfo as hai

from pymediainfo import Track


__all__ = [
    'AlbumFile',
    ]




class AlbumFile:

    '''AlbumFile is a wrapper over MediaInfo, providing easier access to mediainfo.'''

    def __init__(self, path: Path|str):

        if not (path := Path(path).resolve()).is_file():
            raise FileNotFoundError(CANT_FIND_SRC_FOR_ALBUMFILE_1.format(path))
        self.__path: Path = path
        self.__mediainfo: MediaInfo = getMediaInfo(path)
        self.__ffprobe: dict|None = None
        self.__crc32: str|None = None

    #* built-in methods override ---------------------------------------------------------------------------------------

    def __getattr__(self, __name: str) -> Any:
        return getattr(self.__mediainfo, __name)

    def __getstate__(self) -> dict:
        return self.__dict__

    def __setstate__(self, state: dict):
        self.__dict__.update(state)

    #* input -----------------------------------------------------------------------------------------------------------

    @property
    def path(self) -> Path:
        return self.__path

    @property  # NOTE no setter for read-only path
    def src(self) -> str:
        return self.__path.resolve().as_posix()

    @property
    def srcname(self) -> str:
        return self.__path.name

    #* crc32 -----------------------------------------------------------------------------------------------------------

    @property
    def crc32(self) -> str:
        if not self.__crc32: self.__crc32 = getCRC32(self.path, prefix='', pass_not_found=True)
        return self.__crc32

    @property
    def crc(self) -> str:
        return self.crc32

    #* basic file info -------------------------------------------------------------------------------------------------

    @property
    def size(self) -> int:
        return self.path.stat().st_size

    @property
    def suffix(self) -> str:
        return self.path.suffix

    @property
    def ext(self) -> str:
        return self.suffix.lower().lstrip('.')

    @property
    def format(self) -> str:
        return fmt.lower() if (fmt := self.gtr.format) else self.ext

    #* file type -------------------------------------------------------------------------------------------------------

    @property
    def gtr(self) -> Track:
        return self.__mediainfo.general_tracks[0]

    @property
    def vtr(self) -> Track:
        return self.__mediainfo.video_tracks[0]

    @property
    def atr(self) -> Track:
        return self.__mediainfo.audio_tracks[0]

    @property
    def itr(self) -> Track:
        return self.__mediainfo.image_tracks[0]

    @property
    def has_video(self) -> bool:
        return bool(self.__mediainfo.video_tracks)

    @property
    def has_audio(self) -> bool:
        return bool(self.__mediainfo.audio_tracks)

    @property
    def has_image(self) -> bool:
        return bool(self.__mediainfo.image_tracks)

    @property
    def is_video(self) -> bool:
        return (self.ext in COMMON_VIDEO_EXTS) and self.has_video

    @property
    def is_image(self) -> bool:
        return (self.ext in COMMON_IMAGE_EXTS) and self.has_image

    @property
    def is_audio(self) -> bool:
        return (self.ext in COMMON_AUDIO_EXTS) and self.has_audio

    @property
    def is_text(self) -> bool:
        if self.tracks[1:]: return True
        return False

    @property
    def text(self) -> str:
        return self.path.read_text(encoding='utf-8-sig')

    @property
    def is_valid(self) -> bool:
        if not self.is_audio: return False
        if self.format != EXTS2FORMATS.get(self.ext): return False
        if not tstFFmpegDecode(self.path): return False
        return True

    @property
    def is_hires(self) -> bool:
        return self.hr_bit > 0 or self.hr_freq > 0

    @property
    def bit(self) -> int:
        if self.atr:
            if self.atr.bit_depth:
                return self.atr.bit_depth
        return 0
