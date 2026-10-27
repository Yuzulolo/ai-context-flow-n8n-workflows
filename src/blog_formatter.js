/* Deterministic renderer for the user-supplied Plurality post HTML. No network calls. */
function fail(code, detail) { throw new Error(`${code}: ${detail}`); }
function esc(value) { return String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#8217;').replace(/—/g, '&mdash;').replace(/→/g, '&rarr;'); }
function text(value) { return esc(value).replace(/\r/g, ''); }
function url(value, { back = false } = {}) {
  const raw = String(value || '').trim();
  if (back && raw === 'javascript:history.back()') return raw;
  // n8n's isolated Code runtime does not expose the URL constructor.
  if (!/^https?:\/\/[^\s/?#<>"'`]+[^\s<>"'`]*$/i.test(raw)) fail('INVALID_URL', raw || '(empty)');
  return esc(raw);
}
function inline(source) {
  const s = String(source);
  const pattern = /(!?\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let out = '', last = 0, m;
  while ((m = pattern.exec(s))) {
    out += text(s.slice(last, m.index));
    const token = m[0];
    if (token.startsWith('![')) fail('UNSUPPORTED_INLINE_IMAGE', 'Inline figures need an approved figure component.');
    if (token.startsWith('[')) {
      const match = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      out += `<a href="${url(match[2])}" target="_blank" rel="noopener">${text(match[1])}</a>`;
    } else if (token.startsWith('**')) out += `<strong>${text(token.slice(2, -2))}</strong>`;
    else if (token.startsWith('*')) out += `<em>${text(token.slice(1, -1))}</em>`;
    else out += `<code>${text(token.slice(1, -1))}</code>`;
    last = pattern.lastIndex;
  }
  return out + text(s.slice(last));
}
function plainInline(source) {
  return String(source).replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1').replace(/`([^`]+)`/g, '$1');
}
function slug(label, used) {
  const base = label.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 64) || 'section';
  let candidate = base, number = 2;
  while (used.has(candidate)) candidate = `${base}-${number++}`;
  used.add(candidate); return candidate;
}
function listMarker(line) { const m = line.match(/^(\s*)([-*+] |\d+\. )(.*)$/); return m && { indent: m[1].length, kind: /^\d/.test(m[2]) ? 'ol' : 'ul', value: m[3] }; }
function parseList(lines, start, depth) {
  const first = listMarker(lines[start]);
  const tag = first.kind;
  let i = start, html = `<${tag}>\n`;
  while (i < lines.length) {
    const m = listMarker(lines[i]);
    if (!m || m.indent < depth) break;
    if (m.indent > depth) fail('INVALID_LIST_INDENT', lines[i]);
    if (m.kind !== tag) break;
    html += `  <li>${inline(m.value)}`;
    i++;
    const next = i < lines.length && listMarker(lines[i]);
    if (next && next.indent > depth) {
      const nested = parseList(lines, i, next.indent);
      html += `\n${nested.html}`; i = nested.next;
    }
    html += '</li>\n';
  }
  return { html: html + `</${tag}>`, next: i };
}
function renderMarkdown(markdown, expectedTitle) {
  const lines = String(markdown).replace(/\r\n?/g, '\n').split('\n');
  const toc = [], used = new Set(), blocks = [], warnings = [];
  let i = 0, sawBody = false;
  while (i < lines.length) {
    const line = lines[i], trimmed = line.trim();
    if (!trimmed) { i++; continue; }
    if (/^# /.test(line)) {
      if (sawBody || line.slice(2).trim() !== expectedTitle) fail('UNEXPECTED_H1', line);
      i++; continue;
    }
    sawBody = true;
    if (/^```/.test(trimmed)) {
      const code = []; i++;
      while (i < lines.length && !/^```/.test(lines[i].trim())) code.push(lines[i++]);
      if (i >= lines.length) fail('UNCLOSED_CODE_FENCE', 'Missing closing ```');
      i++; warnings.push('Code fence rendered inside existing callout styling.');
      blocks.push(`<div class="pn-callout"><pre><code>${text(code.join('\n'))}</code></pre></div>`); continue;
    }
    if (/^## /.test(line)) {
      const label = line.slice(3).trim();
      if (/^(faqs?|frequently asked questions)$/i.test(label)) fail('FAQ_IN_MARKDOWN', 'Supply approved FAQ pairs in content_assets.faq instead.');
      const id = slug(label, used); toc.push({ id, label }); blocks.push(`<h2 id="${id}">${inline(label)}</h2>`); i++; continue;
    }
    if (/^### /.test(line)) { blocks.push(`<h3>${inline(line.slice(4).trim())}</h3>`); i++; continue; }
    if (/^#{4,6} /.test(line)) fail('UNSUPPORTED_HEADING_LEVEL', line);
    if (/^!\[[^\]]*\]\([^)]+\)/.test(trimmed)) fail('UNSUPPORTED_INLINE_IMAGE', 'Need approved figure markup before rendering inline images.');
    if (/^\|/.test(trimmed) && i + 1 < lines.length && /^\|?\s*:?-{3,}/.test(lines[i + 1].trim())) {
      const cols = row => row.trim().replace(/^\||\|$/g, '').split('|').map(x => x.trim());
      const heads = cols(line); i += 2; const rows = [];
      while (i < lines.length && /^\|/.test(lines[i].trim())) { rows.push(cols(lines[i])); i++; }
      if (rows.some(r => r.length !== heads.length)) fail('INVALID_TABLE', 'Uneven table columns');
      blocks.push(`<div class="pn-table-wrap"><table><thead><tr>${heads.map(h => `<th>${inline(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${inline(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`); continue;
    }
    const lm = listMarker(line);
    if (lm) { const result = parseList(lines, i, lm.indent); blocks.push(result.html); i = result.next; continue; }
    if (/^> /.test(line)) {
      const parts = [];
      while (i < lines.length && /^> /.test(lines[i])) parts.push(lines[i++].slice(2));
      blocks.push(`<div class="pn-callout"><p>${inline(parts.join(' '))}</p></div>`); continue;
    }
    if (/^---+$/.test(trimmed)) { i++; continue; }
    const parts = [];
    while (i < lines.length && lines[i].trim() && !/^(#{1,6} |```|> |!\[|\|)/.test(lines[i]) && !listMarker(lines[i])) parts.push(lines[i++].trim());
    if (!parts.length) fail('UNSUPPORTED_MARKDOWN', line);
    blocks.push(`<p>${inline(parts.join(' '))}</p>`);
  }
  if (!toc.length) fail('MISSING_H2', 'Article needs at least one H2 section.');
  return { html: blocks.join('\n\n'), toc, warnings };
}
function fixedBlocks(html) { return [...html.matchAll(/<style>[\s\S]*?<\/style>|<script>[\s\S]*?<\/script>/g)].map(m => m[0]); }
function replace(template, name, value) {
  const token = `{{${name}}}`;
  if (!template.includes(token)) fail('MISSING_TEMPLATE_TOKEN', name);
  return template.split(token).join(value);
}
function buildPost(input, template) {
  const article = input.article_draft || {};
  const approval = input.approval || {};
  const assets = input.content_assets || {};
  if (approval.status !== 'approved' || !approval.reviewer || !approval.approved_at) fail('NOT_APPROVED', 'Explicit reviewer, approval date, and approved status are required.');
  if (!article.title || !article.article_markdown) fail('MISSING_ARTICLE', 'Title and Markdown are required.');
  if (approval.approved_article_markdown !== article.article_markdown || approval.approved_title !== article.title) fail('APPROVED_VERSION_MISMATCH', 'Approved title and Markdown must match the input exactly.');
  if (!assets.post_date || !assets.featured_img_url || !assets.featured_img_alt) fail('MISSING_ASSETS', 'Date, approved hero URL, and alt text are required.');
  const rendered = renderMarkdown(article.article_markdown, article.title);
  const faq = assets.faq || [];
  if (!Array.isArray(faq)) fail('INVALID_FAQ', 'FAQ must be an array.');
  const toc = [...rendered.toc];
  let faqHtml = '', faqSchema = '';
  if (faq.length) {
    if (toc.some(x => x.id === 'faqs')) fail('DUPLICATE_FAQ', 'Article already has an FAQ section.');
    toc.push({ id: 'faqs', label: 'Frequently Asked Questions' });
    faqHtml = `<h2 id="faqs">Frequently Asked Questions</h2>\n<div class="pn-faq">\n${faq.map((item, i) => {
      if (!item.question || !item.answer) fail('INVALID_FAQ', `FAQ item ${i + 1} is incomplete`);
      return `  <details class="pn-faq-item"${i === 0 ? ' open' : ''}><summary>${text(item.question)}</summary><div class="pn-faq-answer"><p>${inline(item.answer)}</p></div></details>`;
    }).join('\n')}\n</div>`;
    faqSchema = faq.map(item => JSON.stringify({ '@type': 'Question', name: item.question, acceptedAnswer: { '@type': 'Answer', text: plainInline(item.answer) } })).join(',\n    ');
  }
  let out = template;
  const values = {
    POST_TITLE: text(article.title), POST_DATE: text(assets.post_date), FEATURED_IMG_URL: url(assets.featured_img_url), FEATURED_IMG_ALT: text(assets.featured_img_alt),
    BACK_LINK_HREF: url(assets.back_link_href || 'javascript:history.back()', { back: true }),
    TOC: toc.map(x => `<li><a href="#${x.id}">${inline(x.label)}</a></li>`).join('\n          '),
    CONTENT: rendered.html, FAQ_HTML: faqHtml, FAQ_SCHEMA: faqSchema,
  };
  for (const [name, value] of Object.entries(values)) out = replace(out, name, value);
  if (!faq.length) out = out.replace(/<script type="application\/ld\+json">[\s\S]*?<\/script>\s*/, '');
  if (/{{[A-Z_]+}}/.test(out)) fail('LEFTOVER_TEMPLATE_TOKEN', 'Output still contains placeholders.');
  if (JSON.stringify(fixedBlocks(out)) !== JSON.stringify(fixedBlocks(template))) fail('FIXED_BLOCK_CHANGED', 'CSS or behavior script changed.');
  const hrefs = [...out.matchAll(/<li><a href="#([a-z0-9-]+)">/g)].map(m => m[1]);
  const ids = [...out.matchAll(/<h2 id="([a-z0-9-]+)">/g)].map(m => m[1]);
  if (JSON.stringify(hrefs) !== JSON.stringify(ids) || new Set(ids).size !== ids.length) fail('TOC_MISMATCH', 'TOC links and H2 IDs differ.');
  const imageTags = [...out.matchAll(/<img\b[^>]*>/g)].map(m => m[0]);
  for (const tag of imageTags) if (!/src="https?:\/\/[^\"]+"/.test(tag) || !/alt="[^\"]+"/.test(tag)) fail('INVALID_IMAGE', tag);
  return { wordpress_html: out, title: article.title, meta_description: article.meta_description || '', template_version: input.template_version || '', build_manifest: { toc_ids: ids, image_count: imageTags.length, faq_count: faq.length }, validation: { valid: true, warnings: rendered.warnings } };
}
if (typeof module !== 'undefined') module.exports = { buildPost, renderMarkdown };
