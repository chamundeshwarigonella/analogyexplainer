import io
import unittest
from contextlib import redirect_stderr

from explainer.cli import main


def run(*argv, replies=()):
    """Run the CLI and return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    answers = iter(replies)
    with redirect_stderr(err):
        code = main(list(argv), ask=lambda _prompt: next(answers), out=out)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def test_explains_a_topic_at_the_right_level(self):
        code, out, _ = run("photosynthesis", "--age", "10")
        self.assertEqual(code, 0)
        self.assertIn("Photosynthesis  (ages 9-12)", out)
        self.assertIn("Analogy: A leaf is a tiny kitchen", out)
        self.assertIn(" 4. Out comes sugar (food) and oxygen", out)

    def test_multi_word_topic(self):
        code, out, _ = run("water", "cycle", "--age", "14")
        self.assertEqual(code, 0)
        self.assertIn("The water cycle  (ages 13+)", out)

    def test_typo_says_what_it_guessed(self):
        code, out, _ = run("gravty")
        self.assertEqual(code, 0)
        self.assertIn("(Showing Gravity for 'gravty'.)", out)

    def test_unknown_topic(self):
        code, out, _ = run("water")
        self.assertEqual(code, 1)
        self.assertIn("Did you mean: The water cycle?", out)

    def test_list(self):
        code, out, _ = run("--list")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 5)

    def test_too_young(self):
        code, _, err = run("gravity", "--age", "4")
        self.assertEqual(code, 2)
        self.assertIn("age must be 6 or over", err)

    def test_no_topic_is_a_usage_error(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
            main([])
        self.assertEqual(ctx.exception.code, 2)

    def test_quiz(self):
        # Ages 6-8 gravity quiz: answers are b, a, c. Get the last one wrong.
        code, out, _ = run("gravity", "--age", "7", "--quiz", replies=["b", "a", "a"])
        self.assertEqual(code, 0)
        self.assertIn("You scored 2/3.", out)
        self.assertIn("Q3: the answer was c) Yes, but weaker than Earth's.", out)

    def test_quiz_stopped_early(self):
        def stop(_prompt):
            raise EOFError

        out = io.StringIO()
        code = main(["gravity", "--quiz"], ask=stop, out=out)
        self.assertEqual(code, 1)
        self.assertIn("Quiz stopped.", out.getvalue())


if __name__ == "__main__":
    unittest.main()
