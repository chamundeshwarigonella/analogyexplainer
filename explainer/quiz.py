"""Ask a short multiple-choice quiz and mark it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from explainer.topics import MAX_CHOICES, Question

LETTERS = "abcdef"[:MAX_CHOICES]


@dataclass(frozen=True)
class Miss:
    number: int  # 1-based question number
    question: Question
    given: int  # index of the choice the reader picked


@dataclass(frozen=True)
class QuizResult:
    total: int
    misses: tuple[Miss, ...]

    @property
    def score(self) -> int:
        return self.total - len(self.misses)


def parse_answer(raw: str, n_choices: int) -> int | None:
    """Turn 'b', 'B)', or '2' into a choice index. Returns None if invalid."""
    text = raw.strip().lower().rstrip(")")
    if len(text) == 1 and text in LETTERS[:n_choices]:
        return LETTERS.index(text)
    if text.isdigit() and 1 <= int(text) <= n_choices:
        return int(text) - 1
    return None


def mark(questions: Sequence[Question], answers: Sequence[int]) -> QuizResult:
    """Compare answers with the correct choices."""
    if len(answers) != len(questions):
        raise ValueError(f"expected {len(questions)} answers, got {len(answers)}")
    misses = tuple(
        Miss(number, question, given)
        for number, (question, given) in enumerate(zip(questions, answers), start=1)
        if given != question.answer
    )
    return QuizResult(total=len(questions), misses=misses)


def run_quiz(
    questions: Sequence[Question],
    ask: Callable[[str], str] = input,
    say: Callable[[str], None] = print,
) -> QuizResult:
    """Ask each question in turn, re-asking until the answer is valid."""
    say(f"\nQuiz: {len(questions)} questions")
    answers = []
    for number, question in enumerate(questions, start=1):
        say(f"\nQ{number}. {question.text}")
        for letter, choice in zip(LETTERS, question.choices):
            say(f"   {letter}) {choice}")
        n = len(question.choices)
        while (picked := parse_answer(ask("Your answer: "), n)) is None:
            say(f"Please answer {_options(n)}.")
        answers.append(picked)
    return mark(questions, answers)


def format_result(result: QuizResult) -> str:
    lines = [f"You scored {result.score}/{result.total}."]
    if not result.misses:
        lines.append("Perfect, well done!")
    for miss in result.misses:
        q = miss.question
        right = f"{LETTERS[q.answer]}) {q.choices[q.answer]}"
        lines.append(f"✗ Q{miss.number}: the answer was {right}. Remember: {q.remember}")
    return "\n".join(lines)


def _options(n: int) -> str:
    """'a, b or c' for n=3."""
    letters = list(LETTERS[:n])
    return ", ".join(letters[:-1]) + " or " + letters[-1]
