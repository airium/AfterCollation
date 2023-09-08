from imports import *




def _cli(paths: list[Path]):

    n = len(paths)
    if (n == 1) and (path := paths[0]).is_dir():
        main2doStandardCheck(paths[0])
    elif (n == 1) and (path := paths[0]).is_file() and VR_OUT_FILENAME_REGEX.match(path.name):
        main2doComparisonFromCSV(paths[0])
    elif n == 2 and paths[0].is_dir() and paths[1].is_dir():
        main2doMatching2CSV(paths[0], paths[1])
    elif paths and (not n % 2) and all(p.is_file() and p.suffix.endswith(VX_MAIN_EXTS) for p in paths):
        main2doDroppedComparison(*paths)
    else:
        printUsage(VR_USAGE_0, paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
