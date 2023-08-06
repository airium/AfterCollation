from imports import *


VNA_USAGE = f'''
VideoNamingAlpha (VNA) only accepts the following input:
1. drop/cli a single folder where any M2TS (BDMV) resides

VNA includes the following behaviors:
1. locate all M2TS and try find their volume numbers
2. generate a CSV/YAML/JSON in which you can fill pre-encoding instruction

The video naming fields in the CSV/YAML/JSON can be accepted by VND.
'''




def main(input_dir: Path):

    logger = initLogger(log_path := input_dir.parent.joinpath(f'VNA-{TIMESTAMP}.log'))
    logger.info(f'Using VideoNamingAlpha (VNA) of AfterCollation {AC_VERSION}')
    logger.info(f'The user input is "{input_dir}".')

    # TODO better adding CLI interface in the future
    config: dict = readConf4VNA(__file__, input_dir)

    # TODO support DVD in the future
    if not (m2ts_paths := listFile(input_dir, ext='m2ts')):
        logger.error('No M2TS found under your input.')
        return

    assumed_vols = guessVolNumsFromPaths(m2ts_paths, input_dir, logger)
    if ENABLE_AUDIO_SAMPLES_IN_VNA:
        logger.info('Full reading the M2TS to pick audio samples (this will be slow) ...')

    mp = NUM_CPU_JOBS if ENABLE_AUDIO_SAMPLES_IN_VNA else NUM_IO_JOBS
    logger.info(f'Loading files with {mp} workers ...')
    with logging_redirect_tqdm([logger]):
        pbar = tqdm.tqdm(total=len(m2ts_paths), desc='Loading', dynamic_ncols=True, ascii=True, unit='file')

        def callback(result):
            pbar.update(1)
            logger.info(f'Added "{result[VNA_PATH_CN]}".')

        ret = []
        with Pool(mp) as pool:
            for m2ts_path, assumed_vol in zip(m2ts_paths, assumed_vols):
                ret.append(pool.apply_async(toVNAFullDict, args=(m2ts_path, assumed_vol, input_dir), callback=callback))
            pool.close()
            pool.join()
        pbar.close()
        vna_full_dicts: list[dict[str, str]] = [r.get() for r in ret]

    vna_base_dict = dict(zip(vna_full_dicts[0].keys(), itertools.repeat(BASE_LINE_LABEL)))
    vna_base_dict.update({k: '' for k in VNA_BASE_LINE_USER_DICT.keys()})
    vna_full_dicts = [vna_base_dict] + vna_full_dicts

    for ext in VNA_OUTPUT_EXTS:
        if config.get(ext, False):
            out_file = input_dir.parent.joinpath(f'VNA-{TIMESTAMP}.{ext}')
            print(f'Generating pre-encoding instruction sheet at "{out_file}"...')
            working_list = quotFields4CSV(vna_full_dicts) if ext == 'csv' else vna_full_dicts
            if not globals()[f'listM2TS2{ext.upper()}'](out_file, working_list):
                print(f'! Failed to write {out_file}.')




def _cli(*paths: Path):

    n = len(paths)
    if (n == 1) and (path := paths[0]).is_dir():
        main(path)
    else:
        printCliNotice(VNA_USAGE, paths)




if __name__ == '__main__':
    try:
        _cli(*[Path(p) for p in sys.argv[1:]])
    except:
        traceback.print_exc()
        print('Run into an unexpected error as above. Please report.')
    input('Press ENTER to exit...')
