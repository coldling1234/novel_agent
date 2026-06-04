"""实体抽取相关的数据结构。"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """单个实体的结构定义。"""

    name: str = Field(description="实体名称，例如角色名、地点名、物品名")
    category: str = Field(description="实体类型，例如角色、场景、物品、组织")
    description: str = Field(description="实体在大纲中的简短说明")
    attributes: Dict[str, str] = Field(
        default_factory=dict,
        description="实体的补充属性，例如身份、阵营、外观、用途、出现章节等",
    )
    source_evidence: str = Field(description="从原始大纲中提取该实体的依据或相关片段")


class EntityExtractionResult(BaseModel):
    """实体抽取的完整结果。"""

    entities: List[Entity] = Field(default_factory=list, description="从大纲中抽取出的实体列表")
