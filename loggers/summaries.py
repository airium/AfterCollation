import string
import logging
from pathlib import Path

from utils import listFile
from checkers import AlbumInfo
from utils import getPrintLen


__all__ = ['logScansSummary', 'logMusicSummary']




def logScansSummary(root:Path, files:list[Path], logger):

    records : dict[str, dict[str, int]] = {}

    max_path_len = 0

    for file in sorted(files):
        path = file.relative_to(root).parent.as_posix()
        ext = suffix[1:] if (suffix := file.suffix.lower()).startswith('.') else suffix
        if records.get(path):
            records[path][ext] = records[path].get(ext, 0) + 1
        else:
            records[path] = {ext: 1}

        ascii = len([c for c in path if c in string.printable])
        non_ascii = len(path) - ascii
        max_path_len = max(max_path_len, ascii + 2 * non_ascii)

    logger.info('↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓')
    logger.info(f'Scans layout under "{root}":')
    for path, count in records.items():
        ascii = len([c for c in path if c in string.printable])
        non_ascii = len(path) - ascii
        txt = f'{path}' + (' ' * (max_path_len - ascii - 2*non_ascii)) + ' :'
        for t, n in count.items():
            txt += f' {t.upper()}×{n}'
        logger.info(txt)
    logger.info('↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑')




def logMusicSummary(root:Path, ais:list[AlbumInfo], logger:logging.Logger):
    '''
    Print a generic summary about the content in each album folder.
    Previously, it's not very convenient to compactly list the files within each album.
    '''

    max_len = 0
    for ai in ais:
        dirname = ai.root.name
        # NOTE we add at least 10 more '.' in printing
        assumed_print_length = getPrintLen(dirname) + 10
        if assumed_print_length > max_len:
            max_len = assumed_print_length

    logger.info('↓' * max_len)

    for ai in ais:
        logger.info(f'"{ai.root.name}"' + '.' * (max_len - getPrintLen(ai.root.name)))
        if ai.hires_discs: # HR may have FLAC/SCANS/TXT/MKV
            msg = ''
            for i, hd in enumerate(ai.hires_discs):
                if flac := listFile(hd, ext='flac', rglob=False): msg += f' {len(flac):2d}xFLAC'
                if txts := listFile(hd, ext='txt', rglob=False): msg += f' {len(txts):2d}xTXT'
                if mkvs := listFile(hd, ext='mkv', rglob=False): msg += f' {len(mkvs):2d}xMKV'
                if i != len(ai.hires_discs) - 1: msg += ' |'
            logger.info(f'╚═ HiRes:{msg}')
        if ai.split_discs: # SD may have FLAC/MP3/AAC/LOG/TXT/MKV
            msg = ''
            for i, sd in enumerate(ai.split_discs):
                if flac := listFile(sd, ext='flac', rglob=False): msg += f' {len(flac):2d}xFLAC'
                if mp3s := listFile(sd, ext='mp3', rglob=False): msg += f' {len(mp3s):2d}xMP3'
                if aacs := listFile(sd, ext='m4a', rglob=False): msg += f' {len(aacs):2d}xAAC'
                if logs := listFile(sd, ext='log', rglob=False): msg += f' {len(logs):2d}xLOG'
                if txts := listFile(sd, ext='txt', rglob=False): msg += f' {len(txts):2d}xTXT'
                if mkvs := listFile(sd, ext='mkv', rglob=False): msg += f' {len(mkvs):2d}xMKV'
                if i != len(ai.split_discs) - 1: msg += ' |'
            logger.info(f'╚═ Split:{msg}')
        if ai.joint_discs:  # JD may have FLAC/CUE/LOG/COVER/TXT/MKV
            msg = ''
            for i, jd in enumerate(ai.joint_discs):
                if flac := listFile(jd, ext='flac', rglob=False): msg += f' {len(flac):2d}xFLAC'
                if cues := listFile(jd, ext='cue', rglob=False): msg += f' {len(cues):2d}xCUE'
                if logs := listFile(jd, ext='log', rglob=False): msg += f' {len(logs):2d}xLOG'
                if jpgs := listFile(jd, ext='jpg', rglob=False): msg += f' {len(jpgs):2d}xCOVER'
                if txts := listFile(jd, ext='txt', rglob=False): msg += f' {len(txts):2d}xTXT'
                if mkvs := listFile(jd, ext='mkv', rglob=False): msg += f' {len(mkvs):2d}xMKV'
                if i != len(ai.joint_discs) - 1: msg += ' |'
            logger.info(f'╚═ Joint:{msg}')
        if ai.scans_dirs:   # BK may have WEBP/JPG
            msg = ''
            for i, bd in enumerate(ai.scans_dirs):
                if webps := listFile(bd, ext='webp', rglob=False): msg += f' {len(webps):2d}xWEBP'
                if jpgs := listFile(bd, ext=['jpg', 'jpeg'], rglob=False): msg += f' {len(jpgs):2d}xJPG'
                if i != len(ai.scans_dirs) - 1: msg += ' |'
            logger.info(f'╚═ Scans:{msg}')
        if ai.video_dirs:   # MV may have MKV
            msg = ''
            for i, vd in enumerate(ai.video_dirs):
                if mkvs := listFile(vd, ext='mkv', rglob=False): msg += f' {len(mkvs):2d}MKV'
                if i != len(ai.video_dirs) - 1: msg += ' |'
            logger.info(f'╚═ Video:{msg}')

    logger.info('↑' * max_len)
