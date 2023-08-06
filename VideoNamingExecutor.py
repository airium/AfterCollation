from imports import *


VNE_USAGE = f'''
VideoNamingExecutor (VNE) only accepts the following input:
1. drop/cli a single VND.csv

VNE includes the following behaviors:
1. check the naming draft from VND
2. do auto naming/indexing for empty fields
3. do naming check, optionally with files check
4. place the files with the target naming and layout by copying or hardlinking (optimally)
'''




def main(csv_path: Path):

    logger = initLogger(log_path := csv_path.parent.joinpath(f'VNE-{TIMESTAMP}.log'))
    logger.info(f'Using VideoNamingExecutor (VNE) of AfterCollation {AC_VERSION}')

    base_naming_dict, file_naming_dicts = loadVNDNaming(csv_path, logger)
    cleanNamingDicts(base_naming_dict, file_naming_dicts, logger)
    if not chkNamingDicts(base_naming_dict, file_naming_dicts, logger): return

    dst_parent_dir = Path(p) if (p := base_naming_dict[FULLPATH_VAR]) else csv_path.parent
    src_file_paths = [Path(d[FULLPATH_VAR]) for d in file_naming_dicts]
    if not tstIO4VNE(src_file_paths, dst_parent_dir, logger): return
    hl = tstMkHardlinks(src_file_paths, dst_parent_dir)
    mp = getCRC32MultiProc(src_file_paths, logger)

    (season := Season()).dst_parent = dst_parent_dir.as_posix()
    season.add(toCoreFileObjs(src_file_paths, logger, mp=mp))
    cmpCfCRC32(season.cfs, [naming_info[CRC32_VAR] for naming_info in file_naming_dicts], logger)
    applyNamingDicts(season, base_naming_dict, file_naming_dicts, logger)
    doAutoIndexing(season, logger)
    # chkSeasonNaming(season, logger)
    stageClassificationName(season, logger)
    chkNamingDependency(season, logger)
    if ENABLE_FILE_CHECKING_IN_VNE:
        if not chkSeasonFiles(season, logger): return
    if not chkFinalNamingConflict(season, logger): return
    logNamingSummary(base_naming_dict, file_naming_dicts, season, logger)
    if not doNaming(season, hl, logger): return




def _cli(*paths: Path):

    n = len(paths)
    if n == 1 and paths[0].is_file() and paths[0].suffix.lower() == '.csv':
        main(paths[0])
    else:
        printCliNotice(VNE_USAGE, paths)




if __name__ == '__main__':
    try:
        _cli(*[Path(p) for p in sys.argv[1:]])
    except:
        traceback.print_exc()
        print('Run into an unexpected error as above. Please report.')
    input('Press ENTER to exit...')
