
import logging
import itertools
from pathlib import Path

from .subtitle import *
from .fileutils import listFile
from configs.commons import *
from configs.runtime import *

from fontTools.ttLib import TTFont, TTCollection
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e




__all__ = ['tstFontPath', 'getValidFontPaths', 'toTTFontObjs', 'listFontNamesInTTFontObjs']



def tstFontPath(path:Path) -> bool:

    if not path.is_file():
        return False

    if path.suffix.lower().endswith(COMMON_F_FONT_EXTS):
        try:
            TTFont(path, checkChecksums=2)
        except:
            return False
        else:
            return True

    if path.suffix.lower().endswith(COMMON_C_FONT_EXTS):
        try:
            TTCollection(path, checkChecksums=2)
        except:
            return False
        else:
            return True

    return False




def getValidFontPaths(inp: list[Path]) -> list[Path]:
    possible_fonts = listFile(*inp, ext=COMMON_FONT_EXTS, rglob=False)
    ret = []
    for possible_font in possible_fonts:
        if tstFontPath(possible_font):
            ret.append(possible_font)
    return ret




def toTTFontObjs(inp: list[Path]) -> list[TTFont]:
    '''NOTE use `getValidFontPaths` to filter out invalid font files if the input is unverified.'''
    fs = [TTFont(f) for f in listFile(*inp, ext=COMMON_F_FONT_EXTS, rglob=False)]
    cs = [TTCollection(f) for f in listFile(*inp, ext=COMMON_C_FONT_EXTS, rglob=False)]
    return list(itertools.chain(fs, *cs))




def listFontNamesInTTFontObjs(inp: list[TTFont]) -> list[str]:
    ret = []
    for f in inp:
        base_names : list[str] = []
        sub_family_names : list[str] = []
        name_table = f['name']
        if name_table and isinstance(name_table, table__n_a_m_e):
            for n in name_table.names:
                # print(f'{n.nameID:4d} {n.langID:4d} {n.platformID:4d} {n.platEncID:4d} {n.toUnicode()}')
                if n.nameID in ENABLED_FONT_NAME_IDS:
                    try:
                        base_names.append(n.toUnicode())
                    except:
                        base_names.append(n.toStr())
                elif n.nameID in FONT_SUBFAMILY_NAME_IDS:
                    try:
                        sub_family_names.append(n.toUnicode())
                    except:
                        sub_family_names.append(n.toStr())
            if sub_family_names:
                for b, s in itertools.product(base_names, sub_family_names):
                    ret.append(f'{b} {s}')
            ret.extend(base_names)
    return sorted((set(ret)))




def chkFontSufficiency(ass_files:list[Path], font_files:list[Path], logger:logging.Logger):

    # TODO this is currently a preliminary implementation

    ass_files = listFile(ass_files, ext=COMMON_TEXT_SUB_EXTS, rglob=False)
    font_files = listFile(font_files, ext=COMMON_FONT_EXTS, rglob=False)

    valid_ass_files = filterValidASSFiles(ass_files)
    valid_font_files = getValidFontPaths(font_files)

    if len(ass_files) != len(valid_ass_files):
        logger.warning('Some input ASS files are invalid.')
    if len(font_files) != len(valid_font_files):
        logger.warning('Some input FONT files are invalid.')

    ass_font_objs = toAssFileObjs(valid_ass_files)
    success, all_font_names_in_ass_files = listFontNamesInAssFileObjs(ass_font_objs)
    if not success:
        logger.warning('Some ASS files contain tags that cannot be parsed by the library. '
                       'The accuracy of font listing may be lowered a little bit.')

    ttfont_objs = toTTFontObjs(valid_font_files)
    all_font_names_in_font_files = listFontNamesInTTFontObjs(ttfont_objs)

    if diff := set(all_font_names_in_ass_files).difference(all_font_names_in_font_files):
        logger.warning('Some fonts in ASS may be missing in the font 7z/zip/rar:')
        for i, font in enumerate(diff):
            logger.warning(f'{i:03d}: {font}')
