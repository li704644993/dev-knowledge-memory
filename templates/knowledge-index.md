---
title: 需求开发知识库
type: note
tags: [development, workflow]
status: configured
source_agent: dev-knowledge-memory
publish: false
---

# 需求开发知识库

本目录专门保存开发知识，不保存通用调研笔记或完整聊天记录。

- 知识根目录：`{{KNOWLEDGE_DIR}}`
- Basic Memory 项目：`{{MEMORY_PROJECT}}`
- MCP 服务：`{{MCP_SERVER}}`
- `concepts/`：概念、别名、模型与 ID 含义。
- `topics/`：当前业务机制、读写入口、跨项目链路。
- `changes/`：需求决策、已确认根因与可复用经验。

开发前按需检索，核对相关源码；完成后更新主题并保存有复用价值的决策。没有新增知识时不必生成文档。不能把表名直接当成业务写入方案。

初始没有业务知识。需要首次做针对性的源码调研，或导入使用者指定的已有技术文档；安装本身不会自动学会项目。

只读写此开发目录，不跨入 Research 或其他 Obsidian 目录，除非使用者明确要求。此约定和 MCP 项目范围不是整个 AI 的文件系统隔离。
