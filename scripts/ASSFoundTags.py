import os
import sys
import re

# 定义要寻找的特殊标签
special_tags = ["1img", "2img", "3img", "4img", "1vc", "2vc", "3vc", "4vc", "1va", "2va", "3va", "4va", "distort", "frs", "fsc", "fsvp", "fshp", "jitter", "mover", "moves3", "moves4", "movevc", "rndx", "rndy", "rndz", "rnds", "rnd", "z"]

def find_special_tags(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        
        # 忽略注释中的特殊标签
        content = re.sub(r'Comment:.*?$', '', content, flags=re.MULTILINE)
        
        # 寻找特殊标签
        found_tags = []
        for tag in special_tags:
            escaped_tag = r'\\' + re.escape(tag) if tag != "fsc" else r'\\' + re.escape(tag) + r'\d+'
            if re.search(escaped_tag, content, flags=re.IGNORECASE):
                found_tags.append(tag)
        
        return found_tags

def process_file(file_path):
    found_tags = find_special_tags(file_path)
    if found_tags:
        print(f'文件路径: {file_path}')
        print(f'使用的特殊标签: {", ".join(found_tags)}')
        print()

# 检查命令行参数
if len(sys.argv) < 2:
    print("请将ASS文件或包含ASS文件的文件夹拖动到脚本上执行")
    sys.exit(1)

# 获取拖动到脚本上的文件或文件夹路径
paths = sys.argv[1:]

ass_files = []  # 存储所有的ASS文件路径

for path in paths:
    if os.path.isfile(path):
        # 处理单个ASS文件
        if path.endswith('.ass'):
            ass_files.append(path)
        else:
            print(f"忽略非ASS文件: {path}")
    elif os.path.isdir(path):
        # 处理包含ASS文件的文件夹
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file).replace('/', os.sep)
                if file_path.endswith('.ass'):
                    ass_files.append(file_path)
    else:
        print(f"无效的文件或文件夹路径: {path}")

# 按照字典序对ASS文件路径进行排序
ass_files.sort()

# 处理所有的ASS文件
for file_path in ass_files:
    process_file(file_path)

input("Press Enter to exit...")
