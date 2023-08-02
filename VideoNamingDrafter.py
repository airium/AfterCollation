from imports import *

VND_USAGE = f'''
VideoNamingDrafter (VND) only accepts the following input:
1. drop/cli a single folder
2. drop/cli a single folder and a single VNA.csv/yaml/json

VND includes the following behaviors:
1. check the file integrity and mediainfo, and then generate a VND.log for your inspection
2. try guessing some naming fields from the input files (also from VNA if supplied)
3. generate a VND.csv which can be used to name the files by VNE
'''




def season(input_dir:Path, vna_file:Path|None=None):

    logger = initLogger(log_path := input_dir.parent.joinpath(f'VND-{TIMESTAMP}.log'))
    logger.info(f'Using VideoNamingDrafter (VND) of AfterCollation {AC_VERSION}')
    logger.info(f'The input dir is "{input_dir}' + (f' and "{vna_file}".' if vna_file else '.'))

    # TODO re-enable multiprocessing in the future, which can make CRC32 much faster on NVMe SSD
    # try:
    #     multiproc = is_ssd(input_dir)
    # except KeyError: # NOTE RAMDISK or other SCSI disks may have this issue
    #     multiproc = MULTI_PROC_FALLBACK
    #     logger.info(f'SSD checker failed to detect if the input is of SSD or not. Falling back to user config.')
    # except Exception as e:
    #     multiproc = MULTI_PROC_FALLBACK
    #     logger.info(f'SSD checker ran into an unknown error {e}. Please report.')
    # if multiproc:
    #     logger.info('Enabled multi-process.')

    vna_base, vna_configs = loadVNAInfo(vna_file, logger)

    logger.info(f'Locating all media files...')
    all_files = filterOutCDsScans(listFile(input_dir))
    vnd_files = filterOutCDsScans(listFile(input_dir, ext=VNx_ALL_EXTS))
    if (diffs := set(all_files).difference(set(vnd_files))):
        for diff in diffs: logger.error(f'Disallowed file "{diff}".')

    logger.info(f'Loading files with CRC32 checking (this can be slow) ...')
    fis = []
    for vnd_file in tqdm.tqdm(vnd_files, desc='Loading', unit='file', leave=False, ascii=True, dynamic_ncols=True):
        fis.append(FI(vnd_file, init_crc32=False))
    # cmpCRC32FI(fis, findCRC32InFilenames(vnd_files), logger)
    if ENABLE_FILE_CHECKING_IN_VNA:
        chkFiles(fis, logger)

    if vna_base or vna_configs:
        logger.info(f'Matching files to VNA instruction ...')
        # first fill each FI from VNA
        # this is because audio samples will not appear in naming_dicts
        # so we cannot send naming_dicts to fillFieldsFromVNA() in which it needs the audio samples
        fillNamingFieldsFromVNA(fis, vna_configs, logger)
    # now we can get each file's naming dict, also the default
    naming_dicts = pickInfo4NamingDraft(fis, logger)
    default_dict = dict(zip(naming_dicts[0].keys(), itertools.repeat(BASE_LINE_LABEL)))
    for k in VNX_BASE_LINE_EDITABLE_DICT.keys():
        default_dict[k] = '' # make useful fields empty to notify the user that they can fill it
    # don't forget to update the default dict from VNA, which is not updated in fillFieldsFromVNA()
    for k, v in VNA_BASE_LINE_EDITABLE_DICT.items():
        default_dict[k] = vna_base.get(v, '')

    logger.info(f'Preparing to generate the naming proposal ...')
    # looks good, now start writing the csv
    csv_path = input_dir.parent.joinpath(f'VND-{TIMESTAMP}.csv')
    csv_dicts = quotEntries4CSV([default_dict] + naming_dicts)
    if not writeCSV(csv_path, csv_dicts):
        logger.error(f'Failed to save the naming proposal to "{csv_path}".')
    else:
        logger.info(f'The naming proposal is saved to "{csv_path}".')

    logging.shutdown()




def _cli(*paths:Path):

    n = len(paths)
    if (n == 1) and (path := paths[0]).is_dir():
        season(path)
    elif n == 2 and paths[0].is_dir() and paths[1].is_file() and re.match(VNA_CONFS_FILENAME_PATTERN, paths[1].name):
        season(paths[0], paths[1])
    elif n == 2 and paths[1].is_dir() and paths[0].is_file() and re.match(VNA_CONFS_FILENAME_PATTERN, paths[0].name):
        season(paths[1], paths[0])
    else:
        printCliNotice(VND_USAGE, paths)




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
