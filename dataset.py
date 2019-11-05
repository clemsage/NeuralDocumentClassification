#!/usr/bin/env python3
"""
Created on Tue Nov 05 09:53:17 2019

@author: Douzon
@mail: thibault.douzon@esker.fr

"""
import os
import re
import tarfile
import time

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from multiprocessing import Pool
from typing import Dict, List, IO, Union, Optional

import tqdm


class_names = ["email", "form", "handwritten", "invoice", "advertisement"]
class_to_idx = {
    "letter": 0,
    "form": 1,
    "email": 2,
    "handwritten": 3,
    "advertisement": 4,
    "scientific report": 5,
    "scientific publication": 6,
    "specification": 7,
    "file folder": 8,
    "news article": 9,
    "budget": 10,
    "invoice": 11,
    "presentation": 12,
    "questionnaire": 13,
    "resume": 14,
    "memo": 15,
}


already_done = ("d", "j")


def timeit(f):
    def wrap(*args, **kwargs):
        t = time.time()
        f(*args, **kwargs)
        print(f"Elapsed time: {time.time() - t:0.3f}s")

    return wrap


def parse_labels(label_path: Path, data_filter_f=None) -> Dict[int, List[str]]:
    label_d = defaultdict(list)
    with label_path.open("r") as label_file:
        for line in label_file:
            filename, label = line.split()

            label = int(label)

            if data_filter_f and data_filter_f(filename, label):
                label_d[label].append(filename)
    return label_d


def filter_data(filename: str, label: int):
    if filename < "images{}/{}/".format(*already_done) and label in [
        class_to_idx[c] for c in class_names
    ]:
        return True
    return False


def get_all_labels(dir_path: Path) -> Dict[int, List[str]]:
    merge_d = defaultdict(list)
    for file in dir_path.iterdir():
        if file.suffix.endswith("txt"):
            file_d = parse_labels(file, filter_data)

            for k, v in file_d.items():
                merge_d[k].extend(v)
    for l in merge_d.values():
        l.sort()
    return merge_d


def get_xml_name(tif_name: str) -> str:
    assert tif_name.endswith("tif")

    new_filename = os.path.split(os.path.split(tif_name)[0])[-1] + ".xml"
    return os.path.split(tif_name)[0] + "/" + new_filename


cpio_re = re.compile(r"images./([a-z])/([a-z]).*")


def get_cpio_name(file_name: str) -> Optional[str]:

    match = cpio_re.match(file_name)
    if match is not None:
        return "images.{}.{}.cpio".format(*match.groups())
    else:
        return None
    
    
def extract_file(file_name: str, dataset_dir: Union[Path, str]) -> Optional[IO]:
    if isinstance(dataset_dir, str):
        dataset_dir = Path(dataset_dir)

        assert dataset_dir.is_dir()

    cpio_name = get_cpio_name(file_name)

    if cpio_name is None:
        return None

    archive = tarfile.open(dataset_dir / Path(cpio_name), "r")

    return archive.extractfile(file_name)


def write_file(file: IO, name: str, dataset_dir: Union[Path, str]):
    assert not file.closed

    if isinstance(dataset_dir, str):
        dataset_dir = Path(dataset_dir)

        assert dataset_dir.is_dir()

    inter_dir = ""
    suffix = ".unk"
    if name.endswith("xml"):
        inter_dir = "ocr"
        suffix = ".xml"

    elif name.endswith("tif"):
        inter_dir = "image"
        suffix = ".tif"

    inter_dir = Path(inter_dir)

    file_path = (
        dataset_dir
        / inter_dir
        / Path(os.path.split(os.path.split(name)[0])[-1] + suffix)
    )

    with file_path.open("wb") as out_file:
        out_file.write(file.read())


def extract_and_write(
    file: str,
    dataset_dir_src: Union[Path, str],
    dataset_dir_dst: Union[Path, str]
):
    file_stream = extract_file(file, dataset_dir_src)
    write_file(file_stream, file, dataset_dir_dst)


@timeit
def process_all_files(
    file_l: List[str],
    dataset_dir_src: Union[Path, str],
    dataset_dir_dst: Union[Path, str],
    max_executors=8,
):
    mp_extract_and_write = partial(
        extract_and_write,
        dataset_dir_src=dataset_dir_src,
        dataset_dir_dst=dataset_dir_dst
    )

    with Pool(max_executors) as executor:
        executor.map(mp_extract_and_write, file_l)
        # list(tqdm.tqdm(executor.imap(mp_extract_and_write, file_l), total=len(file_l)))



if __name__ == "__main__":
    tobacco_path = Path(r"D:\Tobacco\\")
    seminaire_path = Path(r"F:\tobacco_dataset\\")
    label_path = Path(r"F:\labels\\")
    all_tif_per_label = get_all_labels(label_path)

    all_xml_per_label = {
        k: list(map(get_xml_name, v)) for k, v in all_tif_per_label.items()
    }

    process_all_files(all_xml_per_label[11], tobacco_path, seminaire_path)
