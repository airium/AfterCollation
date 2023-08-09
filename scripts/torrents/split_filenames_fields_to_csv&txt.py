from __init__ import *
import re
from pathlib import Path
from configs.regex import VCBS_COREFILE_FILENAME_PATTERN
from helpers.naming import splitGroupTag


src_path = PARENT / 'seen_filenames.txt'
out_path = PARENT / 'seen_filename_gtfx.csv'
grptags_path = PARENT / 'seen_filenames_grptags.txt'
titles_path = PARENT / 'seen_filenames_titles.txt'
fulldesp_path = PARENT / 'seen_filenames_fulldesp.txt'
suffixes_path = PARENT / 'seen_filenames_suffixes.txt'

grptags_list: list[str] = list()
titles_list: list[str] = list()
fulldesp_list: list[str] = list()
suffixes_list: list[str] = list()

csv_fobj = out_path.open(mode='w', encoding='utf-8-sig')
csv_fobj.write('"filename","grptags","title","fulldesp","suffix"\n')
for txt_line in src_path.read_text(encoding='utf-8-sig').splitlines():
    if m := re.match(VCBS_COREFILE_FILENAME_PATTERN, txt_line):
        g, t, f, x = m.group('g'), m.group('t'), m.group('f'), m.group('x')
        grptags_list.extend([g.strip() for g in splitGroupTag(g, clean=False, remove_empty=False)])
        titles_list.append(t.strip())
        fulldesp_list.append(f.strip() if f else '')
        suffixes_list.append(x.strip() if x else '')
    else:
        g, t, f, x = '', '', '', ''
        print(f'Failed: "{txt_line}"')
    csv_fobj.write(f'"{txt_line}","{g}","{t}","{f}","{x}"\n')

grptags_list = sorted(set(grptags_list))
titles_list = sorted(set(titles_list))
fulldesp_list = sorted(set(fulldesp_list))
suffixes_list = sorted(set(suffixes_list))

grptags_path.write_text('\n'.join(grptags_list), encoding='utf-8-sig')
titles_path.write_text('\n'.join(titles_list), encoding='utf-8-sig')
fulldesp_path.write_text('\n'.join(fulldesp_list), encoding='utf-8-sig')
suffixes_path.write_text('\n'.join(suffixes_list), encoding='utf-8-sig')

grptags_char_path = PARENT / 'seen_filenames_grptags_char.txt'
titles_char_path = PARENT / 'seen_filenames_titles_char.txt'
fulldesp_char_path = PARENT / 'seen_filenames_fulldesp_char.txt'
suffixes_char_path = PARENT / 'seen_filenames_suffixes_char.txt'