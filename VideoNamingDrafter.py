from imports import *


VND_USAGE = f'''
VideoNamingDrafter (VND) only accepts the following input:
1. drop/cli a single folder (and optionally a single VNA.csv/yaml/json)

The script includes the following behaviors:
1. check the file integrity and mediainfo, and then generate a VND.log for your inspection
2. guess some naming fields from the input files, also fill from VNA if supplied
3. output a VND.csv that you can fill in with naming fields and send to VNE
'''




def main(input_dir: Path, vna_file: Path|None = None):

    logger = initLogger(log_path := input_dir.parent.joinpath(f'VND-{TIMESTAMP}.log'))
    logger.info(f'Using VideoNamingDrafter (VND) of AfterCollation {AC_VERSION}')
    logger.info(f'The input dir is "{input_dir}' + (f' and "{vna_file}"' if vna_file else '') + '.')

    vna_base_naming_dict, vna_file_naming_dicts = readVNANamingFile(vna_file, logger)

    paths = listVNxFilePaths(input_dir, logger)
    cfs = toCoreFilesWithTqdm(paths, logger, mp=getCRC32MultiProc(paths, logger))
    cmpCfCRC32(cfs, findCRC32InFilenames(paths), logger)
    if ENABLE_FILE_CHECKING_IN_VND: chkSeasonFiles(cfs, logger)

    # NOTE first guess naming and then fill each CF from VNA
    # so the naming instruction in VNA will not be overwritten
    # also, audio samples will not appear in file_naming_dicts to be sent to VNE
    # so we cannot use file_naming_dicts for copyNamingFromVNA()
    doEarlyNamingGuess(cfs, logger)
    copyFileNamingFromVNA(cfs, vna_file_naming_dicts, logger)
    file_csv_dicts = toVNDTableDicts(cfs, logger)

    # don't forget to update the default dict from VNA, which is not updated in fillFieldsFromVNA()
    # NOTE leave useful fields as '' to notify the user that they can fill it
    base_csv_dict = {k: BASE_LINE_LABEL for k in VND_FULL_DICT.keys()}
    base_csv_dict.update({k: '' for k in VND_BASE_LINE_USER_DICT.keys()})
    base_csv_dict.update({k: vna_base_naming_dict.get(v, '') for k, v in VNA_BASE_LINE_USER_DICT.items()})

    writeVNDTable(input_dir.parent.joinpath(f'VND-{TIMESTAMP}.csv'), base_csv_dict, file_csv_dicts, logger)




def _cli(*paths: Path):

    n = len(paths)
    if (n == 1) and (path := paths[0]).is_dir():
        main(path)
    elif n == 2 and paths[0].is_dir() and paths[1].is_file() and re.match(VNA_OUT_FILENAME_REGEX, paths[1].name):
        main(paths[0], paths[1])
    elif n == 2 and paths[1].is_dir() and paths[0].is_file() and re.match(VNA_OUT_FILENAME_REGEX, paths[0].name):
        main(paths[1], paths[0])
    else:
        printCliNotice(VND_USAGE, paths)




if __name__ == '__main__':
    try:
        _cli(*[Path(p) for p in sys.argv[1:]])
    except:
        traceback.print_exc()
        print('Run into an unexpected error as above. Please report.')
    input('Press ENTER to exit...')
