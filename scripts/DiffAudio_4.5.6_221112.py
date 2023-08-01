# coding=utf-8

import sys
if sys.version_info < (3, 10):
    input('作者太懒啦想让您用个 Python 3.10'); sys.exit()
from itertools import starmap
from multiprocessing import Pool
from pathlib import Path
from time import strftime
from typing import List, Tuple

try:
    import numpy as np                      # pip install numpy
    import scipy.signal as sps              # pip install scipy
    import ffmpeg                           # pip install ffmpeg-python
    import pymediainfo                      # pip install pymediainfo
    miparse = pymediainfo.MediaInfo.parse
except ImportError:
    input('缺库啦，装下面这些：\n'
          '# pip install numpy scipy ffmpeg-python pymediainfo')
    sys.exit()

####################################################################################################

# current version
VERSION = '5.0.0 20230201'
TIME = strftime('DiffAudio-Report-%y%m%d-%H%M%S')
HELP_MESSAGE=f'''DiffAudio {VERSION}
1. 请单选一个文件或多选偶数个文件，并点住首个文件后拖动到本脚本上（命令行同理）
2. 如果输入了 1 个文件，则脚本对该音频制作频谱图
3. 如果输入了 2N 个文件，则脚本对逐对文件 1|N+1, 2|N+2 ... N|2N 执行偏移检查、做差、画频谱'''

####################################################################################################

# this is the start point and length (both in second) used to detect the offset between two audio tracks
# *change them accordingly if you want to detect the offset from other interval
CHK_OFFSET_STA = 0
CHK_OFFSET_LEN = 30
assert CHK_OFFSET_LEN > 0
# we know (a²+b²)/ab>=2 and ==2 only if a==b, but if <=`XCORR_RATIO` we still think a==b
XCORR_RATIO = 4
# if the average difference on samples is below this value, then we think 2 audio are the same
# note the difference is defined in integer value of 16-bit PCM, i.e. the max/min value of audio is 32767/-32768
# 1 for 16-bit integer PCM == 1.5e-6 for floating PCM (2**16*1.5e-5=0.98)
MAX_DIFF_MEAN = 1

####################################################################################################

class Report:
    '''Info to gather during processing.'''

    audio1 = Path()  # path to source audio 1
    audio2 = Path()  # path to source audio 2
    infos = []  # info message
    warnings = []  # warning messages
    errors = []  # error messages
    attentions = []  # attention message

    def __init__(self):  # refresh object reference
        self.errors = []
        self.infos = []
        self.warnings = []
        self.attentions = []


def readAudio(path: Path, id: str | int = 0, start: int = 0, length: int = 0) -> np.ndarray:
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


def chkOffset(f1: Tuple[Path, str | int],
              f2: Tuple[Path, str | int],
              start: int = 0,
              length: int = 1440000) -> Tuple[int, int]:
    '''
    Calculate the offset between 2 audio [`path`, `track_id`] by samples within [start, start+length].
    Return the starting sample index.
    '''
    a1, a2 = starmap(readAudio, ((*f1, start, length), (*f2, start, length)))
    if len(a1) < length: a1 = np.pad(a1, (0, length - len(a1)))
    if len(a2) < length: a2 = np.pad(a2, (0, length - len(a2)))
    xcorr = sps.fftconvolve(a1, a2[::-1])
    idx = np.argmax(xcorr)
    if (a1**2 + a2**2).sum() / xcorr[idx] <= XCORR_RATIO:
        idx = idx - len(a2) + 1
        start1, start2 = (max(0, idx), abs(min(0, idx)))
    else:
        start1, start2 = (0, 0)
    return start1, start2


def diffAudio(f1: Tuple[Path, str | int, int], f2: Tuple[Path, str | int, int]) -> Tuple[np.ndarray, int, int]:
    '''
    Read 2 audio of [path, audio_id, offset] by ffmpeg.
    Return audio1-audio2 [ndarray] and the sample counts [int, int] after offset.
    The reason why we return audio sample count here instead of using mediainfo is that
    audio header may be incorrect due to concatenating etc.
    '''
    a1, a2 = starmap(readAudio, (f1, f2))
    l1, l2 = len(a1), len(a2)
    if l := (l1 - l2):
        a1, a2 = a1[:l1 - l], a2[:l2 + l]
    return np.subtract(a1, a2), l1, l2


def mkSpectrogram(img_path: Path, audio: np.ndarray, fs: int = 48000) -> bool:
    '''Draw spectrogram to `img_path` from `audio`.'''
    success = True
    try:
        (ffmpeg.input('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar=fs)
               .filter('showspectrumpic', s='2048x1024')
               .output(str(img_path.resolve()), pix_fmt='rgb24')
               .run(input=audio.astype(np.int16).tobytes(), overwrite_output=True, quiet=True))
    except Exception:
        success = False
    return success


def TaskEvenFilesWorker(f1: Path, f2: Path):

    rep = Report()
    rep.audio1 = f1
    rep.audio2 = f2
    mi1a: List[pymediainfo.Track] = miparse(f1).audio_tracks
    mi2a: List[pymediainfo.Track] = miparse(f2).audio_tracks

    print(f'chk info between "{f1.name}" & "{f2.name}"')
    if len(mi1a) == 0 or len(mi2a) == 0:
        rep.errors.append(f'no audio track (①={len(mi1a)} ②={len(mi2a)})')
        return rep
    if len(mi1a) - len(mi2a):
        rep.warnings.append(f'different audio track number (①={len(mi1a)} ②={len(mi2a)})')


    print(f'checking offset/diff between "{f1.name}" & "{f2.name}"')
    for i, (a1, a2) in enumerate(zip(mi1a, mi2a), start=1):

        if a1.bit_depth and a2.bit_depth and (a1.bit_depth - a2.bit_depth):
            rep.warnings.append(f'a:{i} diff depth (①={a1.bit_depth} ②={a2.bit_depth})')
        if a1.sampling_rate - a2.sampling_rate:
            rep.errors.append(f'a:{i} diff sample rate (①={a1.sampling_rate} ②={a2.sampling_rate})')
        if a1.channel_s - a2.channel_s:
            rep.errors.append(f'a:{i} diff channel amount (①={a1.channel_s} ②={a2.channel_s})')
        if rep.errors: continue

        fs, a1, a2 = a1.sampling_rate, (f1, a1.stream_identifier), (f2, a2.stream_identifier)
        start1, start2 = chkOffset(a1, a2, start=fs * CHK_OFFSET_STA, length=fs * CHK_OFFSET_LEN)
        if offset := (start1 - start2):
            rep.warnings.append(f'a:{i} detected offset by {offset} samples ({offset/fs:.4f} sec ①[{start1}:] == ②[{start2}:])')
        diff, len1, len2 = diffAudio((*a1, start1), (*a2, start2))
        if dlen := (len1 - len2):
            rep.warnings.append(f'a:{i} diff audio length ①={len1} ②={len2} (①-②={dlen} or {dlen/fs:.4f} sec)')
        if (diff_mean := (np.abs(diff / len(diff)).sum())) > MAX_DIFF_MEAN:
            img_path = f2.with_suffix('.png')
            success = mkSpectrogram(img_path, diff, fs)
            if success: rep.attentions.append(f'a:{i} possibly diff audio (diff={diff_mean:.1e}) ⚠CHECK SPECTROGRAM⚠')
            else: rep.errors.append(f'a:{i} failed to make spectrogram')
        else:
            rep.infos.append(f'a:{i} audio ok (diff={diff_mean:.1e})')

    return rep


def writeReport2txt(txt_path: Path, reports: List[Report]):
    BREAK_LINE = '〰' * 40 + '\n'
    with txt_path.open('w', encoding='utf-8-sig') as txt:
        txt.write('DiffAudio ' + VERSION + '\n')
        txt.write(BREAK_LINE)
        for rep in reports:
            txt.write(f'①: {rep.audio1}\n')
            txt.write(f'②: {rep.audio2}\n')
            for war in rep.warnings:
                txt.write(f'    ⚠ {war}\n')
            for err in rep.errors:
                txt.write(f'    ❌ {err}\n')
            for att in rep.attentions:
                txt.write(f'    ❌ {att}\n')
            for inf in rep.infos:
                txt.write(f'    ✔ {inf}\n')
            txt.write(BREAK_LINE)


def TaskEvenFiles(paths: List[Path]):
    path_pairs = tuple(zip(paths[:len(paths) // 2], paths[len(paths) // 2:]))

    # # single thread
    # results = list(starmap(Task2WorkV2, path_pairs))
    # mkReportV2(paths[0].parent.joinpath(TIME + '.txt'), results)

    # multi-processing
    results = Pool().starmap(TaskEvenFilesWorker, path_pairs)
    writeReport2txt(paths[0].parent.joinpath(TIME + '.txt'), results)


def TaskSingleFile(audio: Path):
    for i, a in enumerate(miparse(audio).audio_tracks, start=1):
        mkSpectrogram(audio.with_suffix(f'.a{i}.png'), readAudio(audio, a.stream_identifier), a.sampling_rate)


if __name__ == "__main__":
    try:
        paths = sys.argv[1:]
        if len(paths) == 1: TaskSingleFile(Path(paths[0]))
        elif len(paths) % 2 == 0: TaskEvenFiles(list(map(Path, paths)))
        else: input(HELP_MESSAGE)
    except Exception as e:
        input(e)
