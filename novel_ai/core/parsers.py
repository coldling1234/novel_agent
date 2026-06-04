"""LangChain 结构化输出解析器。"""

from __future__ import annotations

from langchain_core.output_parsers import PydanticOutputParser

from novel_ai.schemas.background import (
    BackgroundExpansionResult,
    EntityBackgroundExpansionResult,
    WorldBackgroundResult,
)
from novel_ai.schemas.dynamic_characters import DynamicCharacterArchiveResult
from novel_ai.schemas.dynamic_scenes import DynamicSceneArchiveResult
from novel_ai.schemas.entity import EntityExtractionResult
from novel_ai.schemas.meta_rules import MetaRuleArchiveResult


def create_entity_parser() -> PydanticOutputParser:
    """创建实体抽取结果解析器。"""

    return PydanticOutputParser(pydantic_object=EntityExtractionResult)


def create_background_parser() -> PydanticOutputParser:
    """创建背景扩写结果解析器。"""

    return PydanticOutputParser(pydantic_object=BackgroundExpansionResult)


def create_world_background_parser() -> PydanticOutputParser:
    """创建世界背景和物理法则解析器。"""

    return PydanticOutputParser(pydantic_object=WorldBackgroundResult)


def create_entity_background_parser() -> PydanticOutputParser:
    """创建实体背景扩写解析器。"""

    return PydanticOutputParser(pydantic_object=EntityBackgroundExpansionResult)


def create_meta_rule_archive_parser() -> PydanticOutputParser:
    """创建元规则档案解析器。"""

    return PydanticOutputParser(pydantic_object=MetaRuleArchiveResult)


def create_dynamic_scene_archive_parser() -> PydanticOutputParser:
    """创建动态场景档案解析器。"""

    return PydanticOutputParser(pydantic_object=DynamicSceneArchiveResult)


def create_dynamic_character_archive_parser() -> PydanticOutputParser:
    """创建动态角色档案解析器。"""

    return PydanticOutputParser(pydantic_object=DynamicCharacterArchiveResult)
