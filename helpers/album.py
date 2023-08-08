from pathlib import Path
from logging import Logger
from configs import *
from utils import *


class AlbumInfo:

    def __init__(self, root: Path):

        self.root : Path = root

        self.year: int = -100
        self.month: int = 0
        self.day: int = 0

        self.prename: str = ''
        self.midname: str = ''
        self.aftname: str = ''

        self.artists: str = ''

        self.edition: str = ''

        self.hr_bit: int = 0
        self.hr_freq: int = 0

        self.has_flac: bool = False
        self.has_aac: bool = False
        self.has_mp3: bool = False
        self.has_webp: bool = False
        self.has_jpg: bool = False
        self.has_vid: bool = False

        self.split_discs : list[Path] = []
        self.joint_discs : list[Path] = []
        self.hires_discs : list[Path] = []
        self.scans_dirs : list[Path] = []
        self.video_dirs : list[Path] = []
        self.miscs_dirs : list[Path] = []

        self.txt_files : list[Path] = []
        self.credits : list[str] = []
        self.catalogs : list[str] = []

        self.logs = []

    @property
    def date(self) -> str:
        ret = ''
        if self.year > -31: ret += f'{self.year:02d}'
        if self.month > 0: ret += f'{self.month:02d}'
        if self.day > 0: ret += f'{self.day:02d}'
        return ret

    @property
    def has_scans(self) -> bool:
        return self.has_webp or self.has_jpg

    @property
    def is_hires(self) -> bool:
        return self.hr_bit > 0 or self.hr_freq > 0

    @property
    def credit(self) -> str:
        return '; '.join(self.credits)

    @property
    def total_items(self) -> int:
        return len(self.split_discs) + len(self.joint_discs) + len(self.hires_discs) \
             + len(self.scans_dirs) + len(self.video_dirs) + len(self.miscs_dirs)

    def __bool__(self) -> bool:
        return bool(self.total_items)


    def _chkSplitDiscImpl(self, disc_dir:Path):

        aroot = self.root

        #* audio check ***************************************************

        aud_files = listFile(disc_dir, ext=AUD_EXTS_IN_CDS, rglob=False)
        aud_minfos = [getMediaInfo(f) for f in aud_files]

        valid_aud_files = []
        valid_aud_minfos = []
        for f, m in zip(aud_files, aud_minfos):
            if m.audio_tracks:
                valid_aud_files.append(f)
                valid_aud_minfos.append(m)
            else:
                self.logs.append((2, f'Not an audio file "{f.relative_to(aroot)}".'))

        aud_gtrs = [m.general_tracks[0] for m in valid_aud_minfos]
        aud_atrs = [m.audio_tracks[0] for m in valid_aud_minfos]

        seen_album_names = []
        seen_artists = []

        for aud_file, gtr, atr in zip(valid_aud_files, aud_gtrs, aud_atrs):
            rel_path = aud_file.relative_to(aroot)
            match gtr.format:
                case 'FLAC':
                    expected_ext = '.flac'
                case 'MPEG Audio':
                    expected_ext = '.mp3'
                case 'AAC LC':
                    expected_ext = '.m4a'
                case _:
                    raise ValueError(f'Updated {AUD_EXTS_IN_CDS=}.')
            if aud_file.suffix.lower() != expected_ext:
                self.logs.append((2, f'File extension mismatches actual file content "{rel_path}".'))

            if self.hr_bit and self.hr_bit != atr.bit_depth:
                self.logs.append((2, f'Hi-Res bit depth label is incorrect for "{rel_path}".'))
            if self.hr_freq and self.hr_freq != atr.sampling_rate:
                self.logs.append((2, f'Hi-Res sampling rate label is incorrect for "{rel_path}".'))

            if gtr.format == 'FLAC':
                wav_filesize = atr.bit_depth * atr.sampling_rate * atr.channel_s * atr.duration / 8 / 1000
                if atr.stream_size > wav_filesize * 0.9:
                    self.logs.append((1, f'FLAC compression ratio is too low for "{rel_path}".'))
            if atr.channel_s != 2:
                self.logs.append((2, f'Channel count is not 2 for "{rel_path}".'))
            if atr.stream_size / gtr.file_size < 0.9:
                self.logs.append((1, f'Embedded cover art may be too large for "{rel_path}".'))

            if m := re.match(FRONT_INDEXED_TRACKNAME_PATTERN, aud_file.name):
                idx, trname = m.group('idx'), m.group('trname')
                if gtr.track_name and trname and not matchTrackName(trname, gtr.track_name):
                    self.logs.append((2, f'Track name mismatches "{rel_path}".'))
                if gtr.track_name_position and not matchIndex(idx, gtr.track_name_position):
                    self.logs.append((2, f'Track index mismatches "{rel_path}".'))
                if gtr.track_name_total and not matchIndex(len(aud_files), gtr.track_name_total):
                    self.logs.append((2, f'Total track count mismatches "{rel_path}".'))

            if gtr.album: seen_album_names.append(gtr.album)
            if gtr.performer: seen_artists.append(gtr.performer)
            if gtr.album_performer: seen_artists.append(gtr.album_performer)
            if gtr.composer: seen_artists.append(gtr.composer)
            if gtr.album_composer: seen_artists.append(gtr.album_composer)

            if not tryFFMPEGDecode(aud_file):
                self.logs.append((2, f'Decoding "{rel_path}" failed.'))

        seen_artists = list(set(seen_artists))
        if seen_artists and self.artists and not matchArtistsName(self.artists, seen_artists):
            self.logs.append((1, f'The ARTIST label in dirname is not seen in audio metadata.'))

        seen_album_names = list(set(seen_album_names))
        if len(seen_album_names) > 1:
            self.logs.append((1, f'Audio metadata contains different album names under "{disc_dir.relative_to(aroot)}".'))
        album_name_matched = matchAlbumName(self.prename, self.midname, seen_album_names)
        if not album_name_matched:
            self.logs.append((1, f'The album name in dirname is not seen in audio metadata data.'))

        #* log check *****************************************************

        # TODO add more LOG check
        log_files = listFile(disc_dir, ext='log', rglob=False)
        for log_file in log_files:
            if tstFileEncoding(log_file, 'utf-16-le'):
                pass
            elif tstFileEncoding(log_file, 'utf-8-sig'):
                self.logs.append((0, f'EAC LOG "{log_file.relative_to(disc_dir)}" '
                            'should be better preserved as UTF-16-LE instead of UTF-8-BOM.'))
            else:
                self.logs.append((2, f'EAC LOG "{log_file.relative_to(disc_dir)}" decoding failed.'))

        #* img check *****************************************************

        img_files = listFile(disc_dir, ext=IMG_EXTS_IN_CDS, rglob=False)
        for img_file in img_files:
            if not tryFFMPEGDecode(img_file):
                self.logs.append((2, f'Decoding "{img_file.relative_to(aroot)}" failed.'))
            if img_file.name == 'Cover.jpg':
                iinfo = getMediaInfo(img_file).image_tracks[0]
                if (iinfo.width and iinfo.width > NORMAL_COVER_ART_LENGTH) \
                or (iinfo.height and iinfo.height > NORMAL_COVER_ART_LENGTH) \
                or (iinfo.stream_size and iinfo.stream_size > NORMAL_COVER_ART_FILESIZE):
                    self.logs.append((1, f'The cover art "{img_file.relative_to(aroot)}" is too large.'))
                if not tryFFMPEGDecode(img_file):
                    self.logs.append((2, f'Decoding "{img_file.relative_to(aroot)}" failed.'))


    def chkHiResDiscs(self):

        for disc_dir in self.hires_discs:
            self._chkSplitDiscImpl(disc_dir)


    def chkSplitDiscs(self):

        for disc_dir in self.split_discs:
            self._chkSplitDiscImpl(disc_dir)


    def chkJointDiscs(self):

        aroot : Path = self.root
        logs : list[tuple[int, str]] = []

        for disc_dir in self.joint_discs:

            #* audio check ***************************************************

            aud_files = listFile(disc_dir, ext=AUD_EXTS_IN_CDS, rglob=False)
            aud_minfos = [getMediaInfo(f) for f in aud_files]

            valid_aud_files = []
            valid_aud_minfos = []
            for f, m in zip(aud_files, aud_minfos):
                if m.audio_tracks:
                    valid_aud_files.append(f)
                    valid_aud_minfos.append(m)
                else:
                    logs.append((2, f'Not an audio file "{f.relative_to(aroot)}".'))

            aud_gtrs = [m.general_tracks[0] for m in valid_aud_minfos]
            aud_atrs = [m.audio_tracks[0] for m in valid_aud_minfos]

            for aud_file, gtr, atr in zip(valid_aud_files, aud_gtrs, aud_atrs):
                rel_path = aud_file.relative_to(aroot)
                match gtr.format:
                    case 'FLAC':
                        expected_ext = '.flac'
                    case 'MPEG Audio':
                        expected_ext = '.mp3'
                    case 'AAC LC':
                        expected_ext = '.m4a'
                    case _:
                        raise ValueError(f'Updated {AUD_EXTS_IN_CDS=}.')
                if aud_file.suffix.lower() != expected_ext:
                    logs.append((2, f'File extension mismatches actual file content "{rel_path}".'))

                if gtr.format == 'FLAC':
                    wav_filesize = atr.bit_depth * atr.sampling_rate * atr.channel_s * atr.duration / 8 / 1000
                    if atr.stream_size > wav_filesize * 0.9:
                        logs.append((1, f'FLAC compression ratio is too low for "{rel_path}".'))
                if atr.channel_s != 2:
                    logs.append((2, f'Channel count is not 2 for "{rel_path}".'))
                if atr.stream_size / gtr.file_size < 0.9:
                    logs.append((1, f'Embedded cover art may be too large for "{rel_path}".'))

                seen_artists = []
                if gtr.performer: seen_artists.append(gtr.performer)
                if gtr.album_performer: seen_artists.append(gtr.album_performer)
                if gtr.composer: seen_artists.append(gtr.composer)
                if gtr.album_composer: seen_artists.append(gtr.album_composer)
                if seen_artists and self.artists and not matchArtistsName(self.artists, seen_artists):
                    logs.append((1, f'The ARTIST label in dirname is not seen in audio metadata under "{disc_dir.relative_to(aroot)}".'))

                if gtr.album and not matchAlbumName(self.prename, self.midname, gtr.album):
                    logs.append((1, f'The album name in dirname is not seen in audio metadata data under "{disc_dir.relative_to(aroot)}".'))

                if not tryFFMPEGDecode(aud_file):
                    logs.append((2, f'Decoding "{aud_file.relative_to(aroot)}" failed.'))

            #* cue check *****************************************************

            # TODO use utils.cuesheet to better check the files
            cue_files = listFile(disc_dir, ext='cue', rglob=False)
            for cue_file in cue_files:
                if tstFileEncoding(cue_file, 'utf-8-sig'):
                    content = cue_file.read_text(encoding='utf-8-sig')
                    if m := re.search(FILENAME_IN_CUE_PATTERN, content):
                        filename = m.group('filename')
                        if cue_file.with_name(filename) not in aud_files:
                            logs.append((2, f'Cannot find "{filename}" specified in CUESHEET "{cue_file.relative_to(aroot)}".'))
                else:
                    logs.append((2, f'Failed to parse "{cue_file.relative_to(aroot)}".'))

            #* log check *****************************************************

            log_files = listFile(disc_dir, ext='log', rglob=False)
            for log_file in log_files:
                if tstFileEncoding(log_file, 'utf-16-le'):
                    pass
                elif tstFileEncoding(log_file, 'utf-8-sig'):
                    logs.append((1, f'EAC LOG "{log_file.relative_to(aroot)}" '
                                'should be better preserved as UTF-16-LE instead of UTF-8-BOM.'))
                else:
                    logs.append((2, f'EAC LOG "{log_file.relative_to(aroot)}" decoding failed.'))

            #* img check *****************************************************

            img_files = listFile(disc_dir, ext=IMG_EXTS_IN_CDS, rglob=False)
            for img_file in img_files:
                if not tryFFMPEGDecode(img_file):
                    logs.append((2, f'Decoding "{img_file.relative_to(aroot)}" failed.'))
                if img_file.name == 'Cover.jpg':
                    iinfo = getMediaInfo(img_file).image_tracks[0]
                    if (iinfo.width and iinfo.width > NORMAL_COVER_ART_LENGTH) \
                    or (iinfo.height and iinfo.height > NORMAL_COVER_ART_LENGTH) \
                    or (iinfo.stream_size and iinfo.stream_size > NORMAL_COVER_ART_FILESIZE):
                        logs.append((1, f'The cover art "{img_file.relative_to(aroot)}" is too large.'))
                    if not tryFFMPEGDecode(img_file):
                        logs.append((2, f'Decoding "{img_file.relative_to(aroot)}" failed.'))

        self.logs += logs


    def chkScansDirs(self):

        logs : list[tuple[int, str]] = []

        for scans_dir in self.scans_dirs:
            # NOTE Scans checking is now done in ScansRechecker.py for now
            pass

        self.logs += logs


    def chkMvDir(self):
        logs : list[tuple[int, str]] = []
        # TODO what we can check for MV?
        self.logs += logs


    def chkCreditFiles(self):

        logs : list[tuple[int, str]] = []
        credit_msgs = list()

        for path in self.txt_files:
            if tstFileEncoding(path, 'utf-8-sig'):
                content = path.read_text('utf-8-sig')
                if not content.startswith(STD_TSDM_CREDIT_TEXT):
                    if path.name == STD_TSDM_CREDIT_TEXT:
                        logs.append((2, 'Not using TSDM credit text.'))
                        credit_msgs.append(content.strip().replace('\n', ' '))
                    else:
                        logs.append((0, 'Not using TSDM credit text.'))
                        credit_msgs.append(content.strip().replace('\n', ' '))
                else:
                    credit_msgs.append(DEFAULT_TSDM_CREDIT)
                    credit_msg = content.replace(STD_TSDM_CREDIT_TEXT, '').strip().replace('\n', ' ')
                    if credit_msg:
                        logs.append((0, f'Found custom lines in TSDM credit text: "{credit_msg}".'))
                        credit_msgs.append(credit_msg)
            else:
                logs.append((2, 'File encoding error (not utf-8-bom).'))

        credit_msgs = list(credit_msgs)
        if DEBUG: logs.append((0, 'credits: ' + ('|'.join(credit_msgs))))
        self.credits = list(set(credit_msgs))

        self.logs = logs
        return self


def matchAlbumName(pre:str|None, mid:str|None, seen_names:str|list[str]) -> bool:
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




def matchArtistsName(art:str|None, seen_artists:str|list[str]) -> bool:
    if isinstance(seen_artists, str): seen_artists = [seen_artists]
    if (not art) or (not seen_artists):
        return False
    if art:
        for seen_artist in seen_artists:
            if suppressPunctuation(art) in suppressPunctuation(seen_artist): return True
    return False




def matchTrackName(path_trname:str|None, metadata_trname:str) -> bool:
    if not path_trname or not metadata_trname:
        return False
    if suppressPunctuation(path_trname) == suppressPunctuation(metadata_trname):
        return True
    return False




def matchIndex(index:int|str, metadata_index:int|str) -> bool:
    if (not index) or (not metadata_index):
        return False # this is safe as idx=0 is not allowed
    index = int(index)
    metadata_index = int(metadata_index)
    if index == metadata_index:
        return True
    return False




def lookupVGMDB(album_info:AlbumInfo, logger):

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
        if (m := re.match(CATALOG_MULTIDISC_PATTERN, catalog)): catalog = m['catalog']
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




def listAlbumDirsFromCDsDir(cds_dir:Path, logger:Logger, root_is_cds:bool=True) -> list[Path]:
    '''
    List all possible ALBUM directories under the "CDs" dir.
    This function can identify grouped album folders.
    The function also check if there is unnecessary files directly under the "CDs" directory.

    Return: list[Path]: the list of album folder under "cds_dir"
    '''

    if DEBUG: assert cds_dir.is_dir()

    if root_is_cds and cds_dir.name != STD_CDS_DIRNAME:
        logger.warning(f'Skipped "{cds_dir}" as its name is not "{STD_CDS_DIRNAME}".')
        return []

    if root_is_cds:
        logger.info(f'Inspecting "{cds_dir}" (CDs ROOT)...')
    else:
        logger.info(f'Inspecting "{cds_dir}" (CDs CLUSTER)...')

    # file types other than `ALL_EXTS_IN_CDS` are already warned in main()
    # but we don't allow any file directly lying under "CDs"
    for file_path in listFile(cds_dir, ext=ALL_EXTS_IN_CDS, rglob=False):
        logger.error(f'"{file_path}" is not allowed to be placed here.')

    ret = []
    for dir_path in listDir(cds_dir, rglob=False):

        subdirs_path = listDir(dir_path, rglob=False)
        subfiles_path = listFile(dir_path, ext=ALL_EXTS_IN_CDS, rglob=False)

        if len(subdirs_path) == 0 and len(subfiles_path) == 0:
            logger.warning(f'"{dir_path.relative_to(cds_dir)}" is empty.')
            continue
        if len(subdirs_path) == 1 and len(subfiles_path) == 0:
            logger.warning(f'"{dir_path.relative_to(cds_dir)}" seems unnecessary as contains only 1 folder and no file.')

        # all allowed ALBUM placement under CDs:
        # 1: CDs/ALBUM/*
        # 2: CDs/CLUSTER/ALBUM/*
        # NOTE we only allow a-single-level clustering under CDs, as 2

        # layout 1
        if re.match(ALBUM_DIR_MIN_PATTERN, dir_path.name.lower()):
            logger.info(f'Added "{dir_path}".')
            ret.append(dir_path)
        # layout 2
        # NOTE only go deeper if the parent is CDs
        elif root_is_cds and any(re.match(ALBUM_DIR_MIN_PATTERN, sb.name.lower()) for sb in subdirs_path):
            # NOTE disable subfolder check in CLUSTER
            logger.warning(f'Found a cluster "{dir_path.name}" under "{STD_CDS_DIRNAME}". '
                           f'This is a rare usage.')
            ret += listAlbumDirsFromCDsDir(dir_path, logger, root_is_cds=False)
        else:
        # we just skip these failed dirname
        # it's expensive to determine if the dirs with a malformed name contains valid album content
        # TODO: can we still try to determine ALBUM with malformed name? this will require changing later functions
            logger.error(f'Excluded "{dir_path}/*" as its dirname is not recognised.')

    return ret