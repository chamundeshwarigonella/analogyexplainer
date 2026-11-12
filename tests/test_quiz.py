import unittest

from explainer.quiz import format_result, mark, parse_answer, run_quiz
from explainer.topics import Question

QUESTIONS = (
    Question("2 + 2?", ("3", "4", "5"), answer=1, remember="2 + 2 = 4."),
    Question("Sky colour?", ("Blue", "Green", "Red"), answer=0, remember="The sky looks blue."),
    Question("Ice is...", ("Hot", "Wet sand", "Frozen water"), answer=2, remember="Ice is frozen water."),
)


class ParseAnswerTest(unittest.TestCase):
    def test_letters_and_numbers(self):
        self.assertEqual(parse_answer("a", 3), 0)
        self.assertEqual(parse_answer(" B ", 3), 1)
        self.assertEqual(parse_answer("c)", 3), 2)
        self.assertEqual(parse_answer("2", 3), 1)

    def test_invalid(self):
        for raw in ("", "d", "0", "4", "ab", "maybe", "-1"):
            self.assertIsNone(parse_answer(raw, 3), raw)


class MarkTest(unittest.TestCase):
    def test_all_right(self):
        result = mark(QUESTIONS, [1, 0, 2])
        self.assertEqual((result.score, result.total), (3, 3))
        self.assertIn("Perfect", format_result(result))

    def test_some_wrong(self):
        result = mark(QUESTIONS, [0, 0, 1])
        self.assertEqual(result.score, 1)
        self.assertEqual([m.number for m in result.misses], [1, 3])
        text = format_result(result)
        self.assertIn("You scored 1/3.", text)
        self.assertIn("Q1: the answer was b) 4. Remember: 2 + 2 = 4.", text)
        self.assertIn("Q3: the answer was c) Frozen water.", text)

    def test_wrong_number_of_answers(self):
        with self.assertRaises(ValueError):
            mark(QUESTIONS, [1, 0])


class RunQuizTest(unittest.TestCase):
    def test_reasks_until_the_answer_is_valid(self):
        replies = iter(["x", "b", "1", "c"])
        said = []
        result = run_quiz(QUESTIONS, ask=lambda _prompt: next(replies), say=said.append)
        self.assertEqual(result.score, 3)
        self.assertIn("Please answer a, b or c.", said)


if __name__ == "__main__":
    unittest.main()
