# from __future__ import annotations

# import re
from typing import Any
from pathlib import Path

from utils import *
from configs import *
from pymediainfo import Track


__all__ = [
    'ImageFile',
    ]




class ImageFile:

    '''ImageFile is a wrapper over MediaInfo, providing easier access to mediainfo.'''

    def __init__(
        self,
        path: Path|str,
        ):

        if not (path := Path(path).resolve()).is_file():
            raise FileNotFoundError(f'Cannot find the file "{path}" to init an ImageFile instance.')
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
    def itr(self) -> Track:
        return self.__mediainfo.image_tracks[0]

    @property
    def has_image(self) -> bool:
        return bool(self.__mediainfo.image_tracks)

    @property
    def is_image(self) -> bool:
        return (self.ext in COMMON_IMAGE_EXTS) and self.has_image

    @property
    def is_valid(self) -> bool:
        if not self.is_image: return False
        if self.format != EXTS2FORMATS.get(self.ext): return False
        if not tstFFmpegDecode(self.path): return False
        return True

    @property
    def ffprobe(self) -> dict:
        if self.__ffprobe == None: self.__ffprobe = FFprobe(self.path)
        return self.__ffprobe

    #* mediainfo -------------------------------------------------------------------------------------------------------

    @property
    def width(self) -> int:
        if self.is_image:
            if self.format == 'webp':
                return self.ffprobe.get('streams', [{}])[0].get('width', 0)
            else:
                return int(self.itr.width) if self.itr.width else 0
        else:
            return 0

    @property
    def height(self) -> int:
        if self.is_image:
            if self.format == 'webp':
                return self.ffprobe.get('streams', [{}])[0].get('height', 0)
            else:
                return int(self.itr.height) if self.itr.height else 0
        else:
            return 0
