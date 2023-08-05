from __future__ import annotations

import re
from typing import Any
from pathlib import Path
from multiprocessing import Pool

from utils import *
from configs import *

from pymediainfo import Track


__all__ = [
    'CF',
    'CoreFile',
    'getCoreFile',
    'getCoreFileList',
    ]




class CoreFile:
    '''
    CoreFile is a wrapper over MediaInfo, providing easier access to mediainfo.
    A `core file` means it's one in `VNx_ALL_EXTS` (MKV/MKA/MP4/FLAC/PNG/ASS/7Z/ZIP/RAR)
    i.e. the core part of files in a BDRip (to the contrary of CDs/Scans).

    VideoNaming tools depends on this class.
    '''

    def __init__(self,
                 path:Path|str,
                 init_crc32:bool=False,
                 init_audio_samples:bool=False) -> None:

        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f'Missing "{self.path}" at CoreFile instantiation.')
        self.path = path

        self.minfo = getMediaInfo(path)
        self.dst = ''

        for v in VNA_USER_DICT.values():
            setattr(self, v, '')
        for v in VND_USER_DICT.values():
            setattr(self, v, '')

        self._crc32 : str = ''
        self._audio_samples = ''

        if init_crc32:
            self._crc32 = getCRC32(self.path, prefix='')

        if init_audio_samples and self.has_audio and ENABLE_AUDIO_SAMPLES_IN_VNA:
            self._audio_samples = pickAudioSamples(self.path)


    def __getattr__(self, __name: str) -> Any:
        return getattr(self.minfo, __name)


    def __getstate__(self) -> dict:
        return self.__dict__


    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)


    def updateFromVNA(self, vna_config:dict[str, str]) -> None:
        for k, v in VNA_USER_DICT.items():
            setattr(self, v, vna_config.get(v, ''))


    def updateFromVND(self, vnd_config:dict[str, str]) -> None:
        for k, v in VND_USER_DICT.items():
            setattr(self, v, vnd_config.get(v, ''))


    def copyNaming(self, cf:CF):
        self.l = cf.l
        self.t = cf.t
        self.i1 = cf.i1
        self.i2 = cf.i2
        self.n = cf.n
        self.c = cf.c

    @property
    def crc(self) -> str:
        return self.crc32

    # faster access to naming fields
    @property # NOTE no setter for read-only path
    def src(self) -> str:
        return self.path.resolve().as_posix()
    # @property
    # def dst(self) -> str:
    #     return getattr(self, DSTPATH_VAR, '')
    @property
    def g(self) -> str:
        return getattr(self, GRPTAG_VAR, '')
    @g.setter
    def g(self, v:str) -> None:
        setattr(self, GRPTAG_VAR, v)
    @property
    def s(self) -> str:
        return getattr(self, SHOWNAME_VAR, '')
    @s.setter
    def s(self, v:str) -> None:
        setattr(self, SHOWNAME_VAR, v)
    @property
    def l(self) -> str:
        return getattr(self, LOCATION_VAR, '')
    @l.setter
    def l(self, v:str) -> None:
        setattr(self, LOCATION_VAR, v)
    @property
    def t(self) -> str:
        return getattr(self, TYPENAME_VAR, '')
    @t.setter
    def t(self, v:str) -> None:
        setattr(self, TYPENAME_VAR, v)
    @property
    def i1(self) -> str:
        return getattr(self, IDX1_VAR, '')
    @i1.setter
    def i1(self, v:str) -> None:
        setattr(self, IDX1_VAR, v)
    @property
    def i2(self) -> str:
        return getattr(self, IDX2_VAR, '')
    @i2.setter
    def i2(self, v:str) -> None:
        setattr(self, IDX2_VAR, v)
    @property
    def n(self) -> str:
        return getattr(self, NOTE_VAR, '')
    @n.setter
    def n(self, v:str) -> None:
        setattr(self, NOTE_VAR, v)
    @property
    def c(self) -> str:
        return getattr(self, CUSTOM_VAR, '')
    @c.setter
    def c(self, v:str) -> None:
        setattr(self, CUSTOM_VAR, v)
    @property
    def x(self) -> str:
        return getattr(self, SUFFIX_VAR, '')
    @x.setter
    def x(self, v:str) -> None:
        setattr(self, SUFFIX_VAR, v)
    @property # NOTE no setter for read-only extension
    def e(self) -> str:
        return self.ext

    @property
    def has_duration(self) -> bool:
        return not (self.general_tracks[0].duration is None)

    @property
    def has_video(self) -> bool:
        return bool(self.video_tracks)
    @property
    def has_audio(self) -> bool:
        return bool(self.audio_tracks)
    @property
    def has_menu(self) -> bool:
        return bool(self.menu_tracks)
    @property
    def has_text(self) -> bool:
        return bool(self.text_tracks)
    @property
    def has_image(self) -> bool:
        return bool(self.image_tracks)
    @property
    def has_other(self) -> bool:
        return bool(self.other_tracks)
    @property
    def num_audio(self) -> int:
        return len(self.audio_tracks)
    @property
    def gtr(self) -> Track:
        return self.general_tracks[0]
    @property
    def duration(self) -> int:
        if not self.has_duration: return 0
        '''The unit is millisecond.'''
        return int(float(self.general_tracks[0].duration))
    @property
    def file_size(self) -> int:
        return int(self.general_tracks[0].file_size)
    @property
    def ext(self) -> str:
        ret = self.suffix
        return ret[1:] if ret.startswith('.') else ret
    @property
    def suffix(self) -> str:
        return self.path.suffix.lower()


    @property
    def format(self) -> str:
        if ret := self.general_tracks[0].format:
            return ret
        else:
            return self.ext
    @property
    def crc32(self) -> str:
        if not self._crc32: self._crc32 = getCRC32(self.path, prefix='', pass_not_found=True)
        return self._crc32


    @property
    def audio_samples(self) -> str:
        if not ENABLE_AUDIO_SAMPLES_IN_VNA: return ''
        if not self.has_audio: return ''
        if not self._audio_samples: self._audio_samples = pickAudioSamples(self.path)
        return self._audio_samples


    @property
    def menu_timestamps(self) -> list[list[int]]:
        '''The unit is millisecond.'''
        ret = []
        for menu_track in self.menu_tracks:
            menu_dict = menu_track.to_data()
            matches = [re.match(MEDIAINFO_CHAPTER_PATTERN, k) for k in menu_dict.keys()]
            matches = [[int(_) for _ in m.groups()] for m in matches if m]
            matches = [(3600000*m[0] + 60000*m[1] + m[2]) for m in matches if len(m) == 3]
            ret.append(matches)
        return ret


    def fmtGeneralDuration(self) -> str:
        t = self.duration
        if t <= 0: return ''
        h, t = divmod(t, 3600000)
        m, t = divmod(t,   60000)
        s, t = divmod(t,    1000)
        return f'{h:02d}:{m:02d}:{s:02d}.{t:03d}'


    def fmtFileSize(self) -> str:
        n = self.file_size
        if n <= 0: return ''
        g, n = divmod(n, 1000**3)
        m, n = divmod(n, 1000**2)
        k, n = divmod(n, 1000**1)
        return ((f'{g:_>2d}g' if g else '___') +
                (f'{m:_>3d}m' if m else '____') +
                (f'{k:_>3d}k' if k else '____') +
                (f'{n:_>3d}' if n else '___'))



    def countEachTrackType(self) -> dict:
        tracks : dict[str, int]= {}
        for i, t in enumerate(self.tracks[1:], start=1):
            key = (t.format if t.format else t.track_type)
            tracks[key] = tracks.get(key, 0) + 1
        return tracks


    def fmtTrackTypeCounts(self) -> str:
        '''NOTE this function keeps no order of the tracks.'''
        ret = []
        for k, v in self.countEachTrackType().items():
            ret.append(f'{v}x{k}' if v > 1 else f'{k}')
        return '／'.join(ret)


    def fmtTrackTypeCountsWithOrder(self) -> str:
        '''
        NOTE this function keeps the track order when grouping
        HEVC+FLAC+FLAC+AAC+FLAC shows as HEVC／FLAC×2／AAC／FLAC instead of HEVC／FLAC×3／AAC
        '''
        tracks = []
        last = {}
        for i, t in enumerate(self.tracks[1:], start=1):
            key = (t.format if t.format else t.track_type)
            if key in last.keys():
                last[key] += 1
            else:
                if last:
                    last_key = list(last.keys())[0]
                    num = last.pop(last_key)
                    tracks.append(f'{last_key}' + (f'×{num}' if num > 1 else ''))
                last[key] = 1
            if not self.tracks[1:][i:]: # if no track left
                num = last[key]
                tracks.append(f'{key}' + (f'×{num}' if num > 1 else ''))
        return '／'.join(tracks)


    def digestVideoTracksInfo(self) -> list[str]:
        # hevc|1920×1080|23.98|cfr|10b|main10|yuv420|12345.67s[|Full][|DEFAULT][|Forced][|Delay=?]
        video_infos = []
        for t in self.video_tracks:
            info = []
            # always shown info
            info += [f'{v}'.lower() if (v := t.format) else 'FORMAT?']
            info += [f'{t.width}×{t.height}' + (f'{v}'.upper()[0] if (v := t.scan_type) else '')] # progressive/interlaced
            info += [f'{t.frame_rate_mode}'.lower()]
            info += [f'{float(v):.2f}'] if (v := t.frame_rate) else ['FPS?']
            info += [f'{v}b'] if (v := t.bit_depth) else ['DEPTH?']
            info += [f'{v}'.split('@')[0].replace(' ', '').replace(':', '').lower()] if (v := t.format_profile) else ['PROFILE?']
            info += [(f'{v}' if (v:= t.color_space) else 'COLOR?') + (f'{v}'.replace(':','') if (v:= t.chroma_subsampling) else '?')]
            info += [f'{float(v)/1000:.2f}s'] if (v := t.duration) else ['TIME?']
            # selective info
            info += [f'{v}'.upper()] if (v := t.language) else ''
            info += ['FULL'] if t.color_range != 'Limited' else ''
            info += ['DEFAULT'] if t.default == 'Yes' else ''
            info += ['FORCED'] if t.forced == 'Yes' else ''
            info += [f'DELAY={v}'] if (v := t.delay) else ''
            video_infos.append('|'.join(info))
        return video_infos


    def digestAudioTracksInfo(self) -> list[str]:
        # flac|6ch[|16b]|48kHz[|750kbps][|DEFAULT][|FORCED][|DELAY=?]
        audio_infos = []
        for t in self.audio_tracks:
            info = []
            # always shown
            info += [f'{info}'.lower()] if (info := t.format) else ['FORMAT?']
            info += [f'{info}ch' if (info := t.channel_s) else 'CHANNEL?']
            info += [f'{info}b'.lower()] if (info := t.bit_depth) else '' # some formats have no depth like AAC
            info += [f'{info/1000:.0f}kHz'] if (info := t.sampling_rate) else ['KHZ?']
            info += [f'{info/1000:.0f}kbps'] if (info := t.bit_rate) else '' # some formats have no bit rate mode like AAC
            info += [f'{float(info)/1000:.2f}s'] if (info := t.duration) else ['TIME?']
            info += [f'{info}'.lower()] if (info := t.language) else ['LANG?']
            # selective
            info += ['DEFAULT'] if t.default == 'Yes' else ''
            info += ['FORCED'] if t.forced == 'Yes' else ''
            info += [f'DELAY={info}'] if (info := t.delay) else ''
            audio_infos.append('|'.join(info))
        return audio_infos


    def digestTextTracksInfo(self) -> list[str]:
        # PGS|ja[|DEFAULT][|FORCED][×2]
        data = {}
        for t in self.text_tracks:
            info = []
            # always
            info += [f'{info}' if (info := t.format) else 'FORMAT?']
            info += [f'{info}' if (info := t.language) else 'LANG?']
            # selective
            info += ['DEFAULT'] if t.default == 'Yes' else ''
            info += ['FORCED'] if t.forced == 'Yes' else ''
            key = '|'.join(info)
            data[key] = data.get(key, 0) + 1
        return [f'({k})×{v}' for k, v in data.items()]


    def digestMenuTracksInfo(self) -> list[str]:
        # MKV/MKA: ja|7／en|5
        # MP4: 7／5
        menu_infos = []
        for t in self.menu_tracks:
            d = t.to_data()
            keys = [k for k in d.keys() if re.match(MEDIAINFO_CHAPTER_PATTERN, k)]
            info = []
            info += [d[keys[0]][:2]] if self.format == 'matroska' else ''
            info += [f'{len(keys)}']
            menu_infos += ['|'.join(info)]
        return menu_infos


    def digestFpsInfo(self) -> list[str]:
        if not self.has_video: return []
        ret = []
        for t in self.video_tracks:
            fps = str(t.frame_rate) if t.frame_rate else 'FPS?'
            st = (f'{v}'.upper()[0] if (v := t.scan_type) else '')
            ret.append(f'{fps}{st}')
        return ret


    def fmtFpsInfo(self) -> str:
        return '／'.join(self.digestFpsInfo())




CF = CoreFile




def getCoreFile(path:Path, **kwargs:Any) -> CoreFile:
    return CoreFile(path, **kwargs)




def getCoreFileList(paths:list[Path], kwargs:dict|list[dict]={}, mp:int=NUM_IO_JOBS) -> list[CoreFile]:

    if isinstance(kwargs, dict):
        kwargs = [kwargs] * len(paths)

    if mp > 1:
        ret = []
        pool = Pool(mp)
        for path, kwarg in zip(paths, kwargs):
            ret.append(pool.apply_async(CoreFile, (path,), kwarg))
        pool.close()
        pool.join()
        ret = [r.get() for r in ret]
    else:
        ret = []
        for path, kwarg in zip(paths, kwargs):
            ret.append(CoreFile(path, **kwarg))

    return ret
