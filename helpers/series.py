from __future__ import annotations

from typing import Any
from pathlib import PurePath
from logging import Logger

from configs import *
from .naming import *
import helpers.season as hs


__all__ = [
    'Series',
    ]




class Series:

    def __init__(self, /, seasons: list[hs.Season]|None = None, logger: Logger|None = None, **kwargs: Any):

        self.__seasons: list[hs.Season] = []
        if seasons: self.add(seasons)

        self.__logger: Logger|None = logger
        # attach the naming fields of variable names to this instance

        setattr(self, GRPTAG_VAR, kwargs.pop(GRPTAG_VAR, ''))  # self.g
        setattr(self, TITLE_VAR, kwargs.pop(TITLE_VAR, ''))  # self.t
        setattr(self, SUFFIX_VAR, kwargs.pop(SUFFIX_VAR, ''))  # self.x
        self.dst_parent = self.dst_parent  # clean and make the path posix

        if logger: logger.debug('Unused kwargs: ' + ('|'.join(f'{k}={v}' for k, v in kwargs.items())))

    #* access init parameters ------------------------------------------------------------------------------------------

    @property
    def logger(self) -> Logger|None:
        return self.__logger

    @logger.setter
    def logger(self, logger: Logger|None):
        self.__logger = logger

    #* output ----------------------------------------------------------------------------------------------------------

    @property
    def dst_parent(self) -> str:
        return getattr(self, FULLPATH_VAR)

    @dst_parent.setter
    def dst_parent(self, path: str|PurePath):
        setattr(self, FULLPATH_VAR, PurePath(path).as_posix())

    @property
    def dstname(self) -> str:
        g = f'[{self.g}]'
        t = self.t
        x = f'[{x}]' if (x := self.x) else ''
        return f'{g} {t} {x}'.strip(string.whitespace + '/\\')

    @property
    def dst(self) -> str:
        '''The full path to the proposed output season dir.'''
        return PurePath(self.dst_parent).joinpath(self.dstname).as_posix()

    #* shortcut access to naming fields --------------------------------------------------------------------------------

    @property
    def g(self) -> str:
        if g := getattr(self, GRPTAG_VAR):
            return g
        if STD_GRPTAG:
            return STD_GRPTAG
        raise ValueError('No group tag is set.')

    @g.setter
    def g(self, grptag: str) -> None:
        setattr(self, GRPTAG_VAR, normFullGroupTag(grptag))

    @property
    def t(self) -> str:
        if t := getattr(self, TITLE_VAR):
            return t
        if FALLBACK_TITLE:
            return FALLBACK_TITLE
        raise ValueError('No title is set.')

    @t.setter
    def t(self, title: str) -> None:
        setattr(self, TITLE_VAR, normTitle(title))

    @property
    def x(self) -> str:
        return getattr(self, SUFFIX_VAR)

    @x.setter
    def x(self, suffix: str) -> None:
        setattr(self, SUFFIX_VAR, normFullSuffix(suffix))

    #* contained seasons -----------------------------------------------------------------------------------------------

    @property
    def seasons(self) -> list[hs.Season]:
        return self.__seasons[:]  # return a shallow copy so the user cant mess with the internal list

    def add(self, seasons: hs.Season|list[hs.Season], hook: bool = True) -> None:
        if isinstance(seasons, hs.Season):
            seasons = [seasons]
        for season in seasons:
            match ((season in self.__seasons), bool(hook)):
                case True, True:
                    season.parent = self
                case True, False:
                    pass
                case False, True:
                    self.__seasons.append(season)
                    season.parent = self
                case False, False:
                    self.__seasons.append(season)

    def remove(self, seasons: hs.Season|list[hs.Season], unhook: bool = True) -> None:
        if isinstance(seasons, hs.Season):
            seasons = [seasons]
        for season in seasons:
            for i, _season in enumerate(self.__seasons):
                if _season is season:
                    self.__seasons.pop(i)
                    if unhook:
                        if season.parent == self:
                            season.parent = None
                    break
