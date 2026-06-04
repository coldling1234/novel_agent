"""项目配置读取。

所有与大模型相关的配置都从 .env 或系统环境变量读取，
避免把模型参数散落在业务代码中，后续切换模型服务会更方便。
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

import dotenv

dotenv.load_dotenv()



@dataclass(frozen=True)
class LLMConfig:
    """大模型调用配置。"""

    model: str
    temperature: float
    base_url: Optional[str] = None


def _get_float_env(name: str, default: float) -> float:
    """读取浮点型环境变量。

    如果用户在 .env 中误填了非数字内容，这里会给出清晰错误，方便定位配置问题。
    """

    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} 必须是数字，当前值为：{raw_value}") from exc


def load_llm_config(model_override: Optional[str] = None) -> LLMConfig:
    """从环境变量读取大模型配置。

    model_override 用于保留命令行 --model 的覆盖能力；
    如果没有传入，则读取 .env 中的 OPENAI_MODEL。
    """


    return LLMConfig(
        model=model_override or "deepseek-v4-pro",
        temperature=_get_float_env("OPENAI_TEMPERATURE", 0),
    )
