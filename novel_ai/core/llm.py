"""大模型实例创建。"""

from __future__ import annotations

from typing import Optional

from langchain_openai import ChatOpenAI

from novel_ai.config import load_llm_config


def create_chat_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """创建聊天模型实例。"""

    llm_config = load_llm_config(model_name)
    return ChatOpenAI(
        model=llm_config.model,
        temperature=llm_config.temperature,
        base_url=llm_config.base_url,
    )
