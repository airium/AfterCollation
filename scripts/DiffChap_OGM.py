import re
import sys
from pathlib import Path
from time import strftime, sleep

if sys.version_info[:2] < (3, 6):
    print("Sorry, at least Python 3.6")
    input("Press ENTER to exit...")
    sys.exit(1)

HELP = """DiffChap 0.2.0 20220602
多选复数个OGM格式章节文件并选中首个OGM文件拖动到本脚本上
前半部分章节应与后半部分章节一一对应
注意文件顺序
"""

TIME_THRESHOLD = 0.01 # max allowed time difference
CHAP_TIME_PATTERN = re.compile(r"^CHAPTER([0-9][0-9])=([0-9][0-9]):([0-9][0-9]):([0-9][0-9]\.[0-9][0-9][0-9])$")
CHAP_NAME_PATTERN = re.compile(r"^CHAPTER([0-9][0-9])NAME=(.+)$")

# https://docs.python.org/3/library/codecs.html#standard-encodings
# the codec list determines the order of encoding to be attempted in `worker`
CODEC_LIST = ["utf_8", "utf_8_sig", "shift_jis", "gb2312", "gbk", "big5", "windows-1252"]


def worker(fp1:Path, fp2:Path):
    ret = []

    f1_ok = f2_ok = False
    is_ogm_chap_line = lambda x: True if CHAP_TIME_PATTERN.match(x) or CHAP_NAME_PATTERN.match(x) else False
    for enc in CODEC_LIST:
        try:
            with fp1.open('r', encoding=enc) as fo1:
                lines1 = fo1.readlines()
                assert sum(list(map(is_ogm_chap_line, lines1))) == len(lines1)
                f1_ok = True
                break
        except:
            continue
    for enc in CODEC_LIST:
        try:
            with fp2.open('r', encoding=enc) as fo2:
                lines2 = fo2.readlines()
                assert sum(list(map(is_ogm_chap_line, lines2))) == len(lines2)
                f2_ok = True
                break
        except:
            continue
    if f1_ok and f2_ok:
        pass
    else:
        ret.append("Error: unknown file content")
        return ret

    if len(lines1) - len(lines2):
        ret.append(f"Error: number of entry inconsistent ({len(lines1)} vs {len(lines2)})")
    for i, (line1, line2) in enumerate(zip(lines1, lines2), start=1):
        line1, line2 = line1.strip(), line2.strip()
        if i % 2: # chapter time line
            val1 = CHAP_TIME_PATTERN.match(line1).groups()
            val2 = CHAP_TIME_PATTERN.match(line2).groups()
            # idx1, idx2 = val1[0], val2[0]
            # if idx1 != idx2:
            #     ret.append(f"Error: chapter index not much at line {i:2d}: {idx1} vs {idx2}")
            time1 = 3600 * int(val1[1]) + 60 * int(val1[2]) + float(val1[3])
            time2 = 3600 * int(val2[1]) + 60 * int(val2[2]) + float(val2[3])
            if abs(time1 - time2) > TIME_THRESHOLD:
                ret.append(f"Error: time differs too much at line {i:2d}: {line1} vs {line2}")
        else: # chapter name line
            val1 = CHAP_NAME_PATTERN.match(line1).groups()
            val2 = CHAP_NAME_PATTERN.match(line2).groups()
            # idx1, idx2 = val1[0], val2[0]
            # if idx1 != idx2:
            #     ret.append(f"Error: chapter index not much at line {i:2d}: {idx1} vs {idx2}")
            if (mo := re.match(r"Chapter ([0-9][0-9])", val1[1])):
                if mo.groups()[0] != val1[0]:
                    ret.append(f"Error: chapter index in name is not correct at line {i:2}: {line1}")
            elif 'vcb' in str(fp1):
                    ret.append(f"Warning: using custom chapter name at line {i:2}: {line1}")
            if (mo := re.match(r"Chapter ([0-9][0-9])", val2[1])):
                if mo.groups()[0] != val2[0]:
                    ret.append(f"Error: chapter index in name is not correct at line {i:2}: {line2}")
            elif 'vcb' in str(fp2):
                    ret.append(f"Warning: using custom chapter name at line {i:2}: {line2}")

    return ret if ret else ("Pass",)


fpaths = list(map(Path, sys.argv[1:]))

# sanity check
if len(fpaths) == 0:
    print(HELP)
    input("Press ENTER to exit...")
    sys.exit(1)
if len(fpaths) % 2:
    print("File number must be multiples of 2")
    input("Press ENTER to exit...")
    sys.exit(1)
for fpath in fpaths:
    if fpath.is_dir():
        print(f"Directory has NOT been supported")
        input("Press ENTER to exit...")
        sys.exit(1)
    if fpath.suffix != '.txt':
        print(f"Only txt file for input")
        input("Press ENTER to exit...")
        sys.exit(1)

# looks OK, let's start the job
num = len(fpaths) // 2
ret = []
for fp1, fp2 in zip(fpaths[:num], fpaths[num:]):
    ret.append(worker(fp1, fp2))
result_path = fpaths[0].with_name(f'result-{strftime("%y%m%d-%H%M%S.txt")}')
with result_path.open('w', encoding='utf-8-sig') as fo:
    for fp1, fp2, r in zip(fpaths[:num], fpaths[num:], ret):
        fo.write(f"{fp1.name}\n")
        fo.write(f"{fp2.name}\n")
        for l in r:
            fo.write(f"\t{l}\n")
print(f"Succeeded with result at: {result_path}")
sleep(3)
sys.exit(0)
