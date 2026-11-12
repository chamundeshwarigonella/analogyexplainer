import json
import tempfile
import unittest
from pathlib import Path

from explainer.topics import (
    LEVELS,
    TopicError,
    find_topic,
    level_for_age,
    load_topics,
    normalise,
)


def write_topics(data) -> Path:
    """Write data to a temporary topics file and return its path."""
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle:
        if isinstance(data, str):
            handle.write(data)
        else:
            json.dump(data, handle)
    return Path(handle.name)


def minimal_topic(title="Test topic", aliases=()):
    lesson = {
        "analogy": "An analogy.",
        "steps": ["One"],
        "quiz": [{"question": "Q?", "choices": ["a", "b"], "answer": 0, "remember": "R."}],
    }
    return {"title": title, "aliases": list(aliases), "levels": {lvl: lesson for lvl in LEVELS}}


class BundledTopicsTest(unittest.TestCase):
    def test_every_topic_has_all_levels_and_a_three_question_quiz(self):
        topics = load_topics()
        self.assertEqual(len(topics), 5)
        for topic in topics.values():
            for level in LEVELS:
                lesson = topic.lessons[level]
                self.assertTrue(lesson.analogy)
                self.assertTrue(lesson.steps)
                self.assertEqual(len(lesson.quiz), 3, f"{topic.key}/{level}")


class LevelForAgeTest(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(level_for_age(6), "young")
        self.assertEqual(level_for_age(8), "young")
        self.assertEqual(level_for_age(9), "middle")
        self.assertEqual(level_for_age(12), "middle")
        self.assertEqual(level_for_age(13), "teen")
        self.assertEqual(level_for_age(40), "teen")

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            level_for_age(5)
        with self.assertRaises(ValueError):
            level_for_age(121)


class FindTopicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.topics = load_topics()

    def test_exact_key(self):
        match = find_topic("gravity", self.topics)
        self.assertEqual(match.topic.key, "gravity")
        self.assertFalse(match.corrected)

    def test_case_spacing_and_dashes_are_ignored(self):
        self.assertEqual(normalise("  Water_Cycle "), "water cycle")
        self.assertEqual(find_topic("WATER   cycle", self.topics).topic.key, "water-cycle")

    def test_alias(self):
        self.assertEqual(find_topic("circuits", self.topics).topic.key, "electricity")

    def test_typo_is_corrected(self):
        match = find_topic("photosynthesys", self.topics)
        self.assertEqual(match.topic.key, "photosynthesis")
        self.assertTrue(match.corrected)

    def test_partial_name_gives_suggestions_not_a_guess(self):
        match = find_topic("water", self.topics)
        self.assertIsNone(match.topic)
        self.assertIn("The water cycle", match.suggestions)

    def test_unknown_topic(self):
        match = find_topic("volcanoes", self.topics)
        self.assertIsNone(match.topic)

    def test_blank_query(self):
        self.assertIsNone(find_topic("   ", self.topics).topic)


class LoadTopicsValidationTest(unittest.TestCase):
    def assertRejected(self, data, message_part):
        with self.assertRaises(TopicError) as ctx:
            load_topics(write_topics(data))
        self.assertIn(message_part, str(ctx.exception))

    def test_valid_minimal_file_loads(self):
        topics = load_topics(write_topics({"test": minimal_topic()}))
        self.assertEqual(topics["test"].title, "Test topic")

    def test_bad_json(self):
        self.assertRejected("{not json", "not valid JSON")

    def test_missing_file(self):
        with self.assertRaises(TopicError):
            load_topics(Path("/no/such/topics.json"))

    def test_missing_level(self):
        topic = minimal_topic()
        del topic["levels"]["teen"]
        self.assertRejected({"test": topic}, "missing level 'teen'")

    def test_unknown_level(self):
        topic = minimal_topic()
        topic["levels"]["adult"] = topic["levels"]["teen"]
        self.assertRejected({"test": topic}, "unknown level(s) adult")

    def test_answer_out_of_range(self):
        topic = minimal_topic()
        topic["levels"]["young"] = json.loads(json.dumps(topic["levels"]["young"]))
        topic["levels"]["young"]["quiz"][0]["answer"] = 5
        self.assertRejected({"test": topic}, "is not one of the choices")

    def test_answer_must_not_be_a_boolean(self):
        topic = minimal_topic()
        topic["levels"]["young"] = json.loads(json.dumps(topic["levels"]["young"]))
        topic["levels"]["young"]["quiz"][0]["answer"] = True
        self.assertRejected({"test": topic}, "'answer' must be a int")

    def test_two_topics_cannot_share_a_name(self):
        data = {"a": minimal_topic("First", ["shared"]), "b": minimal_topic("Second", ["Shared"])}
        self.assertRejected(data, "used by both")


if __name__ == "__main__":
    unittest.main()
