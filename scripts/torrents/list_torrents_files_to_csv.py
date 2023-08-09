from __init__ import *

import sys
from pathlib import Path
from multiprocessing import Pool
from utils.fileutils import listFile
from configs.runtime import VNx_ALL_EXTS

from bencoder import decode, encode


filterout = ('cd', 'cds', 'scan', 'scans', 'hi-res', 'bk')




def worker(torrent: Path) -> list[str]:

    ret = []
    content: dict = decode(torrent.read_bytes())

    root = content[b'info'][b'name'].decode('utf-8')

    if content[b'info'].get(b'files'):  # if multi files

        paths = []
        for file in content[b'info'][b'files']:
            path_parts = [b.decode('utf-8') for b in file[b"path"]]
            if any(part.lower() in filterout for part in path_parts):
                continue
            if not path_parts[-1].lower().endswith(VNx_ALL_EXTS):
                continue
            if not path_parts[-1].lower().startswith('['):
                continue
            paths.append(path_parts)

        if any(len(path_parts) == 1 for path_parts in paths):  # means season folder
            for path_parts in paths:
                season = root
                location = '/'.join(path_parts[:-1])
                filename = path_parts[-1]
                ret.append((f'""\t"{season}"\t"{location}"\t"{filename}"\n'))
        else:  # means series folder
            for path_parts in paths:
                series = root
                season = path_parts[0]
                location = '/'.join(path_parts[1:-1])
                filename = path_parts[-1]
                ret.append((f'"{series}"\t"{season}"\t"{location}"\t"{filename}"\n'))

    else:  # if single file
        ret.append((f'""\t""\t""\t"{root}"\n'))

    print(torrent)

    return ret




if __name__ == '__main__':

    sys.argv.append('Z:/all')
    torrents = listFile(*sys.argv[1:], ext='torrent')
    if not torrents: sys.exit()
    csv_path = PARENT / 'torrents_files.csv'
    fobj = csv_path.open('w', encoding='utf-8-sig')
    fobj.write('"series"\t"season"\t"location"\t"filename"\n')
    with Pool() as pool:
        results = pool.map_async(worker, torrents, chunksize=100)
        results.wait()
    for result in results.get():
        for line in result:
            fobj.write(line)
    fobj.close()
