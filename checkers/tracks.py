__all__ = [
    'chkCoreFileFormat',
    'chkCfContainerFormat',
    'chkCfTracks',
    ]

from logging import Logger

from utils import *
from langs import *
from configs import *

from helpers.corefile import CF
from .video import *
from .audio import *
from .image import *
from .text import *
from .menu import *
from .archive import *
from .fonts import *




def chkCoreFileFormat(cf: CF, logger: Logger):
    logger.info(CHECKING_1.format(cf.path))
    if not chkCfContainerFormat(cf, logger):
        return
    match cf.ext:
        case 'mkv'|'mp4':
            chkCfTracks(cf, logger)
            chkCfVidTracks(cf, logger)
            chkCfAudTracks(cf, logger)
            chkMenuTracks(cf, logger)
            chkTextTracks(cf, logger)
        case 'mka':
            chkCfTracks(cf, logger)
            chkCfAudTracks(cf, logger)
        case 'flac':
            chkCfTracks(cf, logger)
            chkCfAudTracks(cf, logger)
        case 'png':
            chkCfTracks(cf, logger)
            chkImageTracks(cf, logger)
        case 'ass':
            chkAssFile(cf, logger)
        case '7z'|'zip'|'rar':
            chkArcFile(cf, logger)
        case _:
            logger.error(GOT_BUT_EXPECT_ONE_OF_2.format(cf.ext, VX_ALL_EXTS))




def chkCfTracks(cf: CF, logger: Logger) -> bool:

    if not cf.tracks[1:]:
        logger.info(FILE_HAS_NO_MEDIA_TRACK_0)
        return False

    for other_track in cf.other_tracks:
        logger.warning(FILE_HAS_UNCOMMON_TRACK_1.format(other_track.track_type))

    # track order
    track_ids = {'Video': 1, 'Audio': 2, 'Text': 3, 'Menu': 4, 'Image': 5}
    last_track_type = -1
    for i, track in enumerate(cf.tracks[1:]):
        track_type = track_ids.get(track.track_type, 9999)
        if track_type < last_track_type:
            logger.warning(FILE_TRACK_ORDER_INCORRECT_0)
            break
        last_track_type = track_type

    tracks_types = set(t.track_type for t in cf.tracks[1:])
    if not tracks_types.issubset(MAXIMAL_TRACK_TYPES_IN_EXT[cf.ext]):
        logger.error(FILE_HAS_DISALLOWED_TRACK_0)
        return False
    if not set(MINIMAL_TRACK_TYPES_IN_EXT[cf.ext]).issubset(tracks_types):
        logger.error(FILE_LACKS_REQUIRED_TRACK_0)
        return False

    return True




def chkCfContainerFormat(cf: CF, logger: Logger) -> bool:
    expected_format = EXTS2FORMATS.get(cf.ext)
    if expected_format == None:
        logger.error(UNHANDLED_EXT_1.format(cf.ext))
        return False
    elif expected_format != cf.format:
        logger.error(MISMATCHED_FMT_2.format(cf.format, cf.ext))
        return False
    return True
