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

        self.__seasons: set[hs.Season] = set()
        if seasons: self.add(seasons)

        self.__logger: Logger|None = logger
        # attach the naming fields of variable names to this instance

        setattr(self, GRPTAG_VAR, kwargs.pop(GRPTAG_VAR, ''))  # self.g
        setattr(self, TITLE_VAR, kwargs.pop(TITLE_VAR, ''))  # self.t
        setattr(self, SUFFIX_VAR, kwargs.pop(SUFFIX_VAR, ''))  # self.x
        setattr(self, FULLPATH_VAR, kwargs.pop(FULLPATH_VAR, ''))  # self.dst_parent
        self.dst_parent = self.dst_parent  # clean and make the path posix

        if kwargs and logger: logger.debug('Unused kwargs: ' + ('|'.join(f'{k}={v}' for k, v in kwargs.items())))

    #* access logger ---------------------------------------------------------------------------------------------------

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
    def name(self) -> str:
        g = f'[{self.g}]'
        t = self.t
        x = f'[{x}]' if (x := self.x) else ''
        return f'{g} {t} {x}'.strip(string.whitespace + '/\\')

    @property
    def dst(self) -> str:
        '''The full path to the proposed output season dir.'''
        return PurePath(self.dst_parent).joinpath(self.name).as_posix()

    #* shortcut access to naming fields --------------------------------------------------------------------------------

    @property
    def g(self) -> str:
        if g := getattr(self, GRPTAG_VAR):
            return g
        if STD_GRPTAG:
            return STD_GRPTAG
        raise ValueError('No group tag is set.')

    @g.setter
    def g(self, grptag: str):
        setattr(self, GRPTAG_VAR, normFullGroupTag(grptag))

    @property
    def t(self) -> str:
        if t := getattr(self, TITLE_VAR):
            return t
        if FALLBACK_TITLE:
            return FALLBACK_TITLE
        raise ValueError('No title is set.')

    @t.setter
    def t(self, title: str):
        setattr(self, TITLE_VAR, normTitle(title))

    @property
    def x(self) -> str:
        return getattr(self, SUFFIX_VAR)

    @x.setter
    def x(self, suffix: str):
        setattr(self, SUFFIX_VAR, normFullSuffix(suffix))

    #* contained seasons -----------------------------------------------------------------------------------------------

    @property
    def seasons(self) -> list[hs.Season]:
        return list(self.__seasons)

    def add(self, seasons: hs.Season|list[hs.Season], hook: bool = True):
        if isinstance(seasons, hs.Season):
            seasons = [seasons]
        for season in seasons:
            self.__seasons.add(season)
            if hook: season.parent = self

    def remove(self, seasons: hs.Season|list[hs.Season], unhook: bool = True):
        if isinstance(seasons, hs.Season):
            seasons = [seasons]
        for season in seasons:
            self.__seasons.discard(season)
            if unhook and season.parent == self:
                season.parent = None
