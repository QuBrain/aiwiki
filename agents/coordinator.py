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
        self._track(self.name, "starting cycle")
        # First priority: review external agent submissions
        reviewed = self._review_external_submissions()
        if reviewed:
            self._track(self.name, f"reviewed external: {reviewed.get('slug', 'unknown')}")
            return reviewed

        # Second priority: improve existing low-quality articles
        improved = self._improve_low_quality()
        if improved:
            self._track(self.name, f"improved article: {improved.get('slug', 'unknown')}")
            return improved

        # Third priority: pick from pending See also topics
        pending = db.pop_pending_topic()
        if pending:
            topic, category = pending
            existing = db.get_article(db.slugify(topic))
            if existing:
                return self._review_existing(existing)
            return self._create_new(topic, category)

        # Otherwise pick from the static topic list
        topic, category = pick_topic()
        existing = db.get_article(db.slugify(topic))
        if existing:
            return self._review_existing(existing)
        return self._create_new(topic, category)

    def _review_external_submissions(self) -> dict | None:
        """Review articles submitted by external agents that need review."""
        pending = db.get_articles_needing_review()
        if not pending:
            return None
        article = pending[0]
        full = db.get_article(article["slug"])
        if not full:
            return None
        # Run critic and fact-checker
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
                f"Review complete. Some issues were flagged. The article author has been notified."
            )
        else:
            db.add_talk_message(
                full["id"], self.name,
                "Review complete. No significant issues found. Article is published."
            )

        return {"action": "reviewed_external", "article_id": full["id"], "slug": full["slug"]}

    def _improve_low_quality(self) -> dict | None:
        articles = db.get_all_articles()
        if not articles:
            return None

        # First priority: articles with unresolved talk page feedback
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

            # Check if there's unresolved feedback on the talk page
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

        # Pick from unresolved feedback first, then thin articles
        if candidates_with_feedback:
            candidate = candidates_with_feedback[0]
            # Collect talk page feedback to pass to the improver
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
                return result

        if not candidates_thin:
            return None

        candidate = min(candidates_thin, key=lambda a: len(a["content"].split()))
        return self.quality_improver.act({"article": candidate})

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
