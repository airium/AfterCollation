from imports import *

SR_USAGE = f'''ScansRechecker (SR) only accepts the following input:
1. drop/cli a single folder (ideally "Scans")

SR includes the following behaviors:
1. locate all "{STD_BKS_DIRNAME}" and (only) process all their sub-dirs.
2. use a temporary dir "/{TEMP_DIR_PATH}" and hardlink to bypass rare characters in path.
3. check dir/file names, format/infos and do a full decoding test.

A processing log (SR-*.log) will be generated for later review.
'''




def main(root):

    logger = initLogger(log_path := root.parent.joinpath(f'SR-{TIMESTAMP}.log'))
    logger.info(f'Using ScansRechecker (SR) of AfterCollation {AC_VERSION}')
    logger.info(f'The user input is "{root}".')

    if platform.system() == 'Windows':
        temp_dir = getTempDir4Hardlink(root)
        if temp_dir: logger.info(f'Enabled hardlink mode and using a temporary dir "{temp_dir}".')
        else: logger.info(f'Cannot use hardlink mode. `cwebp` will fail if non-windows-1252 character exists in filepath.')
    else:
        temp_dir = None

    for scans_dir in getScansDirs(root, logger=logger):
        logger.info(f'================================================================================================')
        logger.info(f'Checking "{scans_dir}".')
        logger.info(f'Checking file types ...')
        files = getScansFiles(scans_dir, logger=logger)
        logger.info(f'Checking file names ...')
        chkScansNaming(scans_dir, logger=logger)
        logger.info(f'Checking file formats/metadata/content ...')
        chkScansFiles(files, temp_dir, logger=logger)
        logger.info(f'Printing scans layout summary ...')
        logScansSummary(scans_dir, files, logger=logger)

    logger.info('Scans checking completed.')
    logger.info('')
    logger.info('NEXT:')
    logger.info(f'View the log "{log_path}".')
    logger.info(f'For any ERROR, you should now start fixing them.')
    logger.info(f'For any WARNING, you should make sure they do not matter.')
    logger.info(f'Some INFO may still contain a notice, do not skip them too fast.')
    logger.info('')
    logger.info('You should always manually view all files to check if the image content is proper,')
    logger.info('As this tool NEVER knows if you placed unrelated files or misplaced files.')
    logger.info('')

    try:
        if temp_dir and not list(temp_dir.iterdir()):
            temp_dir.rmdir()
            logger.info(f'Removed empty temp dir "{temp_dir}".')
    except OSError:
        pass

    logging.shutdown()
    return




def _cli(*paths:Path):

    n = len(paths)
    if (n == 1) and (path := paths[0]).is_dir():
        main(paths[0])
    else:
        printCliNotice(SR_USAGE, paths)




if __name__ == '__main__':

    paths = [Path(p) for p in sys.argv[1:]]
    if DEBUG:
        _cli(*paths)
    else: # if catch the exception as below, vscode doesn't jump to the actual line
        try:
            _cli(*paths)
        except Exception as e:
            print(f'Run into an unexpected error:\n{e}\nPlease report.')

    input('Press ENTER to exit...')
