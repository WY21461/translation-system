from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True)
class OCRResult:
    text: str
    engine: str
    warning: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def extract_text_from_image(image: str | Path | BinaryIO, tesseract_cmd: str = "") -> OCRResult:
    """从图片中提取文字。

    依赖 Pillow + pytesseract。若本机没有安装 Tesseract，会返回 warning，
    不影响文本翻译主流程。
    """
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return OCRResult(text="", engine="pytesseract", warning="缺少 pillow 或 pytesseract 依赖，请先安装 requirements.txt。")

    try:
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        img = Image.open(image)
        text = pytesseract.image_to_string(img, lang="eng+chi_sim")
        return OCRResult(text=text.strip(), engine="pytesseract")
    except Exception as exc:  # OCR 属进阶功能，失败时给可读反馈。
        return OCRResult(text="", engine="pytesseract", warning=f"OCR 失败：{exc}")
