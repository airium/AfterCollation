from __future__ import annotations

import itertools
from typing import Any
from pathlib import Path
from logging import Logger


from utils import *
from configs import *
from .parser import *
from .naming import *
from .misc import *
import helpers.corefile as hc



__all__ = [
    'Season',
    'applyNamingDicts',
    'fromSeasonDir',
    ]




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




def applyNamingDicts(
    season: Season,
    default_dict: dict[str, str],
    naming_dicts: list[dict[str, str]],
    logger: Logger
    ):
    '''
    Do a plain copy from the user input (VND.csv) to our internal data structure (Season).
    However, we will fill some empty fields with default values if not specified.

    #! Before calling this function, you should better call `cleanNamingDicts()` and `chkNamingDicts()` first.
    '''

    cfs = season.cfs
    if DEBUG: assert len(cfs) == len(naming_dicts)

    logger.info('Applying naming plan ...')

    if default_dict[GRPTAG_VAR]:
        season.g = default_dict[GRPTAG_VAR]
    else:
        grptags = [naming_dict[GRPTAG_VAR] for naming_dict in naming_dicts]
        if all(grptags):
            season.g = max(set(grptags), key=grptags.count)
            logger.info('Found empty base/default group tag but this is filled for each file. '
                        f'The program assumed the most common "{season.g}" as the title for the root dir. '
                        'You should better recheck this.')
        else:
            season.g = STD_GRPTAG
            logger.info(f'Found empty base/default group tag. The program filled it with the standard "{STD_GRPTAG}".')

    if default_dict[TITLE_VAR]:
        season.t = default_dict[TITLE_VAR]
    else:
        titles = [naming_dict[TITLE_VAR] for naming_dict in naming_dicts]
        if any(titles):
            season.t = max(set(titles), key=titles.count)
            logger.info('Found empty base/default show name but this is filled for each file. '
                        f'The program assumed the most common "{season.t}" as the show name for the root dir. '
                        'You should better recheck this.')
        else:
            season.t = FALLBACK_TITLE
            logger.info('Found empty base/default show name everywhere. '
                        'The program cannot guess this for you, so filled it with a mystery value.')

    season.x = default_dict[SUFFIX_VAR]
    # season.dst = default_dict[FULLPATH_VAR]

    for i, cf, naming_dict in zip(itertools.count(), cfs, naming_dicts):
        logger.info(f'Applying naming plan for "{cf.crc}" ...')

        cf.g = naming_dict[GRPTAG_VAR] if naming_dict[GRPTAG_VAR] else season.g
        if cf.g != season.g:
            logger.warning('Using non-default group tag.')

        cf.t = naming_dict[TITLE_VAR] if naming_dict[TITLE_VAR] else season.t
        if cf.t != season.t:
            logger.warning('Using non-default title.')

        if naming_dict[FULLDESP_VAR]:
            if m := re.match(CRC32_CSV_FIELD_REGEX, naming_dict[FULLDESP_VAR]):
                crc32 = m.group('crc32').lower()
                for ref_cf in (cfs[:i] + cfs[i+1:]):
                    if ref_cf.crc32.lower() == crc32:
                        cf.depends = ref_cf
                        logger.info(f'Set file 0x{cf.crc32} to copy/link the naming of file 0x{ref_cf.crc32}.')
                        break
                if not cf.depends:
                    logger.error(f'Failed to find the appointed file 0x{crc32} to copy/link the naming from.')
            else:
                if any((naming_dict[CLASSIFY_VAR],
                        naming_dict[IDX1_VAR],
                        naming_dict[IDX2_VAR],
                        naming_dict[SUPPLEMENT_VAR])):
                    logger.warning('Found using customised description. '
                                   'Will clear classification, main/sub index and supplement fields.')
                cf.f = naming_dict[FULLDESP_VAR]
        else:
            cf.c = naming_dict[CLASSIFY_VAR]
            cf.i1 = naming_dict[IDX1_VAR]
            cf.i2 = naming_dict[IDX2_VAR]
            cf.s = naming_dict[SUPPLEMENT_VAR]

        cf.l = STD_SPS_DIRNAME if (cf.c and not naming_dict[LOCATION_VAR]) else ''

        # possible suffix cases:
        # 1. root has no suffix or a non-lang-suffix like [Lite]:
        # if (not default_dict[SUFFIX_VAR]) or (default_dict[SUFFIX_VAR] not in AVAIL_SUB_LANG_TAGS):
        #     pass # dont touch any file suffix, as the files are free to use any suffix is this case (at least here)
        # 2. root has a language suffix like [CHS], files should have the same suffix
        if season.x and (season.x in AVAIL_SEASON_LANG_SUFFIXES):
            cf.x = season.x
            if naming_dict[SUFFIX_VAR]:
                logger.warning(f'Overridden suffix with the base/default language suffix "{default_dict[SUFFIX_VAR]}".')
        # #! there is a missing case above: root is missing language tag, but videos have language tags
        # #! since the default_dict will be disposed after this function and wont get checked afterwards
        # #! we need to catch it now
        # if cf.e in VNx_WITH_AUD_EXTS and not default_dict[SUFFIX_VAR]:
        #     logger.warning('Found video with language tag, but the root/default dir is missing language tag.')




def fromSeasonDir(season_dir: Path, logger: Logger) -> Season|None:

    paths = filterOutCDsScans(listFile(season_dir, ext=VNx_ALL_EXTS, rglob=True))

    default_dict: dict[str, str] = d if (d := parseSeasonDirName(season_dir, logger=logger)) else {}
    if not default_dict: return None

    naming_dicts: list[dict[str, str]] = []
    for path in paths:
        if not (d := parseCoreFileName(path, location=path.relative_to(season_dir).as_posix(), logger=logger)):
            return None
        naming_dicts.append(d)

    season = Season()
    season.add(hc.toCoreFilesWithTqdm(paths, logger=logger, mp=getCRC32MultiProc(paths)))
    cleanNamingDicts(default_dict, naming_dicts, logger)
    applyNamingDicts(season, default_dict, naming_dicts, logger)
    decomposeFullDesp(season, logger)
    return season
