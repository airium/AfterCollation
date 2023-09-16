from imports import *




def _cli(paths: list[Path]):
    if paths:
        processScansSourceDirs(paths)
    else:
        printUsage(SD_USAGE_0, paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
