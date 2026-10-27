# Contributing improvements

1. Create a branch from `main` in your fork or checkout.
2. Import the workflow you want to change into your own n8n instance. Keep production services and credentials in n8n; use a test sheet and test buckets when possible.
3. Export the updated workflow JSON to the matching file in `workflows/`.
4. Remove `credentials` objects and any token, spreadsheet ID, bucket ID, project ID, folder ID, personal path, or execution data. Restore the `REPLACE_WITH_...` placeholders and blank Google document/tab selectors used in this repository.
5. Run `python3 scripts/check_exports.py` and describe which branch you changed, how you tested it, and any new service/cost in the pull request.

Do not commit `.env`, n8n database backups, execution logs, screenshots containing account data, or credential exports. Keep the workflow's sticky-note setup instructions current when a node or dependency changes.

## Using an improved version

After a pull request is merged, back up the corresponding live n8n workflow. Import the updated JSON as a **new inactive copy**, configure its credentials and destinations, and test the changed branch with one item. Switch over only after the copy passes; keep the previous workflow until the new one is verified.
