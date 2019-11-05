#!/usr/bin/env python3
"""
Created on Tue Nov 05 09:53:17 2019

@author: Douzon
@mail: thibault.douzon@esker.fr

"""
import os

from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def parse_labels(label_path: Path, data_filter_f=None) -> Dict[int, List[str]]:
    label_d = defaultdict(list)
    with label_path.open('r') as label_file:
        for line in label_file:
            filename, label = line.split()

            label = int(label)

            if data_filter_f and data_filter_f(filename, label):
                label_d[label].append(filename)
    return label_d


def filter_data(filename, label):
    if filename < 'imagesd/j/' and label in [0, 2, 10, 11, 13, 14]:
        return True
    return False


def get_all_labels(dir_path: Path) -> Dict[int, List[str]]:
    merge_d = defaultdict(list)
    for file in dir_path.iterdir():
        if file.suffix.endswith('txt'):
            file_d = parse_labels(file, filter_data)

            for k, v in file_d.items():
                merge_d[k].extend(v)
    return merge_d


if __name__ == "__main__":
    label_path = Path(R"F:\labels\\")
    all_labels = get_all_labels(label_path)
    
    print(sum(map(len, all_labels.values())))
    print({k: len(v) for k, v in all_labels.items()})

