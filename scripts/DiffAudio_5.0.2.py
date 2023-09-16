# coding=utf-8

import sys
if sys.version_info < (3, 10):
    input('作者太懒啦想让您用个 Python 3.10'); sys.exit()
from itertools import starmap
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import strftime
from typing import List, Tuple
import os
import time
import re
try:
    import numpy as np                      # pip install numpy
    import scipy.signal as sps              # pip install scipy
    import ffmpeg                           # pip install ffmpeg-python
    import pymediainfo                      # pip install pymediainfo
    import argparse
    miparse = pymediainfo.MediaInfo.parse
except ImportError:
    input('缺库啦，装下面这些：\n'
          '# pip install numpy scipy ffmpeg-python pymediainfo')
    sys.exit()

####################################################################################################

# current version
VERSION = '5.0.2 230828'
TIME = strftime('DiffAudio-Report-%y%m%d-%H%M%S')

ffmpeg_path = ""
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
class SmartFomatter(argparse.HelpFormatter):
    def _split_lines(self, text: str, width: int) -> list[str]:
        return text.splitlines()


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
                                    .run(capture_stdout=True, quiet=True, cmd=ffmpeg_path)[0], np.int16)
    else:
        audio = np.frombuffer(ffmpeg.input(path.resolve())[f'a:{id}']
                                    .filter('atrim', start_sample=start)
                                    .output('-', ac=1, format='s16le', acodec='pcm_s16le')
                                    .run(capture_stdout=True, quiet=True, cmd=ffmpeg_path)[0], np.int16)
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
               .run(input=audio.astype(np.int16).tobytes(), overwrite_output=True, quiet=True, cmd=ffmpeg_path))
    except Exception:
        success = False
    return success


def TaskCompareFilesWorker(f1: Path, f2: Path, result_path:Path):

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
            img_path = result_path.joinpath(f2.with_suffix('.png').name)
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


def TaskCompareFiles(paths1: List[Path], paths2:List[Path]):
    path_pairs = tuple(zip(paths1, paths2, [result_path]*len(paths1)))
    if para_mode == 0:
        # single thread
        results = list(starmap(TaskCompareFilesWorker, path_pairs))
    elif para_mode == 1:
    # multi-processing
        with Pool(thread_count) as pool:
            results =  pool.starmap(TaskCompareFilesWorker, path_pairs)
    else:
    # multi-threading
        with ThreadPoolExecutor(thread_count) as pool:
            results = pool.map(TaskCompareFilesWorker, paths1, paths2, [result_path]*len(paths1))
    writeReport2txt(result_path.joinpath(TIME + '.txt'), results)

def TaskSingleFileWorker(audio: Path, result_path:Path):
    for i, a in enumerate(miparse(audio).audio_tracks, start=1):
        mkSpectrogram(result_path.joinpath(audio.with_suffix(f'.a{i}.png').name), readAudio(audio, a.stream_identifier), a.sampling_rate)

def TaskSingleFile(paths: List[Path]):
    if para_mode == 0:
        # single thread
        list(starmap(TaskSingleFileWorker, tuple(zip(paths, [result_path]*len(paths)))))
    elif para_mode == 1:
    # multi-processing
        with Pool(thread_count) as pool:
            pool.starmap(TaskSingleFileWorker, tuple(zip(paths, [result_path]*len(paths))))
    else:
    # multi-threading
        with ThreadPoolExecutor(thread_count) as pool:
            pool.map(TaskSingleFileWorker, tuple(paths), tuple([result_path]*len(paths)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=SmartFomatter)
    source_file = parser.add_argument_group("Source Option")
    source_file.add_argument("--mode", dest="work_mode", type=int, choices=[1,2], default=2, help="Work mode:\n1: Make audio spectrum for every input video specied by --target.\n2: compare two sets of video.\n default:2")
    source_file.add_argument("-r","--ref", action="store", dest="ref_path_list", help="The path file of the reference video(s).")
    source_file.add_argument("-t", "--target", action="store",dest="target_path_list", help="The path file of the video(s) you want to compare.", required=True)
    source_file.add_argument("--ffmpeg", action="store", dest="ffmpeg_path", default="ffmpeg.exe", help="The path of ffmpeg.exe. Search in PATH when it isn't assigned.")
    output_file = parser.add_argument_group("Output Option")
    output_file.add_argument("-o", "--output", action="store", dest="result_path", default="DiffAudio_Result", help="The path you want to save the images and txt. Default: 'DiffAudio_Result' in current work path.")
    parallel_option = parser.add_argument_group("Parallel Option")
    parallel_option.add_argument("--para-mode", action="store", dest="para_mode", type=int, default=2,choices=[0,1,2], help='''The mode of paralle processing:\n0——Single Thread.\n1——multi-Processing (Fastest but require HUGE memory).\n2——multi-Threading (Acceptable speed and momory use, default)''')
    parallel_option.add_argument("--thread", action="store", dest="thread_count", type=int, help="The count of parallel task.\n para-mode=1, the default is 8\n para-mode=2, the default is you cpu threads.")
    debug_option = parser.add_argument_group("Debug Option")
    debug_option.add_argument("--benchmark", action="store_true", dest="benchmark", help="Print the processing time in the end.")
    args = parser.parse_args()
    para_mode = args.para_mode
    thread_count = args.thread_count
    work_mode = args.work_mode
    if args.benchmark:
        start_time = time.time()
    if not thread_count:
        if para_mode == 1: thread_count = 8
        if para_mode == 2: thread_count = os.cpu_count()

    target_path = Path(args.target_path_list)
    if not target_path.is_absolute:  target_path = target_path.absolute()        
    target_path_list = []
    path_patern = re.compile(r'''(^["|']?(?P<path>[^"']+)["|']?$)''')
    with open(target_path, 'r', encoding="utf-8") as f:
        target_path_list_raw=f.read().split("\n")
        for object in target_path_list_raw:
            target_path_list.append(path_patern.search(object).group("path"))

    result_path = Path(args.result_path)
    if not result_path.is_absolute():  result_path = result_path.absolute()
    if not result_path.is_dir(): os.mkdir(result_path)

    ffmpeg_path = args.ffmpeg_path
    if work_mode == 1:
        TaskSingleFile(list(map(Path, target_path_list)))
    elif work_mode == 2:
        ref_path_list = []
        ref_path = Path(args.ref_path_list)
        if not ref_path.is_absolute:  ref_path = ref_path.absolute()
        with open(ref_path, 'r', encoding="utf-8") as f:
            ref_path_list_raw=f.read().split("\n")
            for object in ref_path_list_raw:
                ref_path_list.append(path_patern.search(object).group("path"))
        TaskCompareFiles(list(map(Path, ref_path_list)), list(map(Path, target_path_list)))
    
    if args.benchmark:
        end_time = time.time()
        print(f"Time use:{end_time-start_time}(s)")