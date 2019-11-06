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
from typing import Dict, List, IO, Union, Optional, Tuple

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
already_done = (already_done[0], *already_done)


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
    if filename < "images{}/{}/{}".format(*already_done) and label in [
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


def get_stored_file_name(file_in_archive_name: str) -> Tuple[Path, Path]:
    inter_dir = ""
    suffix = ".unk"
    if file_in_archive_name.endswith("xml"):
        inter_dir = "ocr"
        suffix = ".xml"

    elif file_in_archive_name.endswith("tif"):
        inter_dir = "image"
        suffix = ".tif"

    assert inter_dir
    assert suffix in ".xml .tif".split()

    inter_dir = Path(inter_dir)

    return (
        inter_dir,
        Path(os.path.split(os.path.split(file_in_archive_name)[0])[-1] + suffix),
    )


def extract_file(file_name: str, dataset_dir: Union[Path, str]) -> Optional[IO]:
    if isinstance(dataset_dir, str):
        dataset_dir = Path(dataset_dir)

        assert dataset_dir.is_dir()

    cpio_name = get_cpio_name(file_name)

    if cpio_name is None:
        return None

    try:
        archive = tarfile.open(dataset_dir / Path(cpio_name), "r")
    except FileNotFoundError:
        return None

    return archive, archive.extractfile(file_name)


def write_file(
    archive: tarfile.TarFile, file: IO, name: str, dataset_dir: Union[Path, str]
):
    if isinstance(dataset_dir, str):
        dataset_dir = Path(dataset_dir)

        assert dataset_dir.is_dir()

    inter_dir, short_file_name = get_stored_file_name(name)

    file_path = dataset_dir / inter_dir / short_file_name

    with file_path.open("wb") as out_file:
        out_file.write(file.read())

    file.close()
    archive.close()


def extract_and_write(
    file: str, dataset_dir_src: Union[Path, str], dataset_dir_dst: Union[Path, str]
):
    archive, file_stream = extract_file(file, dataset_dir_src)

    if file_stream is None:
        return

    write_file(archive, file_stream, file, dataset_dir_dst)


@timeit
def process_all_files(
    file_l: List[str],
    dataset_dir_src: Union[Path, str],
    dataset_dir_dst: Union[Path, str],
    max_executors=6,
):
    mp_extract_and_write = partial(
        extract_and_write,
        dataset_dir_src=dataset_dir_src,
        dataset_dir_dst=dataset_dir_dst,
    )

    # list(tqdm.tqdm(map(mp_extract_and_write, file_l), total=len(file_l)))

    with Pool(max_executors) as executor:
    #     executor.map(mp_extract_and_write, file_l)
        list(tqdm.tqdm(executor.imap(mp_extract_and_write, file_l), total=len(file_l)))


if __name__ == "__main__":
    tobacco_path = Path(r"D:\Tobacco\\")
    seminaire_path = Path(r"F:\tobacco_dataset2\\")
    label_path = Path(r"F:\labels\\")
    all_tif_per_label = get_all_labels(label_path)

    all_xml_per_label = {
        k: list(map(get_xml_name, v)) for k, v in all_tif_per_label.items()
    }

    all_xml_file = sorted(sum(all_xml_per_label.values(), []))
    all_tif_file = sorted(sum(all_tif_per_label.values(), []))

    # print(all_xml_file)
    # print(len(all_xml_file))

    # aa_files = [i for i in sum(all_xml_per_label.values(), []) if fil(get_stored_file_name(i)[1])]

    # print(aa_files)

    # z = tarfile.open(tobacco_path / Path(get_cpio_name(aa_files[0])), 'r')

    # aa_archive_xml = [z.getmember(i) for i in aa_files]

    # assert all(t.isfile() for t in aa_archive_xml)

    process_all_files(all_xml_file, tobacco_path, seminaire_path)
    process_all_files(all_tif_file, tobacco_path, seminaire_path)
