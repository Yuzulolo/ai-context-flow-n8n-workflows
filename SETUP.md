# Set up on your own laptop

These exports are templates. The saved n8n credential references were removed, and all account-specific IDs were replaced or cleared. A successful import alone does not authorize any external service.

## 1. Import and prepare n8n

Import the three files in `workflows/` into your own n8n instance. Keep them inactive while configuring them. SEO Discovery uses MCP Client nodes for OpenSEO and AI Context Flow. Content Strategy V1 uses the Firecrawl (`@mendable/n8n-nodes-firecrawl`) and Apify (`@apify/n8n-nodes-apify`) community nodes. If n8n reports a missing node, install its package under **Settings → Community Nodes** on a self-hosted instance, then reopen the workflow. Installing community nodes requires an n8n Owner or Admin account. See [n8n's installation guide](https://docs.n8n.io/integrations/community-nodes/installation-and-management/gui-installation/).

Create or connect your own accounts for the services used below. Enter tokens in **n8n Credentials**, not in workflow JSON or Git. Every teammate needs their own account access and destination IDs; a shared workflow export does not grant access to the original owner's services.

| Service | Used by | Configure |
|---|---|---|
| Google Sheets | All three | [Google Cloud OAuth client](#2-connect-google-sheets-on-self-hosted-n8n), Gmail sign-in, and your own spreadsheet/tabs. |
| OpenSEO | SEO Discovery | [OpenSEO API key](#openseo), OpenSEO project ID, and Bearer credential. |
| OpenRouter | All three | [OpenRouter API key](#openrouter) and Header Auth credential. |
| AI Context Flow | All three | [AI Context Flow PAT](#ai-context-flow) and Bearer credential; your own memory bucket IDs. |
| Firecrawl | Content Strategy V1 | [Firecrawl API key](#firecrawl-and-apify) for `Search web`. |
| Apify | Content Strategy V1 | [Apify API token](#firecrawl-and-apify) for the Reddit actor. |
| Claude subscription | Content Production | [Claude Code login and local bridge](#5-set-up-the-claude-subscription-writer). |
| Google Docs | Disconnected review path only | [Separate Google Docs credential](#optional-google-docs-review-path); not needed for the active path. |

Do not paste a PAT into a Code node. The placeholder bucket IDs in Code nodes are **bucket identifiers**, not credentials.

## 2. Connect Google Sheets on self-hosted n8n

A Client ID and Client Secret prompt is expected. **One-click Google sign-in is available for Google Sheets on n8n Cloud, but not on self-hosted n8n.** On your own laptop, first create a Google Cloud OAuth app; the ID and secret identify that app. You then sign in with your Gmail account to grant access. They are not your Gmail password. [n8n's Google credential guide](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service.md)

1. In n8n, open a Google Sheets node and choose **Create New** under its credential dropdown. Leave the credential panel open so you can copy its **OAuth Redirect URL**. Its display name can be anything, such as `Google Sheets - my account`.
2. In [Google Cloud Console](https://console.cloud.google.com/projectcreate), create or select a project. This Google Cloud project is separate from your OpenSEO project.
3. In the [API Library](https://console.cloud.google.com/apis/library), enable **Google Sheets API** and **Google Drive API** for that project. n8n needs both for Google Sheets.
4. Configure the project's **OAuth consent screen**. For a personal Gmail account, choose **External**; if the app is in **Testing**, add the Gmail account you will sign in with under **Audience → Test users**. **Internal** is for accounts in your Google Workspace organization.
5. Open [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials), select **Create credentials → OAuth client ID**, and choose **Web application**. Under **Authorized redirect URIs**, paste the **exact OAuth Redirect URL displayed by n8n**. A local instance may show `http://localhost:5678/rest/oauth2-credential/callback`; copy the actual URL, including protocol and port. Localhost needs no public domain or port forwarding for this step.
6. Google now shows the **Client ID** and **Client Secret**. Copy both into the n8n Google Sheets credential, click **Sign in with Google**, authorize the requested access, and save the credential.
7. Select that saved credential in **every Google Sheets node** in the three workflows. For each node, select your own spreadsheet and tab and refresh its column mappings after selection. The imported exports have blank document and tab selectors.

If you use **n8n Cloud** and the credential offers **Managed OAuth2**, choose **Sign in with Google** there; the Google Cloud client setup above is for self-hosted instances. [n8n lists the supported managed Google nodes](https://docs.n8n.io/integrations/builtin/credentials/google.md#managed-oauth2-for-n8n-cloud-users).

| Google sign-in error | Check |
|---|---|
| `redirect_uri_mismatch` | Copy the redirect URL from the n8n credential into the Google OAuth client exactly, including `http`/`https` and port. |
| Access denied / app not verified | Add the signing-in Gmail address as a test user on the OAuth consent screen. |
| `invalid_client` | Recopy the Client ID and Client Secret from the same Google OAuth client. |
| Connection stops working after about seven days | Google expires authorization for External apps in Testing mode; reconnect the n8n credential. |

These cases are covered in [n8n's Google OAuth troubleshooting](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service.md#troubleshooting).

## 3. Connect the other services

The exported JSON contains **no selected credentials**. A credential's display name (for example, `Header Auth account`) is only a label in your own n8n; it does not need to match anyone else's name. Create credentials in **Credentials** or from a node's credential dropdown, then select your new credential in **every node** that uses that service. If you cannot edit an existing credential, create one you own and select it instead.

### OpenSEO

1. Create or select your OpenSEO project. In [OpenSEO Settings → API keys](https://www.openseo.so/docs/mcp#connect-with-an-api-key), create a personal API key while the intended workspace is active. Copy it when shown.
2. In SEO Discovery's `MCP Client- openseo`, keep `https://app.openseo.so/mcp` and **Authentication → Bearer Auth**. Create a Bearer Auth credential and enter the raw OpenSEO API key. Save and select it. The node calls `research_keywords`.
3. Replace `REPLACE_WITH_YOUR_OPENSEO_PROJECT_ID` in that node with **your project's ID**. This ID identifies the research project; it is not the API token. If you cannot find it, OpenSEO's MCP can list your projects and return their IDs. [OpenSEO MCP setup](https://www.openseo.so/docs/mcp#troubleshooting)

### OpenRouter

1. Create your own API key in the [OpenRouter dashboard](https://openrouter.ai/developers). The workflow uses OpenRouter's HTTP chat API, not an MCP connection. Check the selected models and your account's available credit before a large run.
2. In each HTTP Request node whose URL is `https://openrouter.ai/api/v1/chat/completions`, keep **Authentication → Generic Credential Type** and **Generic Auth Type → Header Auth**. Create a Header Auth credential. Its header **Name** must be exactly `Authorization`; its **Value** must be `Bearer <your OpenRouter API key>` (including the space). The credential's display name can be anything, such as `OpenRouter - my account`.
3. Save and select it in every OpenRouter request. Content Strategy V1 also has two such nodes named `HTTP Request` and `HTTP Request1`, so find them by URL. The **Send Headers** toggle is for other request headers and does not replace the credential. [OpenRouter's API example](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion)

### AI Context Flow

1. Obtain a **personal access token (PAT) from your own AI Context Flow account**. The endpoint is `https://app.plurality.network/mcp`. For this headless n8n workflow, use a PAT as Bearer authentication. [AI Context Flow MCP overview](https://plurality.network/ai-context-flow/)
2. In SEO Discovery's `Save ACF Social Ideas to Memory` and Content Production's `Save Article to AI Context Flow` MCP Client nodes, keep **Authentication → Bearer Auth**. Create a Bearer Auth credential with the **raw PAT** in its token field, without typing `Bearer `; n8n adds that prefix. Save and select it in both nodes.
3. In Content Strategy V1, also select that Bearer credential in the HTTP Request nodes `List ACF Blogs Ideas` and `Read Current Week Memory`. Their requests use the same ACF MCP endpoint. Replace the separate bucket-ID placeholders in [section 4](#4-set-up-the-destinations).

The **Settings → MCP** page in n8n configures access *to n8n*. It does not connect these outbound ACF nodes. A PAT authenticates an account; a bucket ID chooses where its memories are read or saved. [n8n's MCP Client authentication](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp.md#credentials)

### Firecrawl and Apify

- **Firecrawl:** Create an API key under [Firecrawl Dashboard → API Keys](https://docs.firecrawl.dev/integrations/n8n). In Content Strategy V1's `Search web`, create/select a Firecrawl credential and paste the key into its API Key field. Install the Firecrawl community node if n8n says it is missing.
- **Apify:** Get an API token from [Apify Console → API & Integrations](https://docs.apify.com/integrations/api). In Content Strategy V1's `Run an Actor and get dataset`, create/select an Apify API credential. The export selects a Reddit Comment Scraper actor; confirm that actor is available to your account and review its current pricing and input before running it. [Apify's n8n guide](https://docs.apify.com/integrations/n8n)

If an OpenRouter node says **Authorization failed** with `No cookie auth credentials found`, check that the node selects your credential and that its saved header name/value are correct. The screenshot is consistent with a request that lacks a usable `Authorization` header; it does not prove exactly which credential setting is wrong. Open **Error details → From HTTP Request** for the response if the new credential still fails. Test a single node before running a full workflow, since model calls can cost money.

## 4. Set up the destinations

Create a spreadsheet with these tabs and first-row headers, or use a team spreadsheet that already has them. The header spelling and capitalization matter to n8n's column mappings. After selecting a tab in each node, refresh the mapping and verify its fields.

| Tab | Used by | First-row headers / content |
|---|---|---|
| **Content Engine** | SEO Discovery writes; Content Strategy V1 reads | `Topic`, `Primary Keyword`, `Search Volume`, `KD`, `Intent`, `Content objective`, `Product relevance`, `Strategic Pillar`, `Angle`, `POV`, `Status`, `Generate`, `Draft URL`, `Publish URL` |
| **Brand Context** | Content Strategy V1 reads | Add at least one row of your own brand, audience, product, and voice guidance. This read node has no fixed column mapping; inspect the resulting row before the first run. |
| **Human Approval #1** | Content Strategy V1 writes; Content Production reads | `Topic`, `Primary Keyword`, `Search Volume`, `KD`, `Intent`, `Content objective`, `Product relevance`, `Angle`, `source_row`, `article_audience`, `content_gap`, `core_argument`, `unique_pov`, `recommend_title`, `approval` |

Both strategy branches write to **Human Approval #1** with `approval` initially false. After reviewing one row, set its `approval` cell to `true`; Content Production's `Get row(s) in sheet` filters that column for `true`. For a first test, make sure only the intended row matches. Both strategy write nodes use an update matching column (`Primary Keyword` for sheet topics; `source_row` for memory topics); keep those headers present.

Give the Google account used in n8n access to edit the output tabs. Point SEO Discovery's `Append row in sheet` to **Content Engine**; Content Strategy V1's two read nodes to **Content Engine** and **Brand Context**, and its two approval write nodes to **Human Approval #1**; Content Production's `Get row(s) in sheet` to **Human Approval #1**. The optional raw keyword watchlist and Google Docs review path are disconnected.

Create or select these AI Context Flow buckets and copy their IDs into the named nodes:

| Bucket | Placeholder | Node to edit |
|---|---|---|
| `ideas for ACF social media` | `REPLACE_WITH_YOUR_SOCIAL_IDEAS_BUCKET_ID` | SEO Discovery → `Package Social Idea Watchlist` |
| `ACF Blogs Ideas` | `REPLACE_WITH_YOUR_ACF_BLOG_IDEAS_BUCKET_ID` | Content Strategy V1 → `List ACF Blogs Ideas` **and** `Select Current Week Memory` |
| Article review bucket of your choice | `REPLACE_WITH_YOUR_REVIEW_BUCKET_ID` | Content Production → `Prepare Plurality Review Package` |

If using the memory source in Content Strategy V1, add a note titled for the current Monday–Friday week, such as `26th Oct-30th Oct 2026`. Set `idea_source` in `Choose Idea Source` to `memory`; use `sheet` for Content Engine topics.

SEO Discovery's disconnected `Append or update row in sheet` node is an optional **Search Demand Watchlist**. It is not needed for the main flow. If you connect it, create a tab and refresh its mappings; several legacy header names contain leading or trailing spaces, so inspect the node's schema before creating the header row.

### Optional Google Docs review path

Content Production's `Create Article Review Doc`, `Insert Article Content`, and `Submit for Human Approval #2` nodes are disconnected. You do **not** need Google Docs to run the active article path. To develop that optional path, enable the **Google Docs API** and **Google Drive API** in the Google Cloud project, create a **Google Docs OAuth2** credential with the same Google OAuth setup above, select your Docs folder in the create node, and point the Sheets node to a **Human Approval #2** tab with headers `primary_keyword`, `article_title`, `Google_doc`, `qa_decision`, `qa_issues`, `approval`, `human_feedback`. Connecting these nodes also requires designing and testing their handoff. [n8n Google OAuth guide](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service.md)

## 5. Set up the Claude subscription writer

Content Production's active writing node calls a bridge running on **your** laptop. The bridge requires Python 3, Claude CLI, a signed-in Claude subscription, and the files in `scripts/` and `prompts/`. It rejects API-key authentication.

1. [Install Claude Code](https://code.claude.com/docs/en/setup), then run `claude auth login` and choose your **claude.ai subscription**. Check `claude auth status` on the same laptop and user account that will run the bridge. [Claude authentication guide](https://code.claude.com/docs/en/authentication)
2. Copy `.env.example` to `.env`. Generate a long random value for `CLAUDE_BRIDGE_TOKEN` (for example, `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`) and put it in `.env`. If `claude` is not on the bridge process's `PATH`, set `CLAUDE_BIN` to its absolute path.
3. If n8n runs in **Docker Desktop** on the same laptop, the exported node calls `http://host.docker.internal:8765/write-article`. Set `CLAUDE_BRIDGE_HOST=0.0.0.0` in `.env` so the container can reach the host service; `127.0.0.1` accepts only host-local connections. Keep the bearer token private and limit access to port 8765 with your host firewall. For n8n running directly on the host, keep `CLAUDE_BRIDGE_HOST=127.0.0.1` and change the node URL to `http://127.0.0.1:8765/write-article`. [Docker host connection guide](https://docs.docker.com/desktop/features/networking/networking-how-tos/#connect-a-container-to-a-service-on-the-host)
4. Run `python3 scripts/run_claude_writer_bridge.py` on your laptop and keep it running while n8n writes an article. Check `http://127.0.0.1:8765/health` locally. From Docker, also verify the container can reach `http://host.docker.internal:8765/health` before a full article run.
5. In n8n, give `Claude Subscription - Article Writer` its **own HTTP Bearer** credential whose raw token equals `CLAUDE_BRIDGE_TOKEN`. Do not select the AI Context Flow Bearer credential for this node.

The bridge uses your subscription allowance. OpenRouter still handles research, outline, QA, and the unfinished revision branch. Do not use a full Content Production run merely to check bridge sign-in: it can select multiple approved rows and incur repeated model calls.

## 6. Test in order

1. **SEO Discovery:** Set a seed topic, confirm OpenSEO returns keyword rows, OpenRouter returns article opportunities, the Content Engine gets rows, and one dated social idea memory appears in your target bucket. The optional Search Demand Watchlist Sheets node remains disconnected.
2. **Content Strategy V1:** Start with `idea_source=sheet` and one topic in Content Engine. Confirm research and a new Human Approval #1 row. Then, if wanted, test `idea_source=memory` with a current-week note in your `ACF Blogs Ideas` bucket.
3. **Content Production:** Approve one Human Approval #1 row, verify the bridge health check, then run the workflow. Check the QA decision and pending-review memory. QA `revise` reaches a revision model but has no loop back to QA; `human_review` does not reach the save node.

These workflows can call paid services and write to Sheets and AI Context Flow. Review destination accounts, selected rows, and usage limits before a live run.

## Current limits

- Content Production's Google Docs review chain and branded HTML formatter are disconnected. No WordPress credential, draft creation, or publishing step is included.
- The article memory is a **pending human review** package; QA pass is not human approval.
- The legacy diagnostic and alternative OpenRouter writer nodes in Content Production are disconnected.
- AI Context Flow's bucket IDs differ per account. Connecting a PAT does not automatically choose the intended bucket.
