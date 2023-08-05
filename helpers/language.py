from configs.runtime import LANG_SUFFIX_UNIFORMATION_DICT
from .naming import clean1Suffix

__all__ = ['toUniformLangTag', 'toUniformLangTags']




def toUniformLangTag(suffix:str) -> str:
    '''Return empty if the input language is not accepted in the standard.'''
    suffix = clean1Suffix(suffix).lower()
    return LANG_SUFFIX_UNIFORMATION_DICT.get(suffix, '')




def toUniformLangTags(text:str|list[str]) -> list[str]:
    if isinstance(text, str):
        text = text.split('&')
    ret = [toUniformLangTag(t) for t in text if t]
    return [t for t in ret if t]
