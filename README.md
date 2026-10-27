# AI Context Flow n8n workflows

Three importable n8n workflows for discovering search topics, developing content strategies, and producing article drafts. The exports contain **no n8n credentials or account-specific bucket, project, spreadsheet, or folder IDs**. Each teammate supplies their own connections after import.

| Workflow | What it does | Main outputs |
|---|---|---|
| [SEO Discovery](workflows/seo-discovery.json) | Researches a seed topic with OpenSEO, analyzes article opportunities with OpenRouter, and packages social idea prompts. | Content Engine sheet; `ideas for ACF social media` memory bucket. |
| [Content Strategy V1](workflows/content-strategy-v1.json) | Takes ideas from the Content Engine sheet **or** the weekly `ACF Blogs Ideas` memory bucket, researches them, and creates strategies. | Human Approval #1 sheet. |
| [Content Production](workflows/content-production.json) | Reads approved strategies, researches and outlines an article, writes it through a local Claude subscription bridge, and runs editorial QA. | Pending-review article in an AI Context Flow memory bucket when QA passes. |

The workflows are inactive on import. **No workflow here publishes to WordPress.** Content Production's revision branch, Google Docs review path, and HTML formatter have known disconnected handoffs; see [Setup and limits](SETUP.md).

## Get started

1. Import the three JSON files from `workflows/` into your own n8n instance.
2. Follow [SETUP.md](SETUP.md) to configure each external service and replace every `REPLACE_WITH_...` value. The colored notes on each canvas point to the exact nodes.
3. Run one small test through SEO Discovery, then Content Strategy V1, then Content Production after approving a strategy row.

The [Claude bridge](scripts/claude_writer_bridge.py), [launcher](scripts/run_claude_writer_bridge.py), and [writer prompt](prompts/article-writer-system.txt) are included for Content Production. Keep your real `.env` file and all API keys on your own laptop; `.env.example` contains names only.

## Improving the workflows

Make changes in your own n8n copy, export the updated JSON, remove credentials and personal IDs, and open a pull request. Run `python3 scripts/check_exports.py` before committing. See [CONTRIBUTING.md](CONTRIBUTING.md).
