import os
import pathlib
import requests
import tqdm
import zipfile

gdrive_files = {
    "label": ("1kW1Mh6EXWL6_LQf_Jhu3udGjSldQIhax", "./dataset/label.txt",),
    "ocr": ("1DMZLcddKudTrHOtkdcJQiKIHPTRLSXxP", "./tmp/ocr.zip",),
    "image": ("156QjHOKbpLqVNmssYlfuuaKsu8yQzs7a", "./tmp/image.zip",),
}


def download_file_from_google_drive(id, destination):
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith("download_warning"):
                return value

        return None

    def save_response_content(response, destination):
        CHUNK_SIZE = 1024  # 32768
        with open(destination, "wb") as f:
            with tqdm.tqdm(unit="B", unit_divisor=1024, unit_scale=True) as pbar:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        pbar.update(len(chunk))

    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params={"id": id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {"id": id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def download_and_extract(key):
    file_id, destination = gdrive_files[key]
    print(f"Downloading {os.path.split(destination)[-1]}")
    download_file_from_google_drive(file_id, destination)

    dest_dir = "dataset"
    
    if not os.path.exists(dest_dir) or not os.path.isdir(dest_dir):
        os.mkdir(dest_dir)
    
    if destination.endswith(".zip"):
        print(f"Unzipping {destination} to dataset/{os.path.splitext(os.path.split(destination)[-1])[0]}…")
        with zipfile.ZipFile(destination, "r") as zip_fp:
            zip_fp.extractall(dest_dir)
        
        print(f"Cleaning {destination}")
        os.remove(destination)


if __name__ == "__main__":
    download_and_extract("ocr")
