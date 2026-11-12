"""Command line: explain <topic> [--age N] [--quiz] | --list"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Callable, TextIO

from explainer.quiz import format_result, run_quiz
from explainer.topics import (
    DEFAULT_TOPICS_FILE,
    Topic,
    TopicError,
    find_topic,
    level_for_age,
    load_topics,
)

AGE_LABELS = {"young": "ages 6-8", "middle": "ages 9-12", "teen": "ages 13+"}
WIDTH = 78


def render_lesson(topic: Topic, level: str) -> str:
    lesson = topic.lessons[level]
    heading = f"{topic.emoji} {topic.title}".strip()
    lines = [
        f"{heading}  ({AGE_LABELS[level]})",
        "",
        textwrap.fill(f"Analogy: {lesson.analogy}", WIDTH, subsequent_indent=" " * 9),
        "",
        "Key steps:",
    ]
    for number, step in enumerate(lesson.steps, start=1):
        lines.append(textwrap.fill(f" {number}. {step}", WIDTH, subsequent_indent="    "))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="explain",
        description="Explain a concept with an analogy, pitched at the reader's age.",
    )
    parser.add_argument("topic", nargs="*", help="what to explain, e.g. photosynthesis or water cycle")
    parser.add_argument("--age", type=int, default=10, help="reader's age, 6 or over (default 10)")
    parser.add_argument("--quiz", action="store_true", help="finish with a short quiz")
    parser.add_argument("--list", action="store_true", help="list the topics available")
    parser.add_argument("--topics-file", type=Path, default=DEFAULT_TOPICS_FILE, help=argparse.SUPPRESS)
    return parser


def main(
    argv: list[str] | None = None,
    ask: Callable[[str], str] = input,
    out: TextIO | None = None,
) -> int:
    """Run the CLI. Returns the exit code: 0 ok, 1 topic not found or quiz stopped, 2 bad input."""
    out = out or sys.stdout

    def say(text: str = "") -> None:
        print(text, file=out)

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        topics = load_topics(args.topics_file)
    except TopicError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for key in sorted(topics):
            say(f"{topics[key].emoji} {topics[key].title}".strip())
        return 0

    if not args.topic:
        parser.error("say what to explain, or use --list")

    try:
        level = level_for_age(args.age)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    query = " ".join(args.topic)
    match = find_topic(query, topics)
    if match.topic is None:
        say(f"Sorry, I don't know about '{query}' yet.")
        if match.suggestions:
            say(f"Did you mean: {', '.join(match.suggestions)}?")
        say("Use --list to see every topic.")
        return 1

    if match.corrected:
        say(f"(Showing {match.topic.title} for '{query}'.)")
        say()
    say(render_lesson(match.topic, level))

    if args.quiz:
        try:
            result = run_quiz(match.topic.lessons[level].quiz, ask=ask, say=say)
        except (EOFError, KeyboardInterrupt):
            say("\nQuiz stopped.")
            return 1
        say()
        say(format_result(result))
    return 0
