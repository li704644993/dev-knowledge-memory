# dev-knowledge-memory

为 Codex 配置一套可检索、可维护的个人开发知识库：**需求开始前先找已有知识，完成后主动总结并沉淀，下一次新会话继续复用。**

正文保存在本地 Markdown；Obsidian 负责阅读与编辑；Basic Memory 提供 MCP 检索和读写；Codex 的固定指引与 Skill 负责执行流程。

它不是另一个编码 Agent，不会让模型永久学会你的代码，也不会自动采集全部聊天。它把开发中确认过的知识保存为下一次可以找到、可以核对的资料。

## 目录

- [适合谁](#适合谁)
- [实际工作方式](#实际工作方式)
- [组成与边界](#组成与边界)
- [快速开始](#快速开始)
- [根配置说明](#根配置说明)
- [知识如何组织](#知识如何组织)
- [什么时候自动沉淀](#什么时候自动沉淀)
- [导入已有技术文档](#导入已有技术文档)
- [确认安装是否有效](#确认安装是否有效)
- [更新与卸载](#更新与卸载)
- [常见问题与排障](#常见问题与排障)
- [兼容性与许可](#兼容性与许可)

## 适合谁

- 经常在同一组仓库里做开发，但每次新会话都要重新解释业务背景。
- 一个需求涉及前端、后端、脚本或多个服务，希望保留跨仓库调用关系。
- 不想每次手工找历史聊天，也不想把所有文档塞进 AGENTS.md。
- 愿意保留原始证据、更新旧主题，不希望 AI 凭一个表名就猜测写入方案。
- 想将需求开发知识与通用调研、个人日记等 Obsidian 内容分开。

如果只是偶尔修改一个小项目，几份仓库 Markdown 可能已经够用。该方案增加了 Basic Memory 环境、MCP 进程、文件索引和本地 embedding 模型的维护成本。

## 实际工作方式

### 第一次处理某个主题

```text
你：修改商品的自定义属性更新逻辑，增加……

Codex：
  检索“商品、自定义属性、更新”等业务词与代码别名
  -> 没有匹配资料，明确说明知识缺口
  -> 对当前源码做针对性调研
  -> 确认业务入口和此次需求后实施
  -> 更新/创建主题笔记，保存必要的决策
  -> 回读保存结果，告诉你实际更新了哪篇笔记
```

### 下一次新开会话

```text
你：给商品属性更新增加……

Codex：
  自动检索已有主题
  -> 读取匹配笔记的正文、状态和源码依据
  -> 只核对这次要改的相关实现
  -> 执行新需求
  -> 回写受到影响的主题
```

不要求你每次再说“先学习项目”或“帮我沉淀”。但是使用者仍需要描述本次需求，并告知只有自己知道的事实，例如“生产已经验证通过”。

### “自动”到底指什么

自动指 **当前 Agent 根据固定规则在任务内进行检索和完成后的知识更新**。不是关闭窗口后继续工作的后台服务，也不是每条消息都生成一篇技术文档。

这是指令驱动的流程，依赖模型遵循指引、客户端正确加载 Skill、MCP 连接成功。不能保证模型永不漏读或误判；因此流程要求呈现引用的资料、保存的路径和真实验证状态，而不是只说“我已经记住了”。

## 组成与边界

```text
本仓库的根配置
  -> 安装脚本
     -> Codex 全局 AGENTS.md 中的一小段适用规则
     -> 用户级 development-memory Skill + settings.json
     -> development_memory MCP 配置
     -> 独立 Basic Memory 状态目录

用户开发需求
  -> Skill 按需调用 Basic Memory
  -> ObsidianVault/Development 中的 Markdown
  -> 核对当前仓库源码
  -> 完成后更新同一份 Markdown
```

### 开发知识与调研知识分开

例如你原来的目录是：

```text
ObsidianVault/
  Research/       通用资料调研，保持原来的流程
  Daily/          日记
  Development/    本方案唯一的开发知识根
```

Basic Memory 的独立配置只注册 `Development`，以 `--project work-development` 启动；不把整个 vault 注册为项目。Codex 配置只暴露必要的检索、读取、编辑工具，不暴露项目创建/切换/删除等管理入口。

Skill 和全局指引要求开发时不读取其他 Obsidian 文件夹，也不跨目录追踪笔记链接，除非用户明确要求。**这不是整个 AI 的文件系统隔离。**Agent 仍有自己的文件工具；源码、配置和必要的仓库文档也仍然可以查阅。本方案不修改网络策略、操作系统文件权限或其他 MCP 的访问权限。

它不会改动你已有的通用调研 Skill。若原有 Skill 的触发范围覆盖业务开发，需参照下文的排障说明把两者分流。

## 快速开始

以下是 macOS/Linux/WSL 的配置方式。脚本用 Python 标准库，不需要安装本仓库的 Python 包。

### 1. 准备环境

需要：

- 可使用本地 MCP 和用户级 Skill 的 Codex 客户端。
- Python 3.12 或更高版本。
- uv，用于单独安装 Basic Memory。
- 一个本地 Obsidian vault，或你想作为笔记目录使用的本地文件夹。

Basic Memory 使用本地 SQLite 向量扩展，**它的 Python 运行时必须支持 SQLite 扩展加载**。检查准备给 Basic Memory 使用的 Python：

```bash
python3.12 -c 'import sqlite3; c = sqlite3.connect(":memory:"); c.enable_load_extension(True); c.close(); print("SQLite extension loading available")'
```

如果失败，不要继续假装语义检索可用。选择已经支持该能力的 Python，例如 Homebrew Python 或 uv-managed CPython，不要求替换你的系统默认 Python。

可以用 uv 准备一个独立运行时：

```bash
uv python install 3.12
uv python find --managed-python 3.12
```

用输出的实际 Python 路径安装 Basic Memory：

```bash
uv tool install 'basic-memory==0.23.2' \
  --prerelease=allow \
  --python /absolute/path/to/python3.12
```

`/absolute/path/to/python3.12` 必须替换为你的实际路径。该版本的依赖链包含预发布包，因此显式允许 prerelease；这不代表所有依赖已完整锁定。Basic Memory 单独安装，本仓库不复制它的源码或依赖。

确认命令位置：

```bash
command -v basic-memory
basic-memory --version
```

后续配置使用命令的绝对路径，避免桌面客户端 PATH 与终端不一致。

### 2. 获取仓库

克隆你收到的仓库地址，或将仓库解压到一个你愿意保留的位置：

```bash
git clone <本仓库实际地址> dev-knowledge-memory
cd dev-knowledge-memory
```

这里没有假设固定 GitHub 地址，维护者发布到公司 Git 或其他平台都可以。

### 3. 创建根配置

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "work_roots": ["~/Projects"],
  "knowledge_dir": "~/Documents/ObsidianVault/Development",
  "codex_home": "~/.codex",
  "skills_dir": "~/.agents/skills",
  "memory_state_dir": "~/.basic-memory-development",
  "basic_memory_command": "~/.local/bin/basic-memory",
  "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "embedding_dimensions": 384,
  "semantic_min_similarity": 0.4
}
```

各目录和命令路径要按你的机器修改。`work_roots` 必须已经存在，知识子目录可以由安装器创建。路径支持绝对路径和 `~`，不支持相对于运行目录的路径或 `$HOME` 字符串替换。

`config.json` 被 Git 忽略，不会进入推广仓库。示例目录不是必须的命名；如果你已有 vault，请选它下面一个专门的开发子目录，不要填写整个 vault 根。

### 4. 先预览，再安装

```bash
python3.12 scripts/install.py --dry-run
python3.12 scripts/install.py --initialize-index
```

可以显式传其他根配置文件：

```bash
python3.12 scripts/install.py --config /absolute/path/to/my-config.json --dry-run
```

预览不会创建目录、写配置、启动 MCP 或构建索引。正式安装会：

1. 创建开发知识目录及 `concepts/`、`topics/`、`changes/`。
2. 在独立状态目录写 Basic Memory 本地项目配置。
3. 将通用 Skill 复制到配置的用户级 skills 目录，并生成实际路径设置。
4. 向 Codex `config.toml` 和全局 `AGENTS.md` 添加带标记的配置区块。
5. 新知识目录没有 README 时创建入口说明；已有笔记和 README 不覆盖。
6. 使用 `--initialize-index` 时调用 Basic Memory 完成首次索引。

本地 embedding 可能需要首次下载模型；初始化网络需求来自依赖与模型获取，不能说首次安装完全离线。使用本地 provider 不会把笔记正文交给 embedding 云服务。Codex 自身仍按其模型连接处理读取到的上下文，不等于全部 AI 处理都在本地。

只想安装配置而暂时不构建索引，可以不加 `--initialize-index`；完成后再带该参数执行同一命令。初始化报错会显示原错误并返回失败，不会静默换成其他 provider 或全库搜索。

### 5. 在 Obsidian 中查看

如果 Development 在已有 vault 内，直接在 Obsidian 文件列表中查看它，无需创建第二个 vault。不要在 vault 里再初始化嵌套 vault。

如果使用的是独立笔记目录，则可以把它作为一个 vault 打开。Obsidian 和 Basic Memory 操作同一份 Markdown，不进行两个版本之间的复制同步。Obsidian 不是运行 MCP 的前提；普通编辑器也能查看文件。

### 6. 重新打开 Codex

重启客户端并新建会话，让全局规则、用户级 Skill 和新 MCP 被加载。独立会话是否真正按流程工作，按[确认安装是否有效](#确认安装是否有效)进行观察。

安装不会导入你的历史聊天，也不会自动知道业务模型。第一次仍需调研或导入已有技术文档。

## 根配置说明

| 字段 | 含义 |
|---|---|
| `work_roots` | 哪些仓库范围使用本流程，可填写多个工作目录或具体仓库；外部 worktree 需要 Agent 核对 Git common directory 归属 |
| `knowledge_dir` | 唯一的开发笔记根，不填整个 vault |
| `codex_home` | 要配置的 Codex home；自定义 CODEX_HOME 的用户要填写对应位置，并确保客户端也使用它 |
| `skills_dir` | 客户端实际扫描的用户级 Skill 目录，示例使用官方用户目录 `~/.agents/skills` |
| `memory_state_dir` | Basic Memory 独立配置、数据库、日志及模型缓存的位置，不属于笔记正文目录 |
| `basic_memory_command` | 已安装 Basic Memory 的绝对命令路径 |
| `embedding_model` | 已被你安装的 FastEmbed 支持的本地模型名，示例为多语言 MiniLM |
| `embedding_dimensions` | 与模型实际输出一致的向量维度 |
| `semantic_min_similarity` | 语义候选阈值；0.4 是小型中文资料库的起点，不是通用准确率保证 |

安装器不猜缺失路径，也不检测后替换使用者的模型。配置字段缺失或不支持会报错。

MCP 服务名固定为 `development_memory`，Basic Memory 项目名固定为 `work-development`，Skill 名为 `development-memory`。这三个名称是流程协议，不按业务主题增加实例或 Skill。

如果机器已有同名 MCP 且指向不同目录，安装会报错；不能静默覆盖其他知识库。已有 Basic Memory 配置与目标不一致时也会报错，需使用者明确审阅差异。首次使用可以选一个全新的独立状态目录。

如修改已有实例的模型、维度或阈值，需要同时审阅根配置、独立 Basic Memory 配置及生成的 Skill 设置；模型/维度变化后还需完整重建向量索引。不要只修改字段、继续使用旧模型生成的向量。

## 知识如何组织

```text
Development/
  README.md
  concepts/
    document-versions.md
  topics/
    property-values.md
    localization.md
  changes/
    YYYY-MM-DD-some-requirement.md
```

### concepts：概念与别名

回答“用户说的是什么”。例如旧/新版本业务术语、对应模型、节点 ID 与文件 ID 的区别。常用叫法、表名和函数名参与搜索，不需要全写进启动指令。

### topics：当前机制

回答“现在怎么运作”。保存读写入口、跨仓库调用链、数据关系、重要约束和已确认的副作用。每个主题维护一个主要文档，后续需求改变机制时更新它。

### changes：需求与决策

回答“那次为什么这么做”。保存可复用的根因、关键取舍和未采用方案，关联主题。不要仅把 diff 翻译为散文，也不要每个需求都重复整篇模型说明。

笔记建议记录：title、aliases、repositories、status、last_checked、source_agent、publish=false、源码符号、实际核对版本和验证范围。具体写法在 Skill 的 [note-format.md](skills/development-memory/references/note-format.md)。

[虚构示例](examples/catalog-property-values.md)仅用于解释文档形态，不含真实公司知识，也不会被安装到笔记目录。

## 什么时候自动沉淀

| 任务情况 | 收尾行为 |
|---|---|
| 改变现有业务机制 | 更新相应主题，保留无关部分 |
| 确认一个隐蔽根因或重要取舍 | 新增需求/排障记录并关联主题 |
| 已确认的代码调研，无代码修改 | 保存可复用机制与证据 |
| 改了一句普通文案 | 通常不生成笔记 |
| 方案还在讨论 | 不覆盖当前机制；需要保存时明确 planned |
| 代码已改，尚未联调 | 标注 implemented-unverified，不声称运行验证通过 |
| 引入一份旧文档 | 标注 imported-partially-verified，并区分原文与当前源码 |
| 窗口关闭/任务被中断 | 不能保证已经执行收尾；恢复后先读取状态 |

最终回复应能核对：

```text
已更新 topics/某主题.md，补充了本次变化及源码依据。
代码尚未联调，笔记已标注实现未验证。
```

“我记住了”不是成功标准。真正的成功是文件落盘、MCP 可以回读，下一次相关任务可以检索到且正确使用它。

## 导入已有技术文档

配置好之后，在当前项目向 Codex 提出：

```text
将我指定的这两份技术文档整理到开发知识库。
保留来源、适用范围、关键表与源码入口。
只做必要的源码核对，区分历史描述与当前事实。
相关主题已存在时更新原主题，不重复创建。
不要修改源文档或导入 Research 的其他内容。
```

使用者负责指定要导入的资料。导入时可以补充相关源码依据，但不得把旧方案、未经复现的故障或推断直接标成当前 verified。

后续开发不要求再次回读原来的外部笔记目录；知识主题里应保留足够的说明与来源指针。需要检查当前行为时查看源码，不用全量重学。

## 确认安装是否有效

以下是使用者验收步骤，不是仓库自带的自动化测试；安装不会替你启动额外 AI 会话。

### 配置被发现

```bash
codex mcp get development_memory
```

自定义 Codex home 时，在这个命令与客户端启动时使用相同 CODEX_HOME。配置应显示正确的 Basic Memory 命令、开发目录、单项目启动参数及环境变量。

在客户端中确认 development-memory Skill 可见。如果不可见，核对实际 Skill 发现目录和客户端配置，再重新启动。

### MCP 能读取笔记

首次没有业务资料时，可先让 Agent 列出 `work-development` 的根目录，应只看到开发目录中的内容。不存在笔记不能伪造检索结果。

导入真实主题之后，让 Agent 用一个业务词搜索，阅读匹配正文；确认状态和 source 指向正确项目。语义得分最高不一定就是正确资料，精确标识符搜索也要保留。

### 新会话无需提醒

在配置范围内的新会话只提出相关需求，不加“去知识库学习”。观察它是否先调用 development_memory、阅读正确主题，再核对源码；最终是否保存了真正有复用价值的变化。

不要为了验收运行会写生产数据的任务。源码只读调查也可以观察检索和沉淀行为。数据库写入、测试或其他额外动作仍受本次用户授权和仓库规则约束。

### 实际验证记录

2026-10-21 在 macOS ARM64 上完成以下实际验证：

- 安装器语法与 Skill 元数据校验。
- 使用临时 Codex home、Skill 目录、知识目录和状态目录执行预览；预览没有创建安装产物。
- 正式安装保留已有模型配置、其他 MCP、Skill 禁用配置和个人指引。
- 同一配置重复安装，没有重复区块或额外写入。
- Codex CLI 能解析生成的 development_memory 配置。
- Basic Memory 0.23.2 能读取生成的独立配置，并完成词法索引和 384 维多语言向量初始化；验证复用了已经下载的模型缓存。

原始个人部署另已验证中文检索、MCP 读写与回读。没有为本仓库新增自动化测试，也没有验证 Windows 原生或所有其他客户端。新会话自动遵循流程依然是模型行为，需要使用者独立验收；不能把一台机器的结果推广为百分之百的保证。

## 更新与卸载

### 更新

安装脚本在两个 Codex 文件中只管理以下标记区块：

```text
# BEGIN dev-knowledge-memory
...本方案的配置/指引...
# END dev-knowledge-memory
```

同一份配置重复执行不会重复添加区块。更新仓库后可以再预览并安装；安装器会刷新它管理的 Skill 文件。直接修改安装后的 Skill 再运行安装会被源版本覆盖，定制应该修改仓库中的 Skill，再检查安装计划。

已有 Basic Memory 独立配置不一致时先报错，不自动改用另一个目录，不自动重建错误维度的数据库。所有配置写入都完成后才执行可选索引；磁盘权限或写入失败会报错，多个文件的写入不是一个全局原子事务，需按输出查看是否存在部分安装。

Basic Memory 自动升级被关闭，维护者升级依赖版本时应重新检查该版本的 CLI 参数、MCP 工具和配置字段。本方案没有自更新任务。

### 卸载

1. 从实际使用的 Codex config.toml 中删除本仓库标记的 MCP 区块。
2. 从全局 AGENTS.md 中删除本仓库标记的指引区块，保留原有规则。
3. 删除本方案安装的 development-memory Skill 目录；不要删除其他 Skill。
4. 重启 Codex，确认连接和 Skill 不再启用。
5. 开发 Markdown 可以继续保留，Obsidian 仍能阅读；Basic Memory 状态与模型缓存是否移除由使用者决定。

卸载并不需要删除知识文件，也不应该清空整个 Codex home、Obsidian vault 或已有 Basic Memory 安装。

## 常见问题与排障

### 每次仍然不查知识库

检查全局 AGENTS.md 是否实际生效、有无 AGENTS.override.md 覆盖、客户端是否使用另一 CODEX_HOME、项目是不是在 work_roots 范围，以及 Skill/MCP 是否已加载。安装器遇到非空的全局 AGENTS.override.md 会停止，避免向不生效的文件写入指引；这种情况需使用者手工把流程合并进实际生效的指引。

### 新会话打开后什么都不发生

正常。空白会话还没有开发任务。“自动”不是没有输入就启动全库学习；收到相关任务后才按需检索。

### 关键词命中，语义检索没有结果

先确认模型/维度与实际索引一致。中文资料要选择适合语言的模型，阈值也可能把正确候选过滤。不要根据一次查询就宣称语义检索无效或随意降低阈值；检查正文、检索词和源事实，模型切换后完整重建向量。

### SQLite 报 enable_load_extension 不存在

这是 Basic Memory 所用 Python 的构建能力问题。用支持 SQLite 扩展的 Python 重新安装该工具，之后重建项目索引。只修改运行安装脚本的 Python 并不会改变已经安装的 Basic Memory 运行时。

### Markdown 被当成普通文件，标题和语义信息异常

核对 Basic Memory 实际运行时和当前版本的 Markdown/MIME 识别。修正运行环境后可执行完整索引重建；不要只看到文件名搜索命中就认为正文已经建立语义索引。

### 安装器报告同名 MCP 或现有配置冲突

不要强制覆盖。先查看同名服务是否属于其他知识库。当前版本只管理固定服务名和一个开发知识项目，多独立实例不是支持范围。早期手工部署需要显式合并，不能凭一个安装命令静默替换。

### 写入提示等待授权、审批失败或 pending

这不是成功保存。处理客户端授权/审批问题后再确认写入；pending 需要等实际 materialization 并回读。安装器不修改客户端的审批策略，也不关闭已有授权机制。

### 开发资料又被写进 Research

检查旧的研究/发布 Skill 是否把“业务代码调研、开发总结”也当成通用研究。将它的描述限定为通用外部调研，把需求开发资料路由到 development-memory。不要同时让两个 Skill 自动沉淀同一项工作。

### 本地知识库等于全部离线吗

不等于。本地 Markdown、SQLite、FastEmbed 推理与缓存是本地的；首次下载依赖/模型仍需网络，Codex 使用的模型端点也独立于此方案。公司资料应按使用者已有的工具/数据政策处理，不因为“存本地”就自动改变那些政策。

### 没有 Obsidian 能用吗

能。核心是本地 Markdown + Basic Memory MCP + Agent 流程，Obsidian 是推荐的人工阅读整理界面，不是硬依赖。

### 其他 AI 客户端能用吗

Basic Memory 支持其他 MCP 客户端，方法也可复用；但本仓库的安装器只生成 Codex 配置。其他客户端要配置自己的 MCP、Skill 发现及持久指引，不能把 Codex 的配置直接当成通用安装已完成。

## 兼容性与许可

- 自动安装目标为本地 Codex；脚本使用 Python 3.12+ 标准库。
- 配置写法面向 macOS/Linux/WSL；Windows 原生的 uv executable 位置、Skill 发现和客户端运行时未专门验收。安装器不会自动安装系统软件或替换默认 Python。
- Basic Memory 集成基线为 0.23.2；MCP 工具字段与客户端能力可能随版本变化。
- 本仓库代码、原创 Skill 和文档采用 [MIT](LICENSE)。Basic Memory 是独立依赖，采用其自己的 AGPL-3.0 许可；本仓库的 MIT 不改变它或其他依赖的许可。
- 本仓库不包含个人工程笔记、真实公司代码或生产配置。推广仓库与使用者的知识库是两个不同的目录，不应一并打包发布。

相关依据：

- [Basic Memory](https://github.com/basicmachines-co/basic-memory)
- [Basic Memory 语义检索说明](https://github.com/basicmachines-co/basic-memory/blob/main/docs/semantic-search.md)
- [Codex MCP 配置](https://developers.openai.com/codex/mcp)
- [Codex Skill 机制](https://developers.openai.com/codex/skills)
- [Codex AGENTS.md 加载规则](https://developers.openai.com/codex/guides/agents-md)
- [Obsidian Markdown 存储说明](https://help.obsidian.md/data-storage)

本项目借鉴“工作完成后保留可复用经验、下一次开发前检索”的工程知识闭环，不需要部署完整自动记忆框架或换一个 Agent。
