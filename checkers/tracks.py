import logging
from utils.fileinfo import FI
from utils.ffmpegutils import *
from configs import *


def chkTracksFI(fi:FI, logger:logging.Logger):

    if not fi.tracks[1:]:
        logger.info('The input file has no media tracks.')

    # track order
    track_ids = {'General': 0, 'Video': 10, 'Audio': 20, 'Text': 30, 'Menu': 40, 'Image': 1000}
    last_track_type = -1
    for i, track in enumerate(fi.tracks):
        track_type = track_ids.get(track.track_type, 9999)
        if track_type < last_track_type:
            logger.warning(f'Track order is incorrect (expect video>audio(flac>aac|ac3)>text>menu).')
            break
        last_track_type = track_type

    # expected_format = EXTS2FORMATS.get(input.ext)
    # if not expected_format:
    #     logger.error(f'Unhandled image file extension "{input.ext}".')
    # if expected_format != input.gtr.format:
    #     logger.error(f'The actual media format "{input.gtr.format}" mismatched file extension "{input.ext}".')

    for other_track in fi.other_tracks:
        logger.warning(f'The file has uncommon track "{other_track.track_type}".')