from imports import *




def _album_draft(input_paths: list[Path]):

    dst_parent = initAlbumDraftDstParentDir(input_paths=input_paths, script_path=Path(__file__).parent)
    if DEBUG: assert dst_parent, CANT_INIT_OUTPUT_DIR_0

    logger = initLogger(log_path := (dst_parent / AD_LOG_FILENAME))
    logger.info(USING_AD_1.format(AC_VERSION))
    logger.info(THE_OUTPUT_DIR_IS_1.format(dst_parent))

    w = len(str(len(input_paths)))
    for i, path in enumerate(input_paths, start=1):
        procAlbumSrc(path, dst_parent / AD_DIRNAME_3.format(TIMESTAMP, f'{i:0>{w}}', path.name), logger)




def _cli(paths: list[Path]):
    if paths:
        _album_draft(paths)
    else:
        printUsage(AD_USAGE_0, paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
