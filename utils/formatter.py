__all__ = ['formatFileSize1', 'formatFileSize2', 'formatTimeLength']

import math




def formatFileSize1(number: int) -> str:
    units = ['B', 'K', 'M', 'G', 'T', 'P']
    if number:
        base = 1000
        magnitude = int(math.floor(math.log(number, 1000)))
        return f'{number/base**magnitude:.3f}{units[magnitude]}'
    else:
        return '0B'




def formatFileSize2(n: int) -> str:
    if n < 0:
        return ''
    if n == 0:
        return '0'
    else:
        g, n = divmod(n, 1000**3)
        m, n = divmod(n, 1000**2)
        k, n = divmod(n, 1000**1)
        ret = ''
        ret += (f'{g:2d}g' if g else '   ')
        ret += (f'{m:3d}m' if m else '    ')
        ret += (f'{k:3d}k' if k else '    ')
        ret += (f'{n:3d}' if n else '   ')
        return ret




def formatTimeLength(n: int) -> str:
    '''The input `n` is in milliseconds.'''
    if n < 0:
        return ''
    if n == 0:
        return '0'
    else:
        h, n = divmod(n, 3600000)
        m, n = divmod(n, 60000)
        s, n = divmod(n, 1000)
        ret = ''
        ret += (f'{h:2d}h' if h else '   ')
        ret += (f'{m:2d}m' if m else '   ')
        ret += (f'{s:2d}s' if s else '   ')
        ret += (f'{n:3d}' if n else '   ')
        return ret
