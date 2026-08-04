from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Callable, List


@dataclass(frozen=True)
class BatchTranslateResult:
    translated_markdown: str
    outline: List[str]
    translated_units: int

    def to_dict(self) -> dict:
        return asdict(self)


def extract_outline(markdown_text: str) -> List[str]:
    outline = []
    for line in markdown_text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            outline.append("  " * (level - 1) + f"- {title}")
    return outline


def _translate_table_line(line: str, translate_func: Callable[[str], str]) -> str:
    if not line.strip().startswith("|"):
        return line
    cells = line.split("|")
    new_cells = []
    for cell in cells:
        raw = cell.strip()
        if not raw or re.fullmatch(r":?-{3,}:?", raw):
            new_cells.append(cell)
        else:
            prefix_space = " " if cell.startswith(" ") else ""
            suffix_space = " " if cell.endswith(" ") else ""
            new_cells.append(prefix_space + translate_func(raw) + suffix_space)
    return "|".join(new_cells)


def translate_markdown(markdown_text: str, translate_func: Callable[[str], str]) -> BatchTranslateResult:
    """翻译 Markdown，同时保持目录结构、代码块、列表和表格分隔线。"""
    lines = markdown_text.splitlines()
    output = []
    in_code_block = False
    translated_units = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            output.append(line)
            continue
        if in_code_block or not stripped:
            output.append(line)
            continue
        if re.fullmatch(r"[-*_]{3,}", stripped):
            output.append(line)
            continue
        if stripped.startswith("|"):
            translated = _translate_table_line(line, translate_func)
            output.append(translated)
            translated_units += 1 if translated != line else 0
            continue

        heading = re.match(r"^(#{1,6})(\s+)(.+)$", line)
        if heading:
            translated_title = translate_func(heading.group(3).strip())
            output.append(f"{heading.group(1)}{heading.group(2)}{translated_title}")
            translated_units += 1
            continue

        list_item = re.match(r"^(\s*(?:[-*+] |\d+\. ))(.+)$", line)
        if list_item:
            translated_item = translate_func(list_item.group(2).strip())
            output.append(f"{list_item.group(1)}{translated_item}")
            translated_units += 1
            continue

        output.append(translate_func(line.strip()))
        translated_units += 1

    return BatchTranslateResult("\n".join(output), extract_outline(markdown_text), translated_units)
