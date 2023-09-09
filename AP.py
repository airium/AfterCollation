from imports import *




def _cli(paths: list[Path]):

    n = len(paths)
    if n >= 1 and all(p.is_dir() for p in paths):
        collectAlbumsInfo(paths)
    elif n == 1 and paths[0].is_file() and paths[0].suffix.lower() == '.csv':
        placeAlbums(paths[0])
    else:
        printUsage(AP_USAGE_0.format(STD_CDS_DIRNAME), paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
