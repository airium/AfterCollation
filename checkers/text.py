import logging

from configs import *
from utils import *
from helpers.corefile import CF


__all__ = ['chkTextTracks', 'chkPGS', 'chkAssFile', 'cmpTextContent']




def chkTextTracks(cf:CF, logger:logging.Logger):

    if cf.ext not in COMMON_VIDEO_EXTS:
        logger.error(f'The file is not a known file type with text.')
        return
    if cf.ext not in VNx_VID_EXTS:
        logger.warning(f'The text checker is not designed to check the file type "{cf.ext}".')
        return
    if not cf.has_text:
        return

    text_tracks = cf.text_tracks
    if len(text_tracks) > 1:
        logger.info(f'The file has multiple ({len(text_tracks)}) text tracks.')

    for text_track in text_tracks:
        match text_track.format:
            case 'PGS':
                chkPGS(cf, logger)
            case 'ASS':
                chkPGS(cf, logger)
            case _:
                logger.warning(f'Unhandled text track format "{text_track.format}".')

    if (cf.ext in VNx_EXT_AUD_EXTS) and cf.text_tracks:
        logger.warning('External audio track should not have subtitle track.')
    for i, text_track in enumerate(cf.text_tracks, start=1):
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




def chkPGS(cf:CF, logger:logging.Logger):
    logger.info('PGS checking inside a video file is not supported yet.')




def chkAssFile(cf:CF, logger:logging.Logger):
    if (ass_obj := toAssFileObj(cf.path, test=True)):
        for section in ass_obj.extra_sections:
            logger.warning(f'Found unnecessary ASS section "{section.name}". '
                           'Consider removing it using the standalone tools in the `scripts` folder.')
    else:
        logger.error('The ASS file is invalid or of non-standard encoding.')
        return

    # TODO add more ass content checking




def cmpTextContent(fi1:CF|list[CF], fi2:CF|list[CF], logger:logging.Logger):
    logger.info('Text content comparison inside media files is not supported yet.')
