from configs.constants import UNIQUE_CHARS
from configs.user import ASS_LANG_THRESHOLD




def getAssTextLangDict(text:str|list[str]) -> dict[str, bool]:
    if isinstance(text, list): text = ''.join(text)
    chars = set(text)
    ret = {}
    for k, v in UNIQUE_CHARS.items():
        ret[k] = True if len(chars.intersection(v)) > ASS_LANG_THRESHOLD else False
    return ret
