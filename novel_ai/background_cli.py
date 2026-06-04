"""Command-line entry point for background expansion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from novel_ai.chains.background import (
    create_background_expansion_chain,
    create_constrained_entity_background_chain,
)
from novel_ai.chains.entity import create_extraction_chain
from novel_ai.core.parsers import create_entity_background_parser, create_entity_parser
from novel_ai.io_utils import load_json_text, read_outline, read_text_file, save_json, to_pretty_json


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for background expansion."""

    parser = argparse.ArgumentParser(description="背景扩写入口：初始大纲扩写，或手动实体背景扩写。")
    parser.add_argument("--outline", type=str, default=None, help="初始大纲路径；默认读取 outline.txt")
    parser.add_argument("--entities-output", type=str, default="output/entities.json", help="实体摘要 JSON 输出路径")
    parser.add_argument("--background-output", type=str, default="output/backgrounds.json", help="背景扩写 JSON 输出路径")
    parser.add_argument("--manual-entity", type=str, default=None, help="手动提供的单个实体内容")
    parser.add_argument("--manual-entity-file", type=str, default=None, help="手动实体文本文件")
    parser.add_argument(
        "--manual-entity-output",
        type=str,
        default="output/manual_entity_backgrounds.json",
        help="手动实体背景扩写 JSON 输出路径",
    )
    parser.add_argument("--entities-json", type=str, default="output/entities.json", help="已有实体档案 JSON 路径")
    parser.add_argument("--backgrounds-json", type=str, default="output/backgrounds.json", help="已有背景档案 JSON 路径")
    parser.add_argument("--meta-rules-json", type=str, default="output/meta_rules.json", help="已有元规则档案 JSON 路径")
    parser.add_argument("--dynamic-scenes-json", type=str, default="output/dynamic_scenes.json", help="已有动态场景档案 JSON 路径")
    parser.add_argument(
        "--dynamic-characters-json",
        type=str,
        default="output/dynamic_characters.json",
        help="已有动态人物档案 JSON 路径",
    )
    parser.add_argument("--model", type=str, default=None, help="模型名称；默认读取项目配置")
    return parser


def _read_outline(path: str | None) -> str:
    return read_text_file(path) if path else read_outline()


def _read_manual_entity(args: argparse.Namespace) -> str:
    if args.manual_entity:
        return args.manual_entity.strip()
    if args.manual_entity_file:
        return read_text_file(args.manual_entity_file)
    raise ValueError("手动实体扩写需要提供 --manual-entity 或 --manual-entity-file")


def _load_optional_json(path: str) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        return {"missing": path}
    return json.loads(load_json_text(file_path))


def _build_all_archives_json(args: argparse.Namespace) -> str:
    archives = {
        "entities": _load_optional_json(args.entities_json),
        "backgrounds": _load_optional_json(args.backgrounds_json),
        "meta_rules": _load_optional_json(args.meta_rules_json),
        "dynamic_scenes": _load_optional_json(args.dynamic_scenes_json),
        "dynamic_characters": _load_optional_json(args.dynamic_characters_json),
    }
    return json.dumps(archives, ensure_ascii=False, indent=2)


def run_initial_background_expansion(args: argparse.Namespace) -> None:
    """Extract entities and expand backgrounds from the initial outline."""

    outline = _read_outline(args.outline)
    extraction_chain = create_extraction_chain(args.model)
    entity_parser = create_entity_parser()
    entity_result = extraction_chain.invoke(
        {
            "outline": outline,
            "format_instructions": entity_parser.get_format_instructions(),
        }
    )

    save_json(entity_result, args.entities_output)
    print(f"实体摘要完成，已保存到：{args.entities_output}")

    background_chain = create_background_expansion_chain(args.model)
    background_result = background_chain.invoke(
        {
            "outline": outline,
            "entities_json": to_pretty_json(entity_result),
        }
    )

    save_json(background_result, args.background_output)
    print(f"背景扩写完成，已保存到：{args.background_output}")


def run_manual_entity_background_expansion(args: argparse.Namespace) -> None:
    """Expand background for a manually provided entity under all archive constraints."""

    outline = _read_outline(args.outline)
    manual_entity = _read_manual_entity(args)

    extraction_chain = create_extraction_chain(args.model)
    entity_parser = create_entity_parser()
    entity_result = extraction_chain.invoke(
        {
            "outline": manual_entity,
            "format_instructions": entity_parser.get_format_instructions(),
        }
    )

    background_parser = create_entity_background_parser()
    background_chain = create_constrained_entity_background_chain(args.model)
    background_result = background_chain.invoke(
        {
            "outline": outline,
            "manual_entity": manual_entity,
            "entities_json": to_pretty_json(entity_result),
            "all_archives_json": _build_all_archives_json(args),
            "format_instructions": background_parser.get_format_instructions(),
        }
    )

    save_json(background_result, args.manual_entity_output)
    print(f"手动实体背景扩写完成，已保存到：{args.manual_entity_output}")


def run() -> None:
    """Execute background expansion."""

    load_dotenv()
    args = build_parser().parse_args()
    if args.manual_entity or args.manual_entity_file:
        run_manual_entity_background_expansion(args)
        return
    run_initial_background_expansion(args)
