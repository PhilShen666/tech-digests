FEEDS = {
    "google_ai": "https://blog.research.google/feeds/posts/default",
    "meta_ai": "https://ai.meta.com/blog/rss/",
    "openai": "https://openai.com/news/rss.xml",
    "huggingface": "https://huggingface.co/blog/feed.xml",
    "deepmind": "https://deepmind.google/blog/rss.xml",
    "anthropic": "https://www.anthropic.com/news/rss.xml",
    "mistral": "https://mistral.ai/news/feed.xml",
    "cohere": "https://cohere.com/blog/rss.xml",
    "the_gradient": "https://thegradient.pub/rss/",
    "papers_with_code": "https://paperswithcode.com/latest",
    "hackernews": "https://hnrss.org/frontpage?q=AI+machine+learning+recommender",
}

ARXIV_CATEGORIES = {
    "arxiv_ai": "cs.AI",
    "arxiv_lg": "cs.LG",
    "arxiv_cl": "cs.CL",
    "arxiv_ir": "cs.IR",
}

# Absolute caps — not per-day. A week digest and a month digest return the same max.
SECTION_LIMITS = {
    "model_advancements": 5,
    "ai_applications": 5,
    "recommendation_systems": 3,
}
