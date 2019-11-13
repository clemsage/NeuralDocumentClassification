import itertools
import re

from pathlib import Path
from typing import Union, Optional
from xml.etree import ElementTree as et


page_number_re = re.compile(r"\npgNbr=\d+\n")


def parse_xml(xml_path: Union[Path, str], *, page_split=False):
    if isinstance(xml_path, str):
        xml_path = Path(xml_path)

    assert xml_path.exists(), f"File {xml_path!s} not found"
    assert xml_path.is_file(), f"File {xml_path!s} is not a file"

    xml_tree = et.parse(str(xml_path))
    xml_root = xml_tree.getroot()

    assert xml_root is not None, f"File {xml_path!s} is not an XML file"

    text_content = xml_root.find("ot").text

    # Removing page markers
    # Removing new lines
    # Splitting on page markers
    text_content = (
        page_number_re.sub("pgNbr", text_content).replace("\n", " ").split("pgNbr")[:-1]
    )

    if not page_split:
        text_content = ''.join(itertools.chain(*text_content))

    return text_content


if __name__ == "__main__":
    print(parse_xml(r"test\ocr\cjc51c00.xml"))
