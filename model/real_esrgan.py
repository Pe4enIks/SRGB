from pathlib import PurePath
from typing import Any

import numpy as np
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact


def configure(root: PurePath, config: dict[str, Any]) -> Any:
    """
    Create Real-ESRGAN model from configuration dictionary.

    Parameters
    ----------
    root : PurePath
        Path to project root directory.
    config : dict[str, Any]
        Dictionary with configuration parameters.

    Returns
    -------
    Any
        Real-ESRGAN model.
    """
    model, netscale, dni_weight = None, None, None

    model_path = str(root / config["weights"])
    if config["onnx"]:
        onnx_path = str(root / config["onnx"])
    else:
        onnx_path = None
    model_name = config["model_name"]
    denoise_strength = config["denoise_strength"]

    if model_name == "RealESRGAN_x4plus":
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        netscale = 4
    elif model_name == "RealESRNet_x4plus":
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        netscale = 4
    elif model_name == "RealESRGAN_x4plus_anime_6B":
        model = RRDBNet(
            num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4
        )
        netscale = 4
    elif model_name == "RealESRGAN_x2plus":
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=2,
        )
        netscale = 2
    elif model_name == "realesr-animevideov3":
        model = SRVGGNetCompact(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_conv=16,
            upscale=4,
            act_type="prelu",
        )
        netscale = 4
    elif model_name == "realesr-general-x4v3":
        model = SRVGGNetCompact(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_conv=32,
            upscale=4,
            act_type="prelu",
        )
        netscale = 4
    else:
        raise ValueError(f"model {model_name} does not exist.")

    if model_name == "realesr-general-x4v3" and denoise_strength < 1.0:
        wdn_model_path = str(root / config["wdn_weights"])
        model_path = [model_path, wdn_model_path]
        dni_weight = [denoise_strength, 1.0 - denoise_strength]

    upsampler = RealESRGANer(
        scale=netscale,
        model_path=model_path,
        dni_weight=dni_weight,
        model=model,
        tile=config["tile"],
        tile_pad=config["tile_pad"],
        pre_pad=config["pre_pad"],
        half=not config["fp32"],
        gpu_id=config["gpu_id"],
        backend=config["backend"],
        onnx_path=onnx_path,
        triton_url=config["triton_url"],
        triton_model_name=config["triton_model_name"],
        triton_model_version=config["triton_model_version"],
        outscale=config["outscale"],
        hf_repository=config["huggingface_model_repository"],
    )
    return upsampler


def predict(
    img: np.ndarray,
    upsampler: Any,
) -> np.ndarray:
    """
    Enhance low resolution image using Real-ESRGAN model.

    Parameters
    ----------
    img : np.ndarray
        Image in (h, w, c) format.
    upsampler : Any
        Real-ESRGAN model.

    Returns
    -------
    np.ndarray
        High resolution image in (h*, w*, c) format.
    """
    out_img, _ = upsampler.enhance(img)
    return out_img
