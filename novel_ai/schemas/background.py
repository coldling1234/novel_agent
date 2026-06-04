"""背景扩写相关的数据结构。"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class EntityBackground(BaseModel):
    """单个实体的背景扩写结果。"""

    name: str = Field(description="实体名称，需要与实体抽取结果中的 name 对应")
    category: str = Field(description="实体类型，例如角色、场景、物品、组织")
    background: str = Field(description="围绕该实体扩写出的背景设定")
    details: Dict[str, str] = Field(
        default_factory=dict,
        description="结构化细节，例如人物经历、性格动机、地点位置、物品来源、组织目标等",
    )
    story_function: str = Field(description="该实体在故事中的叙事作用")
    consistency_notes: str = Field(description="扩写时需要保持一致的设定边界或注意事项")


class WorldBackgroundResult(BaseModel):
    """第一层背景扩写：世界背景与底层物理法则。"""

    worldview: str = Field(description="故事所在的世界背景，包括时代、社会环境、主要矛盾和整体氛围")
    physical_laws: str = Field(description="故事底层物理法则，说明后续所有实体扩写不可违背的基础规则")
    law_boundaries: Dict[str, str] = Field(
        default_factory=dict,
        description="结构化法则边界，例如科技上限、超自然限制、生存规则、环境约束等",
    )
    consistency_notes: str = Field(description="后续扩写必须遵守的世界背景和物理法则注意事项")


class EntityBackgroundExpansionResult(BaseModel):
    """第二层背景扩写：受世界背景和物理法则约束的实体背景。"""

    entity_backgrounds: List[EntityBackground] = Field(
        default_factory=list,
        description="逐个实体的背景扩写列表",
    )


class BackgroundExpansionResult(WorldBackgroundResult):
    """完整背景扩写结果。"""

    entity_backgrounds: List[EntityBackground] = Field(
        default_factory=list,
        description="在世界背景和底层物理法则约束下扩写出的实体背景列表",
    )
