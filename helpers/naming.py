from configs import *
from utils.chars import isDecimal
from pathlib import Path

__all__ = ['splitGroupTags',
           'cleanDecimal', 'cleanName', 'cleanPath', 'cleanGroupName', 'cleanSuffix']



def splitGroupTags(chars:str, remove_empty:bool=False) -> list[str]:
    tags = chars.strip().split('&')
    if remove_empty: tags = [_.strip() for _ in tags if _.strip()]
    return tags




def cleanDecimal(chars:str) -> str:

    chars = chars.strip() # firstly, strip it

    if isDecimal(chars): # quick exit
        return chars

    # filter the path
    chars = ''.join([c for c in chars if c in '01234567890.'])
    # handle user input like '1...' and '1.2.3.4'
    split_parts, valid_parts, n = chars.split('.'), [], 0
    for sc in split_parts:
        if sc:
            valid_parts.append(sc)
            n += 1
        if n == 2: # only keep at most 2 parts
            break

    return '.'.join(valid_parts)




def cleanName(chars:str) -> str:
    chars = chars.strip()
    # filter the path
    chars = ''.join([c for c in chars if c in VALID_FILENAME_CHARS])
    # remove leading '.' and ' ' which are allowed chars in path
    while chars.startswith(('.', ' ')): chars = chars[1:]
    # remove trailing '.' and ' ' which are allowed chars in path
    while chars.endswith(('.', ' ')): chars = chars[:-1]
    return chars




def cleanPath(path:str) -> str:
    # as_posix() converts '\' to '/' and removes redundant '/'s
    path = str(Path(path.strip()).as_posix())
    # split the path with '/' to parts
    split_parts = path.split('/')
    for i, part in enumerate(split_parts):
        split_parts[i] = cleanName(part)
    # only keep non-empty parts
    split_parts = [p for p in split_parts if p]
    if path[0] == '/':
        return '/' + '/'.join(split_parts)
    else:
        return '/'.join(split_parts)




def cleanGroupName(chars:str) -> str:
    chars = ''.join([c for c in chars if c in VALID_GRPNAME_CHARS])
    # '&. -' is allowed in user input but should not be at start/end
    while chars.startswith((' ', '.', '-', '&')): chars = chars[1:]
    while chars.endswith((' ', '.', '-', '&')): chars = chars[:-1]
    return chars




def cleanSuffix(chars:str) -> str:
    chars = ''.join([c for c in chars if c in VALID_LANGTAG_CHARS])
    # '&' is allowed in user input but should not be at start/end
    while chars.startswith('&'): chars = chars[1:]
    while chars.endswith('&'): chars = chars[:-1]
    return chars
