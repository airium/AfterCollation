from imports import *




def _cli(paths: list[Path]):
    if paths: processAlbumSourceDirs(paths)
    else: printUsage(AD_USAGE_0, paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
