import logging

from configs import *
from utils import *


__all__ = ['chkTextTracks', 'chkPGS', 'chkAssFile', 'cmpTextContent']




def chkTextTracks(fi:FI, logger:logging.Logger):

    if fi.ext not in COMMON_VIDEO_EXTS:
        logger.error(f'The file is not a known file type with text.')
        return
    if fi.ext not in VNx_VID_EXTS:
        logger.warning(f'The text checker is not designed to check the file type "{fi.ext}".')
        return
    if not fi.has_text:
        return

    text_tracks = fi.text_tracks
    if len(text_tracks) > 1:
        logger.info(f'The file has multiple ({len(text_tracks)}) text tracks.')

    for text_track in text_tracks:
        match text_track.format:
            case 'PGS':
                chkPGS(fi, logger)
            case 'ASS':
                chkPGS(fi, logger)
            case _:
                logger.warning(f'Unhandled text track format "{text_track.format}".')

    if (fi.ext in VNx_EXT_AUD_EXTS) and fi.text_tracks:
        logger.warning('External audio track should not have subtitle track.')
    for i, text_track in enumerate(fi.text_tracks, start=1):
        # TODO: confirm PGS should be default or not
        if i == 1:
            if text_track.default != 'Yes':
                logger.warning('The first text track is not marked as DEFAULT.')
        else:
            if text_track.default == 'Yes':
                logger.warning(f'The video text #{i} should not be as DEFAULT.')
        if text_track.format not in COMMON_TEXT_FORMATS:
            logger.warning(f'The text track format is uncommon ({text_track.format}).')
        if text_track.language not in COMMON_SUBS_LANGS:
            logger.warning(f'The text track language is missing or uncommon ({text_track.language}).')
        if text_track.forced == 'Yes':
            logger.warning(f'The text track should not be Forced..')




def chkPGS(fi:FI, logger:logging.Logger):
    logger.info('PGS checking inside a video file is not supported yet.')




def chkAssFile(fi:FI, logger:logging.Logger):
    if not tstAssFile(fi.path):
        logger.error('The ASS file is invalid or of non-standard encoding.')
        return
    ass_obj = toAssObjs(fi.path)[0]
    for section in ass_obj.extra_sections:
        logger.warning(f'Found unnecessary ASS section "{section.name}". '
                       'Consider removing it using the standalone tools in the `scripts` folder.')

    # TODO add more ass content checking




def cmpTextContent(fi1:FI|list[FI], fi2:FI|list[FI], logger:logging.Logger):
    logger.info('Text content comparison inside media files is not supported yet.')
