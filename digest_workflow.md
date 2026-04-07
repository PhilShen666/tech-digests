You are generating a tech digest. Follow these steps in order.

## Step 1 — Parse the time range

Parse the time range from the user's request or `$ARGUMENTS` into absolute `since` (YYYY-MM-DD) and `until` (YYYY-MM-DD) dates. Use today's actual system date as the anchor.

Time range vocabulary to handle (not exhaustive):
- "today" → since=today, until=today
- "yesterday" → since=yesterday, until=yesterday
- "last 2 days" / "past 2 days" → since=2 days ago, until=today
- "last week" / "past week" → since=7 days ago, until=today
- "last month" → since=30 days ago, until=today
- "since Monday" → since=most recent Monday, until=today
- "YYYY-MM-DD..YYYY-MM-DD" → explicit range

Default if nothing is given: last 24 hours (since=yesterday, until=today).

## Step 2 — Fetch raw items via WebFetch

Fetch all sources **sequentially** (one WebFetch call at a time — do NOT parallelize). For each, extract items published within [since, until] UTC. Build a list of items with fields: `source`, `title`, `url`, `published`, `summary`, `authors`.

**arXiv — 4 calls**

For each row below, call WebFetch on:
```
https://export.arxiv.org/api/query?search_query=cat:<CATEGORY>+AND+submittedDate:[<SINCE_DT>+TO+<UNTIL_DT>]&sortBy=submittedDate&sortOrder=descending&max_results=20
```
where `<SINCE_DT>` = since date as `YYYYMMDD000000` (no hyphens, 14 digits) and `<UNTIL_DT>` = until date as `YYYYMMDD235959`.

| Source name | CATEGORY |
|-------------|----------|
| arxiv_lg    | cs.LG    |
| arxiv_cl    | cs.CL    |
| arxiv_ir    | cs.IR    |
| arxiv_ai    | cs.AI    |

Parse the Atom XML: each `<entry>` yields title, the `href` link where `type="text/html"`, `<published>`, `<summary>`, and `<author><name>` elements. Deduplicate across categories by URL.

**RSS/Atom blog feeds — 5 calls**

| Source name | URL |
|-------------|-----|
| google_ai   | https://blog.research.google/feeds/posts/default |
| openai      | https://openai.com/news/rss.xml |
| anthropic   | https://www.anthropic.com/news/rss.xml |
| deepmind    | https://deepmind.google/blog/rss.xml |
| huggingface | https://huggingface.co/blog/feed.xml |

Parse each RSS/Atom XML: use `<item>` or `<entry>` elements, extracting title, link, `<pubDate>` or `<published>`, and description/summary. Include only items whose date falls within [since, until].

**On any WebFetch failure**: note the source name and continue. List failures in the Appendix.

## Step 3 — Categorize

Assign every item to exactly one of these buckets, or drop it:

- **model_advancements**: New model architectures, training algorithms, scaling laws, inference optimization, quantization, RLHF/alignment methods, evaluation benchmarks for model capabilities, hardware-software co-design for training. Sources arxiv_lg, arxiv_ai, arxiv_cl are strong signals.
- **ai_applications**: Applied AI products, case studies, deployment stories, AI for science, multimodal applications, AI agents in production, tools and frameworks. Blog posts from labs (Google, Meta, OpenAI, etc.) often land here.
- **recommendation_systems**: Retrieval, ranking, collaborative filtering, embedding-based RecSys, click-through rate prediction, sequential recommendation, multi-task RecSys. Source arxiv_ir is a strong signal.
- **drop**: Off-topic (not AI or RecSys), purely administrative (job postings, policy announcements without technical content), duplicates.

When in doubt between model_advancements and ai_applications, prefer ai_applications for blog-style posts and model_advancements for papers with new algorithmic contributions.

## Step 4 — Score and select

Within each section, score items on:
1. **Relevance** to the section (0–3)
2. **Innovation impact** — how much does it advance the field? (0–3)
3. **Popularity / signal** — high-profile venue, lab, or HN traction (0–2)

Sum the scores and rank descending. Apply **absolute caps** (not per-day):
- model_advancements: top **5**
- ai_applications: top **5**
- recommendation_systems: top **3**

Do not pad with weak items. If a section has fewer strong items than the cap, return fewer.

## Step 5 — Pick spotlights

In each section, the highest-scoring item is the **spotlight** (marked ⭐). There are at most 3 spotlights total (one per section).

## Step 6 — Fetch spotlight pages (figures + affiliations)

For each spotlight item, fetch its source page. This serves two purposes: extracting affiliations and downloading figures.

**arXiv paper:**
1. Use WebFetch to fetch the abstract page `https://arxiv.org/abs/<arxiv-id>`. Parse the plain-text author list that appears on that page — affiliations are sometimes included as footnote text or parenthetical institution names next to author names. Extract whatever is there.
2. Then use WebFetch on `https://arxiv.org/html/<arxiv-id>` (the paper's HTML rendering). Scan for: (a) affiliation text near author names (look for institution/university/department names in the author block), and (b) 1–2 figures that best represent the paper's main claim — prefer architecture diagrams, headline results plots, or ablation charts. Skip decorative headers, logos, pseudocode tables.
3. Download each chosen figure via Bash `curl -sL "<figure-url>" -o assets/<until>/<slug>-fig<n>.<ext>` where `<slug>` is a kebab-case title shortening (max 40 chars).
4. If no affiliations are found on any page, leave the field blank — never fabricate institutions.
5. If the HTML page is unavailable or has no usable figures, skip — do not create broken image links. Note the omission.

**Blog post:**
1. Use WebFetch to fetch the post URL.
2. Pick 1–2 in-body images (not logos, not banners). Download the same way.
3. Authors and affiliations for blog posts are usually the publishing lab (e.g. "Google DeepMind", "Anthropic") — use the source name as the institution if no individual authors are listed.
4. Skip gracefully if nothing usable.

Create `assets/<until>/` via Bash `mkdir -p assets/<until>` before downloading.

## Step 7 — Write the digest

Write the file `digests/<until>.md` using the Write tool.

### File structure

```
# Tech Digest — <since> to <until>

> **Model Advancements:** N items · **AI Applications:** N items · **Recommendation Systems:** N items

---

## Model Advancements

<spotlight item, then remaining items>

---

## AI Applications

<spotlight item, then remaining items>

---

## Recommendation Systems

<spotlight item, then remaining items>

---

## Appendix: Sources

**Fetched:** source1, source2, ...
**Failed:** source3 (ErrorType), ...  ← omit this line if no failures
```

### Standard item format

```markdown
### <Title>

- **Link:** <url>
- **Authors:** <name1>, <name2> — <Institution1>, <Institution2>  (omit if blank)
- **Published:** <YYYY-MM-DD> · **Source:** <source>

**Summary**

<5–8 sentences in your own words. Cover: (1) the problem and why the prior art
was unsatisfying, (2) the core method or contribution, (3) experimental setup
at a high level, (4) headline results with concrete numbers from the source.
Do not copy-paste the abstract. Paraphrase, compress, and add context.>

**Key Innovation**

<2–4 sentences in your own framing. State precisely what is novel vs. prior
work. Explain what it unlocks, simplifies, or invalidates. Be specific and
opinionated — avoid generic phrases like "this is an important step forward"
or "promising direction".>
```

### Spotlight item format (replaces standard, starts with ⭐)

```markdown
### ⭐ <Title>

- **Link:** <url>
- **Authors:** <names> — <institutions>  (omit if blank)
- **Published:** <YYYY-MM-DD> · **Source:** <source>

**Summary**

<Same as standard: 5–8 sentence substantive summary.>

**Key Innovation**

<Same as standard: 2–4 sentences, your own framing, specific and opinionated.>

**Why this is the spotlight**

<1–2 sentences: why this item beats the others in this section.>

**Deeper dive**

<2–4 paragraphs. Go beyond the abstract: describe the key architectural
choices or algorithmic steps, the ablations that reveal what actually matters,
quantitative comparisons to the closest baselines, and any failure modes or
limitations the authors flag. A practitioner should be able to read this
section instead of the paper for a first pass.>

**Critical figures**

![Figure 1 — <short caption>](assets/<until>/<slug>-fig1.<ext>)
*<One sentence you write explaining what to look at in this figure and why it
matters to the paper's claim.>*

![Figure 2 — <short caption>](assets/<until>/<slug>-fig2.<ext>)
*<One sentence caption.>*
```

Omit the **Critical figures** block entirely if no figures were downloaded for this spotlight.

## Step 8 — Commit results and create GitHub issue

1. Use `mcp__github__push_files` to commit in a single commit to `PhilShen666/tech-digests` on branch `main`:
   - `digests/<until>.md`
   - All files under `assets/<until>/` (one entry per file)
   Commit message: `Digest <until>`

2. Use `mcp__github__create_issue` on `PhilShen666/tech-digests` with:
   - title: `Tech Digest <until>`
   - body: the full digest markdown (same content as `digests/<until>.md`),
     but with every local figure path `assets/<until>/<file>` rewritten to
     `https://raw.githubusercontent.com/PhilShen666/tech-digests/main/assets/<until>/<file>`
     so figures render inline in the GitHub issue.

3. Print the issue URL and the commit SHA as your final output.

## Step 9 — Reply to the user

Reply with:
- Confirmation line: "Digest saved to `digests/<until>.md` and published as GitHub issue"
- Issue URL
- Per-section item counts
- Any warnings: sources that failed, spotlights where figures were omitted

Keep the reply short — the user can read the issue or file.
