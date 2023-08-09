from __init__ import *


src_path = PARENT / 'torrents_files.csv'
series_path = PARENT / 'seen_series.txt'
seasons_path = PARENT / 'seen_seasons.txt'
locations_path = PARENT / 'seen_locations.txt'
filenames_path = PARENT / 'seen_filenames.txt'

series_set = set()
seasons_set = set()
locations_set = set()
filenames_set = set()

for torrent_file_line in src_path.read_text(encoding='utf-8-sig').splitlines()[1:]:
    if torrent_file_line:
        series, season, location, filename = torrent_file_line.split('\t')
        series_set.add(series.strip('"'))
        seasons_set.add(season.strip('"'))
        locations_set.add(location.strip('"'))
        filenames_set.add(filename.strip('"'))

series_path.write_text('\n'.join(sorted(series_set)), encoding='utf-8-sig')
seasons_path.write_text('\n'.join(sorted(seasons_set)), encoding='utf-8-sig')
locations_path.write_text('\n'.join(sorted(locations_set)), encoding='utf-8-sig')
filenames_path.write_text('\n'.join(sorted(filenames_set)), encoding='utf-8-sig')
