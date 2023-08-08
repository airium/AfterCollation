import re
from logging import Logger
from pathlib import PurePath

from configs.runtime import *
from configs.regex import *

__all__ = [
    'parseSeriesDirName',
    'parseSeasonDirName',
    'parseCoreFileName',
    ]




def parseSeriesDirName(path: PurePath, logger: Logger|None = None) -> dict[str, str]|None:
    naming_dict = {k: '' for k in VND_FULL_DICT.values()}
    if m := re.match(VCBS_SERIES_ROOT_DIRNAME_PATTERN, path.name.strip()):
        names = m.groupdict()
        naming_dict[FULLPATH_VAR] = path.as_posix()
        naming_dict[GRPTAG_VAR] = g if (g := names['g']) else ''
        naming_dict[TITLE_VAR] = t if (t := names['t']) else ''
        return naming_dict
    else:
        if logger: logger.error(f'Failed to parse the series name "{path.name}".')
        return None




def parseSeasonDirName(path: PurePath, logger: Logger|None = None) -> dict[str, str]|None:
    naming_dict = {k: '' for k in VND_FULL_DICT.values()}
    if m := re.match(VCBS_SEASON_ROOT_DIRNAME_PATTERN, path.name.strip()):
        names = m.groupdict()
        naming_dict[FULLPATH_VAR] = path.as_posix()
        naming_dict[GRPTAG_VAR] = g if (g := names['g']) else ''
        naming_dict[TITLE_VAR] = t if (t := names['t']) else ''
        naming_dict[SUFFIX_VAR] = x if (x := names['x']) else ''
        return naming_dict
    else:
        if logger: logger.error(f'Failed to parse the season name "{path.name}".')
        return None




def parseCoreFileName(path: PurePath, logger: Logger|None = None, location: str|None = None) -> dict[str, str]|None:
    naming_dict = {k: '' for k in VND_FULL_DICT.values()}
    if m := re.match(VCBS_COREFILE_FILENAME_PATTERN, path.name.strip()):
        names = m.groupdict()
        naming_dict[FULLPATH_VAR] = path.as_posix()
        naming_dict[GRPTAG_VAR] = g if (g := names['g']) else ''
        naming_dict[TITLE_VAR] = t if (t := names['t']) else ''
        naming_dict[LOCATION_VAR] = location if location else ''
        naming_dict[FULLDESP_VAR] = d if (d := names['d']) else ''
        naming_dict[SUFFIX_VAR] = x if (x := names['x']) else ''
        naming_dict[QLABEL_VAR] = q if (q := names['qlabel']) else ''
        naming_dict[TLABEL_VAR] = t if (t := names['tlabel']) else ''
        return naming_dict
    else:
        if logger: logger.error(f'Failed to parse "{path.name}".')
        return None
