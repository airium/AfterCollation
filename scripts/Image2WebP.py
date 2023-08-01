import sys
import os
from rich.progress import (
    Progress,
    TextColumn,
    MofNCompleteColumn,
    BarColumn,
    TimeRemainingColumn,
)
from rich.console import Console
from PIL import Image
from multiprocessing import Pool, Manager
import subprocess
import time
from rich.live import Live


Image.MAX_IMAGE_PIXELS = 1000000000


# 要处理的图片类型
image_type = ["png", "bmp", "tif", "webp"]


# cwebp命令路径
cwebp = "D:\\Download\\Tool\\libwebp\\bin\\cwebp.exe"
# dwebp命令路径
dwebp = "D:\\Download\\Tool\\libwebp\\bin\\dwebp.exe"
# webpinfo命令路径
webpinfo = "D:\\Download\\Tool\\libwebp\\bin\\webpinfo.exe"


progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=None),
    MofNCompleteColumn(),
    "•",
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    TimeRemainingColumn(),
)


def read_image(path):
    unprocessed_images = []
    if os.path.isfile(path):
        if path.count(".") > 0:
            ft = path.split(".")
            if image_type.__contains__(ft[len(ft) - 1]):
                unprocessed_images.append(path)
    else:
        for dp, dn, fn in os.walk(path):
            if len(fn) > 0:
                for f in fn:
                    if f.count(".") > 0:
                        ft = f.split(".")
                        if image_type.__contains__(ft[len(ft) - 1].lower()):
                            unprocessed_images.append(os.path.join(dp, f))
    return unprocessed_images


def process_image(image_path: str, share: dict, lock, err_list: list):
    if image_path.lower().endswith(".bmp"):
        # Convert BMP to PNG using Pillow
        png_path = f'{image_path[:image_path.rfind(".")]}.png'
        with Image.open(image_path) as im:
            im.save(png_path, "PNG")
        image_path = png_path

    if image_path.lower().endswith(".webp"):
        rcommand = f'{webpinfo} "{image_path}"'
        output, error = run_command(rcommand)
        if output.__contains__("Format: Lossless"):
            # Lossless WebP, decode to PNG and encode with cwebp
            png_path = f'{image_path[:image_path.rfind(".")]}_result.png'
            rcommand = f'{dwebp} "{image_path}" -quiet -o "{png_path}"'
            output, error = run_command(rcommand)
            if len(error) > 0:
                ferror = {"command": rcommand, "output": output, "error": error}
                lock.acquire()
                share["task"] = int(share["task"]) + 1
                err_list.append(ferror)
                lock.release()
                return
            else:
                image_path = png_path
        elif output.__contains__("Format: Lossy"):
            # Lossy WebP, skip encoding and decoding tasks
            lock.acquire()
            share["task"] = int(share["task"]) + 1
            lock.release()
            return

    im = Image.open(image_path)
    # print(f'{image} | {im.format} | {im.size} | {im.mode}')
    width = im.size[0]
    height = im.size[1]
    out_path = image_path[: image_path.rfind(".")] + ".webp"

    # command = f"{cwebp} -q 90 -metadata icc -m 6 -mt -sharp_yuv -af -pre 2 -noalpha -quiet -low_memory "
    command = f"{cwebp} -q 90 -metadata icc -m 6 -mt -sharp_yuv -quiet "
    if height > 16383 and height > width:
        command = f"{command} -resize 0 16383"
    if width > 16383 and width > height:
        command = f"{command} -resize 16383 0"
    rcommand = f'{command} "{image_path}" -o "{out_path}"'
    output, error = run_command(rcommand)
    ferror = {}
    if len(error) > 0:
        if error.__contains__("Error code: 6"):
            rcommand = f'{command} -segments 1 "{image_path}" -o "{out_path}"'
            output, error = run_command(rcommand)
            if len(error) > 0:
                ferror["command"] = rcommand
                ferror["output"] = output
                ferror["error"] = error
        else:
            ferror["command"] = rcommand
            ferror["output"] = output
            ferror["error"] = error
    lock.acquire()
    share["task"] = int(share["task"]) + 1
    if ferror:
        err_list.append(ferror)
        # Delete the 0-byte WebP file if encoding failed
        if os.path.exists(out_path) and os.path.getsize(out_path) == 0:
            os.remove(out_path)
    lock.release()


def run_command(command):
    # 执行命令，并捕获标准输出和错误输出
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    # 将输出信息转换为字符串并返回
    output = stdout.decode("utf-8")
    error = stderr.decode("utf-8")
    return output, error


if __name__ == "__main__":
    file_paths = sys.argv[1:]
    start = time.time()
    unprocessed_images: list[str] = []
    for file_path in file_paths:
        unprocessed_images.extend(read_image(file_path))

    if len(unprocessed_images) == 0:
        Console().print("[red]未找到符合要求的图片！")
    else:
        path_dict = {}
        for image in unprocessed_images:
            key = image[: image.rfind(".")]
            if path_dict.get(key) is None:
                list = []
                list.append(image)
                path_dict[key] = list
            else:
                list = path_dict[key]
                list.append(image)
                path_dict[key] = list
        duplicate_images = []
        for key, images in path_dict.items():
            if len(images) > 1:
                duplicate_images.append(key)
        if duplicate_images:
            Console().print("[red]存在重名图片！")
            for key in duplicate_images:
                images = path_dict[key]
                # Console().print("[yellow]重名图片：")
                for image in images:
                    Console().print(image)
        else:
            live = Live(auto_refresh=False)
            with live:
                # pool = Pool(processes=5)
                pool = Pool()
                manager = Manager()
                share = manager.dict()
                err_list = manager.list()
                lock = manager.Lock()
                task = progress.add_task(
                    "[green]Processing...", total=len(unprocessed_images)
                )
                share["task"] = 0
                for image in unprocessed_images:
                    pool.apply_async(process_image, (image, share, lock, err_list))
                pool.close()
                while not progress.finished:
                    progress.update(task, completed=share["task"])
                    live.update(progress, refresh=True)
                    time.sleep(0.1)
                live.stop()
                pool.join()
                if err_list:
                    for error in err_list:
                        Console().print(error["command"])
                        Console().print(error["output"])
                        Console().print(error["error"])
                for image_path in unprocessed_images:
                    if image_path.lower().endswith(".webp"):
                        # Delete the decoded PNG file
                        png_path = f'{image_path[:image_path.rfind(".")]}_result.png'
                        if os.path.exists(png_path):
                            os.remove(png_path)
                    if image_path.lower().endswith(".bmp"):
                        # Delete the encoded PNG file
                        png_path = f'{image_path[:image_path.rfind(".")]}.png'
                        if os.path.exists(png_path):
                            os.remove(png_path)
    end = time.time()
    total_time = f"总耗时：{time.strftime('%H:%M:%S', time.gmtime(end - start))}"
    error_count = len(err_list)
    error_message = f"[red]报错数量：{error_count}"
    print(total_time)
    Console().print(error_message)

    input("Press Enter to exit...")
