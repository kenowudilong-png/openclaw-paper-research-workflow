# OpenClaw Paper Research Workflow

把“找论文、下载 PDF、整理进 Notion”这件事交给 OpenClaw 自动完成。

这是一个可分享的 OpenClaw skill 项目。用户只需要告诉 AI 论文方向、年份范围和数量，OpenClaw 就会自动完成：

- 搜索候选论文
- 下载 PDF
- 写入 Notion 论文库
- 在支持的情况下把 PDF 作为附件上传到 Notion

适合想把论文检索流程标准化、自动化，并分享给别人直接复用的人。

## 它能做什么

- 根据自然语言需求搜索论文
- 自动回退多种检索源，提高搜索成功率
- 下载 PDF 到本地
- 将论文信息写入 Notion 数据库
- 优先写入 `files` 类型属性；没有文件列时，自动把 PDF 作为页面内文件块上传
- 支持安装到 `~/.openclaw/skills`，方便直接接入 OpenClaw

## 适合的使用方式

1. 把这个仓库链接发给 OpenClaw
2. 让 OpenClaw 读取这个仓库并运行安装脚本
3. 用户提供自己的 Notion Integration Token 和 Notion 数据库链接
4. OpenClaw 完成配置后，就能直接用自然语言跑完整流程

## 快速开始

先克隆仓库：

```bash
git clone <your-github-repo-url>
cd <repo-dir>
```

安装 skill 到 OpenClaw：

```bash
python3 scripts/install_openclaw_skill.py --bootstrap
```

配置 Notion：

```bash
python3 scripts/install_openclaw_skill.py \
  --token "ntn_xxx" \
  --database-url "https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

如果你的 OpenClaw 使用默认状态目录，脚本会：

- 复制 skill 到 `~/.openclaw/skills/paper-research-workflow`
- 在 `~/.openclaw/openclaw.json` 下写入 `skills.entries.paper-research-workflow.env`
- 自动开启这个 skill

## 在 OpenClaw 里怎么用

装好后，直接对 OpenClaw 说：

```text
帮我找 5 篇 2024-2025 年关于 multi-agent reinforcement learning 的论文，下载 PDF，并写入我的 Notion 论文库。
```

或者：

```text
帮我找 3 篇关于 LLM agent 的代表性综述论文，下载 PDF，导入 Notion，并给每篇写一句中文总结。
```

也可以这样描述得更具体：

```text
帮我找 8 篇 2023-2025 年关于 RAG evaluation 的高相关论文，优先综述和高引用文章，下载 PDF，写入 Notion，并标注一句中文摘要。
```

## Notion 要求

这套流程至少需要：

- 一个 Notion Integration Token
- 一个你有写权限的 Notion 数据库链接

推荐的数据库字段：

- 标题或 `Name`
- `DOI` 或 URL 列
- `摘要` / `Abstract`
- `AI 总结` / `Summary`
- `标签` / `Tags`
- `PDF` / `附件` / `Attachments`（可选，若存在会优先写入文件列）

如果数据库没有文件列，脚本会把 PDF 作为页面内容里的文件块附件上传。

## 工作流概览

1. OpenClaw 解析用户的论文需求
2. skill 搜索候选论文并返回结构化结果
3. OpenClaw 选择更相关的论文
4. skill 下载 PDF
5. skill 将论文信息和 PDF 写入 Notion
6. OpenClaw 向用户汇报结果

## 仓库结构

```text
.
├── README.md
├── LICENSE
├── scripts/
│   └── install_openclaw_skill.py
└── skills/
    └── paper-research-workflow/
        ├── SKILL.md
        ├── requirements.txt
        ├── .env.example
        └── scripts/
            ├── bootstrap.sh
            ├── doctor.sh
            ├── search.sh
            ├── download.sh
            ├── write_notion.sh
            ├── common.py
            ├── notion_api.py
            ├── search.py
            ├── download.py
            ├── write_notion.py
            └── doctor.py
```

## 适合分享给谁

- 已经在用 OpenClaw 的个人研究者
- 想把论文检索接到 Notion 的 AI 工作流用户
- 想把这套流程做成团队内部标准工具的人

## 后续可以扩展什么

- 支持 arXiv、Semantic Scholar、PubMed 等更多检索源
- 增加论文筛选打分逻辑
- 自动生成中文摘要或阅读建议
- 支持定时检索并自动入库
- 进一步发布到 ClawHub，降低安装门槛

## 安全提示

- 不要把自己的 `NOTION_TOKEN` 提交到 GitHub
- 安装脚本会把 token 写入本机 `~/.openclaw/openclaw.json`
- 分享项目时，只分享仓库，不分享你自己的 `openclaw.json`
