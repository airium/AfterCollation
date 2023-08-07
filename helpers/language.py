from configs.runtime import LANG_SUFFIX_UNIFORMATION_DICT
from configs.chars import TAG_SPLITTER
from .naming import normSingleSuffix

__all__ = ['toUniformLangTag', 'toUniformLangTags']




def toUniformLangTag(suffix:str) -> str:
    '''Return empty if the input language is not accepted in the standard.'''
    suffix = normSingleSuffix(suffix).lower()
    return LANG_SUFFIX_UNIFORMATION_DICT.get(suffix, '')




def toUniformLangTags(text:str|list[str]) -> list[str]:
    if isinstance(text, str):
        text = text.split(TAG_SPLITTER)
    ret = [toUniformLangTag(t) for t in text if t]
    return [t for t in ret if t]
