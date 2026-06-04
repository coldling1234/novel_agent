"""元规则档案数据结构。"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class MetaRuleRecord(BaseModel):
    """单条元规则档案。"""

    model_config = ConfigDict(populate_by_name=True)

    rule_level: Literal["L1", "L2"] = Field(
        alias="规则级别",
        description=(
            "规则级别。L1 为不可违背规则，意味着在本故事中不会被打破；"
            "L2 为可违背规则，意味着原则上不允许打破，但特殊情况下可以违背"
        ),
    )
    rule_content: str = Field(alias="规则内容", description="用简短的一句话说明规则内容")
    rule_lifecycle: str = Field(
        alias="规则生命周期",
        description="声明规则的生效范畴，例如一直生效、仅在当前环境下生效、仅在当前时期生效",
    )


class MetaRuleArchiveResult(BaseModel):
    """元规则档案输出。"""

    model_config = ConfigDict(populate_by_name=True)

    meta_rules: List[MetaRuleRecord] = Field(
        default_factory=list,
        alias="元规则档案",
        description="故事中已经明确成立的元规则列表",
    )
