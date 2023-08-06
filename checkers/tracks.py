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




def chkFile(cf:CF, logger:logging.Logger):

    logger.info(f'Checking "{cf.path}" ...')
    if not chkContainer(cf, logger):
        return
    match cf.ext:
        case 'mkv'|'mp4':
            chkTracks(cf, logger)
            chkVideoTracks(cf, logger)
            chkAudioTracks(cf, logger)
            chkMenuTracks(cf, logger)
            chkTextTracks(cf, logger)
        case 'mka':
            chkTracks(cf, logger)
            chkAudioTracks(cf, logger)
        case 'flac':
            chkTracks(cf, logger)
            chkAudioTracks(cf, logger)
        case 'png':
            chkTracks(cf, logger)
            chkImageTracks(cf, logger)
        case 'ass':
            chkAssFile(cf, logger)
        case '7z'|'zip'|'rar':
            chkArcFile(cf, logger)
        case _:
            logger.error(f'Got "{cf.ext}" but {VNx_ALL_EXTS=}.')




def chkTracks(cf:CF, logger:logging.Logger) -> bool:

    if not cf.tracks[1:]:
        logger.error('The file has no media tracks.')
        return False

    for other_track in cf.other_tracks:
        logger.warning(f'The file has uncommon track "{other_track.track_type}".')

    # track order
    track_ids = {'Video': 1, 'Audio': 2, 'Text': 3, 'Menu': 4, 'Image': 5}
    last_track_type = -1
    for i, track in enumerate(cf.tracks[1:]):
        track_type = track_ids.get(track.track_type, 9999)
        if track_type < last_track_type:
            logger.warning(f'The track order is incorrect (expect video>audio(flac>aac|ac3)>text>menu).')
            break
        last_track_type = track_type

    tracks_types = set(t.track_type for t in cf.tracks[1:])
    if not tracks_types.issubset(MAXIMAL_TRACK_TYPES_IN_EXT[cf.ext]):
        logger.error('The file contains disallowed media track type.')
        return False
    if not set(MINIMAL_TRACK_TYPES_IN_EXT[cf.ext]).issubset(tracks_types):
        logger.error('The file lacks required media track type.')
        return False

    return True




def chkContainer(cf:CF, logger:logging.Logger) -> bool:
    expected_format = EXTS2FORMATS.get(cf.ext)

    if expected_format is None:
        logger.error(f'Unhandled file extension "{cf.ext}".')
        return False

    elif expected_format != cf.format:
        logger.error(f'The actual media format "{cf.format}" mismatched file extension "{cf.ext}".')
        return False

    return True
