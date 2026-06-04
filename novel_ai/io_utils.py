"""文本读取与 JSON 写入工具。"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

DEFAULT_OUTLINE_PATH = "outline.txt"
DEFAULT_FOLLOWUP_OUTLINE_DIR = "followup_outlines"
DEFAULT_STORY_OUTPUT_DIR = "output/stories"


def read_outline() -> str:
    """从固定的大纲文件中读取文本内容。

    默认读取项目根目录下的 outline.txt。
    后续如果要支持章节拆分或多文件导入，可以在这里扩展读取策略。
    """

    path = Path(DEFAULT_OUTLINE_PATH)
    if not path.exists():
        raise FileNotFoundError(f"未找到大纲文件：{DEFAULT_OUTLINE_PATH}")

    outline = path.read_text(encoding="utf-8").strip()
    if not outline:
        raise ValueError(f"大纲文件为空：{DEFAULT_OUTLINE_PATH}")

    return outline


def to_pretty_json(data: BaseModel) -> str:
    """把 Pydantic 对象转换为适合保存或传给模型的格式化 JSON 字符串。"""

    return json.dumps(data.model_dump(by_alias=True), ensure_ascii=False, indent=2)


def save_json(result: BaseModel, output_path: str) -> None:
    """将抽取结果保存为 UTF-8 JSON 文件。"""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_pretty_json(result), encoding="utf-8")


def read_text_file(file_path: str | Path) -> str:
    """Read a UTF-8 text file and reject empty input."""

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"未找到文本文件：{path}")
    if not path.is_file():
        raise ValueError(f"路径不是文件：{path}")

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"文本文件为空：{path}")
    return content


def find_latest_txt_file(directory: str | Path) -> Path:
    """Return the newest .txt file in a directory."""

    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    txt_files = [item for item in path.glob("*.txt") if item.is_file()]
    if not txt_files:
        raise FileNotFoundError(f"目录中没有可用的 .txt 后续大纲：{path}")
    return max(txt_files, key=lambda item: item.stat().st_mtime)


def read_followup_outline(file_path: str | None = None, directory: str = DEFAULT_FOLLOWUP_OUTLINE_DIR) -> tuple[Path, str]:
    """Read a specific follow-up outline or the newest .txt outline in a directory."""

    path = Path(file_path) if file_path else find_latest_txt_file(directory)
    return path, read_text_file(path)


def load_json_text(file_path: str | Path) -> str:
    """Load a JSON file and return normalized pretty JSON text."""

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"未找到 JSON 文件：{path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, ensure_ascii=False, indent=2)


def save_text(content: str, output_path: str | Path) -> None:
    """Save UTF-8 plain text, creating parent folders when needed."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def make_story_output_path(outline_path: Path, output_dir: str = DEFAULT_STORY_OUTPUT_DIR) -> Path:
    """Build a stable .txt output path from the follow-up outline filename."""

    return Path(output_dir) / f"{outline_path.stem}_story.txt"


def collect_recent_story_text(source_dir: str = DEFAULT_STORY_OUTPUT_DIR, max_chars: int = 8000) -> tuple[str, str]:
    """Collect the newest generated story text for continuity context."""

    path = Path(source_dir)
    if not path.exists():
        return "暂无最近故事。", "暂无可参考的故事原文。"

    txt_files = [item for item in path.glob("*.txt") if item.is_file()]
    if not txt_files:
        return "暂无最近故事。", "暂无可参考的故事原文。"

    latest_story = max(txt_files, key=lambda item: item.stat().st_mtime)
    story_text = latest_story.read_text(encoding="utf-8").strip()
    if not story_text:
        return "暂无最近故事。", "暂无可参考的故事原文。"

    return latest_story.name, story_text[-max_chars:]
