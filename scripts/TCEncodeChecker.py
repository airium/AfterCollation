import os


def check_txt_encoding(folder_path):
    txt_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(
                (".txt", ".cue")
            ):  # Updated condition to check for .txt and .cue files
                file_path = os.path.join(root, file)
                with open(file_path, "rb") as f:
                    encoding = f.read(3)
                    if encoding != b"\xEF\xBB\xBF":
                        txt_files.append(file_path)
    return txt_files


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("请将文件夹拖动到脚本上执行")
        sys.exit(1)

    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print("输入的路径不是文件夹")
        sys.exit(1)

    txt_files = check_txt_encoding(folder_path)
    if txt_files:
        print("编码不是UTF-8 BOM的TXT或CUE文件路径：")  # Updated print message
        for file_path in txt_files:
            print(file_path)
    else:
        print("没有找到编码不是UTF-8 BOM的TXT或CUE文件")  # Updated print message

    input("Press Enter to exit...")
