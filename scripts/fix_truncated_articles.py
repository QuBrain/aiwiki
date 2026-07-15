#!/usr/bin/env python3
"""
One-shot fix: regenerate all truncated articles (507 chars, mid-sentence cutoffs)
caused by the missing num_predict in the Ollama native endpoint.

Run: python3 scripts/fix_truncated_articles.py
"""
import sys, os, re, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django-like env before importing app code
os.environ.setdefault("AIWIKI_DATABASE_URL", "sqlite:///./data/aiwiki.db")
os.environ.setdefault("AIWIKI_LLM_PROVIDER", "ollama")

import core.database as db
from agents.historian import Historian
from agents.scientist import Scientist
from agents.md_to_blueprint import markdown_to_blueprint
from wiki.article_blueprint import render_article_blueprint

historian = Historian()
scientist = Scientist()

def is_truncated(content: str) -> bool:
    """Check if article was cut off mid-sentence at ~507 chars."""
    if not content:
        return False
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', content).strip()
    # Truncated articles are ~500-510 chars and don't end with a period
    if 500 <= len(content) <= 515 and not text.rstrip().endswith('.'):
        return True
    return False

def regenerate(topic: str, category: str = "science") -> str:
    """Regenerate a full article using the appropriate writer agent."""
    writer = historian if category == "history" else scientist
    result = writer.act({"topic": topic})
    content = result.get("content", "")
    if not content or len(content.split()) < 300:
        return None
    
    # Convert to blueprint format
    try:
        blueprint = markdown_to_blueprint(content, topic)
        rendered = render_article_blueprint(blueprint)
        if rendered and len(rendered) > 500:
            return rendered
    except Exception:
        pass
    
    # Fallback: wrap in basic HTML
    if not content.startswith("<"):
        content = f"<p>{content}</p>"
    return content

def main():
    articles = db.get_all_articles()
    print(f"Total articles: {len(articles)}")
    
    truncated = []
    for a in articles:
        full = db.get_article(a["slug"])
        if full and is_truncated(full.get("content", "")):
            truncated.append(full)
    
    print(f"Truncated articles: {len(truncated)}")
    
    fixed = 0
    failed = 0
    for article in truncated:
        topic = article["title"]
        print(f"  Regenerating: {topic}...", end=" ", flush=True)
        
        # Determine category from content or title
        content_lower = (article.get("content", "") + topic).lower()
        category = "history" if any(w in content_lower for w in ["history", "century", "kingdom", "empire", "war", "ancient", "medieval"]) else "science"
        
        new_content = regenerate(topic, category)
        if new_content and len(new_content.split()) > 300:
            db.update_article(
                article_id=article["id"],
                content=new_content,
                agent_name="Fixer (truncated article regeneration)",
                summary=f"Regenerated truncated article ({len(article['content'].split())} → {len(new_content.split())} words)",
            )
            print(f"OK ({len(new_content.split())} words)")
            fixed += 1
        else:
            print("FAILED")
            failed += 1
        
        # Rate limit: 2s between LLM calls
        time.sleep(random.uniform(1.5, 3.0))
    
    print(f"\nDone: {fixed} fixed, {failed} failed")

if __name__ == "__main__":
    main()
