"""实体抽取链。"""

from __future__ import annotations

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from novel_ai.core.llm import create_chat_model
from novel_ai.core.parsers import create_entity_parser


def create_extraction_chain(model_name: Optional[str] = None):
    """创建 LangChain 实体抽取链。"""

    parser = create_entity_parser()
    llm = create_chat_model(model_name)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是专业的小说设定整理助手，擅长从中文大纲中抽取角色、场景、物品、组织、事件、能力、概念等实体。",
            ),
            (
                "human",
                "请从下面的小说大纲中抽取所有明确或重要的实体。\n\n"
                "要求：\n"
                "1. category 必须使用中文，例如：角色、场景、物品、组织。\n"
                "2. description 要简洁，但要能说明实体在故事中的作用。\n"
                "3. attributes 使用中文键名，尽量补充身份、阵营、关系、用途、地点等信息。\n"
                "4. source_evidence 填写原文中的关键依据，不要编造大纲中没有的信息。\n"
                "5. 只输出符合格式要求的结果。\n\n"
                "{format_instructions}\n\n"
                "小说大纲：\n{outline}",
            ),
        ]
    )

    return prompt | llm | parser
