from imports import *




def _cli(paths: list[Path]):

    n = len(paths)
    if (n == 1) and paths[0].is_dir():
        chkScans(paths[0])
    else:
        printUsage(SR_USAGE_2.format(STD_BKS_DIRNAME, TEMP_DIR_PATH), paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
