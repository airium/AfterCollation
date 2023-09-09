import re
from logging import Logger
from pathlib import PurePath

from langs import *
from configs import *


__all__ = [
    'parseSeriesDirName',
    'parseSeasonDirName',
    'parseCoreFileName',
    'parseAlbumDirName',
    ]




def parseSeriesDirName(path: PurePath, logger: Logger|None = None) -> dict[str, str]|None:
    naming_dict = {k: '' for k in VD_FULL_DICT.values()}
    if m := re.match(VCBS_SERIES_ROOT_DIRNAME_PATTERN, path.name.strip()):
        names = m.groupdict()
        naming_dict[FULLPATH_VAR] = path.as_posix()
        naming_dict[GRPTAG_VAR] = g if (g := names['g']) else ''
        naming_dict[TITLE_VAR] = t if (t := names['t']) else ''
        return naming_dict
    else:
        if logger: logger.error(VP_FAILED_PARSING_SERIES_NAME_1.format(path.name))
        return None




def parseSeasonDirName(path: PurePath, logger: Logger|None = None) -> dict[str, str]|None:
    naming_dict = {k: '' for k in VD_FULL_DICT.values()}
    if m := re.match(VCBS_SEASON_ROOT_DIRNAME_PATTERN, path.name.strip()):
        names = m.groupdict()
        naming_dict[FULLPATH_VAR] = path.as_posix()
        naming_dict[GRPTAG_VAR] = g if (g := names['g']) else ''
        naming_dict[TITLE_VAR] = t if (t := names['t']) else ''
        naming_dict[SUFFIX_VAR] = x if (x := names['x']) else ''
        return naming_dict
    else:
        if logger: logger.error(VP_FAILED_PARSING_SEASON_NAME_1.format(path.name))
        return None




def parseCoreFileName(path: PurePath, logger: Logger|None = None, location: str|None = None) -> dict[str, str]|None:
    naming_dict = {k: '' for k in VD_FULL_DICT.values()}
    if m := re.match(VCBS_COREFILE_FILENAME_PATTERN, path.name.strip()):
        names = m.groupdict()
        naming_dict[FULLPATH_VAR] = path.as_posix()
        naming_dict[GRPTAG_VAR] = g if (g := names['g']) else ''
        naming_dict[TITLE_VAR] = t if (t := names['t']) else ''
        naming_dict[LOCATION_VAR] = location if location else ''
        naming_dict[FULLDESP_VAR] = f if (f := names['f']) else ''
        naming_dict[SUFFIX_VAR] = x if (x := names['x']) else ''
        naming_dict[QLABEL_VAR] = q if (q := names['qlabel']) else ''
        naming_dict[TLABEL_VAR] = t if (t := names['tlabel']) else ''
        return naming_dict
    else:
        if logger: logger.error(VP_FAILED_PARSING_VID_FILENAME_1.format(path.name))
        return None




def parseAlbumDirName(name: str, logger: Logger) -> dict|None:
    pass
