import difflib
import itertools
from pathlib import Path

import utils.mediainfo
from configs import *


import ffmpeg # NOTE if using ffmpeg but numpy, place the functions in ffmpegutils.py
import numpy as np
import numpy.typing as npt
import scipy.signal as sps


__all__ = ['readAudio',
           'pickAudioSamples', 'cmpAudioSamples',
           'calcAudioOffset', 'getAudioFileOffset',
           'subtractAudio', 'subtractAudioFile',
           'mkSpectrogram']



def readAudio(path: Path, id: str | int = 0, start: int = 0, length: int = 0) -> npt.NDArray[np.int16]:
    '''
    Load the file from `path`
    Select audio track `id` and extract its first channel
    Read from `start` to `start+length` if `length`>0 else from `start` to the end
    Audio are always returned as PCM S16LE format to minimise memory cost
    '''
    if length > 0:
        audio = np.frombuffer(ffmpeg.input(path.resolve())[f'a:{id}']
                                    .filter('atrim', start_sample=start, end_sample=start+length)
                                    .output('-', ac=1, format='s16le', acodec='pcm_s16le')
                                    .run(capture_stdout=True, quiet=True)[0], np.int16)
    else:
        audio = np.frombuffer(ffmpeg.input(path.resolve())[f'a:{id}']
                                    .filter('atrim', start_sample=start)
                                    .output('-', ac=1, format='s16le', acodec='pcm_s16le')
                                    .run(capture_stdout=True, quiet=True)[0], np.int16)
    return audio




def pickAudioSamples(path: Path) -> str:
    '''
    Simply use the idx of max value as the anchor point
    then record one point every 3 seconds
    This digest should be robust for removing starting silence, though cannot work video to be sliced
    '''
    mi = utils.mediainfo.getMediaInfo(path)
    if mi.audio_tracks:
        freq = mi.audio_tracks[0].sampling_rate
    else:
        return ''
    if freq:
        freq = int(freq)
    else:
        return ''
    audio = readAudio(path)
    max_idx = audio.argmax()
    start = max_idx % freq
    points = audio[start:freq*120:freq*3].tolist()
    return '|'.join(f'{p:d}' for p in (max(audio), *points))




def cmpAudioSamples(sample1:str, sample2:str, threshold:int=4) -> bool:

    if not sample1 or not sample2:
        return False

    max1, *samples1 = [int(s) for s in sample1.split('|')]
    max2, *samples2 = [int(s) for s in sample2.split('|')]

    if max1 != max2:
        return False

    if len(samples1) == 0 or len(samples2) == 0:
        return False

    matches = list(getMatchedSubSequence(samples1, samples2))
    if len(matches) == 0:
        return False

    matches_lens = [len(match) for match in matches]

    # since we pick a point every 3s
    # we choose at least to make 15s CM possible to match
    # NOTE however, videos shorter than 12s will never get matched
    if any(l > threshold for l in matches_lens):
        return True

    return False




# https://stackoverflow.com/a/32318377/14040883
def getMatchedSubSequence(list1, list2):
    while True:
        mbs = difflib.SequenceMatcher(None, list1, list2).get_matching_blocks()
        if len(mbs) == 1: break
        for i, j, n in mbs[::-1]:
            if n > 0: yield list1[i: i + n]
            del list1[i: i + n]
            del list2[j: j + n]




def calcAudioOffset(a1:npt.NDArray[np.int16], a2:npt.NDArray[np.int16], start:int=0, length:int=1440000) -> tuple[int, int]:
    '''
    Calculate the offset between 2 audio `ndarray` by samples within [start, start+length].
    Return the starting sample index.
    '''
    if len(a1.shape) > 1: a1 = a1[:, 0]
    if len(a2.shape) > 1: a2 = a2[:, 0]
    if len(a1) < length: a1 = np.pad(a1, (0, length - len(a1)))
    if len(a2) < length: a2 = np.pad(a2, (0, length - len(a2)))
    xcorr = sps.fftconvolve(a1, a2[::-1])
    idx = int(np.argmax(xcorr))
    if (a1**2 + a2**2).sum() / xcorr[idx] <= XCORR_RATIO:
        idx = idx - len(a2) + 1
        start1, start2 = (max(0, idx), abs(min(0, idx)))
    else:
        start1, start2 = (0, 0)
    return start1, start2




def getAudioFileOffset(f1: tuple[Path, str|int],
                       f2: tuple[Path, str|int],
                       start: int = 0,
                       length: int = 1440000
                       ) -> tuple[int, int]:
    '''
    Calculate the offset between 2 audio [`path`, `track_id`] by samples within [start, start+length].
    Return the starting sample index.
    '''
    a1, a2 = itertools.starmap(readAudio, ((*f1, start, length), (*f2, start, length)))
    return calcAudioOffset(a1, a2, start, length)




def subtractAudio(a1:np.ndarray, a2:np.ndarray, start1:int=0, start2:int=0) -> np.ndarray:
    '''
    Subtract two 1-D array with optional starting index.
    Return a1[start1:]-a2[start2:]
    '''
    if len(a1.shape) > 1: a1 = a1[:, 0]
    if len(a2.shape) > 1: a2 = a2[:, 0]
    a1 = a1[start1:]
    a2 = a2[start2:]
    l1, l2 = len(a1), len(a2)
    if l := (l1 - l2):
        a1, a2 = a1[:l1 - l], a2[:l2 + l]
    return np.subtract(a1, a2)




def subtractAudioFile(f1: tuple[Path, str|int, int], f2: tuple[Path, str|int, int]) -> tuple[np.ndarray, int, int]:
    '''
    Read 2 audio of [path, audio_id, offset] by ffmpeg.
    Return audio1-audio2 [ndarray] and the sample counts [int, int] after offset.
    The reason why we return audio sample count here instead of using mediainfo is that
    audio header may be incorrect due to concatenating etc.
    '''
    a1, a2 = itertools.starmap(readAudio, (f1, f2))
    l1, l2 = len(a1), len(a2)
    if l := (l1 - l2):
        a1, a2 = a1[:l1 - l], a2[:l2 + l]
    return np.subtract(a1, a2), l1, l2




def mkSpectrogram(img_path: Path, audio: np.ndarray, fs: int = 48000) -> bool:
    '''Draw spectrogram to `img_path` from `audio`.'''
    try:
        (ffmpeg.input('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar=fs)
               .filter('showspectrumpic', s='2048x1024')
               .output(str(img_path.resolve()), pix_fmt='rgb24')
               .run(input=audio.astype(np.int16).tobytes(), overwrite_output=True, quiet=True))
    except:
        return False
    return True
