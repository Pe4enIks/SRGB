import io
import os.path
import zipfile
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import urlencode

import requests


def download_file(pk: str, local_name: str, src_type: str) -> None:
    """
    Скачивание единицы данных через API Yandex Disk.

    Parameters
    ----------
    pk : str
        Публичная ссылка на папку / файл на диске.
    local_name : str
        Путь для сохранения папки / путь к расположению файла (с именем файла).
    src_type : str
        Тип источника, folder / file.

    Returns
    -------
    None
    """
    base_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?"

    final_url = base_url + urlencode(dict(public_key=pk))
    response = requests.get(final_url)
    download_url = response.json()["href"]

    download_response = requests.get(download_url)
    if src_type == "file":
        with open(local_name, "wb") as f:
            f.write(download_response.content)
            print(f"File {local_name} downloaded")
    elif src_type == "folder":
        zip_file = zipfile.ZipFile(io.BytesIO(download_response.content))
        zip_file.extractall(local_name)
        print("Folder downloaded")


def download(download_source: str, save_folder: str) -> None:
    """
    Скачивание данных через API Yandex Disk.

    Parameters
    ----------
    download_source : str
        Url к скачиваемому источнику.
    save_folder : str
        Путь к папке для сохранения папки с Yandex Disk.

    Returns
    -------
    None
    """
    if save_folder:
        save_folder = Path(save_folder)
        os.makedirs(save_folder, exist_ok=True)
    else:
        save_folder = Path.cwd().parent

    files = {
        save_folder: (download_source, "folder"),
    }

    print(f"Will be downloaded {len(files)} sources")
    for name, (src_link, src_type) in files.items():
        download_file(src_link, str(name), src_type)


if __name__ == "__main__":
    parser = ArgumentParser()
    # TODO добавить help
    parser.add_argument("-ds", "--download-source", type=str, required=True)
    parser.add_argument("-sf", "--save-folder", type=str, default=None)
    args = parser.parse_args()

    download(args.download_source, args.save_folder)
