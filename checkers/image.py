import re
import itertools
from pathlib import Path
from logging import Logger

from utils import *
from configs import *
from helpers.corefile import CF


__all__ = ['chkCfImage', 'chkScansImage', 'chkImageTracks', 'cmpImageContent']




def chkCfImage(cf: CF, logger: Logger, decode: bool = True) -> bool:

    if cf.ext not in COMMON_IMAGE_EXTS:
        logger.info('The input file is not an image file.')
        return False

    #* check filesize ******************************************************************************

    filesize = cf.path.stat().st_size
    if filesize == 0:
        logger.error(f'The file is empty.')
        return False  # NOTE return on empty file
    elif filesize < SMALL_IMAGE_FILE_SIZE:
        logger.warning('The image file is very small.')

    #* check format/extension consistency **********************************************************

    expected_format = EXTS2FORMATS.get(cf.ext)
    if not expected_format:
        logger.error(f'Unhandled image file extension "{cf.ext}".')
    if expected_format != cf.format:
        logger.error(f'The actual media format "{cf.format}" mismatched file extension "{cf.ext}".')
        return False

    #* check decoding ******************************************************************************
    if decode and not tstFFmpegDecode(cf.path):
        logger.error(f'Failed to decode the image file.')
        return False

    return True




def chkScansImage(cf: CF, temp_dir: Path|None, logger: Logger, decode: bool = True):

    if not chkCfImage(cf, logger, decode=decode): return

    iinfo = cf.image_tracks[0]

    w, h, mode = 0, 0, ''
    if temp_dir: (work_file := temp_dir.joinpath(f'{time.time_ns()}-{cf.path.name}')).hardlink_to(cf.path)
    else: work_file = cf.path

    match cf.ext:
    #* webp ********************************************************************************************************
        case 'webp':
            ret = tstDwebp(f'{work_file.as_posix()}')
            # NOTE don't decode the raw ret['stderr'], it may contain unknown encoding difficult to determine
            # and actually our regex only need the ASCII part
            if m := re.search(DWEBP_STDERR_PARSE_REGEX, ret['stderr']):
                w, h, mode, alpha = m['width'], m['height'], m['mode'], m['alpha']
                q = getWebpQuality(f'{work_file.as_posix()}')
                if q and not ((DEFAULT_WEBP_QUALITY - 3) < q < (DEFAULT_WEBP_QUALITY + 3)):
                    logger.warning(
                        f'The WEBP file "{cf.path}" may have improper quality '
                        f'(got {q} but expect {DEFAULT_WEBP_QUALITY}).'
                        )
                if alpha:
                    logger.info(f'Note an alpha WEBP file "{cf.path}".')
            else:
                if b'cannot open input file' in ret['stderr']:
                    logger.error(f'Libwebp cannot parse the path "{cf.path}". Consider using hardlink mode.')
                else:
                    logger.error(f'Failed to parse "{cf.path}".')

        #* jpeg ********************************************************************************************************
        case 'jpg'|'jpeg':
            w, h, mode = iinfo.width, iinfo.height, iinfo.compression_mode
            if not any((w, h, mode)):
                logger.error(f'Failed to parse necessary metadata from "{cf.path}".')
            if iinfo.chroma_subsampling and iinfo.chroma_subsampling == '4:4:4':
                # rarely, yuv444 is abnormal, give an info record
                logger.info(f'Note a YUV444 JPEG file "{cf.path}".')
        #* other *******************************************************************************************************
        case _:
            raise ValueError(f'Got "{cf.ext}" but "{ALL_EXTS_IN_SCANS=}"')

    if temp_dir: work_file.unlink()

    #* general info ****************************************************************************************************

    w, h, mode = w if w else 0, h if h else 0, mode if mode else ''
    # general check applies to all formats
    if int(w) >= LARGE_SCANS_THRESHOLD or int(h) >= LARGE_SCANS_THRESHOLD:
        logger.info(f'"{cf.path}" ({int(w)}x{int(h)}) may be 1200dpi or higher. Consider downsampling it.')
    if mode.lower() == 'lossless':
        logger.error(f'Detected lossless image "{cf.path}". This is disallowed.')




def chkImageTracks(cf: CF, logger: Logger, decode: bool = True):

    if cf.ext not in COMMON_IMAGE_EXTS:
        logger.error(f'The file is not a known file type with image.')
        return
    if cf.ext not in VX_IMG_EXTS:
        logger.warning(f'The image checker is not designed to check the file type "{cf.ext}".')
        return
    if not cf.has_image:
        logger.error(f'The file has no image track.')
        return

    chkCfImage(cf, logger, decode=decode)




def cmpImageContent(input1: CF|list[CF], input2: CF|list[CF], logger: Logger):

    if isinstance(input1, CF): input1 = [input1]
    if isinstance(input2, CF): input2 = [input2]

    if not input1 and not input2:
        logger.error('Missing input(s).)')
        return

    has_image = True
    for cf in input1 + input2:
        if not cf.has_menu:
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
