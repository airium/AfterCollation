import re
from pathlib import Path

from .fileutils import tstFileEncoding
from configs.regex import ASS_INLINE_FONTNAME_BASE_PATTERN, ASS_INLINE_STYLENAME_BASE_PATTERN

import ass
from ass_parser import read_ass, AssFile
from ass_tag_parser import parse_ass, AssTagFontName, AssTagResetStyle, AssTagAnimation


__all__ = [
    'tstAssFile',
    'filterValidASSFiles',
    'toAssFileObj',
    'toAssFileObjs',
    'listEventTextsInAssFileObj',
    'listFontNamesInAssFileObj',
    'listFontNamesInAssFileObjs',
    'listStyleNamesInAssFileObj',
    # 'listStyleNamesInAssFileObjs', # seems not useful
    ]




def tstAssFile(path:Path, encoding='utf-8-sig'):
    try:
        if not tstFileEncoding(path, encoding=encoding):
            return False
        # NOTE use 2 existing ass libs to verify
        read_ass(path.read_text(encoding=encoding))
        with path.open('r', encoding=encoding) as fo:
            ass.parse(fo)
        return True
    except:
        return False




def filterValidASSFiles(*path:Path, encoding:str='utf-8-sig') -> list[Path]:
    return [p for p in path if tstAssFile(p, encoding=encoding)]




def toAssFileObj(path:Path, encoding:str='utf-8-sig') -> AssFile:
    '''Use `tstAssFile()` if necessary.'''
    return read_ass(path.read_text(encoding=encoding))




def toAssFileObjs(paths:list[Path], encoding:str|list[str]='utf-8-sig') -> list[AssFile]:
    encodings = [encoding] * len(paths) if isinstance(encoding, str) else encoding
    assert len(paths) == len(encodings)
    return [read_ass(path.read_text(encoding=encoding)) for path, encoding in zip(paths, encodings)]




def _getFontNamesFromAssText(text:str) -> list[str]:
    # https://stackoverflow.com/a/71993116/14040883 is good but the pattern does not work for python
    # let's use a bit ugly implementation by ourselves
    matches = re.findall(ASS_INLINE_FONTNAME_BASE_PATTERN, text)
    matches = [m for m in matches if m]
    matches = [re.sub(r'\s+', ' ', m).strip() for m in matches]
    return matches




def listFontNamesInAssFileObj(assfile_obj:AssFile, used_only:bool=False) -> tuple[bool, list[str]]:
    ok, fonts = True, []


    if not used_only:
        for style in assfile_obj.styles:
            if style.font_name: fonts.append(style.font_name)
    else:
        sub_ok, stylenames = listStyleNamesInAssFileObj(assfile_obj, used_only=used_only)
        ok = ok if sub_ok else False
        for style in assfile_obj.styles:
            if style.name in stylenames:
                if style.font_name: fonts.append(style.font_name)

    for event_text in listEventTextsInAssFileObj(assfile_obj):
        try:
            tags = parse_ass(event_text)
            for tag in tags:
                if isinstance(tag, AssTagFontName):
                    fonts.append(tag.name)
                if isinstance(tag, AssTagAnimation):
                    pass # TODO it seems AssFile has no handling of this?
        except:
            ok = False
        finally: # always run the regex-based font name finder
            fonts.extend(_getFontNamesFromAssText(event_text))
            continue

    return ok, sorted(set(fonts))




def listFontNamesInAssFileObjs(assfiles:list[AssFile], used_only:bool=False) -> tuple[bool, list[str]]:
    fonts = []
    ok = True

    for assfile in assfiles:
        sub_ok, sub_fonts = listFontNamesInAssFileObj(assfile, used_only=used_only)
        ok = ok if sub_ok else False
        fonts.extend(sub_fonts)
    return ok, sorted(set(fonts))




def listEventTextsInAssFileObj(assfile_obj:AssFile) -> list[str]:
    '''Return all non-comment event text in an ASS obj.'''
    return [event.text for event in assfile_obj.events if not event.is_comment]




def _getStyleNameFromAssText(text:str) -> list[str]:
    matches = re.findall(ASS_INLINE_STYLENAME_BASE_PATTERN, text)
    matches = [m for m in matches if m]
    # ? possibly should do nothing to the stylename string?
    # matches = [re.sub(r'\s+', ' ', m).strip() for m in matches]
    return matches




def listStyleNamesInAssFileObj(assfile_obj:AssFile, used_only:bool=False) -> tuple[bool, list[str]]:
    '''
    Return:
    bool: False means that the ass_tag_parser failed => the parsing may be incomplete (very low risk).
    list[str]: the list of style names.
    '''

    styles : dict[str, bool] = {}
    for style in assfile_obj.styles:
        styles[style.name] = False

    if not used_only:
        return True, [str(k) for k in styles.keys()]

    ok = True
    for event in assfile_obj.events:
        if event.is_comment:
            continue

        # NOTE check if the style is defined is beyond the scope of the current project
        if event.style_name and (event.style_name in styles.keys()):
            styles[event.style_name] = True

        try:
            tags = parse_ass(event.text)
            for tag in tags:
                if isinstance(tag, AssTagResetStyle):
                    if tag.style and (tag.style in styles.keys()):
                        styles[tag.style] = True
                if isinstance(tag, AssTagAnimation):
                    pass # TODO it seems AssFile has no handling of this?
        except:
            ok = False
        finally: # always run the regex-based style name finder
            for style in _getStyleNameFromAssText(event.text):
                if style and (style in styles.keys()):
                    styles[style] = True

        # ? have we caught all possible defined style names?
        # we have not yet handled the Animated Transform tag
        # but it seems the regex can catch it?

    return ok, sorted(set([str(k) for (k, v) in styles.items() if v]))




def listStyleNamesInAssFileObjs(assfile_objs:list[AssFile], used_only:bool=False) -> tuple[bool, list[str]]:

    ok, styles = True, []
    for assfile_obj in assfile_objs:
        sub_ok, sub_styles = listStyleNamesInAssFileObj(assfile_obj, used_only=used_only)
        ok = ok if sub_ok else False
        styles.extend(sub_styles)
    return ok, styles
