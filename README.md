# OpenClaw Paper Research Workflow

一个可分享的 OpenClaw 技能项目：用户告诉 AI 要找的论文方向和数量，OpenClaw 自动完成论文搜索、PDF 下载，并写入自己的 Notion 论文库；如果数据库支持文件附件，还会把 PDF 上传到 Notion。

## 功能

- 根据自然语言需求搜索论文
- 自动回退多种检索源
- 下载 PDF 到本地
- 写入 Notion 数据库
- 优先写入 `files` 类型属性；没有文件列时，自动把 PDF 作为页面内的文件块附件上传
- 支持安装到 `~/.openclaw/skills`，适合朋友直接接到自己的 OpenClaw

## 适合的使用方式

1. 你把这个仓库发给朋友
2. 朋友让自己的 OpenClaw 读取这个仓库并运行安装脚本
3. 朋友提供自己的 Notion Integration Token 和 Notion 数据库链接
4. OpenClaw 完成配置后，就能直接用自然语言跑完整流程

## 快速安装

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

## OpenClaw 里怎么用

装好后，直接对 OpenClaw 说：

```text
帮我找 5 篇 2024-2025 年关于 multi-agent reinforcement learning 的论文，下载 PDF，并写入我的 Notion 论文库。
```

或者：

```text
帮我找 3 篇关于 LLM agent 的代表性综述论文，下载 PDF，导入 Notion，并给每篇写一句中文总结。
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

## 发布建议

- 先把仓库推到 GitHub
- 朋友可以直接 clone 后运行安装脚本
- 如果以后你想让安装更傻瓜，可以再发布到 ClawHub

## 安全提示

- 不要把自己的 `NOTION_TOKEN` 提交到 GitHub
- 安装脚本会把 token 写入本机 `~/.openclaw/openclaw.json`
- 分享项目时，只分享仓库，不分享你自己的 `openclaw.json`
