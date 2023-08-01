import langdetect




def chkLang(chars:str, n:int=5) -> str:
    '''
    Check the language of the given string
    chars: the string to chk language
    n: langdetect.detect() is not deterministic, do it this times to minimise randomness
    '''
    if n < 1: n = 1
    found_langs = []
    for _ in range(n):
        # TODO: the detector is not stable enough - seek some better methods
        found_langs.append(langdetect.detect(chars))
    return max(set(found_langs), key=found_langs.count)
