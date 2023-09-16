from __future__ import annotations

import shutil
import itertools
import traceback
from pathlib import Path
from logging import Logger
from typing import Iterable, Callable, Optional
from operator import attrgetter
from multiprocessing import Pool

from langs import *
from utils import *
from configs import *
from loggers import initLogger
import configs.runtime as cr
from .misc import handleResourceSrc
from .image import ImageFile
from .video import VideoFile
from .scans import cleanScansFilenames
from .naming import *
from .dirgetter import proposeFilePath, initAlbumDraftDstParentDir
from .albumfile import AlbumFile
from .albuminfo import AlbumInfo


from pymediainfo import Track


__all__ = [
    'matchAlbumName',
    'matchArtistsName',
    'matchTrackName',
    'matchIndex',
    'lookupVGMDB',
    'listAlbumDirs',
    'pickCoverArtPaths',
    'pickLogPath',
    'pickCuePath',
    'pairLog2JointAud',
    'pairCue2JointAud',
    'pair2xCue2JointAud',
    'pairCueLog2JointAud',
    'pair2xCueLog2JointAud',
    'processAlbumSourceDir',
    'processAlbumSourceDirs',
    'collectAlbumsInfo',
    'placeAlbums',
    ]


def _runJob(job: tuple[Callable, tuple]) -> bool:
    return job[0](*job[1])

def matchAlbumName(pre: str|None, mid: str|None, seen_names: str|list[str]) -> bool:
    if isinstance(seen_names, str): seen_names = [seen_names]
    if (not pre and not mid) or (not seen_names):
        return False
    if pre:
        for seen_name in seen_names:
            if suppressPunctuation(pre) in suppressPunctuation(seen_name):
                return True
    if mid:
        for seen_name in seen_names:
            if suppressPunctuation(mid) in suppressPunctuation(seen_name):
                return True
    # NOTE aftname is not accurate as it is ususally a further description to the album name
    return False




def matchArtistsName(art: str|None, seen_artists: str|list[str]) -> bool:
    if isinstance(seen_artists, str): seen_artists = [seen_artists]
    if (not art) or (not seen_artists):
        return False
    if art:
        for seen_artist in seen_artists:
            if suppressPunctuation(art) in suppressPunctuation(seen_artist): return True
    return False




def matchTrackName(path_trname: str|None, metadata_trname: str) -> bool:
    if not path_trname or not metadata_trname:
        return False
    if suppressPunctuation(path_trname) == suppressPunctuation(metadata_trname):
        return True
    return False




def matchIndex(index: int|str, metadata_index: int|str) -> bool:
    if (not index) or (not metadata_index):
        return False  # this is safe as idx=0 is not allowed
    index = int(index)
    metadata_index = int(metadata_index)
    if index == metadata_index:
        return True
    return False




def lookupVGMDB(album_info: AlbumInfo, logger):

    if album_info.is_hires:
        logger.info(f'Skipped Hi-Res album "{album_info.root.name}".')
        return

    logger.info(f'Looking for "{album_info.root.name}" ...')

    album_ids = set()
    for catalog in album_info.catalogs:
        # XXXX1234~5 => XXXX1234
        # XXXX1234-1 XXXX1234-2 => XXXX1234
        # XXXX1234-01 XXXX1234-02 => XXXX1234
        # XXXX1234A XXXX1234B => XXXX1234
        if (m := re.match(CATALOG_MULTIDISC_REGEX, catalog)): catalog = m['catalog']
        if not catalog: continue
        if result := searchVGMDB(catalog):
            # TODO VGMDB API is unstable, temp fix here
            # this means our VGMDB lib is penetrated
            # if isinstance(result, str):
            #     continue # this is a bug
            if len(found_albums := result.get('results', {}).get('albums', [])) != 1:
                continue
            album_ids.add(found_albums[0]['link'].split('/')[-1])

    if album_info.catalogs and not album_ids:
        logger.warning('Cannot find any album info on VGMDB using possible catalogs. Filenames may be incorrect.')

        # TODO we heavily reused the search result, assemble a class for easier access

    # if midname is present, we first try it alone as it's most likely unique
    if not album_ids and album_info.midname:
        name = re.sub(r'／', r' ', album_info.midname)
        if len(found_albums := searchVGMDB(name).get('results', {}).get('albums', [])) == 1:
            album_ids.add(found_albums[0]['link'].split('/')[-1])

    # if midname is not unique, try prename + midname
    if not album_ids and album_info.midname and album_info.prename:
        name = re.sub(r'／', r' ', album_info.prename + ' ' + album_info.midname)
        if len(found_albums := searchVGMDB(name).get('results', {}).get('albums', [])) == 1:
            album_ids.add(found_albums[0]['link'].split('/')[-1])

    # often we have only the prename, but this very difficult to get the expected results
    # this is because the prename can be expressed in many ways
    if not album_ids and album_info.prename:
        name = re.sub(r'／', r' ', album_info.prename + ' ' + album_info.midname)
        if len(found_albums := searchVGMDB(name).get('results', {}).get('albums', [])) == 1:
            album_ids.add(found_albums[0]['link'].split('/')[-1])

    # but we don't use aftname, it's rarely seen in our releases
    # elif album_info.aftname:
    #     pass

    if not album_ids:
        logger.warning('Cannot find any album info on VGMDB using album name.')
        logger.warning('Cannot find the album on VGMDB or inadequate info to search for it.')
        return

    album_ids = sorted(album_ids)
    if len(album_ids) > 1:
        logger.info(f'Found more than {len(album_ids)} albums resided on VGMDB.')

    vgmdb_dicts = [info for info in [getVGMDBAlbumInfo(album_id) for album_id in album_ids] if info]
    if not vgmdb_dicts:
        logger.error('Failed to obtain the album info from VGMDB. Please check your network connection.')
    if len(vgmdb_dicts) != len(album_ids):
        logger.warning(f'Failed to obtain some album info from VGMDB. Please check your network connection.')

    local_info = album_info
    for vgmdb_dict in vgmdb_dicts:
        vgmdb_info = AlbumInfoVGMDB(vgmdb_dict)

        if local_info.date != vgmdb_info.yymmdd:
            logger.warning(f'Album date mismatches VGMDB.')
        if local_info.midname and not matchAlbumName(local_info.prename, local_info.midname, vgmdb_info.names):
            logger.warning(f'Album name mismatches VGMDB.')
        # NOTE virtual artists (fictional characters in games/videos) may be part of the album name on VGMDB
        # so we need to check if the artist labelled in dirname is part of the VGMDB album name
        if local_info.artists \
        and not matchArtistsName(local_info.artists, vgmdb_info.artists) \
        and not matchAlbumName(local_info.artists, local_info.artists, vgmdb_info.names):
            logger.warning(f'Album artists mismatches VGMDB.')
        if vgmdb_info.is_bonus and 'spcd' not in local_info.prename.lower():
            logger.warning(f'Album is bonus but not labelled with "SPCD".')
        for catalog in vgmdb_info.cd_catalogs:
            # TODO this checking is in fact unstable, but we mostly get the VGMDB through catalog labelled in filenames
            # so in practical we can use this implementation for now, as we should rarely get an unfound
            if catalog.lower() not in local_info.catalogs:
                logger.warning(f'Album catalog "{catalog}" from VGMDB is not labelled in local filenames.')




def listAlbumDirs(root: Path, logger: Logger, root_is_cds: bool = True) -> list[Path]:
    '''
    List all possible ALBUM directories under the "CDs" dir.
    This function can identify grouped album folders.
    The function also check if there is unnecessary files directly under the "CDs" directory.

    Return: list[Path]: the list of album folder under "cds_dir"
    '''

    if DEBUG: assert root.is_dir()

    if root_is_cds and root.name != STD_CDS_DIRNAME:
        logger.warning(AR_SKIPPED_BY_DIRNAME_2.format(root, STD_CDS_DIRNAME))
        return []

    if root_is_cds: logger.info(AR_INSPECTING_2.format(root, 'CDs ROOT'))
    else: logger.info(AR_INSPECTING_2.format(root, 'CDs CLUSTER'))

    ret = []
    for subdir in listDir(root, rglob=False):

        subsubdirs = listDir(subdir, rglob=False)
        subsubfiles = listFile(subdir, ext=ALL_EXTS_IN_CDS, rglob=False)

        if len(subsubdirs) == 0 and len(subsubfiles) == 0:
            logger.warning(AR_FOUND_EMPTY_DIR_1.format(subdir))
            continue
        if len(subsubdirs) == 1 and len(subsubfiles) == 0:
            logger.warning(AR_FOUND_UNNECESSARY_DIR_1.format(subdir))

        #! all allowed ALBUM placement under CDs:
        #! 1: CDs/ALBUM/*
        #! 2: CDs/CLUSTER/ALBUM/*
        #! we allow at most 1 level clustering under CDs (2)

        # layout 1
        if re.match(ALBUM_DIR_MIN_PATTERN, subdir.name.lower()):
            logger.info(f'Added "{subdir}".')
            ret.append(subdir)

        # layout 2
        #! only go deeper if the parent is CDs
        elif root_is_cds and any(re.match(ALBUM_DIR_MIN_PATTERN, ssd.name.lower()) for ssd in subsubdirs):
            logger.info(AR_FOUND_CLUSTER_1.format(subdir.name))
            ret += listAlbumDirs(subdir, logger, root_is_cds=False)

        else:
            logger.warning(AR_IGNORED_DIR_1.format(subdir.relative_to(root)))
            # we just skipped these malformed dirname
            # TODO: can we try to determine whether they are possible album? this requires changing later functions

    return ret




def pickCuePath(cue_paths: list[Path], preferred_name: str|list[str]) -> Path|None:
    '''
    Give a list of cue files, pick the first one that matches the preferred name.
    This will pick utf-8 cue first if possible (note that it only looks at the filename not content).
    Return:
        `Path` if a cue file matches the preferred name
        `None` if no cue file is given or no cue file matches the preferred name
        if no preferred_name is given, the first cue file will be returned
    '''
    if not cue_paths: return None
    if not preferred_name: return cue_paths[0]
    if isinstance(preferred_name, str): preferred_name = [preferred_name]
    for cue_path in [p for p in cue_paths if '.utf' in p.stem.lower()]:
        for name in preferred_name:
            if cue_path.name.lower().startswith(name.lower()):
                return cue_path
    for cue_path in [p for p in cue_paths if '.utf' not in p.stem.lower()]:
        for name in preferred_name:
            if cue_path.name.lower().startswith(name.lower()):
                return cue_path
    return None




def pickLogPath(log_paths: list[Path], preferred_name: str|list[str]) -> Path|None:
    '''
    Give a list of log files, pick the first one that matches the preferred name.
    Return:
        `Path` if a log file matches the preferred name
        `None` if no log file is given or no log file matches the preferred name
        if no preferred_name is given, the first log file will be returned
    '''
    if not log_paths: return None
    if not preferred_name: return log_paths[0]
    if isinstance(preferred_name, str): preferred_name = [preferred_name]
    for log_path in log_paths:
        for name in preferred_name:
            if log_path.name.lower().startswith(name.lower()):
                return log_path
    return None




def pickCoverArtPaths(img_paths: Iterable[Path], preferred_name: str|list[str]|None = None) -> list[Path]:
    '''
    Give a list of cover files, pick all possible cover arts that matches the preferred name.
    A default name 'cover[0-9]{1,2}' will be last searched.
    Return:
        `Path` if a cover file matches the preferred name
        `None` if no cover file is given or no cover file matches the preferred name
        if no preferred_name is given, the first cover file will be returned
    '''
    img_paths = list(img_paths)
    if not img_paths: return []
    if not preferred_name: preferred_name = []
    if isinstance(preferred_name, str): preferred_name = [preferred_name]
    paths: set[Path] = set()
    for img_path in img_paths:
        for name in preferred_name:
            if img_path.stem.lower() == name.lower() or img_path.name.lower() == name.lower():
                paths.add(img_path)
    for img_path in img_paths:
        if re.match(COVER_ART_FILENAME_PATTERN, img_path.name):
            paths.add(img_path)
    return sorted(paths)




def pairLog2JointAud(log_paths: list[Path], aud_paths: list[Path]) -> list[tuple[Path, Path]]:
    '''
    Given two lists of log and audio files, pair and return them if filenames all match.
    Return an empty list if filenames do not match.
    '''
    if DEBUG: assert len(log_paths) == len(aud_paths)
    if len(set(log_paths)) != len(log_paths) or len(set(aud_paths)) != len(aud_paths): return []
    log_paths = sorted(log_paths, key=lambda p: p.stem.lower())
    aud_paths = sorted(aud_paths, key=lambda p: p.stem.lower())
    for log_path, aud_path in zip(log_paths, aud_paths):
        if log_path.stem.lower() == aud_path.stem.lower(): pass
        else: return []
    return list(zip(log_paths, aud_paths))




def pairCue2JointAud(cue_paths: list[Path], aud_paths: list[Path]) -> list[tuple[Path, Path]]:
    '''
    Given two lists of cue and audio files, pair and return them if filenames all match.
    Return an empty list if filenames do not match.
    '''
    if DEBUG: assert len(cue_paths) == len(aud_paths)
    if len(set(cue_paths)) != len(cue_paths) or len(set(aud_paths)) != len(aud_paths): return []
    cue_paths = sorted(cue_paths, key=lambda p: p.stem.lower())
    aud_paths = sorted(aud_paths, key=lambda p: p.stem.lower())
    for cue_path, aud_path in zip(cue_paths, aud_paths):
        if cue_path.stem.lower().startswith(aud_path.stem.lower()): pass
        else: return []
    return list(zip(cue_paths, aud_paths))




def pair2xCue2JointAud(cue_paths: list[Path], aud_paths: list[Path]) -> list[tuple[Path, Path]]:
    '''Similar to `pairCue2JointAud`, but consider sometimes we get 2 cue where 1 is utf8.'''
    if DEBUG: assert len(cue_paths) == 2 * len(aud_paths)
    cue_paths = sorted(cue_paths, key=lambda p: p.stem.lower())
    aud_paths = sorted(aud_paths, key=lambda p: p.stem.lower())
    cue_utf_paths = [cue_path for cue_path in cue_paths if '.utf' in cue_path.name.lower()]
    if len(cue_utf_paths) == len(aud_paths):
        if pairs := pairCue2JointAud(cue_utf_paths, aud_paths):
            return pairs
    cue_non_utf_paths = [cue_path for cue_path in cue_paths if '.utf' not in cue_path.name.lower()]
    if len(cue_non_utf_paths) == len(aud_paths):
        if pairs := pairCue2JointAud(cue_non_utf_paths, aud_paths):
            return pairs
    return []




def pairCueLog2JointAud(cue_paths: list[Path], log_paths: list[Path],
                        aud_paths: list[Path]) -> list[tuple[Path, Path, Path]]:
    if DEBUG: assert len(cue_paths) == len(log_paths) == len(aud_paths)
    if len(set(cue_paths)) != len(cue_paths)\
    or len(set(log_paths)) != len(log_paths)\
    or len(set(aud_paths)) != len(aud_paths):
        return []
    cue_paths = sorted(cue_paths, key=lambda p: p.stem.lower())
    log_paths = sorted(log_paths, key=lambda p: p.stem.lower())
    aud_paths = sorted(aud_paths, key=lambda p: p.stem.lower())
    for cue, log, aud in zip(cue_paths, log_paths, aud_paths):
        if cue.stem.lower().startswith(aud.stem.lower())\
        and log.stem.lower() == aud.stem.lower():
            continue
        else:
            return []
    return list(zip(cue_paths, log_paths, aud_paths))




def pair2xCueLog2JointAud(cue_paths: list[Path], log_paths: list[Path],
                            aud_paths: list[Path]) -> list[tuple[Path, Path, Path]]:
    if DEBUG: assert len(cue_paths) == 2 * len(log_paths) == 2 * len(aud_paths)
    cue_utf_paths = [cue_path for cue_path in cue_paths if '.utf' in cue_path.name.lower()]
    if len(cue_utf_paths) == len(log_paths) == len(aud_paths):
        if pairs := pairCueLog2JointAud(cue_utf_paths, log_paths, aud_paths):
            return pairs
    cue_non_utf_paths = [cue_path for cue_path in cue_paths if '.utf' not in cue_path.name.lower()]
    if len(cue_non_utf_paths) == len(log_paths) == len(aud_paths):
        if pairs := pairCueLog2JointAud(cue_non_utf_paths, log_paths, aud_paths):
            return pairs
    return []




def sortAudioDirs2Discs(aud_dirs: Iterable[Path], logger: Logger, root: Path) -> list[list[Path]]:

    discs: list[list[Path]] = []

    for aud_dir in set(aud_dirs):
        logger.info(PROCESSING_1.format(aud_dir.name))
        rel_path = aud_dir.relative_to(root)

        imgs = listFile(aud_dir, ext=('png', 'jpg', 'jpeg'), rglob=False)

        # NOTE: AD_SRC_EXTS = AD_AUD_EXTS + AD_EAC_EXTS + AD_VID_EXTS + AD_IMG_EXTS
        # acl = Audio + Cue + Log i.e. all artifacts except imgs
        acls = set(listFile(aud_dir, ext=(AD_AUD_EXTS + AD_EAC_EXTS), rglob=False))
        cues = listFile(*acls, ext='cue', rglob=False)
        logs = listFile(*acls, ext='log', rglob=False)

        if mp3s := listFile(aud_dir, ext='mp3', rglob=False):
            discs.append(mp3s)
            acls.difference_update(mp3s)

        # TODO: this is not bug free as cue+m4a(alac) can happen though rarely, give a warning for now
        if m4a_paths := listFile(aud_dir, ext='m4a', rglob=False):
            discs.append(m4a_paths)
            acls.difference_update(m4a_paths)
            if cues: logger.warning(AD_GOT_CUE_IN_M4A_1.format(rel_path))

        auds = listFile(*acls, ext=AD_AUD_EXTS, rglob=False)  #! no m4a and mp3 ↑

        match len(logs), len(cues), len(auds):

        #* NO AUD ------------------------------------------------------------------
            case _, _, 0:
                pass

            #* NO CUE, NO LOG ------------------------------------------------------------------
            case 0, 0, _:  # 0,0,1+ = 1 SD
                discs.append(auds[:])
                acls.difference_update(auds)

            #* NO CUE --------------------------------------------------------------------------
            case 1, 0, _:  # 1,0,1+ = 1 SD
                paths = auds[:]
                paths.append(logs[0])
                discs.append(paths)
                acls.difference_update(paths)
            case _, 0, _:  # 2+,0,1+ = 2+ JD
                if len(logs) == len(auds):
                    if pairs := pairLog2JointAud(logs, auds):
                        pairs = list(pairs)
                    else:
                        pairs = list(zip(logs, auds))
                        logger.warning(AD_POSSIBLY_PICKED_WRONG_LOG_1.format(rel_path))
                    for log_path, aud_path in pairs:
                        paths = [aud_path, log_path]
                        paths.extend(pickCoverArtPaths(imgs))
                        discs.append(paths)
                        acls.difference_update(paths)
                else:
                    logger.error(AD_GOT_AMBIGUOUS_LAYOUT_1.format(rel_path))

            #* NO LOG --------------------------------------------------------------------------
            case 0, 1, 1:  # 0,1,1 = 1 JD (possibly 1 SD though)
                paths = [auds[0], cues[0]]
                paths.extend(pickCoverArtPaths(imgs, cues[0].stem))
                discs.append(paths)
                acls.difference_update(paths)
            case 0, _, 1:  # 0,2+,1 = 1 JD (possibly 1 SD though)
                paths = [auds[0]]
                if cue_path := pickCuePath(cues, auds[0].stem):
                    paths.append(cue_path)
                else:
                    logger.warning(AD_POSSIBLY_PICKED_WRONG_CUE_1.format(rel_path))
                    paths.append(cues[0])
                    paths.extend(pickCoverArtPaths(imgs, cues[0].stem))
                discs.append(paths)
                acls.difference_update(paths)
            case 0, 1, _:  # 0,1,2+ = 1 SD
                paths = auds[:]
                discs.append(paths)
                acls.difference_update(paths)
            case 0, _, _:  # 0,2+,2+ = possibly 2+ JD, wont consider SD
                if len(cues) == len(auds):
                    if pairs := pairCue2JointAud(cues, auds):
                        for cue_path, aud_path in pairs:
                            paths = [aud_path, cue_path]
                            paths.extend(pickCoverArtPaths(imgs))
                            discs.append(paths)
                            acls.difference_update(paths)
                    else:
                        logger.warning(AD_POSSIBLY_PICKED_WRONG_CUE_1.format(rel_path))
                        for cue_path, aud_path in zip(cues, auds):
                            paths = [aud_path, cue_path]
                            paths.extend(pickCoverArtPaths(imgs))
                            discs.append(paths)
                            acls.difference_update(paths)
                elif len(cues) == 2 * len(auds):
                    if pairs := pair2xCue2JointAud(cues, auds):
                        for cue_path, aud_path in pairs:
                            paths = [aud_path, cue_path]
                            paths.extend(pickCoverArtPaths(imgs))
                            discs.append(paths)
                            acls.difference_update(paths)
                    else:
                        logger.error(AD_GOT_AMBIGUOUS_LAYOUT_1.format(aud_dir))

            #* LOG + CUE -----------------------------------------------------------------------
            case 1, 1, 1:  # 1,1,1 = 1 JD
                paths = [auds[0], cues[0], logs[0]]
                paths.extend(pickCoverArtPaths(imgs, [p.stem for p in paths]))
                discs.append(paths)
                acls.difference_update(paths)
            case 1, _, 1:  # 1,2+,1 = 1 JD
                paths = [auds[0], logs[0]]
                if cue_path := pickCuePath(cues, [p.stem for p in paths]):
                    paths.append(cue_path)
                else:
                    logger.warning(AD_POSSIBLY_PICKED_WRONG_CUE_1.format(rel_path))
                    paths.append(cues[0])
                    paths.extend(pickCoverArtPaths(imgs, [p.stem for p in paths]))
                discs.append(paths)
                acls.difference_update(paths)
            case _, 1, 1:  # 2+,1,1 = 1 JD
                logger.warning(AD_GOT_MULTI_LOG_1.format(rel_path))
                paths = [auds[0], cues[0]]
                if log_path := pickLogPath(logs, [p.stem for p in paths]):
                    paths.append(log_path)
                else:
                    logger.warning(AD_POSSIBLY_PICKED_WRONG_LOG_1.format(rel_path))
                    paths.extend(pickCoverArtPaths(imgs, [p.stem for p in paths]))
                discs.append(paths)
                acls.difference_update(paths)
            case _, _, 1:  # 2+,2+,1 = 1 JD
                logger.warning(AD_GOT_MULTI_LOG_1.format(rel_path))
                paths = [auds[0]]
                if cue_path := pickCuePath(cues, auds[0].stem):
                    paths.append(cue_path)
                else:
                    logger.warning(AD_POSSIBLY_PICKED_WRONG_CUE_1.format(rel_path))
                    paths.append(cues[0])
                if log_path := pickLogPath(logs, [p.stem for p in paths]):
                    paths.append(log_path)
                else:
                    logger.warning(AD_POSSIBLY_PICKED_WRONG_LOG_1.format(rel_path))
                    paths.append(logs[0])
                    paths.extend(pickCoverArtPaths(imgs, [p.stem for p in paths]))
                discs.append(paths)
                acls.difference_update(paths)
            case 1, _, _:  # 1,1+,2+ = 1 SD
                paths = auds[:]
                paths.append(logs[0])
                discs.append(paths)
                acls.difference_update(paths)
            case _, _, _:  # 2+,1+,2+ = possibly 2+ JD, wont consider SD
                if len(logs) == len(cues) == len(auds):
                    if pairs := pairCueLog2JointAud(cues, logs, auds):
                        for pair in pairs:
                            paths = list(pair)
                            paths.extend(pickCoverArtPaths(imgs, [p.stem for p in paths]))
                            discs.append(paths)
                            acls.difference_update(paths)
                elif 2 * len(logs) == len(cues) == 2 * len(auds):
                    if pairs := pair2xCueLog2JointAud(cues, logs, auds):
                        for pair in pairs:
                            paths = list(pair)
                            paths.extend(pickCoverArtPaths(imgs, [p.stem for p in paths]))
                            discs.append(paths)
                            acls.difference_update(paths)
                else:
                    logger.error(AD_GOT_AMBIGUOUS_LAYOUT_1.format(rel_path))

        for path in acls:
            logger.warning(AD_UNUSED_FILE_1.format(path.relative_to(root)))

    return discs




def _mvAlbumCDs(cd_paths: list[list[Path]], dst_cds_dir: Path, logger: Logger, root: Path) -> list[tuple[Path, Path]]:

    dsts: list[Path] = []
    jobs: list[tuple[Callable, tuple]] = []

    for i, disc in enumerate(cd_paths, start=1):
        (dst_dir := dst_cds_dir / f'{i:03d}').mkdir(parents=True, exist_ok=True)
        for src in disc:
            afile = AlbumFile(src)
            match afile.ext:
                case 'mp3':
                    dst = (dst_dir / src.name).with_suffix('.mp3')
                    jobs.append((tryHardlinkThenCopy, (src, dst)))
                case 'flac':
                    dst = (dst_dir / src.name).with_suffix('.flac')
                    jobs.append((replaceIfSmaller, (src, dst, afile.bit)))
                case 'm4a':
                    if afile.format == 'alac':
                        dst = (dst_dir / src.name).with_suffix('.flac')
                        jobs.append((toFLAC, (src, dst)))
                    elif afile.format == 'aac':
                        dst = (dst_dir / src.name).with_suffix('.m4a')
                        jobs.append((tryHardlinkThenCopy, (src, dst)))
                    else:
                        logger.warning(AD_GOT_NON_ALAC_AAC_M4A_1.format(src.relative_to(root)))
                        dst = (dst_dir / src.name).with_suffix('.m4a')
                        jobs.append((tryHardlinkThenCopy, (src, dst)))
                case 'wav'|'wav64'|'tak'|'ape':
                    dst = (dst_dir / src.name).with_suffix('.flac')
                    jobs.append((toFLAC, (src, dst)))
                case 'jpg'|'jpeg':
                    dst = (dst_dir / src.name).with_suffix('.jpg')
                    jobs.append((tryHardlinkThenCopy, (src, dst)))
                case 'png'|'bmp':
                    dst = (dst_dir / src.name).with_suffix('.jpg')
                    # TODO: ffmpeg-based toJPG is not good for now
                    jobs.append((toJPG, (src, dst)))
                case 'cue':
                    dst = (dst_dir / src.name).with_suffix('.cue')
                    jobs.append((tryCopy, (src, dst)))
                case 'log':
                    dst = (dst_dir / src.name).with_suffix('.log')
                    jobs.append((tryCopy, (src, dst)))
                case _:
                    dst = (dst_dir / src.name).with_suffix(src.suffix.lower())
                    jobs.append((tryCopy, (src, dst)))
            dsts.append(dst)

    paths = list(itertools.chain.from_iterable(cd_paths))
    with Pool(NUM_CPU_JOBS) as pool:
        logger.info(PROCESSING_QUEUED_JOBS_0)
        succs = pool.map(_runJob, jobs)
    if DEBUG: assert len(paths) == len(jobs) == len(dsts) == len(succs)

    ret: list[tuple[Path, Path]] = []
    for succ, src, dst in zip(succs, paths, dsts):
        if succ:
            ret.append((src, dst))
        else:
            logger.error(FAILED_TO_HANDLE_FILE_1.format(src.relative_to(root)))

    return ret




def collectAlbumsInfo(src_paths: Iterable[Path]):

    src_paths = list(src_paths)
    assert src_paths, GOT_NO_INPUT_0

    ap_csv_path = proposeFilePath(src_paths, AP_CSV_FILENAME)
    try:
        ap_csv_path.parent.mkdir(parents=True, exist_ok=True)
        ap_csv_path.write_bytes(b'')
    except:
        print(CANT_CREATE_CSV_1.format(ap_csv_path))
        return

    ap_dicts: list[dict] = []
    for i, src_path in enumerate(src_paths, start=1):

        print()  # extra blank line
        print(PROCESSING_1.format(src_path))

        src_dsk_dir = src_path / STD_CDS_DIRNAME
        src_img_dir = src_path / STD_BKS_DIRNAME
        src_vid_dir = src_path / STD_SPS_DIRNAME

        src_dsks = listDir(src_dsk_dir, rglob=False)
        for src_dsk in src_dsks:
            if listFile(src_dsk, ext=AD_AUD_EXTS):
                ap_dict = {key: '' for key in AP_CSV_DICT.keys()}
                ap_dict[AP_SRC_PATH_CN] = str(src_dsk)
                ap_dict[AP_DIR_TYPE_CN] = AP_DIR_TYPE_DSK_CN
                # ap_dict[AP_ALBUM_PRENAME_CN] = str(i)
                ap_dicts.append(ap_dict)

        src_imgs = listFile(src_img_dir, ext=ALL_EXTS_IN_SCANS)
        if src_imgs:
            ap_dict = {key: '' for key in AP_CSV_DICT.keys()}
            ap_dict[AP_SRC_PATH_CN] = str(src_img_dir)
            ap_dict[AP_DIR_TYPE_CN] = AP_DIR_TYPE_BKS_CN
            # ap_dict[AP_ALBUM_PRENAME_CN] = str(i)
            ap_dicts.append(ap_dict)

        src_vids = listFile(src_vid_dir, ext=AD_VID_EXTS)
        if src_vids:
            ap_dict = {key: '' for key in AP_CSV_DICT.keys()}
            ap_dict[AP_SRC_PATH_CN] = str(src_vid_dir)
            ap_dict[AP_DIR_TYPE_CN] = AP_DIR_TYPE_SPS_CN
            # ap_dict[AP_ALBUM_PRENAME_CN] = str(i)
            ap_dicts.append(ap_dict)

    ap_dicts = quotFields4CSV(ap_dicts)
    writeCSV(ap_csv_path, ap_dicts)











def placeAlbums(ap_csv_path: Path, dst_root: Optional[Path] = None):

    if not dst_root:
        dst_root = ap_csv_path.parent / STD_CDS_DIRNAME

    if dst_root.exists():
        print(DIR_EXISTS_DEL_FIRST_1.format(dst_root))
        return
    if not tryMkDir(dst_root):
        print(CANT_CREATE_CSV_1.format(dst_root))
        return
    dst_root.mkdir(parents=True, exist_ok=True)

    s, ap_dicts = readCSV(ap_csv_path)
    ap_dicts = unquotFields4CSV(ap_dicts)
    if not s:
        print(CANT_READ_CSV_1.format(ap_csv_path))
        return

    albums: dict[str, dict[str, list[tuple]]] = {}

    last_naming = {'date': '','pre': '','mid': '', 'aft': '','art': '','edt': '', }

    for i, ap_dict in enumerate(ap_dicts, start=1):

        #* src_sd_dir ------------------------------------------------------------------------------

        src_dir = Path(ap_dict[AP_SRC_PATH_CN])
        print(PROCESSING_1.format(src_dir))
        if not src_dir.is_dir():
            print(CANT_FIND_DIR_1.format(src_dir))
            continue
        if not listFile(src_dir):
            print(AP_SKIP_NO_ALBUM_FILE_DIR.format(src_dir))
            continue

        dirtype = ap_dict[AP_DIR_TYPE_CN]
        naming = {'date': normDesp(ap_dict.get(AP_ALBUM_DATE_CN, '')),
                  'pre': normDesp(ap_dict.get(AP_ALBUM_PRENAME_CN, '')),
                  'mid': normDesp(ap_dict.get(AP_ALBUM_NAME_CN, '')),
                  'aft': normDesp(ap_dict.get(AP_ALBUM_AFTNAME_CN, '')),
                  'art': normDesp(ap_dict.get(AP_ALBUM_ARTISTS_CN, '')),
                  'edt': normDesp(ap_dict.get(AP_ALBUM_EDITION_CN, ''))}
        cat = ap_dict.get(AP_CATALOG_CN, str(i))
        if any(naming.values()):
            last_naming.update(naming)

        aid = '/'.join(naming.values())
        albums[aid] = albums.get(aid, {'cd': [], 'bk': [], 'sp': [], 'hr': []})
        if dirtype == AP_DIR_TYPE_DSK_CN:
            mediainfos = [getMediaInfo(f) for f in listFile(src_dir, ext=AD_AUD_EXTS)]
            for mi in mediainfos:
                if (bit := mi.audio_tracks[0].bit_depth) and (rate := mi.audio_tracks[0].sampling_rate):
                    if bit * rate >= 24 * 48000:
                        albums[aid]['hr'].append((cat, src_dir))
                        break
            else:
                albums[aid]['cd'].append((cat, src_dir))

        elif dirtype == AP_DIR_TYPE_BKS_CN:
            albums[aid]['bk'].append((cat, src_dir))
        elif dirtype == AP_DIR_TYPE_SPS_CN:
            albums[aid]['sp'].append((cat, src_dir))
        else:
            print('!!! Unknown dir type: "{}"'.format(dirtype))

    for aid, album in albums.items():

        date, pre, mid, aft, art, edt = aid.split('/')
        dst_dirname = ''
        if date: dst_dirname += f'[{date}] '
        match bool(pre), bool(mid), bool(aft):
            case True, True, True:
                dst_dirname += f'{pre} ｢{mid}｣ {aft}'
            case True, True, False:
                dst_dirname += f'{pre} ｢{mid}｣'
            case True, False, True:
                dst_dirname += f'{pre} {aft}'
            case True, False, False:
                dst_dirname += f'{pre}'
            case False, True, True:
                dst_dirname += f'｢{mid}｣ {aft}'
            case False, True, False:
                dst_dirname += f'｢{mid}｣'
            case False, False, True:
                dst_dirname += f'{aft}'
            case False, False, False:
                dst_dirname += 'NO NAME'
        if art: dst_dirname += f'／{art}'
        if edt: dst_dirname += f' [{edt}]'


        if album['cd']:
            fmts = ['flac', 'aac', 'mp3', 'wv', 'webp', 'jpg', 'mkv']
            auds = list(itertools.chain.from_iterable([listFile(d) for (cat, d) in album['cd']]))
            exts = set([f.suffix.lower() for f in auds])
            if '.flac' in exts: fmts[0] = ''
            if '.m4a' in exts: fmts[1] = ''
            if '.mp3' in exts: fmts[2] = ''
            if '.wv' in exts: fmts[3] = ''

            if album['bk']:
                imgs = list(itertools.chain.from_iterable([listFile(d) for (cat, d) in album['bk']]))
                exts = set([f.suffix.lower() for f in imgs])
                if '.webp' in exts: fmts[4] = ''
                if '.jpg' in exts: fmts[5] = ''

            if album['sp']:
                vids = list(itertools.chain.from_iterable([listFile(d) for (cat, d) in album['sp']]))
                exts = set([f.suffix.lower() for f in vids])
                if '.mkv' in exts: fmts[6] = ''

            fmt = '(' + '+'.join([f for f in fmts if f]) + ')' if fmts else ''
            cd_dst_dirname = f'{dst_dirname} {fmt}'.strip()
            (cd_dst_dir := dst_root / cd_dst_dirname).mkdir(parents=True, exist_ok=True)

            if len(album['cd']) == 1:
                for cat, src_dir in album['cd']:
                    for src in listFile(src_dir):
                        dst = cd_dst_dir / src.relative_to(src_dir)
                        tryHardlinkThenCopy(src, dst)
            else:
                for cat, src_dir in album['cd']:
                    (cd_dst_dir / cat).mkdir(parents=True, exist_ok=True)
                    for src in listFile(src_dir):
                        dst = cd_dst_dir / cat / src.relative_to(src_dir)
                        tryHardlinkThenCopy(src, dst)
            for cat, src_dir in album['bk']:
                (cd_dst_dir / cat).mkdir(parents=True, exist_ok=True)
                for src in listFile(src_dir):
                    dst = cd_dst_dir / STD_BKS_DIRNAME / src.relative_to(src_dir)
                    tryHardlinkThenCopy(src, dst)
            for cat, src_dir in album['sp']:
                (cd_dst_dir / cat).mkdir(parents=True, exist_ok=True)
                for src in listFile(src_dir):
                    dst = cd_dst_dir / STD_SPS_DIRNAME / src.relative_to(src_dir)
                    tryHardlinkThenCopy(src, dst)

        if album['hr']:

            fmts = ['flac', 'wv', 'aac', 'mp3', 'webp', 'jpg', 'mkv']
            auds = list(itertools.chain.from_iterable([listFile(d) for (cat, d) in album['cd']]))
            exts = set([f.suffix.lower() for f in auds])
            if '.flac' in exts: fmts[0] = ''
            if '.wv' in exts: fmts[1] = ''
            if '.m4a' in exts: fmts[2] = ''
            if '.mp3' in exts: fmts[3] = ''

            mi = getMediaInfo(auds[0])
            bit = mi.audio_tracks[0].bit_depth
            sr = mi.audio_tracks[0].sampling_rate

            if album['bk']:
                imgs = list(itertools.chain.from_iterable([listFile(d) for (cat, d) in album['bk']]))
                exts = set([f.suffix.lower() for f in imgs])
                if '.webp' in exts: fmts[4] = ''
                if '.jpg' in exts: fmts[5] = ''

            if album['sp']:
                vids = list(itertools.chain.from_iterable([listFile(d) for (cat, d) in album['sp']]))
                exts = set([f.suffix.lower() for f in vids])
                if '.mkv' in exts: fmts[6] = ''

            if not album['cd']:
                fmt = '(' + '+'.join([f for f in fmts if f]) + ')' if fmts else ''
                cd_dst_dirname = f'{dst_dirname} {fmt}'
                (cd_dst_dir := dst_root / cd_dst_dirname).mkdir(parents=True, exist_ok=True)
            else:
                fmt = '(' + '+'.join([f for f in fmts[:2] if f]) + ')' if fmts else ''
                cd_dst_dirname = f'{dst_dirname} {fmt}'.strip()
                (cd_dst_dir := dst_root / cd_dst_dirname).mkdir(parents=True, exist_ok=True)

            if len(album['hr']) == 1:
                for cat, src_dir in album['hr']:
                    for src in listFile(src_dir):
                        dst = cd_dst_dir / src.relative_to(src_dir)
                        tryHardlinkThenCopy(src, dst)
            else:
                for cat, src_dir in album['hr']:
                    (cd_dst_dir / cat).mkdir(parents=True, exist_ok=True)
                    for src in listFile(src_dir):
                        dst = cd_dst_dir / cat / src.relative_to(src_dir)
                        tryHardlinkThenCopy(src, dst)

            if not album['cd']:
                for cat, src_dir in album['bk']:
                    (cd_dst_dir / cat).mkdir(parents=True, exist_ok=True)
                    for src in listFile(src_dir):
                        dst = cd_dst_dir / STD_BKS_DIRNAME / src.relative_to(src_dir)
                        tryHardlinkThenCopy(src, dst)
                for cat, src_dir in album['sp']:
                    (cd_dst_dir / cat).mkdir(parents=True, exist_ok=True)
                    for src in listFile(src_dir):
                        dst = cd_dst_dir / STD_SPS_DIRNAME / src.relative_to(src_dir)
                        tryHardlinkThenCopy(src, dst)



def _mvAlbumBKs(bk_paths: Iterable[Path], dst_bks_dir: Path, logger: Logger, root: Path) -> list[tuple[Path, Path]]:
    bk_paths = set(bk_paths)

    if not bk_paths:
        shutil.rmtree(dst_bks_dir, ignore_errors=True)
        return []

    dsts: list[Path] = []
    jobs: list[tuple[Callable, tuple]] = []

    for src in bk_paths:
        match (suffix := src.suffix.lower()):
            case '.jpg'|'.jpeg':
                dst = (dst_bks_dir / src.relative_to(root)).with_suffix('.jpg')
                jobs.append((tryHardlinkThenCopy, (src, dst)))
            case '.webp':
                dst = (dst_bks_dir / src.relative_to(root)).with_suffix('.webp')
                jobs.append((tryHardlinkThenCopy, (src, dst)))
            case '.png'|'.bmp'|'.tif'|'.tiff':
                dst = dst_bks_dir / src.relative_to(root).with_suffix('.webp')
                jobs.append((toWebp, (src, dst)))
            case _:  #! we still copy the file since the user thinks the extension is of scans through `AD_IMG_EXTS`
                dst = dst_bks_dir / src.relative_to(root)
                jobs.append((tryHardlinkThenCopy, (src, dst)))
                if DEBUG: logger.debug(GOT_BUT_EXPECT_ONE_OF_2.format(suffix, AD_IMG_EXTS))
                logger.info(GOT_UNSUPP_FILE_1.format(src))
        dsts.append(dst)

    with Pool(NUM_CPU_JOBS) as pool:
        logger.info(PROCESSING_QUEUED_JOBS_0)
        succs = pool.map(_runJob, jobs)
    if DEBUG: assert len(bk_paths) == len(jobs) == len(dsts) == len(succs)

    records: dict[int|str, tuple[Path, Path]] = {}
    for succ, src, dst in zip(succs, bk_paths, dsts):
        if succ:
            fid = getFileID(dst)
            if DEBUG: assert fid not in records.keys(), GOT_IDENTICAL_FILE_1.format(src)
            records[fid] = (src, dst)
        else:
            logger.error(FAILED_TO_HANDLE_FILE_1.format(src.relative_to(root)))

    try:
        condenseDirLayout(dst_bks_dir)
        cleanScansFilenames(dst_bks_dir, logger)
    except Exception as e:
        if DEBUG: traceback.print_exc()
        logger.error(UNEXP_ERR_IN_TIDYING_UP_2.format(dst_bks_dir, e))
        logger.warning(AD_BKS_WILL_BE_REMOVED_0)
        shutil.rmtree(dst_bks_dir, ignore_errors=True)
        return []

    ret: list[tuple[Path, Path]] = []
    for new_dst in listFile(dst_bks_dir):
        if paths := records.get(getFileID(new_dst)):
            src, dst = paths
            ret.append((src, new_dst))
    return ret




def _mvAlbumMVs(mv_paths: Iterable[Path], dst_mvs_dir: Path, logger: Logger, root: Path) -> list[tuple[Path, Path]]:

    records: dict[int|str, tuple[Path, Path]] = {}

    if not mv_paths:
        shutil.rmtree(dst_mvs_dir, ignore_errors=True)
        return []

    for src in mv_paths:
        dst = dst_mvs_dir / src.relative_to(root)
        if tryHardlinkThenCopy(src, dst):
            fid = getFileID(dst)
            assert fid not in records.keys(), GOT_IDENTICAL_FILE_1.format(src)
            records[fid] = (src, dst)
        else:
            logger.error(FAILED_TO_HANDLE_FILE_1.format(src.relative_to(root)))

    try:
        condenseDirLayout(dst_mvs_dir)
    except Exception as e:
        if DEBUG: traceback.print_exc()
        logger.error(UNEXP_ERR_IN_TIDYING_UP_2.format(dst_mvs_dir, e))
        logger.warning(AD_VID_WILL_BE_REMOVED_0)
        shutil.rmtree(dst_mvs_dir, ignore_errors=True)
        return []

    ret: list[tuple[Path, Path]] = []
    for new_dst in listFile(dst_mvs_dir):
        if paths := records.get(getFileID(new_dst)):
            src, dst = paths
            ret.append((src, new_dst))
    return ret




def processAlbumSourceDir(src_path: Path, dst_dir: Path, logger: Logger):
    '''
    Process an album source from `src_path`, and place the processed files in `dst_dir`.
    An album source may be a directory or an archive file that contains one or more discs.
        Nested archives inside the dir or file are not supported for now.
    NOTE: the function assumes that all album files under the source are of the same album.
    NOTE: if they're from different albums, the function can still process them, but the output is unusable for now.
    '''

    if DEBUG: logger.debug(PROCESSING_2.format(src_path, dst_dir))
    else: logger.info(PROCESSING_1.format(src_path))

    #* check output availability ---------------------------------------------------------------------------------------

    try:
        assert not dst_dir.is_file()
        dst_dir.mkdir(parents=True, exist_ok=False)
        (dst_cds_dir := dst_dir / STD_CDS_DIRNAME).mkdir(parents=True, exist_ok=False)
        (dst_bks_dir := dst_dir / STD_BKS_DIRNAME).mkdir(parents=True, exist_ok=False)
        (dst_mvs_dir := dst_dir / STD_SPS_DIRNAME).mkdir(parents=True, exist_ok=False)
        (info_csv_path := dst_dir / AD_INFO_CSV_FILENAME).touch(exist_ok=False)
    except:
        logger.error(DEST_DIR_NOT_AVAIL_1.format(dst_dir))
        shutil.rmtree(dst_dir, ignore_errors=True)
        return

    #* check input, decompress if required -----------------------------------------------------------------------------

    # TODO: can we decompress archives inside the archive?

    tmp_dir = TEMP_DIR_DECOMPRESS / AD_TMP_DIRNAME
    if isinstance(ret := handleResourceSrc(src_path, tmp_dir, logger), Path):
        remove_src: bool = (ret == tmp_dir)
    else:
        logger.error(CANT_HANDLE_SRC_1.format(src_path))
        shutil.rmtree(dst_dir, ignore_errors=True)
        return

    def _cleanUp4Exit(w: Optional[str] = None, e: Optional[str] = None):
        if e: logger.error(e)
        if w: logger.warning(w)
        shutil.rmtree(dst_dir, ignore_errors=True)
        if remove_src: shutil.rmtree(tmp_dir, ignore_errors=True)

    #* validate input files --------------------------------------------------------------------------------------------

    with Pool(NUM_CPU_JOBS) as pool:

        afs = [AlbumFile(path) for path in listFile(src_path, ext=AD_AUD_EXTS)]
        a_vals = pool.map(attrgetter('is_valid'), afs)
        val_afs = [f for valid, f in zip(a_vals, afs) if valid]
        for f in set(afs).difference(val_afs):
            logger.error(INVALID_FILE_1.format(f.path.relative_to(src_path)))

        ifs = [ImageFile(path) for path in listFile(src_path, ext=AD_IMG_EXTS)]
        i_vals = pool.map(attrgetter('is_valid'), ifs)
        val_ifs = [f for valid, f in zip(i_vals, ifs) if valid]
        for f in set(ifs).difference(val_ifs):
            logger.error(INVALID_FILE_1.format(f.path.relative_to(src_path)))

        vfs = [VideoFile(path) for path in listFile(src_path, ext=AD_VID_EXTS)]
        v_vals = pool.map(attrgetter('is_valid'), vfs)
        val_vfs = [f for valid, f in zip(v_vals, vfs) if valid]
        for f in set(vfs).difference(val_vfs):
            logger.error(INVALID_FILE_1.format(f.path.relative_to(src_path)))

    if not all(a_vals + i_vals + v_vals):
        _cleanUp4Exit(e=SKIP_INVALID_SOURCE_1.format(src_path.name))
        return
    if not val_afs:  #! we skip source with no audio files
        _cleanUp4Exit(w=SKIP_EMPTY_SOURCE_1.format(src_path.name))
        return

    #* split files -----------------------------------------------------------------------------------------------------

    cd_paths: Iterable[list[Path]] = sortAudioDirs2Discs(set(f.path.parent for f in val_afs), logger, src_path)
    bk_paths: Iterable[Path] = set(f.path for f in val_ifs).difference(itertools.chain.from_iterable(cd_paths))
    mv_paths: Iterable[Path] = set(f.path for f in val_vfs)
    logger.info(AD_FOUND_IN_TOTAL_3.format(len(cd_paths), len(bk_paths), len(mv_paths)))

    #* transcode/move files --------------------------------------------------------------------------------------------

    cd_paths_mapping: list[tuple[Path, Path]] = _mvAlbumCDs(cd_paths, dst_cds_dir, logger, src_path)
    bk_paths_mapping: list[tuple[Path, Path]] = _mvAlbumBKs(bk_paths, dst_bks_dir, logger, src_path)
    mv_paths_mapping: list[tuple[Path, Path]] = _mvAlbumMVs(mv_paths, dst_mvs_dir, logger, src_path)

    #* record files info -----------------------------------------------------------------------------------------------

    info_dicts: list[dict[str, str]] = []
    for src, dst in cd_paths_mapping:
        info_dicts.append({
            CRC32_CN: getCRC32(dst),
            AD_FILE_TYPE_CN: '1',
            SD_ORIG_PATH_CN: src.relative_to(src_path.parent).as_posix(),
            SD_PROC_PATH_CN: dst.relative_to(dst_cds_dir).as_posix(),
            })
    for src, dst in bk_paths_mapping:
        info_dicts.append({
            CRC32_CN: getCRC32(dst),
            AD_FILE_TYPE_CN: '2',
            SD_ORIG_PATH_CN: src.relative_to(src_path.parent).as_posix(),
            SD_PROC_PATH_CN: dst.relative_to(dst_bks_dir).as_posix(),
            })
    for src, dst in mv_paths_mapping:
        info_dicts.append({
            CRC32_CN: getCRC32(dst),
            AD_FILE_TYPE_CN: '3',
            AD_ORIG_PATH_CN: src.relative_to(src_path.parent).as_posix(),
            AD_PROC_PATH_CN: dst.relative_to(dst_mvs_dir).as_posix(),
            })

    if not writeCSV(info_csv_path, quotFields4CSV(info_dicts)):
        logger.error(FAILED_TO_WRITE_INFO_CSV_1.format(info_csv_path))

    if remove_src: shutil.rmtree(src_path, ignore_errors=True)
    logger.info(PROCESSED_TO_1.format(dst_dir))




def processAlbumSourceDirs(input_paths: list[Path]):

    dst_parent = initAlbumDraftDstParentDir(input_paths=input_paths, script_path=Path(__file__).parent)
    if DEBUG: assert dst_parent, CANT_INIT_OUTPUT_DIR_0

    logger = initLogger(log_path := (dst_parent / AD_LOG_FILENAME))
    logger.info(USING_AD_1.format(AC_VERSION))
    logger.info(THE_OUTPUT_DIR_IS_1.format(dst_parent))

    w = len(str(len(input_paths)))
    for i, path in enumerate(input_paths, start=1):
        processAlbumSourceDir(path, dst_parent / AD_DIRNAME_3.format(TIMESTAMP, f'{i:0>{w}}', path.name), logger)