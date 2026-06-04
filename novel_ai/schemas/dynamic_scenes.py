"""动态场景档案数据结构。"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SceneChangeRecord(BaseModel):
    """单条场景环境变化记录。"""

    model_config = ConfigDict(populate_by_name=True)

    time_node: str = Field(alias="时间节点", description="变化发生的时间点、章节点或剧情阶段")
    change_action: str = Field(alias="变更动作", description="导致环境变化的事件、行为或外部因素")
    change_result: str = Field(alias="变更结果", description="变化后场景环境或可用条件发生了什么改变")


class SceneArchiveRecord(BaseModel):
    """单个动态场景档案。"""

    model_config = ConfigDict(populate_by_name=True)

    scene_name: str = Field(alias="场景名称", description="场景名称")
    initial_environment_description: str = Field(
        alias="初始环境描述",
        description="刚出现时的环境场景描述，包括空间、氛围、资源、危险等初始信息",
    )
    environment_change_chain: List[SceneChangeRecord] = Field(
        default_factory=list,
        alias="环境变化链",
        description="以时间为主线维护的环境变化链条",
    )


class DynamicSceneArchiveResult(BaseModel):
    """动态场景档案输出。"""

    model_config = ConfigDict(populate_by_name=True)

    dynamic_scenes: List[SceneArchiveRecord] = Field(
        default_factory=list,
        alias="动态场景档案",
        description="已出现或已明确提到的场景档案列表",
    )
