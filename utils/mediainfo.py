from pathlib import Path
from multiprocessing import Pool
from configs import *
from pymediainfo import MediaInfo
from typing import cast


__all__ = ['MI',
           'MediaInfo',
           'getMediaInfo',
           'getMediaInfoList',
           'matchTime',
           'matchMenuTimeStamps']


MI = MediaInfo




def getMediaInfo(path:Path) -> MediaInfo:
    return cast(MediaInfo, MediaInfo.parse(path, output=None))




def getMediaInfoList(paths:list[Path], mp:int=1) -> list[MediaInfo]:
    mp = int(mp)
    if mp > 1:
        minfos = list(Pool().map(getMediaInfo, paths))
    else:
        minfos = list(map(getMediaInfo, paths))
    return minfos




def matchTime(duration1:int, duration2:int, threshold:int=SAME_DURATION_THRESHOLD) -> bool:
    '''The unit is millisecond.'''
    if abs(duration1 - duration2) <= threshold:
        return True
    return False




def matchMenuTimeStamps(ts1:list[int], ts2:list[int], threshold:int=SAME_DURATION_THRESHOLD) -> bool:
    if len(ts1) != len(ts2):
        return False
    for t1, t2 in zip(ts1, ts2):
        if not matchTime(t1, t2, threshold):
            return False
    return True
