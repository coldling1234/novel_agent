"""分层背景扩写链。"""

from __future__ import annotations

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from novel_ai.core.llm import create_chat_model
from novel_ai.core.parsers import (
    create_entity_background_parser,
    create_world_background_parser,
)
from novel_ai.io_utils import to_pretty_json
from novel_ai.schemas.background import BackgroundExpansionResult


def create_world_background_chain(model_name: Optional[str] = None):
    """创建第一层世界背景和底层物理法则扩写链。"""

    parser = create_world_background_parser()
    llm = create_chat_model(model_name)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是专业的长篇小说世界观设定策划，负责先确定故事所在世界的背景和底层物理法则。",
            ),
            (
                "human",
                "请基于下面的小说大纲和实体列表，先完成第一层背景扩写：确定故事所在的世界背景和底层物理法则。\n\n"
                "扩写范围：\n"
                "1. worldview：故事所在的世界背景，包括时代、社会环境、主要矛盾和整体氛围。\n"
                "2. physical_laws：底层物理法则，说明故事世界的自然规律、现实/超自然边界、科技或能力上限。\n"
                "3. law_boundaries：用结构化键值记录关键边界，例如科技上限、超自然限制、生存规则、环境约束等。\n"
                "4. consistency_notes：写清后续所有实体扩写必须遵守的注意事项。\n\n"
                "要求：\n"
                "1. 只扩写世界背景和底层物理法则，不要逐个扩写实体。\n"
                "2. 可以合理补充细节，但不能违背大纲和实体列表中已经明确的信息。\n"
                "3. 物理法则必须可用于约束后续实体扩写。\n"
                "4. 只输出符合格式要求的结果。\n\n"
                "{format_instructions}\n\n"
                "小说大纲：\n{outline}\n\n"
                "实体列表 JSON：\n{entities_json}",
            ),
        ]
    )

    return prompt | llm | parser


def create_entity_background_expansion_chain(model_name: Optional[str] = None):
    """创建第二层实体背景扩写链。

    这个链用于后续单独扩写新实体时复用：调用时传入已有 world_background_json，
    它只会扩写实体，不会重新生成世界背景和底层物理法则。
    """

    parser = create_entity_background_parser()
    llm = create_chat_model(model_name)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是专业的长篇小说实体设定策划，负责在既定世界背景和底层物理法则约束下扩写实体背景。",
            ),
            (
                "human",
                "请基于下面的小说大纲、实体列表和已确定的世界背景，完成第二层实体背景扩写。\n\n"
                "实体扩写范围：\n"
                "1. 人物背景：出身经历、性格动机、关系牵引、潜在秘密。\n"
                "2. 地点/场景：地理位置、环境风格、社会功能、危险或秘密。\n"
                "3. 物品/能力/概念：来源、用途、限制、代价、与主线的关系。\n"
                "4. 组织/事件：历史渊源、目标、行动方式、对主线的推动。\n\n"
                "硬性要求：\n"
                "1. 只扩写实体，不要重新生成 worldview、physical_laws、law_boundaries。\n"
                "2. 所有实体扩写必须受限于已确定的世界背景和底层物理法则，不可违背。\n"
                "3. 可以合理补充细节，但不能违背大纲、实体列表和世界背景中已经明确的信息。\n"
                "4. 每个实体都要尽量给出 story_function，说明它在故事中承担什么作用。\n"
                "5. details 使用中文键名，按实体类型填写最有用的结构化细节。\n"
                "6. consistency_notes 写清楚后续创作不能随意改变的设定边界，尤其要指出受哪些物理法则约束。\n"
                "7. 只输出符合格式要求的结果。\n\n"
                "{format_instructions}\n\n"
                "小说大纲：\n{outline}\n\n"
                "已确定的世界背景 JSON：\n{world_background_json}\n\n"
                "待扩写实体列表 JSON：\n{entities_json}",
            ),
        ]
    )

    return prompt | llm | parser


def create_background_expansion_chain(model_name: Optional[str] = None):
    """创建完整背景扩写接口。

    首次处理大纲时使用这个接口：先生成世界背景和底层物理法则，
    再在该法则约束下扩写实体背景，最后合并为 BackgroundExpansionResult。
    """

    world_chain = create_world_background_chain(model_name)
    world_parser = create_world_background_parser()
    entity_chain = create_entity_background_expansion_chain(model_name)
    entity_parser = create_entity_background_parser()

    def invoke(inputs: dict):
        world_background = world_chain.invoke(
            {
                "outline": inputs["outline"],
                "entities_json": inputs["entities_json"],
                "format_instructions": world_parser.get_format_instructions(),
            }
        )
        entity_backgrounds = entity_chain.invoke(
            {
                "outline": inputs["outline"],
                "entities_json": inputs["entities_json"],
                "world_background_json": to_pretty_json(world_background),
                "format_instructions": entity_parser.get_format_instructions(),
            }
        )
        return BackgroundExpansionResult(
            **world_background.model_dump(),
            entity_backgrounds=entity_backgrounds.entity_backgrounds,
        )

    class LayeredBackgroundExpansionChain:
        """适配 LangChain invoke 风格的分层背景扩写接口。"""

        def invoke(self, inputs: dict):
            return invoke(inputs)

    return LayeredBackgroundExpansionChain()


def expand_entity_backgrounds_only(
    *,
    outline: str,
    entities_json: str,
    world_background_json: str,
    model_name: Optional[str] = None,
):
    """只扩写实体背景的调用接口。

    后续新增实体时调用这个函数，传入已有世界背景 JSON，它不会重新扩写
    worldview、physical_laws 或 law_boundaries。
    """

    chain = create_entity_background_expansion_chain(model_name)
    parser = create_entity_background_parser()
    return chain.invoke(
        {
            "outline": outline,
            "entities_json": entities_json,
            "world_background_json": world_background_json,
            "format_instructions": parser.get_format_instructions(),
        }
    )


def create_constrained_entity_background_chain(model_name: Optional[str] = None):
    """Create a chain for manually provided entities constrained by all current archives."""

    parser = create_entity_background_parser()
    llm = create_chat_model(model_name)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是专业长篇小说设定编辑，负责在已有档案约束下，为新提供或手动指定的实体扩写背景。",
            ),
            (
                "human",
                "请基于下面手动提供的实体、结构化实体 JSON 和当前已有档案，为该实体扩写背景。\n\n"
                "硬性要求：\n"
                "1. 扩写必须受到所有已有档案限制，包括世界背景、物理规则、元规则、场景状态、人物状态、关系链和已存在实体设定。\n"
                "2. 可以补充合理细节，但不得推翻、改写或绕开已有档案。\n"
                "3. 如果手动实体与已有实体同名或高度相关，必须沿用已有属性，只能补充未明确的背景。\n"
                "4. 如果手动实体是新增实体，必须说明它与已有世界、人物、场景或事件的关系，并写清一致性边界。\n"
                "5. 只输出符合格式要求的 JSON，不要输出解释。\n\n"
                "{format_instructions}\n\n"
                "原始初始大纲：\n{outline}\n\n"
                "手动提供的实体内容：\n{manual_entity}\n\n"
                "待扩写实体 JSON：\n{entities_json}\n\n"
                "当前已有档案 JSON：\n{all_archives_json}",
            ),
        ]
    )

    return prompt | llm | parser
