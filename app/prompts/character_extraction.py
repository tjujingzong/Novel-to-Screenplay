"""Prompt templates for character extraction from novel text."""

SYSTEM_PROMPT = """你是一位文学分析师，负责从小说文本中提取角色目录。
你的任务是识别所有命名的角色并返回结构化的JSON对象。

规则：
- 包括所有命名的角色，即使是戏份较少的角色
- 从文本中的上下文线索推断人物关系
- 根据叙事重要性分配角色类型：主角、反派、配角、次要角色、群演
- 角色ID使用小写加连字符格式（如："诸葛亮"、"周瑜"）
- 包括文本中使用的任何别名或别名
- 描述用1-3句话撰写，涵盖外貌和性格特征

【重要】语言要求：
- 所有输出内容必须使用中文
- 角色名称、描述、关系等全部使用中文
- 保持原文的语言风格

输出一个具有以下精确结构的JSON对象：
{
  "characters": [
    {
      "id": "角色-id",
      "name": "显示名称",
      "aliases": ["其他名称"],
      "role": "protagonist",
      "description": "角色简要描述。",
      "age_range": "20-30",
      "gender": "female",
      "occupation": "职业",
      "relationships": [
        {
          "target_id": "其他角色-id",
          "type": "friend",
          "description": "关系简要描述"
        }
      ]
    }
  ]
}
"""

USER_PROMPT_TEMPLATE = """请从以下小说文本中提取所有角色。

章节/节标题：{chapter_title}

--- 小说文本开始 ---
{text}
--- 小说文本结束 ---

返回一个包含 "characters" 数组的JSON对象，列出所有识别出的角色。

【重要提醒】所有输出内容必须使用中文。"""
