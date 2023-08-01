import logging
import itertools
from pathlib import Path

from configs import *
from utils import *
from .misc import *

__all__ = ['pickInfo4NamingDraft', 'loadNamingDraftCSV',
           'fmtQualityLabel', 'fmtTrackLabel']




def pickInfo4NamingDraft(fis:list[FI], logger:logging.Logger) -> list[dict[str, str]]:
    ret = []

    for fi in fis:
        d : dict[str, str] = dict()

        for k, v in VNX_ALL_FIELDS_DICT.items():
            d[k] = ''

        d[FULLPATH_CN] = fi.path.resolve().as_posix()
        d[CRC32_CN] = fi.crc32

        for k, v in VNX_USER_FIELDS_NAMING_DICT.items():  # user fields
            # these keys may be already filled from VNA
            d[k] = getattr(fi, v, '')

        # the following keys are just for presenting mediainfo
        # they have no usage in later stages
        d[DURATION_CN] = fi.fmtGeneralDuration()
        d[FILESIZE_CN] = fi.fmtFileSize()
        d[EXTENSION_CN] = fi.ext
        d[CONTAINER_CN] = fi.format
        d[TRACKCOMP_CN] = fi.fmtTrackTypeCountsWithOrder()
        d[TR_VIDEO_CN] = '／'.join(fi.digestVideoTracksInfo())
        d[TR_AUDIO_CN] = '／'.join(fi.digestAudioTracksInfo())
        d[TR_TEXT_CN] = '／'.join(fi.digestTextTracksInfo())
        d[TR_MENU_CN] = '／'.join(fi.digestMenuTracksInfo())

        ret.append(d)

    return ret




def loadNamingDraftCSV(path:Path, logger:logging.Logger) -> tuple[dict[str, str], list[dict[str, str]]]:

    succ, lines = readCSV(path)
    if not succ:
        logger.error(f'Error in loading CSV "{path}".')
        return {}, []
    lines = unquotEntries4CSV(lines)

    try:
        infos = []
        for info in lines:
            d : dict[str, str] = {}
            for k, v in VNX_CSV_PERSISTENT_KEY_DICT.items():
                d[v] = info[k]
            for k, v in VNX_USER_FIELDS_NAMING_DICT.items():
                d[v] = info[k]
            infos.append(d)
        # TODO update the logic to find the base line by BASE_LINE_LABEL, not the first line
        default_info, infos = infos[0], infos[1:]
        enabled = toEnabledList([info[ENABLE_VAR] for info in infos])
        enabled_infos = list(itertools.compress(infos, enabled))
        if len(infos) != len(enabled_infos):
            logger.info(f'Enabled {len(enabled_infos)} out of {len(infos)} files in the naming plan.')
    except KeyError as e:
        logger.error(f'Error in the finding required key in csv data ({e}).')
        return {}, []

    return default_info, enabled_infos




def fmtQualityLabel(fi:FI|MI, logger:logging.Logger|None=None) -> str:

    # files without video track have no quality label
    if not fi.video_tracks: return ''

    vtr = fi.video_tracks[0]

    h = int(vtr.height) if vtr.height else 0
    h = 1080 if (MIN_VID_HEIGHT_TO_STILL_LABEL_AS_1080 <= h <= 1080) else h

    format = (vtr.format if vtr.format else '').lower()
    profile = (vtr.format_profile if vtr.format_profile else '').split('@')[0].replace(' ', '')

    p = ''
    if format == 'hevc':
        if profile == 'Main10':
            p = 'Ma10p'
        elif profile == 'Main':
            p = ''
        elif profile == 'FormatRange' and vtr.bit_depth == 10 and vtr.chroma_subsampling == '4:4:4':
            p = 'Ma444-10p'
        else:
            if logger: logger.warning(f'Unhandled HEVC profile "{profile}".')
    elif format == 'avc':
        if profile == 'High10':
            p = 'Hi10p'
        elif profile == 'High':
            p = ''
        elif profile == 'High4:4:4Predictive':
            p = 'Hi444pp' #
        else:
            if logger: logger.warning(f'Unhandled AVC profile "{profile}" during naming. Please report.')
    else:
        if logger: logger.warning(f'Unhandled video format "{format}" during naming. Please report.')

    st = 'i' if vtr.scan_type == 'Interlaced' else 'p' # actually we don't have any interlaced video
    return f'{p}_{h}{st}' if p else f'{h}{st}'




def fmtTrackLabel(fi:FI|MI, logger:logging.Logger|None=None) -> str:

    if not fi.video_tracks: return ''

    tracks = {}
    for t in (fi.video_tracks + fi.audio_tracks):
        if t.format:
            format = t.format.lower()
            tracks[format] = tracks.get(format, 0) + 1

    tlabel = ''

    if n := tracks.pop('hevc', 0):
        tlabel += (f'{n}x265' if n > 1 else f'x265')
    elif n := tracks.pop('avc', 0):
        tlabel += (f'{n}x264' if n > 1 else f'x264')
    else:
        raise ValueError # it should be impossible to reach here if return if not minfo.video_tracks

    if n := tracks.pop('flac', 0):
        tlabel += (f'_{n}flac' if n > 1 else f'_flac')

    # TODO: do we need to care about the order of the following?

    if n := tracks.pop('aac', 0):
        tlabel += (f'_{n}aac' if n > 1 else f'_aac')

    if n := tracks.pop('ac3', 0):
        tlabel += (f'_{n}ac3' if n > 1 else f'_ac3')

    if n := tracks.pop('dts', 0):
        tlabel += (f'_{n}dts' if n > 1 else f'_dts')

    for k in tracks.keys():
        if logger: logger.warning(f'Unhandled v/a format "{k}". Please report')

    return tlabel
