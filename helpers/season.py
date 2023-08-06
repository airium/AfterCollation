from __future__ import annotations

from typing import Any
from pathlib import Path
from logging import Logger

from configs import *
import helpers.corefile as hc


__all__ = ['Season']




class Season:

    def __init__(
        self,
        /,
        core_files: list[hc.CoreFile]|None = None,
        quality_label: str|None = None,
        logger: Logger|None = None,
        **kwargs: Any
        ):

        self.__cfs: list[hc.CoreFile] = []
        if core_files:
            self.add(core_files)

        self.__fixed_qlabel: str|None = quality_label if quality_label else None
        if logger:
            logger.info(f'Using fixed season quality label: "{quality_label}".')
        self.__cached_qlabel: str|None = None

        self.__logger: Logger|None = logger

        # attach the naming fields of variable names to this instance
        for v in VND_BASE_LINE_USER_DICT.values():
            setattr(self, v, kwargs.pop(v, ''))
        self.dst_parent = self.dst_parent  # clean and make the path resolved

        if logger:
            logger.debug('Input leftover: ' + ('|'.join(f'{k}={v}' for k, v in kwargs.items())))


    #* access init parameters ------------------------------------------------------------------------------------------

    @property
    def cfs(self) -> list[hc.CoreFile]:
        return self.__cfs

    @property
    def logger(self) -> Logger|None:
        return self.__logger

    @logger.setter
    def logger(self, logger: Logger|None) -> None:
        self.__logger = logger

    @property
    def dst_parent(self) -> str:
        return getattr(self, FULLPATH_VAR, '')

    @dst_parent.setter
    def dst_parent(self, path: str|Path) -> None:
        setattr(self, FULLPATH_VAR, Path(path).resolve().as_posix())

    @property
    def qlabel(self) -> str:
        if self.__fixed_qlabel is not None:
            return self.__fixed_qlabel
        if self.__cached_qlabel is not None:
            return self.__cached_qlabel
        qlabels: list[str] = [cf.qlabel for cf in self.cfs if (cf.has_video and (cf.l in ('', '/')))]
        if qlabels:
            qlabel = max(qlabels, key=qlabels.count)
        else:
            qlabel = ''
            if self.__logger:
                self.__logger.warning('This season has no video at its root, so will have no quality label.')
        self.__cached_qlabel = qlabel
        return qlabel

    @qlabel.setter
    def qlabel(self, qlabel: str|None) -> None:
        # TODO: do cleaning and checking for the input
        self.__fixed_qlabel = qlabel
        if (qlabel is not None) and self.__logger:
            self.__logger.info(f'Using fixed season quality label: "{qlabel}".')

    @property
    def dst(self) -> str:
        '''The full path to the proposed output season dir.'''
        return Path(self.dst_parent).joinpath(self.dstname).as_posix()

    #* shotcut access to naming fields ---------------------------------------------------------------------------------

    @property
    def g(self) -> str:
        return ret if (ret := getattr(self, GRPTAG_VAR, '')) else STD_GRPTAG

    @g.setter
    def g(self, v: str) -> None:
        # TODO: do cleaning and checking for the input
        setattr(self, GRPTAG_VAR, v)

    @property
    def t(self) -> str:
        return ret if (ret := getattr(self, TITLE_VAR, '')) else FALLBACK_TITLE

    @t.setter
    def t(self, v: str) -> None:
        # TODO: do cleaning and checking for the input
        setattr(self, TITLE_VAR, v)

    @property
    def x(self) -> str:
        return getattr(self, SUFFIX_VAR, '')

    @x.setter
    def x(self, v: str) -> None:
        # TODO: do cleaning and checking for the input
        setattr(self, SUFFIX_VAR, v)

    @property
    def dstname(self) -> str:
        g = f'[{self.g}]'
        s = self.t
        q = f'[{q}]' if (q := self.qlabel) else ''
        x = f'[{x}]' if (x := self.x) else ''
        return f'{g} {s} {q}'.strip(string.whitespace + '/\\')

    #* methods ---------------------------------------------------------------------------------------------------------

    def add(self, cfs: hc.CoreFile|list[hc.CoreFile], hook: bool = True) -> None:
        self.__cached_qlabel = None  # need to re-generate the quality label if any file added
        if isinstance(cfs, hc.CoreFile):
            cfs = [cfs]
        for cf in cfs:
            if not (cf in self.__cfs):
                self.__cfs.append(cf)
                if hook: cf.season = self

    def remove(self, cfs: hc.CoreFile|list[hc.CoreFile], unhook: bool = True) -> None:
        self.__cached_qlabel = None  # need to re-generate the quality label if any file removed
        if isinstance(cfs, hc.CoreFile):
            cfs = [cfs]
        for cf in cfs:
            for i, _cf in enumerate(self.__cfs):
                if _cf is cf:
                    self.__cfs.pop(i)
                    if unhook: cf.season = None
                    break
