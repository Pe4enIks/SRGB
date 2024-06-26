import math
import os
import random
from argparse import ArgumentParser
from typing import Any

import cv2
import numpy as np
from basicsr.data.degradations import (
    add_jpg_compression,
    circular_lowpass_kernel,
    random_add_gaussian_noise,
    random_add_poisson_noise,
    random_mixed_kernels,
)
from parse import parse_yaml


def set_seed(seed: int) -> None:
    """
    Fix random seed.

    Parameters
    ----------
    seed : int
        Seed value.

    Returns
    -------
    None
    """
    random.seed(seed)
    np.random.seed(seed)


def inter_resolution(
    res_lr: tuple[int, int],
    res_hr: tuple[int, int],
) -> tuple[int, int]:
    """
    Get intermediate resolution between low resolution and high resolution.

    Parameters
    ----------
    res_lr : tuple[int, int]
        Height and width of low resolution image in (h, w) format.
    res_hr : tuple[int, int]
        Height and width of high resolution image in (h, w) format.

    Returns
    -------
    tuple[int, int]
        Height and width of intermediate resolution image in (h, w) format.
    """
    h_lr, w_lr = res_lr
    h_hr, w_hr = res_hr

    scale = (h_lr / h_hr + 1.0) / 2.0
    h_inter = int(h_hr * scale)
    w_inter = int(h_inter * w_hr / h_hr)

    return h_inter, w_inter


def blur_kernels(config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate blur kernels, algorithm from paper https://arxiv.org/abs/2107.10833.

    Parameters
    ----------
    config : dict[str, Any]
        Configuration dictionary with parameters to generate blur kernels.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Convolution kernels for blurring without sync_kernel.
    """
    max_kernel_size = config["max_kernel_size"]

    kernel_size1 = config["max_kernel_size"]
    kernel_size2 = config["max_kernel_size"]

    kernel_list1 = config["stage1"]["kernel_list"]
    kernel_list2 = config["stage2"]["kernel_list"]

    kernel_prob1 = config["stage1"]["kernel_prob"]
    kernel_prob2 = config["stage2"]["kernel_prob"]

    blur_sigma1 = config["stage1"]["blur_sigma"]
    blur_sigma2 = config["stage2"]["blur_sigma"]

    betag_range1 = config["stage1"]["betag_range"]
    betag_range2 = config["stage2"]["betag_range"]

    betap_range1 = config["stage1"]["betap_range"]
    betap_range2 = config["stage2"]["betap_range"]

    sinc_prob1 = config["stage1"]["sinc_prob"]
    sinc_prob2 = config["stage2"]["sinc_prob"]

    if np.random.uniform() < sinc_prob1:
        if kernel_size1 < 13:
            omega_c1 = np.random.uniform(np.pi / 3, np.pi)
        else:
            omega_c1 = np.random.uniform(np.pi / 5, np.pi)
        kernel1 = circular_lowpass_kernel(omega_c1, kernel_size1, pad_to=False)
    else:
        kernel1 = random_mixed_kernels(
            kernel_list1,
            kernel_prob1,
            kernel_size1,
            blur_sigma1,
            blur_sigma1,
            [-math.pi, math.pi],
            betag_range1,
            betap_range1,
            noise_range=None,
        )

    pad_size1 = (max_kernel_size - kernel_size1) // 2
    kernel1 = np.pad(kernel1, ((pad_size1, pad_size1), (pad_size1, pad_size1)))

    if np.random.uniform() < sinc_prob2:
        if kernel_size2 < 13:
            omega_c2 = np.random.uniform(np.pi / 3, np.pi)
        else:
            omega_c2 = np.random.uniform(np.pi / 5, np.pi)
        kernel2 = circular_lowpass_kernel(omega_c2, kernel_size2, pad_to=False)
    else:
        kernel2 = random_mixed_kernels(
            kernel_list2,
            kernel_prob2,
            kernel_size2,
            blur_sigma2,
            blur_sigma2,
            [-math.pi, math.pi],
            betag_range2,
            betap_range2,
            noise_range=None,
        )

    pad_size2 = (max_kernel_size - kernel_size2) // 2
    kernel2 = np.pad(kernel2, ((pad_size2, pad_size2), (pad_size2, pad_size2)))

    return kernel1, kernel2


def resize(
    img: np.ndarray,
    resolution: tuple[int, int],
    config: dict[str, Any],
) -> np.ndarray:
    """
    Image resize algorithm.

    Parameters
    ----------
    img : np.ndarray
        Image in (h, w, c) BGR format.
    resolution : tuple[int, int]
        Target resolution for resizing in (h, w) format.
    config : dict[str, Any]
        Configuration dictionary with parameters to resize.

    Returns
    -------
    np.ndarray
        Resized image.
    """
    resize_type = np.random.choice(config["resize_list"])

    if resize_type == "bilinear":
        img = cv2.resize(img, dsize=resolution[::-1], interpolation=cv2.INTER_LINEAR)
    elif resize_type == "area":
        img = cv2.resize(img, dsize=resolution[::-1], interpolation=cv2.INTER_AREA)
    else:
        raise ValueError(f"{resize_type} interpolation is not implemented")

    return img


def noise(img: np.ndarray, config: dict[str, Any]) -> np.ndarray:
    """
    Noise addition algorithm.

    Parameters
    ----------
    img : np.ndarray
        Image in (h, w, c) BGR format.
    config : dict[str, Any]
        Configuration dictionary with parameters to generate noise.

    Returns
    -------
    np.ndarray
        Noisy image.
    """
    gaussian_noise_prob = config["gaussian_noise_prob"]
    gray_noise_prob = config["gray_noise_prob"]

    if np.random.uniform() < gaussian_noise_prob:
        img = random_add_gaussian_noise(
            img, gray_prob=gray_noise_prob, sigma_range=config["gaussian_sigma_range"]
        )
    else:
        img = random_add_poisson_noise(
            img, gray_prob=gray_noise_prob, scale_range=config["poisson_scale_range"]
        )
    return img


def jpg(img: np.ndarray, config: dict[str, Any]) -> np.ndarray:
    """
    JPEG compression algorithm.

    Parameters
    ----------
    img : np.ndarray
        Image in (h, w, c) BGR format.
    config : dict[str, Any]
        Configuration dictionary with parameters to compress.

    Returns
    -------
    np.ndarray
        Compressed image.
    """
    jpeg_quality = config["jpeg_quality"]
    img = add_jpg_compression(img, jpeg_quality)
    return img


def compress(src_folder: str, dst_folder: str, config_path: str) -> None:
    """
    Compress images and save them in new folder.

    Parameters
    ----------
    src_folder : str
        Folder with images to compress.
    dst_folder : str
        Folder to save compressed images.
    config_path : str
        Path to configuration YAML file.

    Returns
    -------
    None
    """
    config = parse_yaml(config_path)
    os.makedirs(dst_folder, exist_ok=True)
    src_files = os.listdir(src_folder)

    hr_resolution = config["resolution"]
    stages = [stage for stage in config.keys() if stage.startswith("compress")]
    total_stages = len(stages)

    for i, stage in enumerate(stages):
        compress_config = config[stage]
        stage_path = os.path.join(dst_folder, compress_config["name"])
        os.makedirs(stage_path, exist_ok=True)
        lr_resolution = compress_config["resolution"]

        kernel1, kernel2 = blur_kernels(compress_config)
        resolution = inter_resolution(lr_resolution, hr_resolution)

        total_images = len(src_files)
        for j, src_file in enumerate(src_files):
            save_path = os.path.join(stage_path, src_file)
            src_file_global = os.path.join(src_folder, src_file)

            img = cv2.imread(src_file_global).astype(np.float32) / 255.0

            blur_img1 = cv2.filter2D(img, ddepth=-1, kernel=kernel1)
            resized_img1 = resize(blur_img1, resolution, compress_config)
            noisy_img1 = noise(resized_img1, compress_config["stage1"])
            jpg_img1 = jpg(noisy_img1, compress_config["stage1"])

            blur_img2 = cv2.filter2D(jpg_img1, ddepth=-1, kernel=kernel2)
            resized_img2 = resize(blur_img2, lr_resolution, compress_config)
            noisy_img2 = noise(resized_img2, compress_config["stage2"])
            jpg_img2 = jpg(noisy_img2, compress_config["stage2"])

            final_img = (jpg_img2 * 255.0).astype(np.uint8)
            cv2.imwrite(save_path, final_img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

            print(f"{i + 1} / {total_stages} stage,", f"{j + 1} / {total_images} image")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-s",
        "--src",
        type=str,
        required=True,
        help="folder with images to compress",
    )
    parser.add_argument(
        "-d",
        "--dst",
        type=str,
        required=True,
        help="folder to save compressed images",
    )
    parser.add_argument(
        "-c",
        "--cfg",
        type=str,
        default="../configs/compress.yaml",
        help="path to configuration YAML file",
    )
    parser.add_argument(
        "-rs",
        "--random-seed",
        type=int,
        default=42,
        help="random seed value",
    )
    args = parser.parse_args()

    set_seed(args.random_seed)
    compress(args.src, args.dst, args.cfg)
