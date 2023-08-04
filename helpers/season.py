from logging import Logger

from configs.runtime import *
from .corefile import CoreFile


__all__ = ['Season']




class Season: # TODO this is currently a very early class, to be improved in the future

    def __init__(self, logger:Logger|None=None, **kwargs:str):

        for v in VND_BASE_LINE_USER_DICT.values():
            setattr(self, v, kwargs.get(v, ''))
        if logger: logger.debug('Unknown season class input: ' + ('|'.join(f'{k}={v}' for k, v in kwargs.items())))
        self.cfs : list[CoreFile] = []


    @property
    def p(self) -> str:
        return getattr(self, FULLPATH_VAR, '')
    @p.setter
    def p(self, v:str) -> None:
        setattr(self, FULLPATH_VAR, v)
    @property
    def g(self) -> str:
        return getattr(self, GRPTAG_VAR, '')
    @g.setter
    def g(self, v:str) -> None:
        setattr(self, GRPTAG_VAR, v)
    @property
    def s(self) -> str:
        return getattr(self, SHOWNAME_VAR, '')
    @s.setter
    def s(self, v:str) -> None:
        setattr(self, SHOWNAME_VAR, v)
    @property
    def x(self) -> str:
        return getattr(self, SUFFIX_VAR, '')
    @x.setter
    def x(self, v:str) -> None:
        setattr(self, SUFFIX_VAR, v)
