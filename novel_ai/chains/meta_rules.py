"""元规则档案生成链。"""

from __future__ import annotations

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from novel_ai.core.llm import create_chat_model
from novel_ai.core.parsers import create_meta_rule_archive_parser


def create_meta_rule_archive_chain(model_name: Optional[str] = None):
    """创建元规则档案生成链。"""

    parser = create_meta_rule_archive_parser()
    llm = create_chat_model(model_name)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是专业的长篇小说连续性编辑，负责维护故事元规则，尤其擅长区分不可违背规则和可违背规则。",
            ),
            (
                "human",
                "请基于下面的小说大纲、实体列表和背景扩写结果，建立元规则档案。\n\n"
                "元规则档案格式：\n"
                "1. 规则级别：只能填写 L1 或 L2。\n"
                "   - L1：不可违背规则，意味着在本故事中不会被打破。\n"
                "   - L2：可违背规则，意味着原则上不允许打破，但在特殊情况下可以违背。例如校园禁止打架，但某些情境下仍可能发生打架。\n"
                "2. 规则内容：用简短的一句话说明规则。\n"
                "3. 规则生命周期：声明规则的生效范畴，例如一直生效、仅在当前环境下生效、仅在当前时期生效。\n\n"
                "整理原则：\n"
                "1. 只记录规则，不记录角色介绍或场景环境。\n"
                "2. 优先记录已经明确的信息；不要凭空添加与资料冲突的设定。\n"
                "3. 规则内容要短，便于后续创作快速检查。\n"
                "4. 只输出符合格式要求的结果。\n\n"
                "{format_instructions}\n\n"
                "小说大纲：\n{outline}\n\n"
                "实体列表 JSON：\n{entities_json}\n\n"
                "背景扩写 JSON：\n{backgrounds_json}",
            ),
        ]
    )

    return prompt | llm | parser
