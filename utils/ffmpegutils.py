
from pathlib import Path
import ffmpeg

# NOTE this module only contains functions requiring no numpy


__all__ = ['tryFFMPEGDecode', 'tryFFMPEGAudioDecode', 'tryFFMPEGVideoDecode']




def tryFFMPEGDecode(path:Path) -> bool:
    try:
        ffmpeg.input(path.resolve()).output('-', format='null').run(quiet=True)
    except ffmpeg._run.Error:
        return False
    return True




def tryFFMPEGAudioDecode(path:Path, id:int=0) -> bool:
    try:
        ffmpeg.input(path.resolve())[f'a:{id}'].output('-', format='null').run(quiet=True)
    except ffmpeg._run.Error:
        return False
    return True




def tryFFMPEGVideoDecode(path:Path, id:int=0) -> bool:
    try:
        ffmpeg.input(path.resolve())[f'v:{id}'].output('-', format='null').run(quiet=True)
    except ffmpeg._run.Error:
        return False
    return True
