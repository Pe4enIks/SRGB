import os
from argparse import ArgumentParser

import cv2


def split(video: str, folder: str, prefix: str, save_every: int = 1) -> None:
    """
    Разделение видео на кадры.

    Parameters
    ----------
    video : str
        Путь к файлу видео.
    folder : str
        Путь к папке, куда будут сохраняться кадры.
    prefix : str
        Префикс имени файла для каждого кадра.
    save_every : int, optional
        Раз в сколько шагов сохранять кадр.

    Returns
    -------
    None
    """
    os.makedirs(folder, exist_ok=True)

    cap = cv2.VideoCapture(video)
    cnt, success, total = 0, True, int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    while success:
        success, image = cap.read()
        if not success:
            break
        cnt += 1
        if cnt % save_every == 0:
            save_path = os.path.join(folder, f"{prefix}_{cnt}.png")
            cv2.imwrite(save_path, image)
        print(f"{cnt} / {total}")


if __name__ == "__main__":
    parser = ArgumentParser()
    # TODO добавить help
    parser.add_argument("-v", "--video", type=str, required=True)
    parser.add_argument("-f", "--folder", type=str, required=True)
    parser.add_argument("-p", "--prefix", type=str, required=True)
    parser.add_argument("-s", "--save-every", type=int, default=5)
    args = parser.parse_args()

    split(args.video, args.folder, args.prefix, args.save_every)
