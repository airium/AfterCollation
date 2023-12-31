from imports import *




def _cli(paths: list[Path]):

    n = len(paths)
    if (n == 1) and paths[0].is_dir():
        collectVideoInfos(src_dir=paths[0])
    elif n == 2 and paths[0].is_dir() and paths[1].is_file() and VA_OUT_FILENAME_REGEX.match(paths[1].name):
        collectVideoInfos(src_dir=paths[0], va_file=paths[1])
    elif n == 2 and paths[1].is_dir() and paths[0].is_file() and VA_OUT_FILENAME_REGEX.match(paths[0].name):
        collectVideoInfos(src_dir=paths[1], va_file=paths[0])
    elif n == 1 and paths[0].is_file() and VP_CSV_FILENAME_REGEX.match(paths[0].name):
        placeVideos(csv_path=paths[0])
    else:
        printUsage(VP_USAGE_0, paths)




if __name__ == '__main__':
    wrapTrackBack(_cli, sys.argv[1:])
