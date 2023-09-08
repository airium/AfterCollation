from imports import *




def _cli(paths: list[Path]):

    n = len(paths)
    if n >= 1 and all(p.is_dir() for p in paths):
        collectScansDirs(paths)
    elif n == 1 and paths[0].is_file() and SP_CSV_FILENAME_REGEX.match(paths[0].name):
        placeScans(paths[0])
    else:
        printUsage(SP_USAGE_1.format(STD_BKS_DIRNAME), paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
