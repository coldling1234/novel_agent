"""动态场景档案生成链。"""

from __future__ import annotations

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from novel_ai.core.llm import create_chat_model
from novel_ai.core.parsers import create_dynamic_scene_archive_parser


def create_dynamic_scene_archive_chain(model_name: Optional[str] = None):
    """创建动态场景档案生成链。"""

    parser = create_dynamic_scene_archive_parser()
    llm = create_chat_model(model_name)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是专业的长篇小说场景连续性编辑，负责维护每个场景的初始环境和后续环境变化链。",
            ),
            (
                "human",
                "请基于下面的小说大纲、实体列表和背景扩写结果，建立动态场景档案。\n\n"
                "动态场景档案格式：\n"
                "1. 场景名称。\n"
                "2. 初始环境描述：记录该场景刚开始出现时的环境描述。\n"
                "3. 环境变化链：维护以时间为主的变化链条，每条包含时间节点、变更动作、变更结果。\n\n"
                "整理原则：\n"
                "1. 只记录场景，不记录角色成长或世界规则。\n"
                "2. 场景变化链只写环境、资源、危险、状态等空间变化。\n"
                "3. 没有发生变化时，变化链可以只记录“初始”节点，变更动作为“档案建立”，变更结果为初始状态。\n"
                "4. 优先记录已经明确的信息；不要凭空添加与资料冲突的设定。\n"
                "5. 只输出符合格式要求的结果。\n\n"
                "{format_instructions}\n\n"
                "小说大纲：\n{outline}\n\n"
                "实体列表 JSON：\n{entities_json}\n\n"
                "背景扩写 JSON：\n{backgrounds_json}",
            ),
        ]
    )

    return prompt | llm | parser
