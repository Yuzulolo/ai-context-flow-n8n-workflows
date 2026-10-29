# Set up on your own laptop

These exports are templates. The saved n8n credential references were removed, and all account-specific IDs were replaced or cleared. A successful import alone does not authorize any external service.

## 1. Prepare n8n and services

Use an n8n instance that supports the node types in the JSON. SEO Discovery uses the OpenSEO and AI Context Flow MCP client nodes; Content Strategy V1 uses the Firecrawl and Apify community nodes. Install any missing community nodes your n8n instance prompts for. Keep all three workflows inactive while configuring them.

Create or connect your own accounts for the services used below. Enter tokens in **n8n Credentials**, not in workflow JSON or Git:

| Service | Used by | Configure |
|---|---|---|
| Google Sheets | All three workflows | Google Sheets OAuth credential; choose your spreadsheet and tabs in each Sheets node. |
| OpenSEO | SEO Discovery | Bearer credential for `https://app.openseo.so/mcp`; replace `REPLACE_WITH_YOUR_OPENSEO_PROJECT_ID` in `MCP Client- openseo`. |
| OpenRouter | All three workflows | Header Auth credential for your OpenRouter API key; check selected models and available credits. |
| AI Context Flow / Plurality | All three workflows | Bearer PAT credential for `https://app.plurality.network/mcp`; create/select buckets and replace the bucket ID placeholders below. |
| Firecrawl | Content Strategy V1 | Firecrawl API credential for `Search web`. |
| Apify | Content Strategy V1 | Apify API credential and access to the selected Reddit comment scraper actor. Check its pricing and input schema. |
| Claude subscription | Content Production | Claude CLI signed into your own subscription, plus the local bridge described below. |

Do not paste a PAT into a Code node. The placeholder bucket IDs in Code nodes are **bucket identifiers**, not credentials.

### Reconnect credentials after importing the workflows

The exported JSON contains **no selected credentials**. A credential's display name (for example, `Header Auth account`) is only a label in your own n8n; it does not need to match anyone else's name. Create credentials in **Credentials** or from a node's credential dropdown, then select your new credential in **every node** that uses that service. If you cannot edit an existing credential, create one you own and select it instead.

- **OpenRouter:** In each HTTP Request node whose URL is `https://openrouter.ai/api/v1/chat/completions`, keep **Authentication → Generic Credential Type** and **Generic Auth Type → Header Auth**. Create a Header Auth credential. Set its header **Name** to exactly `Authorization` and **Value** to `Bearer <your own OpenRouter API key>` (including the space). Give the credential any useful display name, such as `OpenRouter - my account`. Save it, select it in every OpenRouter request, and test one node. Some of these requests have generic node names. OpenRouter here is an HTTP API, not an MCP server. The **Send Headers** toggle is for other request headers and does not replace the authentication credential.
- **AI Context Flow:** For `Save ACF Social Ideas to Memory` in SEO Discovery and `Save Article to AI Context Flow` in Content Production, keep the MCP Client endpoint `https://app.plurality.network/mcp` and **Authentication → Bearer Auth**. Create a Bearer Auth credential and enter **your own AI Context Flow PAT as the raw token**, without typing `Bearer ` in the token field. Select it in each MCP Client node. Content Strategy V1's `List ACF Blogs Ideas` and `Read Current Week Memory` are HTTP Request nodes; select that same Bearer Auth credential in both. The PAT belongs in the credential, not a bucket-ID field.

If an OpenRouter node says **Authorization failed** with `No cookie auth credentials found`, check that the node selects your credential and that its saved header name/value are correct. The screenshot is consistent with a request that lacks a usable `Authorization` header; it does not prove exactly which credential setting is wrong. Open **Error details → From HTTP Request** for the response if the new credential still fails. Test a single node before running a full workflow, since model calls can cost money.

## 2. Set up the destinations

Create a spreadsheet with tabs and columns matching the selected n8n node mappings, or select your team's existing spreadsheet and refresh every mapping after import. The workflow notes identify the nodes that use each tab:

- **Content Engine** receives article opportunities from SEO Discovery and supplies sheet ideas to Content Strategy V1.
- **Brand Context** supplies brand guidance to Content Strategy V1.
- **Human Approval #1** receives strategies and supplies approved rows to Content Production. Review the approval filter and select one intended row for the first test.
- **Human Approval #2** belongs to a disconnected Google Docs review path in Content Production.

For every Google Sheets node, select your own document and tab. The export deliberately leaves the document and tab selectors blank. For the optional Google Docs path, also choose your own folder.

Create or select these AI Context Flow buckets and copy their IDs into the named nodes:

| Bucket | Placeholder | Node to edit |
|---|---|---|
| `ideas for ACF social media` | `REPLACE_WITH_YOUR_SOCIAL_IDEAS_BUCKET_ID` | SEO Discovery → `Package Social Idea Watchlist` |
| `ACF Blogs Ideas` | `REPLACE_WITH_YOUR_ACF_BLOG_IDEAS_BUCKET_ID` | Content Strategy V1 → `List ACF Blogs Ideas` **and** `Select Current Week Memory` |
| Article review bucket of your choice | `REPLACE_WITH_YOUR_REVIEW_BUCKET_ID` | Content Production → `Prepare Plurality Review Package` |

If using the memory source in Content Strategy V1, add a note titled for the current Monday–Friday week, such as `26th Oct-30th Oct 2026`. Set `idea_source` in `Choose Idea Source` to `memory`; use `sheet` for Content Engine topics.

## 3. Set up the Claude subscription writer

Content Production's active writing node calls a bridge running on **your** laptop. The bridge requires Python 3, Claude CLI, a signed-in Claude subscription, and the files in `scripts/` and `prompts/`. It rejects API-key authentication.

1. Install Claude CLI from its official source and run `claude login` in your user session.
2. Copy `.env.example` to `.env`. Generate a long random value for `CLAUDE_BRIDGE_TOKEN`. If `claude` is not on the bridge process's `PATH`, set `CLAUDE_BIN` to its absolute path.
3. Run `python3 scripts/run_claude_writer_bridge.py` on your laptop. Keep it running while n8n writes an article. Check `http://127.0.0.1:8765/health` locally.
4. In n8n, give `Claude Subscription - Article Writer` an HTTP Bearer credential whose token equals `CLAUDE_BRIDGE_TOKEN`. If n8n runs in Docker on the same laptop, the node currently calls `http://host.docker.internal:8765/write-article`. Change the host if your n8n deployment reaches the laptop differently.

The bridge uses your subscription allowance. OpenRouter still handles research, outline, QA, and the unfinished revision branch. Do not use a full Content Production run merely to check bridge sign-in: it can select multiple approved rows and incur repeated model calls.

## 4. Test in order

1. **SEO Discovery:** Set a seed topic, confirm OpenSEO returns keyword rows, OpenRouter returns article opportunities, the Content Engine gets rows, and one dated social idea memory appears in your target bucket. The optional Search Demand Watchlist Sheets node remains disconnected.
2. **Content Strategy V1:** Start with `idea_source=sheet` and one approved topic. Confirm research and a new Human Approval #1 row. Then, if wanted, test `idea_source=memory` with a current-week note in your `ACF Blogs Ideas` bucket.
3. **Content Production:** Approve one Human Approval #1 row, verify the bridge health check, then run the workflow. Check the QA decision and pending-review memory. QA `revise` reaches a revision model but has no loop back to QA; `human_review` does not reach the save node.

These workflows can call paid services and write to Sheets and AI Context Flow. Review destination accounts, selected rows, and usage limits before a live run.

## Current limits

- Content Production's Google Docs review chain and branded HTML formatter are disconnected. No WordPress credential, draft creation, or publishing step is included.
- The article memory is a **pending human review** package; QA pass is not human approval.
- The legacy diagnostic and alternative OpenRouter writer nodes in Content Production are disconnected.
- AI Context Flow's bucket IDs differ per account. Connecting a PAT does not automatically choose the intended bucket.
