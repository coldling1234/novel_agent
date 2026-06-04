"""Story generation chains and archive selection helpers."""

from __future__ import annotations

import json
from typing import Any, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from novel_ai.core.llm import create_chat_model


def _as_dict(data: BaseModel | dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(data, BaseModel):
        return data.model_dump(by_alias=True)
    if isinstance(data, str):
        return json.loads(data)
    return data


def _to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _extract_entity_names(entity_result: BaseModel | dict[str, Any] | str) -> list[str]:
    data = _as_dict(entity_result)
    names: list[str] = []
    for item in data.get("entities", []):
        name = str(item.get("name", "")).strip()
        if name and name not in names:
            names.append(name)
    return names


def _item_name(item: dict[str, Any]) -> str:
    for key in ("name", "名称", "角色名称", "场景名称", "实体名称"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _matches_item(item: dict[str, Any], names: list[str], followup_outline: str) -> bool:
    item_name = _item_name(item)
    item_text = _to_json(item)
    return any(
        name == item_name or name in item_text or item_name and item_name in followup_outline
        for name in names
    )


def _filter_named_list(items: list[Any], names: list[str], followup_outline: str) -> list[Any]:
    filtered = [
        item
        for item in items
        if isinstance(item, dict) and _matches_item(item, names, followup_outline)
    ]
    return filtered


def build_relevant_archives_json(
    *,
    followup_outline: str,
    extracted_entities: BaseModel | dict[str, Any] | str,
    entities_json: str,
    backgrounds_json: str,
    dynamic_scenes_json: str,
    dynamic_characters_json: str,
) -> str:
    """Select archive entries related to entities extracted from a follow-up outline."""

    names = _extract_entity_names(extracted_entities)
    entities = _as_dict(entities_json)
    backgrounds = _as_dict(backgrounds_json)
    scenes = _as_dict(dynamic_scenes_json)
    characters = _as_dict(dynamic_characters_json)

    relevant_backgrounds = {
        "worldview": backgrounds.get("worldview"),
        "physical_laws": backgrounds.get("physical_laws"),
        "law_boundaries": backgrounds.get("law_boundaries", {}),
        "consistency_notes": backgrounds.get("consistency_notes"),
        "entity_backgrounds": _filter_named_list(backgrounds.get("entity_backgrounds", []), names, followup_outline),
    }

    relevant_archives = {
        "followup_entities": _as_dict(extracted_entities),
        "matched_entity_records": _filter_named_list(entities.get("entities", []), names, followup_outline),
        "matched_backgrounds": relevant_backgrounds,
        "matched_dynamic_scenes": {
            key: _filter_named_list(value, names, followup_outline) if isinstance(value, list) else value
            for key, value in scenes.items()
        },
        "matched_dynamic_characters": {
            key: _filter_named_list(value, names, followup_outline) if isinstance(value, list) else value
            for key, value in characters.items()
        },
    }
    return _to_json(relevant_archives)


def create_recent_story_summary_chain(model_name: Optional[str] = None):
    """Create a plain-text chain that summarizes the newest story text."""

    llm = create_chat_model(model_name)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是长篇小说续写编辑，负责把最近正文压缩成可用于续写的剧情摘要。",
            ),
            (
                "human",
                "请根据下面的最近故事原文，生成一段中文剧情摘要。\n\n"
                "要求：\n"
                "1. 只总结已经发生的事实，包括时间、地点、人物状态、关系变化、未解决危机和伏笔。\n"
                "2. 不要添加原文没有的信息。\n"
                "3. 如果没有可参考原文，输出“暂无最近故事摘要。”。\n"
                "4. 输出纯文本，不要 Markdown。\n\n"
                "最近故事文件：{recent_story_name}\n\n"
                "最近故事原文：\n{recent_story_text}",
            ),
        ]
    )
    return prompt | llm | StrOutputParser()


def create_story_generation_chain(model_name: Optional[str] = None):
    """Create a plain-text chain that writes formal story content."""

    llm = create_chat_model(model_name)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是专业中文长篇小说作者，擅长根据后续大纲和既有档案写正式正文，并保持设定、人物、场景连续性。",
            ),
            (
                "human",
                "请根据下面材料生成正式故事正文。\n\n"
                "创作优先级：\n"
                "1. 后续大纲是主线，正文必须覆盖大纲中的关键事件、人物行动和结果。\n"
                "2. 相关档案只作为背景条件，不能压过大纲，也不能改写既有设定。\n"
                "3. 必须遵守世界背景、物理规则、人物能力、人物性格、场景状态和已有关系。\n"
                "4. 必须参考最近故事摘要衔接剧情，并从故事原文片段中学习叙述语气、节奏和细节密度。\n"
                "5. 不要输出分析、摘要、标题、列表、Markdown 或 JSON，只输出可直接保存到 txt 的小说正文。\n"
                "6. 正文长度尽量接近 {target_length} 字，使用自然段落。\n\n"
                "后续大纲：\n{followup_outline}\n\n"
                "从后续大纲提取的关键实体 JSON：\n{extracted_entities_json}\n\n"
                "根据关键实体筛选出的相关档案 JSON：\n{relevant_archives_json}\n\n"
                "最近故事摘要：\n{recent_summary}\n\n"
                "用于参考风格和衔接的故事原文片段：\n{original_excerpt}",
            ),
        ]
    )
    return prompt | llm | StrOutputParser()
