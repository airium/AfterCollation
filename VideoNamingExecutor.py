from imports import *

VNE_USAGE = f'''
VideoNamingExecutor (VNE) only accepts the following input:
1. drop/cli the VND.csv

VNE includes the following behaviors:
1. check your naming proposal from the input (VND.csv)
2. do auto indexing and naming inference for empty fields
3. place the input files specified in the input to the target filetree/filenames

VNE will try hardlink when placing the target files.
VNE only read the input files, but will NEVER modify or overwrite the input files.
'''




def main(csv_path:Path):

    logger = initLogger(log_path := csv_path.parent.joinpath(f'VNE-{TIMESTAMP}.log'))
    logger.info(f'Using VideoNamingExecutor (VNE) of AfterCollation {AC_VERSION}')
    logger.info(f'The input csv is "{csv_path}"')

    default_dict, naming_dicts = loadVNDNamingInfo(csv_path, logger)
    cleanNamingDicts(default_dict, naming_dicts, logger)
    if not chkNamingDicts(default_dict, naming_dicts, logger): return

    dst_dir_parent = Path(p) if (p := default_dict[FULLPATH_VAR]) else csv_path.parent
    success, mp, hl = tstIO4VNE([d[FULLPATH_VAR] for d in naming_dicts], dst_dir_parent, logger)
    if not success: return

    season = Season(**{FULLPATH_VAR : dst_dir_parent.as_posix()})
    season.cfs.extend(toCoreFilesVNE(naming_dicts, logger, mp=NUM_IO_JOBS if mp else 1))
    cmpCRC32VNE(season.cfs, [naming_info[CRC32_VAR] for naming_info in naming_dicts], logger)
    applyNamingDicts(season, default_dict, naming_dicts, logger)
    doAutoIndexing(season, logger)
    fmtContentName(season, logger)
    # if not chkSeasonNaming(season, logger): return #! disabled for now
    if not chkNamingConflict(season, logger): return
    if not doNaming(season, hl, logger): return




def _cli(*paths:Path):

    n = len(paths)
    if n == 1 and paths[0].is_file() and paths[0].suffix.lower() == '.csv':
        main(paths[0])
    else:
        printCliNotice(VNE_USAGE, paths)




if __name__ == '__main__':
    paths = [Path(p) for p in sys.argv[1:]]
    if DEBUG:
        _cli(*paths)
    else: # if catch the exception as below, vscode doesn't jump to the actual line
        try:
            _cli(*paths)
        except Exception as e:
            print(f'!!! Run into an unexpected error:\n{e}\nPlease report.')

    input('Press ENTER to exit...')
