# novel_ai

这个项目用于从小说初始文本大纲中抽取实体信息，例如角色、场景、物品、组织、事件等，并将结果保存为 JSON 文件。
在实体抽取完成后，程序还会继续对实体进行背景扩写，生成世界观、人物背景、地点地理位置、物品来源等设定内容。
最后程序会基于大纲、实体和背景扩写结果，建立三套故事档案系统，并分别保存为元规则档案、动态场景档案、动态角色档案三个 JSON 文件。

## 需要安装的包

```bash
pip install -r requirements.txt
```

## Redis 存储最近上下文

故事生成入口支持用 Redis 保存和读取最近剧情摘要、最近故事原文片段和生成记录。配置 `.env`：

```env
REDIS_URL=redis://localhost:6379/0
REDIS_NOVEL_ID=default
REDIS_RECENT_EXCERPT_CHARS=8000
```

启用后，`python generate_story.py` 会优先从 Redis 读取：

- `novel:{novel_id}:latest_summary`
- `novel:{novel_id}:latest_excerpt`
- `novel:{novel_id}:latest_story_id`

生成完成后会写入：

- `novel:{novel_id}:latest_summary`
- `novel:{novel_id}:latest_excerpt`
- `novel:{novel_id}:latest_story_id`
- `novel:{novel_id}:stories`
- `novel:{novel_id}:story:{story_id}`

如果 Redis 未配置、未安装依赖或连接失败，程序会自动退回本地 `output/stories/` 的 txt 上下文。也可以强制禁用 Redis：

```bash
python generate_story.py --disable-redis
```

## 新入口架构

项目现在拆分为三个独立入口：

```bash
python background_expand.py
```

背景扩写入口。默认读取 `outline.txt`，生成实体摘要 `output/entities.json` 和背景扩写 `output/backgrounds.json`。

```bash
python background_expand.py --manual-entity "张三的旧指南针" --manual-entity-output output/manual_entity_backgrounds.json
```

手动实体背景扩写。会读取当前已有实体、背景、元规则、动态场景、动态人物档案，用这些档案作为限制条件，为指定实体生成背景。

```bash
python archive_summary.py
```

档案摘要入口。读取 `outline.txt`、`output/entities.json`、`output/backgrounds.json`，生成 `output/meta_rules.json`、`output/dynamic_scenes.json`、`output/dynamic_characters.json`。

```bash
python generate_story.py
```

故事生成入口。读取 `followup_outlines/` 中最新的后续大纲 `.txt`，结合已有档案、最近故事摘要和原文片段，生成正式故事正文。

## 根据后续大纲生成正式故事正文

项目根目录新增 `followup_outlines/` 文件夹，用来存放后续大纲 `.txt` 文件。运行下面命令时，程序会默认读取该文件夹中最新的 `.txt`：

```bash
python generate_story.py
```

生成流程：

1. 从后续大纲中抽取关键实体。
2. 根据关键实体，从已有实体档案、背景档案、动态场景档案、动态人物档案中筛选相关属性。
3. 从 `output/stories/` 中读取最近一篇故事正文，生成最近故事摘要，并截取一段原文作为风格和衔接参考。
4. 以“后续大纲”为主，以档案、最近摘要和原文片段为约束，生成正式故事正文。
5. 输出为 `.txt`，默认保存到 `output/stories/后续大纲文件名_story.txt`。

常用参数：

```bash
python generate_story.py --followup-outline followup_outlines/episode_02.txt --target-length 5000
```

- `--followup-outline`：指定某一个后续大纲文件；不指定时读取 `followup_outlines/` 中最新的 `.txt`。
- `--story-output`：指定正文输出路径。
- `--story-output-dir`：指定正文输出目录，默认 `output/stories`。
- `--story-source-dir`：指定最近故事原文来源目录，默认 `output/stories`。
- `--recent-story-chars`：截取最近故事原文的最大字符数，默认 `8000`。
- `--target-length`：正文目标字数，默认 `3000`。

主要依赖：

- `langchain`：构建提示词、解析结构化输出。
- `langchain-openai`：调用 OpenAI 兼容聊天模型。
- `pydantic`：定义实体 JSON 的结构。
- `python-dotenv`：可选，用于从 `.env` 文件读取环境变量。

## 配置大模型

大模型相关配置统一放在 `.env` 文件中：

```env
OPENAI_API_KEY=请填写你的_API_Key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
OPENAI_TEMPERATURE=0
```

- `OPENAI_API_KEY`：模型服务的 API Key。
- `OPENAI_MODEL`：使用的模型名称。
- `OPENAI_BASE_URL`：OpenAI 官方服务可留空；兼容 OpenAI 协议的第三方服务填写接口地址。
- `OPENAI_TEMPERATURE`：生成随机性，实体抽取建议使用 `0`。

## 使用方式

先在项目根目录编辑 `outline.txt`，写入你的小说初始大纲。

然后运行：

```bash
python background_expand.py
python archive_summary.py
```

## 项目结构

```text
novel_ai/
  chains/
    background.py            # 背景扩写链
    dynamic_characters.py    # 动态角色档案生成链
    dynamic_scenes.py        # 动态场景档案生成链
    entity.py                # 实体抽取链
    meta_rules.py            # 元规则档案生成链
  core/
    llm.py                   # 大模型实例创建
    parsers.py               # Pydantic 结构化输出解析器
  schemas/
    background.py            # 背景扩写数据结构
    dynamic_characters.py    # 动态角色档案数据结构
    dynamic_scenes.py        # 动态场景档案数据结构
    entity.py                # 实体抽取数据结构
    meta_rules.py            # 元规则档案数据结构
  cli.py                     # 命令行参数与主流程
  config.py                  # 从 .env 读取大模型配置
  io_utils.py                # 大纲读取与 JSON 写入
main.py        # 极简启动入口
outline.txt    # 小说初始大纲文本
```

## 实体输出格式

程序会生成类似下面的 JSON：

```json
{
  "entities": [
    {
      "name": "林澈",
      "category": "角色",
      "description": "故事主角",
      "attributes": {
        "身份": "主角"
      },
      "source_evidence": "主角林澈"
    }
  ]
}
```

## 背景扩写逻辑

背景扩写分两层进行：

1. 第一层生成故事所在的世界背景和底层物理法则。
2. 第二层在第一层约束下扩写实体背景，实体扩写不可违背已经生成的物理法则。

后续如果有新增实体，可以直接调用 `expand_entity_backgrounds_only`，传入已有世界背景 JSON 和待扩写实体 JSON，只扩写实体，不重新生成物理法则。

## 背景扩写输出格式

程序还会生成类似下面的背景设定 JSON：

```json
{
  "worldview": "旧港城是一座被钟表工业和海上贸易塑造的城市，镜海则是隐藏在现实背后的异空间。",
  "physical_laws": "现实物理规律稳定生效，镜海相关异常只存在于被设定允许的边界内。",
  "law_boundaries": {
    "科技上限": "城市科技水平接近近现代工业城市",
    "超自然限制": "异常现象不能随意扩展到所有场景"
  },
  "consistency_notes": "后续实体扩写不能突破已确定的物理法则和异常边界。",
  "entity_backgrounds": [
    {
      "name": "旧港城",
      "category": "场景",
      "background": "旧港城位于寒冷海湾的入海口，城市中心保留着大量废弃钟楼和老式工坊。",
      "details": {
        "地理位置": "海湾入海口",
        "社会功能": "港口贸易与钟表制造中心"
      },
      "story_function": "承载主线秘密和失踪案调查的核心舞台。",
      "consistency_notes": "后续描写应保持其港口、钟表工业和旧城区气质。"
    }
  ]
}
```

## 元规则档案输出格式

程序会生成类似下面的元规则档案 JSON：

```json
{
  "元规则档案": [
    {
      "规则级别": "L1",
      "规则内容": "故事世界遵循现实物理和自然规律，没有超自然力量。",
      "规则生命周期": "一直生效"
    }
  ]
}
```

## 动态场景档案输出格式

程序会生成类似下面的动态场景档案 JSON：

```json
{
  "动态场景档案": [
    {
      "场景名称": "荒岛",
      "初始环境描述": "太平洋腹地的热带荒岛，有沙滩、礁石、雨林和山脊，资源有限且危险潜伏。",
      "环境变化链": [
        {
          "时间节点": "初始",
          "变更动作": "档案建立",
          "变更结果": "荒岛保持初始求生环境，淡水、食物和庇护资源需要探索获取。"
        }
      ]
    }
  ]
}
```

## 动态角色档案输出格式

程序会生成类似下面的动态角色档案 JSON：

```json
{
  "动态角色档案": [
    {
      "角色名称": "张三",
      "角色初始描述": "流落荒岛的丈夫，承担主要探索和体力劳动。",
      "角色的技能": ["基本急救知识", "观察和模仿能力"],
      "角色的性格": ["务实", "有责任感", "不善表达"],
      "角色变化链": [
        {
          "时间节点": "初始",
          "变更动作": "档案建立",
          "变更结果": "张三处于求生初期，主要目标是保护小薇并寻找离岛机会。"
        }
      ]
    }
  ]
}
```
