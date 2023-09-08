from imports import *




def _cli(paths: list[Path]):

    n = len(paths)
    if (n == 1) and paths[0].is_dir():
        recordBDMVInfo(paths[0])
    else:
        printUsage(VA_USAGE_0, paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
