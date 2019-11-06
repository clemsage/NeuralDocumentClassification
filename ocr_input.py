import re

from pathlib import Path
from typing import Union, Optional
from xml.etree import ElementTree as et


def parse_xml(xml_path: union[Path, str]):
    if isinstance(xml_path, str):
        xml_path = Path(xml_path)

    assert xml_path.exists(), f"File {xml_path!s} not found"
    assert xml_path.is_file(), f"File {xml_path!s} is not a file"

    xml_tree = et.parse(str(xml_path))
    xml_root = xml_tree.getroot()

    assert xml_root is not None, f"File {xml_path!s} is not an XML file"

    text_content = xml_root["ot"].text
    return text_content


if __name__ == "__main__":
    main()
