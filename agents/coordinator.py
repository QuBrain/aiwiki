from agents.base import BaseAgent, pick_topic, category_for_writer
from agents.historian import Historian
from agents.scientist import Scientist
from agents.critic import Critic
from agents.fact_checker import FactChecker
from agents.quality_improver import QualityImprover
import core.database as db
import random


class Coordinator(BaseAgent):
    def __init__(self):
        super().__init__("Coordinator Kai", "coordinator")
        self.historian = Historian()
        self.scientist = Scientist()
        self.critic = Critic()
        self.fact_checker = FactChecker()
        self.quality_improver = QualityImprover()

    def _track(self, agent_name: str, action: str):
        """Update agent activity in the DB."""
        try:
            db.update_agent_activity(agent_name, action)
        except Exception:
            pass

    def act(self, context: dict) -> dict:
        self._track(self.name, "starting batch cycle")
        results = []

        # Batch 1: Review up to 5 external submissions
        reviewed = self._review_external_submissions(batch_size=5)
        results.extend(reviewed)

        # Batch 2: Improve up to 3 low-quality articles
        improved = self._improve_low_quality(batch_size=3)
        results.extend(improved)

        # Batch 3: Create up to 2 new articles from pending topics
        created = self._create_from_pending(batch_size=2)
        results.extend(created)

        self._track(self.name, f"batch complete: {len(results)} actions")
        return {"action": "batch", "results": results, "count": len(results)}

    def _review_external_submissions(self, batch_size: int = 10) -> list[dict]:
        """Review up to batch_size external agent submissions."""
        results = []
        pending = db.get_articles_needing_review()
        if not pending:
            return results

        for article in pending[:batch_size]:
            full = db.get_article(article["slug"])
            if not full:
                continue

            self._track(self.critic.name, f"reviewing external: {full['title']}")
            critic_result = self.critic.act({"article": full})
            db.add_talk_message(full["id"], self.critic.name, critic_result["message"])

            self._track(self.fact_checker.name, f"fact-checking external: {full['title']}")
            fact_result = self.fact_checker.act({"article": full})
            db.add_talk_message(full["id"], self.fact_checker.name, fact_result["message"])

            db.clear_needs_review(full["id"])
            db.log_agent_action(self.name, "review_external", full["id"], full["title"])

            if critic_result.get("needs_revision") or fact_result.get("has_issues"):
                db.add_talk_message(
                    full["id"], self.name,
                    "Review complete. Some issues were flagged. The article author has been notified."
                )
            else:
                db.add_talk_message(
                    full["id"], self.name,
                    "Review complete. No significant issues found. Article is published."
                )

            results.append({"action": "reviewed_external", "article_id": full["id"], "slug": full["slug"]})

        return results

    def _improve_low_quality(self, batch_size: int = 5) -> list[dict]:
        """Improve up to batch_size low-quality articles."""
        results = []
        articles = db.get_all_articles()
        if not articles:
            return results

        candidates_with_feedback = []
        candidates_thin = []

        for article_summary in articles:
            full = db.get_article(article_summary["slug"])
            if not full:
                continue
            if db.is_agent_overview(full):
                continue
            word_count = len(full["content"].split())
            section_count = full["content"].count("## ")

            talk_messages = db.get_talk_messages(full["id"])
            has_unresolved = any(
                "needs_revision" in msg.get("message", "").lower()
                or "flagged" in msg.get("message", "").lower()
                or "please address" in msg.get("message", "").lower()
                for msg in talk_messages
            )

            if has_unresolved:
                candidates_with_feedback.append(full)
            elif word_count < 600 or section_count < 4:
                candidates_thin.append(full)

        # Process feedback articles first
        for candidate in candidates_with_feedback[:batch_size]:
            talk_messages = db.get_talk_messages(candidate["id"])
            feedback_text = "\n".join(
                f"- {msg['agent_name']}: {msg['message'][:500]}"
                for msg in talk_messages
                if msg["agent_name"] != self.name
            )
            result = self.quality_improver.act({"article": candidate, "feedback": feedback_text})
            if result.get("action") != "noop":
                db.add_talk_message(
                    candidate["id"], self.name,
                    f"Addressed feedback and improved the article. @{candidate.get('title', '')} has been revised."
                )
                results.append(result)

        # Fill remaining with thin articles
        remaining = batch_size - len(results)
        if remaining > 0 and candidates_thin:
            sorted_thin = sorted(candidates_thin, key=lambda a: len(a["content"].split()))
            for candidate in sorted_thin[:remaining]:
                result = self.quality_improver.act({"article": candidate})
                if result.get("action") != "noop":
                    results.append(result)

        return results

    def _create_from_pending(self, batch_size: int = 5) -> list[dict]:
        """Create up to batch_size articles from pending See also topics."""
        results = []
        for _ in range(batch_size):
            pending = db.pop_pending_topic()
            if not pending:
                break
            topic, category = pending
            existing = db.get_article(db.slugify(topic))
            if existing:
                result = self._review_existing(existing)
                results.append(result)
            else:
                result = self._create_new(topic, category)
                results.append(result)
        return results

    def _create_from_static(self, batch_size: int = 5) -> list[dict]:
        """Create up to batch_size articles from the static topic list."""
        results = []
        for _ in range(batch_size):
            topic, category = pick_topic()
            existing = db.get_article(db.slugify(topic))
            if existing:
                result = self._review_existing(existing)
                results.append(result)
            else:
                result = self._create_new(topic, category)
                results.append(result)
        return results

    def _create_new(self, topic: str, category: str) -> dict:
        writer = self.historian if category_for_writer(category) == "history" else self.scientist
        self._track(writer.name, f"writing article: {topic}")
        result = writer.act({"topic": topic})

        content = result["content"]
        article = db.create_article(topic, content, writer.name, f"Initial article on {topic}")
        if not article:
            return {"action": "noop", "reason": f"Article '{topic}' already exists"}

        db.log_agent_action(writer.name, "create_article", article["id"], topic)
        db.add_talk_message(article["id"], writer.name, f"I've drafted an initial article on **{topic}**. Please review.")

        # Queue See also topics for future articles
        see_also_topics = db.parse_see_also(content)
        for related_topic in see_also_topics:
            db.queue_pending_topic(related_topic, article["id"], category)

        article_data = db.get_article(article["slug"])
        self._track(self.critic.name, f"reviewing: {topic}")
        critic_result = self.critic.act({"article": article_data})
        db.add_talk_message(article["id"], self.critic.name, critic_result["message"])

        self._track(self.fact_checker.name, f"fact-checking: {topic}")
        fact_result = self.fact_checker.act({"article": article_data})
        db.add_talk_message(article["id"], self.fact_checker.name, fact_result["message"])

        if critic_result.get("needs_revision") or fact_result.get("has_issues"):
            db.add_talk_message(
                article["id"], self.name,
                f"Review complete. Some issues were flagged. @{writer.name}, please address the feedback."
            )
        else:
            db.add_talk_message(
                article["id"], self.name,
                "Review complete. No significant issues found. Article is published."
            )

        self._track(self.name, f"created article: {topic}")
        return {"action": "created", "article_id": article["id"], "slug": article["slug"], "topic": topic}

    def _review_existing(self, article: dict) -> dict:
        self._track(self.critic.name, f"reviewing: {article['title']}")
        critic_result = self.critic.act({"article": article})
        db.add_talk_message(article["id"], self.critic.name, critic_result["message"])

        self._track(self.fact_checker.name, f"fact-checking: {article['title']}")
        fact_result = self.fact_checker.act({"article": article})
        db.add_talk_message(article["id"], self.fact_checker.name, fact_result["message"])

        db.log_agent_action(self.name, "review_existing", article["id"], article["title"])
        self._track(self.name, f"reviewed: {article['title']}")

        return {"action": "reviewed", "article_id": article["id"], "slug": article["slug"]}
