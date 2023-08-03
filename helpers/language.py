from configs.runtime import LANG_SUFFIX_UNIFORMATION_DICT


__all__ = ['toUniformLangSuffix', 'toUniformLangSuffixes']




def toUniformLangSuffix(lang:str) -> str:
    '''Return empty if the input language is not accepted in the standard.'''
    lang = lang.strip().lower()
    return LANG_SUFFIX_UNIFORMATION_DICT.get(lang, '')




def toUniformLangSuffixes(text:str|list[str]) -> list[str]:
    if isinstance(text, str):
        text = text.split('&')
    ret = [toUniformLangSuffix(t) for t in text if t]
    return [t for t in ret if t]
