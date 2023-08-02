import re
from pathlib import Path

from .fileutils import tstFileEncoding
from configs.regex import ASS_FONT_BASE_PATTERN

import ass
from ass_parser import read_ass, AssFile
from ass_tag_parser import parse_ass, AssTagFontName


__all__ = ['tstAssFile', 'toAssObjs' , 'listFontNamesInAssObjs', 'filterValidASSFiles']




def tstAssFile(inp:Path, encoding='utf-8-sig'):
    try:
        if not tstFileEncoding(inp, encoding=encoding):
            return False
        read_ass(inp.read_text(encoding=encoding))
        with inp.open('r', encoding=encoding) as fobj:
            doc = ass.parse(fobj)
        return True
    except:
        return False



def filterValidASSFiles(*inp:Path, encoding:str='utf-8-sig') -> list[Path]:
    ret = []
    for file in inp:
        if tstAssFile(file):
            ret.append(file)
    return ret




def toAssObjs(*inp:Path, encoding:str|list[str]='utf-8-sig') -> list[AssFile]:
    '''Test `tstAssFile()` if necessary.'''
    n = len(inp)
    encodings = [encoding] * n if isinstance(encoding, str) else encoding
    assert n == len(encodings)
    ret = []
    for path, encoding in zip(inp, encodings):
        ret.append(read_ass(path.read_text(encoding=encoding)))
    return ret




def _getFontFromAssText(text:str) -> list[str]:
    # https://stackoverflow.com/a/71993116/14040883 is good but the pattern does not work for python
    # let's use a bit ugly implementation by ourselves
    matches = re.findall(ASS_FONT_BASE_PATTERN, text)
    matches = [m for m in matches if m]
    # matches = [m.replace('(', ' ') for m in matches]
    # matches = [m.replace(')', ' ') for m in matches]
    matches = [re.sub(r'\s+', ' ', m).strip() for m in matches]
    return matches




def listFontNamesInAssObjs(*ass_file_objs:AssFile) -> tuple[bool, list[str]]:
    fonts = []
    ok = True

    for ass_file in ass_file_objs:
        try:
            for style in ass_file.styles:
                fonts.append(style.font_name)
            for event in ass_file.events:
                text = event.text
                try:
                    tags = parse_ass(text)
                    for tag in tags:
                        if isinstance(tag, AssTagFontName):
                            fonts.append(tag.name)
                except:
                    ok = False
                    # if parse_ass failed, falling back to our regex based font extractor
                    fonts.extend(_getFontFromAssText(text))
                    continue
        except Exception as e:
            ok = False
            continue
    return ok, sorted(set(fonts))
