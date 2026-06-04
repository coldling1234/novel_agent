"""Command-line entry point for follow-up story generation."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from novel_ai.chains.entity import create_extraction_chain
from novel_ai.chains.story_generation import (
    build_relevant_archives_json,
    create_recent_story_summary_chain,
    create_story_generation_chain,
)
from novel_ai.core.parsers import create_entity_parser
from novel_ai.io_utils import (
    collect_recent_story_text,
    load_json_text,
    make_story_output_path,
    read_followup_outline,
    save_text,
    to_pretty_json,
)
from novel_ai.storage.redis_context import RedisStoryContextStore, load_redis_context_config


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for follow-up story generation."""

    parser = argparse.ArgumentParser(description="根据后续大纲生成正式故事正文 txt。")
    parser.add_argument("--followup-outline", type=str, default=None, help="指定单个后续大纲 .txt 文件")
    parser.add_argument("--followup-outline-dir", type=str, default="followup_outlines", help="后续大纲 .txt 文件夹")
    parser.add_argument("--story-output", type=str, default=None, help="故事正文 txt 输出路径；默认按后续大纲文件名生成")
    parser.add_argument("--story-output-dir", type=str, default="output/stories", help="故事正文 txt 输出文件夹")
    parser.add_argument("--story-source-dir", type=str, default="output/stories", help="本地最近故事原文来源目录")
    parser.add_argument("--recent-story-chars", type=int, default=8000, help="最近故事原文片段最大字符数")
    parser.add_argument("--target-length", type=int, default=3000, help="生成正文目标字数")
    parser.add_argument("--entities-json", type=str, default="output/entities.json", help="已有实体档案 JSON 路径")
    parser.add_argument("--backgrounds-json", type=str, default="output/backgrounds.json", help="已有背景档案 JSON 路径")
    parser.add_argument("--dynamic-scenes-json", type=str, default="output/dynamic_scenes.json", help="已有动态场景档案 JSON 路径")
    parser.add_argument(
        "--dynamic-characters-json",
        type=str,
        default="output/dynamic_characters.json",
        help="已有动态人物档案 JSON 路径",
    )
    parser.add_argument("--redis-url", type=str, default=None, help="Redis 连接地址；默认读取 REDIS_URL")
    parser.add_argument("--redis-novel-id", type=str, default=None, help="Redis 小说 ID；默认读取 REDIS_NOVEL_ID 或 default")
    parser.add_argument("--redis-context-ttl", type=int, default=None, help="Redis 上下文过期秒数；默认不过期")
    parser.add_argument("--disable-redis", action="store_true", help="禁用 Redis，强制使用本地 txt 作为上下文来源")
    parser.add_argument("--model", type=str, default=None, help="模型名称；默认读取项目配置")
    return parser


def _build_redis_store(args: argparse.Namespace) -> RedisStoryContextStore:
    config = load_redis_context_config(
        redis_url=args.redis_url,
        novel_id=args.redis_novel_id,
        context_ttl=args.redis_context_ttl,
        recent_excerpt_chars=args.recent_story_chars,
        enabled=not args.disable_redis,
    )
    return RedisStoryContextStore(config)


def _load_recent_context(args: argparse.Namespace, redis_store: RedisStoryContextStore, summary_chain) -> tuple[str, str, str]:
    redis_context = redis_store.get_latest_context()
    if redis_context is not None:
        print("已从 Redis 读取最近剧情摘要和原文片段")
        return redis_context.story_name, redis_context.excerpt, redis_context.summary

    if not args.disable_redis:
        print(f"Redis 上下文不可用，改用本地故事文件：{redis_store.status_message}")

    recent_story_name, recent_story_text = collect_recent_story_text(
        source_dir=args.story_source_dir,
        max_chars=args.recent_story_chars,
    )
    recent_summary = summary_chain.invoke(
        {
            "recent_story_name": recent_story_name,
            "recent_story_text": recent_story_text,
        }
    )
    return recent_story_name, recent_story_text, recent_summary


def run_story_generation(args: argparse.Namespace) -> None:
    """Generate formal story text from a follow-up outline."""

    followup_outline_path, followup_outline = read_followup_outline(
        file_path=args.followup_outline,
        directory=args.followup_outline_dir,
    )

    extraction_chain = create_extraction_chain(args.model)
    entity_parser = create_entity_parser()
    followup_entities = extraction_chain.invoke(
        {
            "outline": followup_outline,
            "format_instructions": entity_parser.get_format_instructions(),
        }
    )

    relevant_archives_json = build_relevant_archives_json(
        followup_outline=followup_outline,
        extracted_entities=followup_entities,
        entities_json=load_json_text(args.entities_json),
        backgrounds_json=load_json_text(args.backgrounds_json),
        dynamic_scenes_json=load_json_text(args.dynamic_scenes_json),
        dynamic_characters_json=load_json_text(args.dynamic_characters_json),
    )

    summary_chain = create_recent_story_summary_chain(args.model)
    redis_store = _build_redis_store(args)
    recent_story_name, recent_story_text, recent_summary = _load_recent_context(args, redis_store, summary_chain)

    story_chain = create_story_generation_chain(args.model)
    story_text = story_chain.invoke(
        {
            "followup_outline": followup_outline,
            "extracted_entities_json": to_pretty_json(followup_entities),
            "relevant_archives_json": relevant_archives_json,
            "recent_summary": recent_summary,
            "original_excerpt": recent_story_text,
            "target_length": args.target_length,
        }
    )

    output_path = args.story_output or make_story_output_path(followup_outline_path, args.story_output_dir)
    save_text(story_text, output_path)

    generated_summary = summary_chain.invoke(
        {
            "recent_story_name": str(output_path),
            "recent_story_text": story_text,
        }
    )
    story_id = redis_store.save_story_context(
        story_text=story_text,
        summary=generated_summary,
        output_file=output_path,
        outline_file=followup_outline_path,
        target_length=args.target_length,
        model=args.model,
    )

    print(f"后续大纲读取完成：{followup_outline_path}")
    print(f"正式故事正文生成完成，已保存到：{output_path}")
    if story_id:
        print(f"Redis 故事上下文已更新：{story_id}")
    elif not args.disable_redis:
        print(f"Redis 故事上下文未更新：{redis_store.status_message}")


def run() -> None:
    """Execute follow-up story generation."""

    load_dotenv()
    args = build_parser().parse_args()
    run_story_generation(args)
