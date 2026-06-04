"""动态角色档案数据结构。"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class CharacterChangeRecord(BaseModel):
    """单条角色变化记录。"""

    model_config = ConfigDict(populate_by_name=True)

    time_node: str = Field(alias="时间节点", description="变化发生的时间点、章节点或剧情阶段")
    change_action: str = Field(alias="变更动作", description="导致角色变化的事件、选择、训练或冲突")
    change_result: str = Field(alias="变更结果", description="变化后角色状态、关系、能力或心理发生了什么改变")


class CharacterArchiveRecord(BaseModel):
    """单个动态角色档案。"""

    model_config = ConfigDict(populate_by_name=True)

    character_name: str = Field(alias="角色名称", description="角色名称")
    initial_description: str = Field(alias="角色初始描述", description="角色首次出现或初始状态下的身份、处境和基本介绍")
    skills: List[str] = Field(default_factory=list, alias="角色的技能", description="角色已经明确拥有的技能、能力或知识储备")
    personality: List[str] = Field(default_factory=list, alias="角色的性格", description="角色已经表现出的性格特征")
    character_change_chain: List[CharacterChangeRecord] = Field(
        default_factory=list,
        alias="角色变化链",
        description="以时间为主线维护的角色变化链条",
    )


class DynamicCharacterArchiveResult(BaseModel):
    """动态角色档案输出。"""

    model_config = ConfigDict(populate_by_name=True)

    dynamic_characters: List[CharacterArchiveRecord] = Field(
        default_factory=list,
        alias="动态角色档案",
        description="已出现或已明确提到的角色档案列表",
    )
