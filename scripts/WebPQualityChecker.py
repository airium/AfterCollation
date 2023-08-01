import argparse
import sys
import os
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from PIL import Image
from multiprocessing import Pool, Manager
import subprocess
import time
from rich.live import Live

Image.MAX_IMAGE_PIXELS = 1000000000

webp_quality = "D:\\Download\\Tool\\libwebp\\bin\\webp_quality.exe"


def read_image(path):
    unprocessed_images = []
    if os.path.isfile(path):
        if path.lower().endswith(".webp"):
            unprocessed_images.append(path)
    else:
        for dp, dn, fn in os.walk(path):
            if len(fn) > 0:
                for f in fn:
                    if f.lower().endswith(".webp"):
                        unprocessed_images.append(os.path.join(dp, f))
    return unprocessed_images


def process_image(image_path, share, lock, quality):
    rcommand = f'{webp_quality} "{image_path}"'
    output, error = run_command(rcommand)
    lock.acquire()
    share["task"] += 1
    value = int(output[output.rfind(":") + 1 :])
    if value < 88 or value > 92:
        quality.append(output)
    lock.release()


def run_command(command):
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    output = stdout.decode("utf-8")
    error = stderr.decode("utf-8")
    return output, error


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the WebP image or directory containing WebP images",
    )
    args = parser.parse_args()

    file_path = args.file_path
    start = time.time()
    unprocessed_images = read_image(file_path)
    if len(unprocessed_images) == 0:
        Console().print("[red]No suitable images found!")
    else:
        live = Live(auto_refresh=False)
        with live:
            progress = Progress(
                TextColumn("[progress.description]{task.description}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                TextColumn(
                    "[progress.processed]Processed: {task.completed}/{task.total}"
                ),
                TimeRemainingColumn(),
                console=live.console,
            )
            pool = Pool()
            manager = Manager()
            share = manager.dict()
            quality = manager.list()
            lock = manager.Lock()
            task = progress.add_task(
                "[green]Processing...", total=len(unprocessed_images)
            )
            share["task"] = 0
            for image in unprocessed_images:
                pool.apply_async(process_image, (image, share, lock, quality))
            pool.close()
            while not progress.finished:
                progress.update(task, completed=share["task"])
                live.update(progress, refresh=True)
                time.sleep(0.1)
            live.stop()
            # Console().print('\n[bold yellow]WebP Quality:')
            for q in quality:
                Console().print(q)
            pool.join()
    end = time.time()
    Console().print(
        f"\nTotal execution time: [bold]{time.strftime('%H:%M:%S', time.gmtime(end - start))}"
    )

    input("Press Enter to exit...")
