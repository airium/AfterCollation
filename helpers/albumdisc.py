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

from pymediainfo import Track

import helpers.albuminfo as hai


__all__ = ['AlbumDisc']


class AlbumDisc:

    def __init__(self):

        self.files : list[Path] = []
        self.catelog : str = ''
        self.edition : str = ''
        self.log_file: Path|None = None
        self.__parent : hai.AlbumInfo|None = None

    @property
    def parent(self) -> hai.AlbumInfo|None:
        return self.__parent

    @parent.setter
    def parent(self, season: hai.AlbumInfo|None):
        self.__parent = season

    @property
    def credit(self) -> str:
        return '; '.join(self.credits)

    @property
    def date(self) -> str:
        if self.parent:
            return self.parent.date
        return ''


    @property
    def freq(self) -> str:
        sdd

    @property
    def bit(self) -> str:
        sdd

    @property
    def lossless(self) -> bool:


class JointDisc(AlbumDisc):


    pass


class SplitDisc(AlbumDisc):
    pass


class HiResDisc(SplitDisc):
