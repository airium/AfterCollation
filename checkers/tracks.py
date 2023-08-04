import logging
from helpers.corefile import CF
from utils.ffmpegutils import *
from configs import *

from .video import *
from .audio import *
from .image import *
from .text import *
from .menu import *
from .archive import *
from .fonts import *


__all__ = [
    'chkFile',
    'chkTracks',
    'chkContainer']




def chkFile(fi:CF, logger:logging.Logger):

    logger.info(f'Checking "{fi.path}" ...')
    if not chkContainer(fi, logger):
        return
    match fi.ext:
        case 'mkv'|'mp4':
            chkTracks(fi, logger)
            chkVideoTracks(fi, logger)
            chkAudioTracks(fi, logger)
            chkMenuTracks(fi, logger)
            chkTextTracks(fi, logger)
        case 'mka':
            chkTracks(fi, logger)
            chkAudioTracks(fi, logger)
        case 'flac':
            chkTracks(fi, logger)
            chkAudioTracks(fi, logger)
        case 'png':
            chkTracks(fi, logger)
            chkImageTracks(fi, logger)
        case 'ass':
            chkAssFile(fi, logger)
        case '7z'|'zip'|'rar':
            chkArcFile(fi, logger)
        case _:
            logger.error(f'Got "{fi.ext}" but {VNx_ALL_EXTS=}.')




def chkTracks(fi:CF, logger:logging.Logger) -> bool:

    if not fi.tracks[1:]:
        logger.error('The file has no media tracks.')
        return False

    for other_track in fi.other_tracks:
        logger.warning(f'The file has uncommon track "{other_track.track_type}".')

    # track order
    track_ids = {'Video': 1, 'Audio': 2, 'Text': 3, 'Menu': 4, 'Image': 5}
    last_track_type = -1
    for i, track in enumerate(fi.tracks[1:]):
        track_type = track_ids.get(track.track_type, 9999)
        if track_type < last_track_type:
            logger.warning(f'The track order is incorrect (expect video>audio(flac>aac|ac3)>text>menu).')
            break
        last_track_type = track_type

    tracks_types = set(t.track_type for t in fi.tracks[1:])
    if not tracks_types.issubset(MAXIMAL_TRACK_TYPES_IN_EXT[fi.ext]):
        logger.error('The file contains disallowed media track type.')
        return False
    if not set(MINIMAL_TRACK_TYPES_IN_EXT[fi.ext]).issubset(tracks_types):
        logger.error('The file lacks required media track type.')
        return False

    return True




def chkContainer(fi:CF, logger:logging.Logger) -> bool:
    expected_format = EXTS2FORMATS.get(fi.ext)

    if expected_format is None:
        logger.error(f'Unhandled file extension "{fi.ext}".')
        return False

    # if the ASS file is non-bom encoding, MediaInfo can recognise it
    if fi.ext == 'ass' and expected_format == 'ASS' and fi.format == 'ass':
        pass
    elif expected_format != fi.format:
        logger.error(f'The actual media format "{fi.format}" mismatched file extension "{fi.ext}".')
        return False

    return True
