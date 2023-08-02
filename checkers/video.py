import re
import logging
from utils import *
from configs import *




def cmpVideoContent(fis1:FI|list[FI], fis2:FI|list[FI], logger:logging.Logger):
    logger.info('Video content comparison is not implemented yet.')
    #TODO can we replace RPC's function here




def chkVideoTracks(fi:FI, logger:logging.Logger, decode:bool=False):

    if fi.ext not in COMMON_VIDEO_EXTS:
        logger.error(f'The file is not a known file type with video.')
        return
    if fi.ext not in VNx_VID_EXTS:
        logger.warning(f'The video checker is not designed to check the file type "{fi.ext}".')
        return
    if not fi.has_video:
        return

    #* ---------------------------------------------------------------------------------------------
    # specific check for each video file type
    match fi.ext:
        case 'mkv':
            for i, vtr in enumerate(fi.video_tracks):
                if i == 0 and vtr.default != 'Yes':
                    logger.warning(f'The MKV video track #{i} is not marked as DEFAULT.')
                if i > 0 and vtr.default == 'Yes':
                    logger.warning(f'The MKV video track #{i} should not be marked as DEFAULT.')
        case 'mp4':
            pass
        case _:
            logger.error(f'Updated {VNx_VID_EXTS=} but forgot to update the checker.')
            return

    #* ---------------------------------------------------------------------------------------------
    # general check applicable to all video files
    if len(fi.video_tracks) > 1:
        logger.error(f'The video has multiple video tracks.')
    if not fi.video_tracks:
        logger.error(f'The video ext {fi.ext} is incorrect.')

    for i, vtr in enumerate(fi.video_tracks):
        if vtr.format not in COMMON_VIDEO_FORMATS:
            logger.warning(f'The video track #{i} encoding format is uncommon ({vtr.format}).')
        if vtr.height not in COMMON_VIDEO_HEIGHTS:
            logger.warning(f'The video track #{i} height is uncommon ({vtr.height}).')
        if vtr.width not in COMMON_VIDEO_WIDTHS:
            logger.warning(f'The video track #{i} width is uncommon ({vtr.width}).')
        if vtr.frame_rate_mode != 'CFR':
            logger.warning(f'The video track #{i} frame rate mode is not CFR ({vtr.frame_rate_mode}).')
        if vtr.frame_rate not in COMMON_VIDEO_FPS:
            logger.warning(f'The video track #{i} frame rate is uncommon ({vtr.frame_rate}).')
        if vtr.bit_depth not in COMMON_VIDEO_DEPTH:
            logger.warning(f'The video track #{i} bit depth is uncommon ({vtr.bit_depth}).')
        if (ff := vtr.format_profile.split('@')[0]) not in COMMON_VIDEO_PROFILES:
            logger.warning(f'The video track #{i} format profile is uncommon ({ff}).')
        if vtr.color_space != 'YUV':
            logger.warning(f'The video track #{i} is not using YUV color space ({vtr.color_space}).')
        if vtr.chroma_subsampling != '4:2:0':
            logger.warning(f'The video track #{i} is not using 4:2:0 ({vtr.chroma_subsampling}).')
        if not vtr.duration:
            logger.warning(f'The video is missing duration information.')
        elif not matchTime(int(float(vtr.duration)), fi.duration, MAX_TRACK_DURATION_DIFF_MS):
            logger.warning(f'The video track #{i} has a different duration.')
        if vtr.language:
            logger.warning(f'The video track #{i} should not have a language tag.')
        if vtr.color_range != 'Limited':
            logger.warning(f'The video track #{i} is using FULL color range.')
        if vtr.forced == 'Yes':
            logger.warning(f'The video track #{i} should not be Forced.')
        if vtr.delay:
            logger.warning(f'The video track #{i} has a delay ({vtr.delay}).')

        # do a full decoding test for each audio track
        if decode:
            if not tryFFMPEGVideoDecode(fi.path, id=i):
                logger.error(f'The video track #{i} failed to decode.')
