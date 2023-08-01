from imports import *

MR_USAGE = f'''MusicRechecker (MR) only accepts the following input:
1. drop/cli a single folder (ideally "CDs")

MR includes the following behaviors:
1. locate all "{STD_CDS_DIRNAME}" and (only) process all their sub-dirs.
2. check dir/file names, format/metadata and do a full decoding test.
3. connect vgmdb to verify the filled metadata is correct or not.

A processing log (MR-*.log) will be generated for later review.
'''




def main(root):

    log_path = paths[0].parent.joinpath(f'MR-{TIMESTAMP}.log')
    logger = initLogger(log_path=log_path)
    logger.info(f'Using MusicRechecker (MR) of AfterCollation {AC_VERSION}')
    logger.info(f'The user input is "{root}".')

    cds_roots = [d for d in listDir(root) if d.name.lower() == STD_CDS_DIRNAME.lower()]

    if not cds_roots:
        logger.info(f'No "{STD_CDS_DIRNAME}" folder is found.')
        logging.shutdown()
        return

    for cds_root in cds_roots:

        # avoid duplicated processing
        if root != cds_root and \
            any(p.lower() == STD_BKS_DIRNAME for p in cds_root.parent.relative_to(root).as_posix().split('/')):
            continue

        logger.info(f'=' * 100) #***************************************************************************************
        logger.info(f'Started in "{cds_root}" ...')

        if DEBUG: assert cds_root.name.lower() == STD_CDS_DIRNAME.lower()
        if cds_root.name != STD_CDS_DIRNAME:
            logger.warning(f'{STD_CDS_DIRNAME} root dirname has incorrect capitalization (got "{cds_root.name}").')

        logger.info(f'Checking file types ............................................................................')
        all_paths = listFile(cds_root)
        cds_paths = listFile(cds_root, ext=ALL_EXTS_IN_CDS)
        if (diffs := set(all_paths).difference(set(cds_paths))):
            for diff in diffs: logger.error(f'Found disallowed file "{diff}".')

        logger.info('Gathering album dirs ............................................................................')
        albums_paths : list[Path] = listAlbumDirsFromCDsDir(cds_root, logger=logger)
        if not albums_paths:
            logger.error('Got no album folder after early filtering.')
            continue

        logger.info(f'Checking albums layout .........................................................................')
        albums_infos : list[AlbumInfo] = []
        for album_path in albums_paths:
            if (a := chkAlbumDirNaming(album_path, logger=logger)):
                albums_infos.append(a)
        if not albums_infos: logger.error('Got no valid album folder after layout check.')

        logger.info(f'Checking file content ..........................................................................')
        for album_info in albums_infos:
            chkAlbumFiles(album_info, logger=logger)
        # ffmpeg decoding is fast, likely not much improvement from mp/mt
        # mtpool = ThreadPoolExecutor(max_workers=4)
        # mtpool.map(chkMusicFiles, albums_infos)
        # mtpool.shutdown(wait=True)
        logContentCheck(albums_infos, logger=logger)

        if ENABLE_VGMDB:
            logger.info(f'Attempting to verify the naming/tagging with VGMDB database ................................')
            for album_info in (pbar := tqdm.tqdm(albums_infos, ascii=True, dynamic_ncols=True)):
                pbar.set_description(f'VGMDB: {album_info.root.name}')
                lookupVGMDB(album_info, logger=logger)
                time.sleep(1)

        logger.info(f'Generating scans summary........................................................................')
        logMusicSummary(root, albums_infos, logger=logger)

        credits = [c for c in [ai.credit for ai in albums_infos] if c]
        if credits:
            logger.info('Found the following source credits from txt files:')
            logger.info('\n'.join(credits))

    logger.info('')
    logger.info('================================================================================')
    logger.info('CDs checking completed.')
    logger.info('')
    logger.info('NEXT:')
    logger.info(f'View the log "{log_path}".')
    logger.info(f'For any ERROR, you should now start fixing them.')
    logger.info(f'For any WARNING, you should make sure they do not matter.')
    logger.info(f'Some INFO may still contains a notice, do not skip them too fast.')

    logging.shutdown()
    return



def _cli(*paths:Path):

    n = len(paths)
    if (n == 1) and (path := paths[0]).is_dir():
        main(paths[0])
    else:
        printCliNotice(MR_USAGE, paths)




if __name__ == '__main__':

    paths = [Path(p) for p in sys.argv[1:]]
    if DEBUG:
        _cli(*paths)
    else: # if catch the exception as below, vscode doesn't jump to the actual line
        try:
            _cli(*paths)
        except Exception as e:
            print(f'Run into an unexpected error:\n{e}\nPlease report.')

    input('Press ENTER to exit...')
