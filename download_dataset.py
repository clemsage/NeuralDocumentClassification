import itertools
import os

from concurrent.futures import ThreadPoolExecutor
from functools import partial

import requests
import tqdm


alpha = "abcdefghijklmnopqrstuvwxyz"


def download_file(url, local_dir=""):
    local_filename = url.split("/")[-1]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(local_dir, local_filename), "wb") as f:
            for chunk in tqdm.tqdm(r.iter_content(chunk_size=8192)):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    # f.flush()
    return local_filename


def download_all_files(max_executors=26, filter_f=None):
    if filter_f is None:

        def filter_f(*args, **kwargs):
            return True

    download_file_and_write = partial(download_file, local_dir=r"D:\Tobacco\\")

    with ThreadPoolExecutor(max_workers=max_executors) as executor:
        res = executor.map(
            download_file_and_write,
            map(
                lambda s: f"https://ir.nist.gov/cdip/cdip-images/images.{'.'.join(s)}.cpio",
                filter(filter_f, itertools.combinations_with_replacement(alpha, 2)),
            ),
        )


if __name__ == "__main__":
    already_done = ("d", "i")

    download_all_files(26, lambda x: x > already_done)
