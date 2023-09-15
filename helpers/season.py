from __future__ import annotations

import itertools
from typing import Any, Iterable
from logging import Logger
from pathlib import Path, PurePath

from utils import *
from langs import *
from configs import *
from .parser import *
from .misc import *

import helpers.naming as hnm
import helpers.corefile as hcf
import helpers.series as hsr
import helpers.misc as hms


__all__ = [
    'Season',
    'applyNamingDicts',
    'fromSeasonDir',
    ]




class Season:

    def __init__(
        self,
        /,
        files: list[hcf.CoreFile]|None = None,
        series: hsr.Series|None = None,
        quality: str|None = None,
        logger: Logger|None = None,
        **kwargs: Any
        ):

        self.__cfs: list[hcf.CoreFile] = list()
        if files: self.add(files)

        self.__series: hsr.Series|None = series

        self.__fixed_qlabel: str|None = quality.strip() if quality else None
        self.__cached_qlabel: str|None = None
        if logger: logger.info(f'Using fixed season quality label: "{quality}".')

        self.__logger: Logger|None = logger

        # attach the naming fields of variable names to this instance

        setattr(self, FULLPATH_VAR, kwargs.pop(FULLPATH_VAR, ''))  # self.dst_parent
        setattr(self, GRPTAG_VAR, kwargs.pop(GRPTAG_VAR, ''))  # self.g
        setattr(self, TITLE_VAR, kwargs.pop(TITLE_VAR, ''))  # self.t
        setattr(self, SUFFIX_VAR, kwargs.pop(SUFFIX_VAR, ''))  # self.x
        self.dst_parent = self.dst_parent  # clean and make the path posix

        if kwargs and logger: logger.debug(UNUSED_KWARGS_1.format('|'.join(f'{k}={v}' for k, v in kwargs.items())))

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
        return getattr(self, FULLPATH_VAR, '')

    @dst_parent.setter
    def dst_parent(self, path: str|PurePath):
        setattr(self, FULLPATH_VAR, PurePath(path).as_posix())

    @property
    def name(self) -> str:
        g = f'[{self.g}]'
        s = self.t
        q = f'[{q}]' if (q := self.qlabel) else ''
        x = f'[{x}]' if (x := self.x) else ''
        return f'{g} {s} {q}{x}'.strip(string.whitespace + '/\\')

    @property
    def dst(self) -> str:
        '''The full path to the proposed output season dir.'''
        return PurePath(self.dst_parent).joinpath(self.name).as_posix()

    #* parent series ---------------------------------------------------------------------------------------------------

    @property
    def parent(self) -> hsr.Series|None:
        return self.__series

    @parent.setter
    def parent(self, series: hsr.Series|None):
        self.__series = series

    #* shortcut access to naming fields --------------------------------------------------------------------------------

    @property
    def g(self) -> str:
        if g := getattr(self, GRPTAG_VAR):
            return g
        if self.parent:
            return self.parent.g
        if STD_GRPTAG:
            return STD_GRPTAG
        raise ValueError('No group tag is set.')

    @g.setter
    def g(self, grptag: str):
        # TODO: do cleaning and checking for the input
        setattr(self, GRPTAG_VAR, hnm.normFullGroupTag(grptag))

    @property
    def t(self) -> str:
        if t := getattr(self, TITLE_VAR):
            return t
        if self.parent:
            return self.parent.t
        if FALLBACK_TITLE:
            return FALLBACK_TITLE
        raise ValueError('No title is set.')

    @t.setter
    def t(self, title: str):
        # TODO: do cleaning and checking for the input
        setattr(self, TITLE_VAR, hnm.normTitle(title))

    @property
    def x(self) -> str:
        return getattr(self, SUFFIX_VAR)

    @x.setter
    def x(self, suffix: str):
        # TODO: do cleaning and checking for the input
        setattr(self, SUFFIX_VAR, hnm.normFullSuffix(suffix))

    #* methods ---------------------------------------------------------------------------------------------------------

    @property
    def qlabel(self) -> str:
        if self.__fixed_qlabel != None:
            return self.__fixed_qlabel
        if self.__cached_qlabel != None:
            return self.__cached_qlabel
        candidates: list[str] = [cf.qlabel for cf in self.files if (cf.has_video and (cf.l in ('', '/')))]
        if candidates:
            qlabel = max(candidates, key=candidates.count)
        else:
            qlabel = ''
            if self.__logger:
                self.__logger.warning(VP_SEASON_HAS_NO_VID_0)
        self.__cached_qlabel = qlabel
        return qlabel

    @qlabel.setter
    def qlabel(self, qlabel: str|None):
        self.__fixed_qlabel = qlabel  # TODO: do cleaning and checking for the input
        if (qlabel is not None) and self.__logger:
            self.__logger.info(VP_USING_FIXED_SEASON_QLABEL_1.format(qlabel))

    #* contained corefiles ---------------------------------------------------------------------------------------------

    @property
    def files(self) -> list[hcf.CoreFile]:
        return self.__cfs[:]

    def add(self, files: hcf.CoreFile|Iterable[hcf.CoreFile], hook: bool = True):
        self.__cached_qlabel = None  # need to re-generate the quality label if any file added
        if isinstance(files, hcf.CoreFile):
            files = [files]
        for file in files:
            self._add(file)
            if hook: file.parent = self

    def _add(self, cf: hcf.CoreFile):
        if cf not in self.__cfs:
            self.__cfs.append(cf)

    def remove(self, files: hcf.CoreFile|list[hcf.CoreFile], unhook: bool = True):
        self.__cached_qlabel = None  # need to re-generate the quality label if any file removed
        if isinstance(files, hcf.CoreFile):
            files = [files]
        for file in files:
            self._remove(file)
            if unhook and file.parent == self:
                file.parent = None

    def _remove(self, cf: hcf.CoreFile):
        if cf in self.__cfs:
            self.__cfs.remove(cf)




def applyNamingDicts(season: Season, default_dict: dict[str, str], naming_dicts: list[dict[str, str]], logger: Logger):
    '''
    Do a plain copy from the user input (VD.csv) to our internal data structure (Season).
    However, we will fill some empty fields with default values if not specified.

    #! Before calling this function, you should better call `cleanNamingDicts()` and `chkNamingDicts()` first.
    '''

    cfs = season.files
    if DEBUG: assert len(cfs) == len(naming_dicts)

    # logger.info('Applying naming plan ...')

    if default_dict[GRPTAG_VAR]:
        season.g = default_dict[GRPTAG_VAR]
    else:
        grptags = [naming_dict[GRPTAG_VAR] for naming_dict in naming_dicts]
        if all(grptags):
            season.g = max(set(grptags), key=grptags.count)
            logger.info(VP_GOT_ONLY_EMPTY_BASE_GRPTAG_1.format(season.g))
        else:
            season.g = STD_GRPTAG
            logger.info(VP_GOT_ALL_EMPTY_BASE_GRPTAG_1.format(STD_GRPTAG))

    if default_dict[TITLE_VAR]:
        season.t = default_dict[TITLE_VAR]
    else:
        titles = [naming_dict[TITLE_VAR] for naming_dict in naming_dicts]
        if any(titles):
            season.t = max(set(titles), key=titles.count)
            logger.info(VP_GOT_ONLY_EMPTY_BASE_TITLE_1.format(season.t))
        else:
            season.t = FALLBACK_TITLE
            logger.info(VP_GOT_ALL_EMPTY_BASE_GRPTAG_0)

    season.x = default_dict[SUFFIX_VAR]
    # season.dst = default_dict[FULLPATH_VAR]

    for i, cf, naming_dict in zip(itertools.count(), cfs, naming_dicts):
        logger.info(VP_APPLYING_NAMING_PLAN_FOR_1.format(cf.crc32))

        cf.g = naming_dict[GRPTAG_VAR] if naming_dict[GRPTAG_VAR] else season.g
        if cf.g != season.g:
            logger.warning(USING_NON_DEFAULT_GRPTAG_0)

        cf.t = naming_dict[TITLE_VAR] if naming_dict[TITLE_VAR] else season.t
        if cf.t != season.t:
            logger.warning(USING_NON_DEFAULT_TITLE_0)

        if naming_dict[FULLDESP_VAR]:
            if m := re.match(CRC32_CSV_FIELD_REGEX, naming_dict[FULLDESP_VAR]):
                crc32 = m.group('crc32').lower()
                for ref_cf in (cfs[:i] + cfs[i + 1:]):
                    if ref_cf.crc32.lower() == crc32:
                        cf.depends = ref_cf
                        logger.info(SET_NAMING_LINKAGE_2.format(cf.crc32, ref_cf.crc32))
                        break
                if not cf.depends:
                    logger.error(SET_NAMING_LINKAGE_FAILED_1.format(crc32))
            else:
                if any((
                    naming_dict[CLASSIFY_VAR],
                    naming_dict[IDX1_VAR],
                    naming_dict[IDX2_VAR],
                    naming_dict[SUPPLEMENT_VAR]
                    )):
                    logger.warning(USING_CUSTOMIZED_NAMING_0)
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
                logger.warning(OVERRIDEN_SUFFIX_1.format(default_dict[SUFFIX_VAR]))
        # #! there is a missing case above: root is missing language tag, but videos have language tags
        # #! since the default_dict will be disposed after this function and wont get checked afterwards
        # #! we need to catch it now
        # if cf.e in VNx_WITH_AUD_EXTS and not default_dict[SUFFIX_VAR]:
        #     logger.warning('Found video with language tag, but the root/default dir is missing language tag.')




def fromSeasonDir(season_dir: Path, logger: Logger) -> Season|None:

    paths = hms.filterOutCDsScans(listFile(season_dir, ext=VX_ALL_EXTS, rglob=True))

    default_dict: dict[str, str] = d if (d := parseSeasonDirName(season_dir, logger=logger)) else {}
    if not default_dict: return None

    naming_dicts: list[dict[str, str]] = []
    for path in paths:
        if not (d := parseCoreFileName(path, location=path.relative_to(season_dir).as_posix(), logger=logger)):
            return None
        naming_dicts.append(d)

    season = Season()
    season.add(hcf.toCoreFilesWithTqdm(paths, logger=logger, mp=hms.getCRC32MultiProc(paths)))
    hnm.cleanNamingDicts(default_dict, naming_dicts, logger)
    applyNamingDicts(season, default_dict, naming_dicts, logger)
    hnm.decomposeFullDesp(season, logger)
    return season
