from imports import *




def main(root):

    logger = initLogger(log_path := root.parent.joinpath(AR_LOG_FILENAME))
    logger.info(USING_AR_1.format(AC_VERSION))
    logger.info(THE_INPUT_IS_1.format(root))

    cds_roots = [d for d in listDir(root) if d.name.lower() == STD_CDS_DIRNAME.lower()]
    if not cds_roots:
        logger.warning(AR_NOT_FOUND_CDS_DIR_2.format(STD_CDS_DIRNAME, root))
        cds_roots = [root]

    for cds_root in cds_roots:
        if any(p.lower() == STD_BKS_DIRNAME.lower() for p in cds_root.relative_to(root).parts[:-1]): continue
        logger.info('')
        logger.info(CHECKING_1.format(cds_root))
        chkAlbumRoot(cds_root, logger=logger)
        logger.info(CHECKED_1.format(cds_root))
        logger.info('')
    logger.info(AR_ENDING_NOTE_1.format(log_path))
    logging.shutdown()
    return




def _cli(paths: list[Path]):
    n = len(paths)
    if (n == 1) and paths[0].is_dir():
        main(paths[0])
    else:
        printUsage(AR_USAGE_1.format(STD_CDS_DIRNAME), paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
