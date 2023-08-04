from imports import *

VNA_USAGE = f'''
VideoNamingAlpha (VNA) only accepts the following input:
1. drop/cli a single folder where any M2TS (BDMV) resides

VNA includes the following behaviors:
1. locate all M2TS and try find their volume numbers
2. generate a CSV/YAML/JSON in which you can fill pre-encoding instruction

The video naming fields in the CSV/YAML/JSON can be accepted by VND.
'''




def main(input_dir:Path):

    # NOTE there is a small difference between Path.resolve() and Path.absolute()
    output_parent = input_dir.absolute().parent
    input_dir = input_dir.resolve()

    print(f'Using VideoNamingAlpha (VNA) of AfterCollation {AC_VERSION}')
    print(f'The user input is "{input_dir}".')

    # TODO better adding CLI interface in the future
    config : dict = readConf4VNA(__file__, input_dir)

    # TODO support DVD in the future
    m2ts_paths = listFile(input_dir, ext='m2ts')
    if not m2ts_paths:
        print('\nNo M2TS found under your input.\n')
        return

    rel_paths_strs = [m2ts_file.parent.relative_to(input_dir).as_posix() for m2ts_file in m2ts_paths]
    rel_paths_parts = [rel_path_str.split('/') for rel_path_str in rel_paths_strs]
    rel_paths_depths = [len(rel_path_parts) for rel_path_parts in rel_paths_parts]
    if len(set(rel_paths_depths)) != 1:
        print(f'!!! M2TS files are placed at different depth under your input. '
              f'This will make volume index detection more inaccurate.')

    assumed_vols = guessVolNumsFromPaths(m2ts_paths, input_dir)

    output_dicts : list[dict[str, str]] = []
    pbar = tqdm.tqdm(total=len(m2ts_paths), desc='Loading', dynamic_ncols=True, ascii=True, unit='file')
    for i, m2ts_path, assumed_vol in zip(itertools.count(), m2ts_paths, assumed_vols):

        pbar.set_description(f'Reading {assumed_vol}-{m2ts_path.stem}')
        m2ts_idx = m2ts_path.stem
        shown_path = m2ts_path.relative_to(input_dir).as_posix()
        if ENABLE_VNA_AUDIO_SAMPLES:
            pbar.write('Reading the full M2TS to pick audio samples (this can be slow) ...')
            audio_samples : str = pickAudioSamples(m2ts_path)
        else:
            audio_samples = ''

        cf : CF = CF(m2ts_path)
        # it seems that keep these BDMV texts is better
        # if (not fi.has_video) and (not fi.has_audio):
        #     print(f'! Skipping {shown_path} as it has no video/audio track.')
        #     continue

        pbar.write(f'Added "{shown_path}".')
        output_dict = {}
        # NOTE the order of keys is defined by VNA_TITLE_DICT
        for key in VNA_CSV_FIELDS_DICT.keys():
            output_dict[key] = ''
        # then we need to fill some of them right now
        output_dict[VNA_PATH_CN] = shown_path
        output_dict[VNA_VOL_CN] = assumed_vol
        output_dict[VNA_IDX_CN] = m2ts_idx
        output_dict[DURATION_CN] = cf.fmtGeneralDuration()
        output_dict[TRACKCOMP_CN] = cf.fmtTrackTypeCounts()
        output_dict[VNA_VID_FPS_CN] = cf.fmtFpsInfo()
        output_dict[VNA_AUDIO_SAMPLES_CN] = audio_samples

        output_dicts.append(output_dict)
        pbar.update(1)
    pbar.close()

    if not output_dicts:
        print('!!! No valid M2TS to be listed for output.')
        return


    base = dict(zip(output_dicts[0].keys(), itertools.repeat(BASE_LINE_LABEL)))
    for k in VNA_BASE_LINE_USER_DICT.keys():
        base[k] = ''
    output_dicts = [base] + output_dicts

    for ext in VNA_OUTPUT_EXTS:
        if config.get(ext, False):
            out_file = output_parent.joinpath(f'VNA-{TIMESTAMP}.{ext}')
            print(f'Generating pre-encoding instruction sheet at "{out_file}"...')
            working_list = quotEntries4CSV(output_dicts) if ext == 'csv' else output_dicts
            if not globals()[f'listM2TS2{ext.upper()}'](out_file, working_list):
                print(f'! Failed to write {out_file}.')




def _cli(*paths:Path):

    n = len(paths)
    if (n == 1) and (path := paths[0]).is_dir():
        main(path)
    else:
        printCliNotice(VNA_USAGE, paths)




if __name__ == '__main__':

    paths = [Path(p) for p in sys.argv[1:]]
    try:
        _cli(*paths)
    except Exception as e:
        print(f'Run into an unexpected error:\n{e}\nPlease report.')
    input('Press ENTER to exit...')
