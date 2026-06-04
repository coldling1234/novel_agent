"""Command-line entry point for archive summarization."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from novel_ai.chains.dynamic_characters import create_dynamic_character_archive_chain
from novel_ai.chains.dynamic_scenes import create_dynamic_scene_archive_chain
from novel_ai.chains.meta_rules import create_meta_rule_archive_chain
from novel_ai.core.parsers import (
    create_dynamic_character_archive_parser,
    create_dynamic_scene_archive_parser,
    create_meta_rule_archive_parser,
)
from novel_ai.io_utils import load_json_text, read_outline, read_text_file, save_json


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for archive summarization."""

    parser = argparse.ArgumentParser(description="档案摘要入口：根据大纲、实体摘要和背景扩写生成档案摘要。")
    parser.add_argument("--outline", type=str, default=None, help="初始大纲路径；默认读取 outline.txt")
    parser.add_argument("--entities-json", type=str, default="output/entities.json", help="实体摘要 JSON 路径")
    parser.add_argument("--backgrounds-json", type=str, default="output/backgrounds.json", help="背景扩写 JSON 路径")
    parser.add_argument("--meta-rules-output", type=str, default="output/meta_rules.json", help="元规则档案 JSON 输出路径")
    parser.add_argument(
        "--dynamic-scenes-output",
        type=str,
        default="output/dynamic_scenes.json",
        help="动态场景档案 JSON 输出路径",
    )
    parser.add_argument(
        "--dynamic-characters-output",
        type=str,
        default="output/dynamic_characters.json",
        help="动态人物档案 JSON 输出路径",
    )
    parser.add_argument("--model", type=str, default=None, help="模型名称；默认读取项目配置")
    return parser


def _read_outline(path: str | None) -> str:
    return read_text_file(path) if path else read_outline()


def run_archive_summary(args: argparse.Namespace) -> None:
    """Generate meta-rule, dynamic-scene, and dynamic-character archives."""

    outline = _read_outline(args.outline)
    entities_json = load_json_text(args.entities_json)
    backgrounds_json = load_json_text(args.backgrounds_json)

    meta_rule_chain = create_meta_rule_archive_chain(args.model)
    meta_rule_parser = create_meta_rule_archive_parser()
    meta_rule_result = meta_rule_chain.invoke(
        {
            "outline": outline,
            "entities_json": entities_json,
            "backgrounds_json": backgrounds_json,
            "format_instructions": meta_rule_parser.get_format_instructions(),
        }
    )

    save_json(meta_rule_result, args.meta_rules_output)
    print(f"元规则档案生成完成，已保存到：{args.meta_rules_output}")

    scene_archive_chain = create_dynamic_scene_archive_chain(args.model)
    scene_archive_parser = create_dynamic_scene_archive_parser()
    scene_archive_result = scene_archive_chain.invoke(
        {
            "outline": outline,
            "entities_json": entities_json,
            "backgrounds_json": backgrounds_json,
            "format_instructions": scene_archive_parser.get_format_instructions(),
        }
    )

    save_json(scene_archive_result, args.dynamic_scenes_output)
    print(f"动态场景档案生成完成，已保存到：{args.dynamic_scenes_output}")

    character_archive_chain = create_dynamic_character_archive_chain(args.model)
    character_archive_parser = create_dynamic_character_archive_parser()
    character_archive_result = character_archive_chain.invoke(
        {
            "outline": outline,
            "entities_json": entities_json,
            "backgrounds_json": backgrounds_json,
            "format_instructions": character_archive_parser.get_format_instructions(),
        }
    )

    save_json(character_archive_result, args.dynamic_characters_output)
    print(f"动态人物档案生成完成，已保存到：{args.dynamic_characters_output}")


def run() -> None:
    """Execute archive summarization."""

    load_dotenv()
    args = build_parser().parse_args()
    run_archive_summary(args)
