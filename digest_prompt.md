You are generating a tech digest from a list of AI/ML/RecSys items provided as JSON.
Each item has: source, title, url, published, summary, authors.

Follow these steps:

## Step 1 - Categorize

Assign every item to exactly one bucket, or drop it:

- **model_advancements**: New model architectures, training algorithms, scaling laws, inference
  optimization, quantization, RLHF/alignment methods, evaluation benchmarks, hardware-software
  co-design for training. arxiv_lg, arxiv_ai, arxiv_cl are strong signals.
- **ai_applications**: Applied AI products, case studies, deployment stories, AI for science,
  multimodal applications, AI agents in production, tools and frameworks. Blog posts from labs
  (Google, OpenAI, Anthropic, DeepMind, HuggingFace) often land here.
- **recommendation_systems**: Retrieval, ranking, collaborative filtering, embedding-based RecSys,
  CTR prediction, sequential recommendation, multi-task RecSys. arxiv_ir is a strong signal.
- **drop**: Off-topic (not AI or RecSys), purely administrative, duplicates.

When in doubt between model_advancements and ai_applications, prefer ai_applications for
blog-style posts and model_advancements for papers with new algorithmic contributions.

## Step 2 - Score and select

Score each item:
1. **Relevance** to its section (0-3)
2. **Innovation impact** - how much does it advance the field? (0-3)
3. **Popularity / signal** - high-profile venue, lab, or traction (0-2)

Rank by total score descending. Apply absolute caps:
- model_advancements: top **5**
- ai_applications: top **5**
- recommendation_systems: top **3**

Do not pad with weak items. If a section has fewer strong items than the cap, return fewer.

## Step 3 - Pick spotlights

The highest-scoring item in each section is the **spotlight** (mark with star emoji ⭐). At most 3 spotlights total.

## Step 4 - Write the digest

Write the full digest in the format below. Base summaries and deeper dives on the provided
summary field and your training knowledge - do NOT hallucinate URLs or paper details.
Do NOT include a "Critical figures" section.

**File structure:**

```
# Tech Digest - <since> to <until>

> **Model Advancements:** N items · **AI Applications:** N items · **Recommendation Systems:** N items

---

## Model Advancements

<spotlight item first, then remaining items>

---

## AI Applications

<spotlight item first, then remaining items>

---

## Recommendation Systems

<spotlight item first, then remaining items>

---

## Appendix: Sources

**Fetched:** source1, source2, ...
**Failed:** source3 (reason), ...  (omit this line if no failures)
```

If a section has no qualifying items, write: `*No items in this window.*`

**Standard item format:**

```markdown
### <Title>

- **Link:** <url>
- **Authors:** <name1>, <name2>  (omit line if blank)
- **Published:** <YYYY-MM-DD> · **Source:** <source>

**Summary**

<5-8 sentences. Cover: (1) the problem and why prior art was unsatisfying, (2) the core
method or contribution, (3) experimental setup, (4) headline results with concrete numbers.
Paraphrase - do not copy the abstract.>

**Key Innovation**

<2-4 sentences. Precisely what is novel vs. prior work. What does it unlock, simplify,
or invalidate? Be specific and opinionated - avoid generic filler phrases.>
```

**Spotlight item format (replaces standard, mark title with ⭐):**

```markdown
### ⭐ <Title>

- **Link:** <url>
- **Authors:** <names>  (omit line if blank)
- **Published:** <YYYY-MM-DD> · **Source:** <source>

**Summary**

<5-8 sentence substantive summary.>

**Key Innovation**

<2-4 sentences, your framing, specific and opinionated.>

**Why this is the spotlight**

<1-2 sentences: why this beats the others in its section.>

**Deeper dive**

<2-4 paragraphs: key architectural choices or algorithmic steps, ablations that reveal
what actually matters, quantitative comparisons to closest baselines, failure modes or
limitations. Base this on the provided summary and your training knowledge.>
```

Output ONLY the markdown digest. No preamble, no explanation, no surrounding code fences.
