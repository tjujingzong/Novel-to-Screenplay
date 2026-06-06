# 剧本 YAML Schema v1.0

## 1. 概述

本文档定义了 **Novel-to-Screenplay** 小说转剧本工具所使用的 YAML Schema。该 Schema 描述了剧本在 YAML 格式下的完整结构，支持机器校验、人工编辑以及与其他工具的互操作。

### 设计理念

该 Schema 基于三个核心原则：

1. **可往返转换**：YAML → 渲染后的剧本 → YAML 的过程不会丢失信息。每个字段都有明确的剧本格式映射，因此 YAML 可以作为无损的中间交换格式。

2. **对 LLM 友好**：字段名称清晰无歧义，大语言模型能够准确理解并填充。我们使用描述性的英文字段名（如 `character_id`、`time_of_day`、`transition_out`），而非晦涩的缩写。

3. **人工可编辑**：编剧可以用任何文本编辑器打开 YAML 文件并进行有意义的修改。结构直观，可选字段真正可选，格式不会被样板代码淹没。

### 参考的行业标准

- **Fountain**（fountain.io）：开源剧本标记语言标准。我们采用了它的元素类型分类体系（action、dialogue、parenthetical、transition）。
- **Final Draft XML 结构**：层级式的 幕(acts) → 场(scenes) → 元素(elements) 组织结构，参照了 Final Draft 的文档模型。
- **WGA（美国编剧工会）标准**：场景标题格式（内/外. 地点 - 时间）、现在时态的动作描写、角色命名惯例均遵循 WGA 格式规范。

---

## 2. 顶层结构

```yaml
screenplay:
  metadata: { ... }        # 作品信息
  characters: [ ... ]      # 角色目录
  structure:               # 层级内容
    acts: [ ... ]
  notes: [ ... ]           # 可选注释
```

---

## 3. 字段说明

### 3.1 元数据（Metadata）

剧本整体的基本信息。

| 字段 | 类型 | 必填 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `title` | string | 是 | - | 作品标题 | `"祝福"` |
| `author` | string | 是 | - | 原著作者 | `"鲁迅"` |
| `adapted_by` | string | 否 | `"AI-Assisted Adaptation"` | 剧本改编者 | `"张三"` |
| `source_material` | string | 否 | `null` | 原著出处说明 | `"根据鲁迅同名小说改编"` |
| `genre` | string | 是 | - | 主要类型 | `"drama"` |
| `subgenres` | [string] | 否 | `[]` | 次要类型标签 | `["tragedy", "social"]` |
| `format` | string | 否 | `"feature_film"` | 剧本格式，见下方枚举 | `"tv_episode"` |
| `target_audience` | string | 否 | `null` | 目标受众 | `"adult"` |
| `estimated_duration_minutes` | int | 否 | `null` | 预计时长（分钟） | `120` |
| `language` | string | 否 | `"zh"` | ISO 639-1 语言代码 | `"en"`、`"zh"` |
| `version` | string | 否 | `"1.0.0"` | Schema 版本号 | `"1.0.0"` |
| `created_at` | string | 否 | 自动生成 | ISO 8601 创建时间 | `"2026-06-06T15:48:51+00:00"` |
| `modified_at` | string | 否 | 自动生成 | ISO 8601 修改时间 | `"2026-06-06T15:48:51+00:00"` |
| `generator` | string | 否 | `"novel-to-screenplay v1.0"` | 生成工具 | `"novel-to-screenplay v1.0"` |

**设计原因**：元数据采用扁平结构（不做多余嵌套），方便查找和编辑。时间戳和生成器由系统自动填充，但允许手动覆盖。`format` 字段使用枚举约束有效的剧本类型，确保下游工具能可靠地决定渲染行为。

### 3.2 角色目录（Characters）

剧本中所有角色的汇总目录。

| 字段 | 类型 | 必填 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `id` | string | 是 | - | 唯一标识符（slug 格式） | `"xiang-lin-sao"` |
| `name` | string | 是 | - | 显示名称 | `"祥林嫂"` |
| `aliases` | [string] | 否 | `[]` | 角色使用过的其他名字 | `["祥林嫂"]` |
| `role` | string | 否 | `"supporting"` | 角色类型，见下方枚举 | `"protagonist"` |
| `description` | string | 否 | `""` | 外貌与性格概述 | `"旧社会的农村妇女，命运悲惨……"` |
| `age_range` | string | 否 | `null` | 年龄范围 | `"26-40"` |
| `gender` | string | 否 | `null` | 性别 | `"female"` |
| `occupation` | string | 否 | `null` | 职业 | `"女工"` |
| `relationships` | [Relationship] | 否 | `[]` | 与其他角色的关系，见下方 | - |
| `notes` | string | 否 | `null` | 选角/导演备注 | `"需要表现力强的演员"` |
| `first_appearance` | string | 否 | 自动计算 | 首次出场的场景 ID | `"act-1-scene-1"` |

**设计原因**：角色以扁平目录的形式存储（不嵌套在幕/场内），作为全剧本的唯一数据源。`id` 是整个剧本中使用的规范引用标识——显示名称可能变化，但 ID 保持稳定。`first_appearance` 在组装时自动计算，方便选角和制作规划。

#### 关系（Relationship，嵌套在角色内）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_id` | string | 是 | 引用另一个 `character.id` |
| `type` | string | 是 | 关系类型：`sister`（姐妹）、`rival`（对手）、`love_interest`（恋爱对象）、`mentor`（导师）等 |
| `description` | string | 否 | 关系的简要描述 |

### 3.3 结构 > 幕（Acts）

剧本的结构层级：幕 包含 场。

| 字段 | 类型 | 必填 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `id` | string | 是 | - | 唯一标识符 | `"act-1"` |
| `number` | int | 是 | - | 顺序幕号 | `1` |
| `title` | string | 否 | `null` | 幕标题 | `"祝福"` |
| `description` | string | 否 | `null` | 幕的简要概述 | `"旧历年底，叙述者回到鲁镇……"` |
| `scenes` | [Scene] | 否 | `[]` | 该幕包含的场景 | 见下方 |

**设计原因**：三幕式结构是最常见的剧本框架。每一幕大致对应小说的 1-3 个章节，提供自然的节奏结构。`number` 字段始终从 1 开始递增。

### 3.4 场景（Scenes）

每个场景表示在单一地点和时间发生的连续片段。

| 字段 | 类型 | 必填 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `id` | string | 是 | - | 唯一标识符 | `"act-1-scene-1"` |
| `number` | int | 是 | - | 全局场景编号 | `1` |
| `heading` | SceneHeading | 是 | - | 场景标题，见下方 | - |
| `description` | string | 否 | `null` | 场景目的/摘要 | `"叙述者在镇上遇见祥林嫂"` |
| `setting` | string | 否 | `null` | 环境详细描写 | `"灰白色的晚云下，雪花飞舞……"` |
| `characters_present` | [string] | 否 | 自动填充 | 在场角色的 ID 列表 | `["wo", "xiang-lin-sao"]` |
| `elements` | [Element] | 是 | `[]` | 有序剧本元素列表 | 见下方 |
| `transition_out` | string | 否 | `null` | 转出方式，见转场枚举 | `"CUT_TO"` |

#### 场景标题（SceneHeading）

| 字段 | 类型 | 必填 | 默认值 | 说明 | 示例 |
|------|------|------|--------|------|------|
| `location` | string | 是 | - | 地点（大写） | `"鲁镇街道及河边"` |
| `time_of_day` | string | 是 | `"DAY"` | 时间，见时间枚举 | `"下午"` |
| `int_ext` | string | 是 | `"INT"` | 内/外景，见内外部枚举 | `"外"` |

**设计原因**：场景标题被拆分为结构化的子字段，而非单一字符串。这使得工具可以按地点、时间或内/外景筛选场景。`characters_present` 从对话元素自动填充，但也可以手动添加沉默出场的角色。

### 3.5 元素（Elements，场景内）

元素是场景的基本构建单元，按顺序排列在数组中，通过 `type` 字段区分类型（判别联合类型）。

#### 动作元素（Action Element）

描述肢体动作、场景细节或视觉信息，始终使用**现在时态**。

```yaml
- type: action
  text: "祥林嫂瞪着眼睛，直直朝叙述者走来。叙述者站住，准备她来讨钱。"
  importance: "key"
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | `"action"` | 是 | - | 固定为 "action" |
| `text` | string | 是 | - | 动作描写（现在时态） |
| `importance` | string | 否 | `"standard"` | `key`（关键）/ `standard`（标准）/ `background`（背景） |

**设计原因**：`importance` 字段帮助渲染工具强调关键动作（加粗、更大字号），并让编辑者在修改时快速识别重要情节节点。

#### 对白元素（Dialogue Element）

角色的台词。

```yaml
- type: dialogue
  character_id: "xiang-lin-sao"
  character_name: "祥林嫂"
  parenthetical: "切切地"
  line: "一个人死了之后，究竟有没有魂灵的？"
  continuation: false
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | `"dialogue"` | 是 | - | 固定为 "dialogue" |
| `character_id` | string | 是 | - | 引用 `characters[].id` |
| `character_name` | string | 是 | - | 显示名称（冗余存储，方便阅读） |
| `line` | string | 是 | - | 对白内容 |
| `parenthetical` | string | 否 | `null` | 表演指示，如 `"(低声)"` |
| `continuation` | bool | 否 | `false` | 若为被打断后继续的对白，则为 true |

**设计原因**：`character_name` 刻意做了冗余（从角色目录复制），以提升人类可读性。编辑者无需反复查对照角色表即可阅读对白。`character_id` 仍然是程序使用的规范引用。

#### 表演指示元素（Parenthetical Element）

独立的舞台指示，插入在对白之间（如 `(停顿)`、`(望向远方)`）。

```yaml
- type: parenthetical
  character_id: "wo"
  text: "(胆怯起来，想全翻过先前的话)"
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"parenthetical"` | 是 | 固定为 "parenthetical" |
| `character_id` | string | 是 | 该指示适用的角色 |
| `text` | string | 是 | 指示文本 |

#### 转场元素（Transition Element）

场景内或场景间的显式转场。

```yaml
- type: transition
  style: "CUT_TO"
  description: "回忆结束，回到现实"
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"transition"` | 是 | 固定为 "transition" |
| `style` | string | 是 | 见转场类型枚举 |
| `description` | string | 否 | 转场的上下文说明 |

#### 注释元素（Note Element）

编辑者/改编者的评论，**不会渲染**在最终剧本输出中。

```yaml
- type: note
  content: "回忆开始：祥林嫂初到鲁四老爷家"
  author: "叙述者"
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `"note"` | 是 | 固定为 "note" |
| `content` | string | 是 | 注释内容 |
| `author` | string | 否 | 注释作者 |

### 3.6 全局注释（Notes）

剧本级别的可选注释。

```yaml
notes:
  - scope: "global"
    content: "本剧本由 AI 自动生成初稿，建议对对白和节奏进行人工打磨。"
    author: "system"
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | string | 否 | `"global"` | 作用域：`"global"`、`"act-1"`、`"act-2-scene-3"` 等 |
| `content` | string | 是 | - | 注释内容 |
| `author` | string | 否 | `"system"` | `"system"` 或人类编辑者姓名 |

---

## 4. 枚举类型

### ScreenplayFormat（剧本格式）
| 值 | 说明 |
|----|------|
| `feature_film` | 院线长片剧本 |
| `tv_episode` | 电视剧单集 |
| `miniseries` | 迷你剧 |
| `short_film` | 短片 |

### RoleType（角色类型）
| 值 | 说明 |
|----|------|
| `protagonist` | 主角，推动故事发展的核心人物 |
| `antagonist` | 反派，主角的主要对立面 |
| `supporting` | 重要配角 |
| `minor` | 有名字但戏份较少的角色 |
| `extra` | 背景/无名角色 |

### TimeOfDay（时间）
| 值 | 说明 |
|----|------|
| `DAY` | 白天 |
| `NIGHT` | 夜晚 |
| `DAWN` | 黎明 |
| `DUSK` | 黄昏 |
| `CONTINUOUS` | 紧接上一场景 |
| `LATER` | 同一地点，稍后时间 |
| `MOMENTS_LATER` | 同一地点，片刻之后 |

### IntExt（内/外景）
| 值 | 说明 |
|----|------|
| `INT` | 内景（建筑内部） |
| `EXT` | 外景（户外） |
| `INT_EXT` | 内外兼有 |
| `EXT_INT` | 由外景转入内景 |

### TransitionType（转场类型）
| 值 | 说明 |
|----|------|
| `CUT_TO` | 标准切换 |
| `FADE_OUT` | 渐隐 |
| `FADE_TO_BLACK` | 淡出至黑屏 |
| `DISSOLVE_TO` | 叠化转场 |
| `SMASH_CUT` | 突兀跳切 |
| `MATCH_CUT` | 相似画面匹配切换 |
| `WIPE_TO` | 擦除转场 |
| `INTERCUT` | 两个场景交替剪辑 |
| `MONTAGE` | 蒙太奇段落 |
| `TIME_LAPSE` | 时间流逝 |

### ElementImportance（元素重要程度）
| 值 | 说明 |
|----|------|
| `key` | 关键情节点，必须突出显示 |
| `standard` | 常规动作 |
| `background` | 环境氛围/背景细节 |

---

## 5. 渲染指南

每种 YAML 元素在传统剧本格式中的渲染方式：

| 元素 | 渲染方式 |
|------|----------|
| **场景标题** | 左对齐，全大写，如 `内. 鲁四老爷书房 - 白天` |
| **动作** | 左对齐，标准段落，现在时态 |
| **对白** | 居中区块：角色名（全大写、居中），对白文本缩进 |
| **表演指示** | 居中，括号包裹，位于角色名和对白之间 |
| **转场** | 右对齐，全大写，如 `切至：` |
| **注释** | 不渲染到最终输出中（仅供编辑参考） |

---

## 6. 校验规则

除类型检查外，还需满足以下交叉引用约束：

1. **角色引用**：对白和表演指示元素中的每个 `character_id` 必须引用有效的 `characters[].id`。
2. **顺序编号**：幕编号必须递增（1, 2, 3...）。场景编号必须在所有幕中全局递增。
3. **非空结构**：剧本必须至少包含一幕。每幕必须至少包含一个场景。每个场景必须至少包含一个元素。
4. **ID 唯一性**：角色 `id` 值必须唯一。场景 `id` 值必须唯一。
5. **关系完整性**：`Relationship.target_id` 必须引用有效的角色 ID。
6. **场景标题格式**：`location` 应为大写。`time_of_day` 和 `int_ext` 必须使用有效的枚举值。

---

## 7. 完整示例

以下示例来自系统对鲁迅小说《祝福》的真实转换结果：

```yaml
# Screenplay YAML v1.0.0
# Generated by novel-to-screenplay tool on 2026-06-06 15:48:51 UTC
# Schema documentation: docs/YAML_SCHEMA.md
---
screenplay:
  metadata:
    title: Adapted Screenplay
    author: Unknown
    adapted_by: AI-Assisted Adaptation
    genre: drama
    subgenres: []
    format: feature_film
    language: zh
    version: 1.0.0
    created_at: '2026-06-06T15:48:51.265042+00:00'
    modified_at: '2026-06-06T15:48:51.265054+00:00'
    generator: novel-to-screenplay v1.0

  characters:
    - id: xiang-lin-sao
      name: 祥林嫂
      aliases:
        - 祥林嫂
      role: protagonist
      description: 
        旧社会的农村妇女，命运悲惨。初登场时头上扎着白头绳，乌裙，蓝夹袄，月白背心，脸色青黄，两颊带红；后期沦为乞丐，头发全白，脸上瘦削不堪，黄中带黑，神色木然。性格勤劳安分，但遭遇丧夫、丧子、被迫改嫁等打击后变得麻木迟钝。
      age_range: 26-40
      gender: female
      occupation: 女工
      relationships: []
      first_appearance: act-1-scene-1

    - id: lu-si-lao-ye
      name: 鲁四老爷
      aliases:
        - 四叔
      role: antagonist
      description: 鲁镇的一个讲理学的老监生，是祥林嫂的雇主。性格保守、封建、自私，厌恶寡妇，迷信忌讳。
      age_range: 50-60
      gender: male
      occupation: 地主/监生
      relationships: []
      first_appearance: act-1-scene-2

    - id: si-shen
      name: 四婶
      aliases:
        - 四太太
      role: supporting
      description: 鲁四老爷的妻子，心肠稍软但受封建思想影响。最初雇用祥林嫂，后因祥林嫂的遭遇而同情，但依然遵循丈夫的告诫。
      age_range: 40-50
      gender: female
      occupation: 家庭主妇
      relationships: []
      first_appearance: act-1-scene-4

    - id: wo
      name: 我
      aliases:
        - 叙述者
      role: supporting
      description: 小说的第一人称叙述者，鲁四老爷的本家侄子，受过新式教育，对祥林嫂的悲剧感到不安和负疚。
      age_range: 20-30
      gender: male
      occupation: 知识分子
      relationships: []
      first_appearance: act-1-scene-1

  structure:
    acts:
      - id: act-1
        number: 1
        title: 祝福
        description: 旧历年底，叙述者回到鲁镇，遇见沦为乞丐的祥林嫂，被她关于灵魂的追问所困扰，随后得知她的死讯，并回忆起她前半生的遭遇。
        scenes:
          - id: act-1-scene-1
            number: 1
            heading:
              location: 鲁镇街道及河边
              time_of_day: 下午
              int_ext: 外
            description: 叙述者在镇上遇见祥林嫂，她已沦为乞丐，询问关于灵魂的事。
            setting: 灰白色的晚云下，雪花飞舞。鲁镇河边，石板路湿滑。祥林嫂衣衫褴褛，头发全白，一手提竹篮（内有一破碗），一手拄一支开裂的长竹竿。
            characters_present:
              - wo
              - xiang-lin-sao
            elements:
              - type: action
                text: 祥林嫂瞪着眼睛，直直朝叙述者走来。叙述者站住，准备她来讨钱。
                importance: key

              - type: dialogue
                character_id: xiang-lin-sao
                character_name: 祥林嫂
                parenthetical: 先开口
                line: 你回来了？
                continuation: false

              - type: dialogue
                character_id: wo
                character_name: 我
                line: 是的。
                continuation: false

              - type: dialogue
                character_id: xiang-lin-sao
                character_name: 祥林嫂
                parenthetical: 没有精采的眼睛忽然发光
                line: 这正好。你是识字的，又是出门人，见识得多。我正要问你一件事——
                continuation: false

              - type: action
                text: 祥林嫂走近两步，放低声音，极秘密似的切切地说。叙述者诧异站立。
                importance: key

              - type: dialogue
                character_id: xiang-lin-sao
                character_name: 祥林嫂
                parenthetical: 切切地
                line: 一个人死了之后，究竟有没有魂灵的？
                continuation: false

              - type: dialogue
                character_id: wo
                character_name: 我
                parenthetical: 吞吞吐吐
                line: 也许有罢，——我想。
                continuation: false

              - type: transition
                style: CUT_TO

            transition_out: CUT_TO

          - id: act-1-scene-2
            number: 2
            heading:
              location: 鲁四老爷书房
              time_of_day: 白天
              int_ext: 内
            description: 叙述者回到书房，感到不安，第二天听到四叔骂祥林嫂是谬种，短工告知她死了。
            setting: 书房内，壁上挂着朱拓的大'寿'字，一边对联'事理通达心气和平'，桌上堆着《康熙字典》《近思录集注》《四书衬》。窗外雪下得大。
            characters_present:
              - wo
              - lu-si-lao-ye
              - duan-gong
            elements:
              - type: action
                text: 叙述者无聊赖地翻书，心里不安。他听到内室有人聚谈，不久听见四叔高声说。
                importance: key

              - type: dialogue
                character_id: lu-si-lao-ye
                character_name: 鲁四老爷
                parenthetical: 且走且高声说
                line: 不早不迟，偏偏要在这时候——这就可见是一个谬种！
                continuation: false

              - type: dialogue
                character_id: duan-gong
                character_name: 短工
                parenthetical: 淡然回答，出去
                line: 怎么死的？——还不是穷死的？
                continuation: false

              - type: action
                text: 叙述者逐渐镇定，但心里负疚。晚饭时四叔俨然陪着，叙述者告知明天要离开。四叔也不很留。
                importance: standard

              - type: transition
                style: CUT_TO

            transition_out: CUT_TO

          - id: act-1-scene-8
            number: 8
            heading:
              location: 鲁四老爷家堂屋/厨房
              time_of_day: 白天（祭祀日）
              int_ext: 内
            description: 回忆：祭祀时祥林嫂被禁止碰祭品，只能烧火。后来她捐了门槛，但再次被阻止，精神崩溃。
            setting: 堂屋中央摆好桌子，系桌帏，准备福礼。厨房灶下。
            characters_present:
              - xiang-lin-sao
              - si-shen
              - lu-si-lao-ye
              - a-niu
            elements:
              - type: action
                text: 祥林嫂照旧去分配酒杯和筷子，四婶慌忙说。
                importance: key

              - type: dialogue
                character_id: si-shen
                character_name: 四婶
                parenthetical: 慌忙
                line: 祥林嫂，你放着罢！我来摆。
                continuation: false

              - type: action
                text: 快够一年，祥林嫂从四婶处支取工钱，换了十二元鹰洋，到土地庙捐了门槛。回来时神气舒畅，眼光有神。
                importance: key

              - type: action
                text: 冬至祭祖时，祥林嫂更出力。她看四婶装好祭品，便坦然去拿酒杯和筷子。
                importance: key

              - type: dialogue
                character_id: si-shen
                character_name: 四婶
                parenthetical: 慌忙大声说
                line: 你放着罢，祥林嫂！
                continuation: false

              - type: action
                text: 祥林嫂像受炮烙似的缩手，脸色变作灰黑，失神站着。直到四叔上香叫她走开，她才走开。
                importance: key

              - type: transition
                style: FLASHBACK_END

            transition_out: FLASHBACK_END

          - id: act-1-scene-9
            number: 9
            heading:
              location: 鲁四老爷家内室/书房
              time_of_day: 黎明（五更）
              int_ext: 内
            description: 叙述者被爆竹声惊醒，知道四叔家在祝福。远处爆竹声连绵，雪花飞舞。他感到懒散舒适，疑虑被祝福的空气扫空。
            setting: 书房内，豆一般大的黄色灯火光。外面爆竹声毕毕剥剥。
            characters_present:
              - wo
            elements:
              - type: action
                text: 叙述者被近旁极响的爆竹声惊醒。看见黄色灯火光，听见鞭炮声，知道是四叔家正在祝福，五更将近。
                importance: key

              - type: action
                text: 他蒙眬中隐约听到远处爆竹声联绵不断，合成一天音响的浓云，夹着团团飞舞的雪花，拥抱了全市镇。
                importance: standard

              - type: action
                text: 他觉得天地圣众歆享了牲醴和香烟，都醉醺醺的在空中蹒跚，预备给鲁镇的人们以无限的幸福。
                importance: key

            transition_out: FADE_OUT

  notes: []
```

---

## 8. 扩展机制

该 Schema 支持在不破坏校验的前提下进行扩展：

- **自定义字段**：任何 YAML 解析器都会保留未知字段。下游工具应忽略无法识别的字段。
- **自定义元素类型**：可以在 `elements` 数组中添加新元素类型。`type` 判别字段支持对已知类型安全解析，未知类型可被当作注释处理。
- **类型特定字段**：例如恐怖剧本可以为动作元素添加 `scare_level`；音乐剧可以添加 `song` 元素。
- **制作元数据**：如 `budget_note`（预算备注）、`casting_priority`（选角优先级）或 `vfx_required`（需要视效）等字段可添加到场景中，不影响剧本结构。

---

## 9. Schema 版本管理

本文档描述的是 **Schema v1.0**。版本号记录在每个生成的 YAML 文件的 `metadata.version` 字段中。未来版本将通过以下方式保持向后兼容：

- 不移除已有字段
- 仅添加可选字段
- 不修改字段类型
- 所有破坏性变更均在变更日志中记录
