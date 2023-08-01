import logging
import itertools

from utils.fileinfo import FI
from utils.ffmpegutils import *
from configs import *


__all__ = ['chkImage', 'cmpImageContent']




def chkImage(input:FI, logger:logging.Logger, decode:bool=True):

    if input.ext not in COMMON_IMAGE_EXTS:
        logger.info('The input file is not an image file.')
        return

    expected_format = EXTS2FORMATS.get(input.ext)
    if not expected_format:
        logger.error(f'Unhandled image file extension "{input.ext}".')
    if expected_format != input.gtr.format:
        logger.error(f'The actual media format "{input.gtr.format}" mismatched file extension "{input.ext}".')

    if decode:
        if not tryFFMPEGDecode(input.path):
            logger.error(f'FFmpeg cannot decode the image file.')




def cmpImageContent(input1:FI|list[FI], input2:FI|list[FI], logger:logging.Logger):

    if isinstance(input1, FI): input1 = [input1]
    if isinstance(input2, FI): input2 = [input2]

    if not input1 and not input2:
        logger.error('Missing input(s).)')
        return

    has_image = True
    for fi in input1 + input2:
        if not fi.has_menu:
            has_image = False
    if not has_image:
        logger.info('No image track found in input(s).')
        return

    match len(input1), len(input2):
        case 1, 1:
            if not input1[0].has_image:
                logger.error(f'"{input1[0].path}" has no image track.')
            elif not input2[0].has_image:
                logger.error(f'"{input2[0].path}" has no image track.')
            else:
                img1s = input1[0].image_tracks
                img2s = input2[0].image_tracks
                if len(img1s) != len(img2s):
                    logger.error(f'Number of image tracks differs: {len(img1s)} vs {len(img2s)}')
                for i, img1, img2 in zip(itertools.count(), img1s, img2s):
                    h1, w1 = img1.height, img1.width
                    h2, w2 = img2.height, img2.width
                    if not (h1 and w1 and h2 and w2):
                        logger.error(f'Image pair #{i} Failed to obtain the image info.')
                        continue
                    if h1 != h2 or w1 != w2:
                        logger.warning(f'Image pair #{i} has different resolution: {w1}x{h1} vs {w2}x{h2}.')
                    # TODO do image diff
        case 1, _:
            logger.info('1 vs multi-input is not supported for image check for now.')
        case _, 1:
            logger.info('Multi vs 1-input is not supported for image check for now.')
        case _, _:
            logger.info('Multi vs multi-input is not supported for image check for now.')
