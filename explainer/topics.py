"""Load topics from topics.json and find the one the user asked for."""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TOPICS_FILE = Path(__file__).with_name("topics.json")

# Reading levels, youngest first. Every topic must provide all three.
LEVELS = ("young", "middle", "teen")
MAX_CHOICES = 6


class TopicError(Exception):
    """The topics file is missing, unreadable or malformed."""


@dataclass(frozen=True)
class Question:
    text: str
    choices: tuple[str, ...]
    answer: int  # index into choices
    remember: str  # shown when the reader gets it wrong


@dataclass(frozen=True)
class Lesson:
    analogy: str
    steps: tuple[str, ...]
    quiz: tuple[Question, ...]


@dataclass(frozen=True)
class Topic:
    key: str
    title: str
    emoji: str
    aliases: tuple[str, ...]
    lessons: dict[str, Lesson]  # level -> lesson


@dataclass(frozen=True)
class Match:
    topic: Topic | None
    corrected: bool = False  # True when we guessed from a typo
    suggestions: tuple[str, ...] = ()  # titles to offer when nothing matched


def level_for_age(age: int) -> str:
    """Map a reader's age to a reading level."""
    if age < 6:
        raise ValueError("age must be 6 or over")
    if age > 120:
        raise ValueError("age must be 120 or under")
    if age <= 8:
        return "young"
    if age <= 12:
        return "middle"
    return "teen"


def normalise(text: str) -> str:
    """Lower-case, treat - and _ as spaces, and collapse runs of spaces."""
    return " ".join(text.lower().replace("-", " ").replace("_", " ").split())


def load_topics(path: Path | str = DEFAULT_TOPICS_FILE) -> dict[str, Topic]:
    """Read and validate the topics file. Raises TopicError on any problem."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TopicError(f"cannot read {path}: {exc.strerror}") from exc
    except json.JSONDecodeError as exc:
        raise TopicError(f"{path} is not valid JSON: {exc.msg} (line {exc.lineno})") from exc

    if not isinstance(raw, dict) or not raw:
        raise TopicError(f"{path} must be a non-empty JSON object of topics")

    topics = {key: _parse_topic(key, body) for key, body in raw.items()}
    _name_index(topics)  # fails early if two topics claim the same name
    return topics


def find_topic(query: str, topics: dict[str, Topic]) -> Match:
    """Find a topic by key, title or alias, forgiving small typos."""
    names = _name_index(topics)
    wanted = normalise(query)
    if not wanted:
        return Match(None)

    if wanted in names:
        return Match(topics[names[wanted]])

    close = difflib.get_close_matches(wanted, names, n=1, cutoff=0.8)
    if close:
        return Match(topics[names[close[0]]], corrected=True)

    suggestions: list[str] = []
    # 0.6 keeps real near-misses ("water" -> "water cycle") but drops weak ones ("water" -> "web").
    for name in difflib.get_close_matches(wanted, names, n=6, cutoff=0.6):
        title = topics[names[name]].title
        if title not in suggestions:
            suggestions.append(title)
    return Match(None, suggestions=tuple(suggestions[:3]))


# --- internals -------------------------------------------------------------


def _name_index(topics: dict[str, Topic]) -> dict[str, str]:
    """Map every normalised key, title and alias to its topic key."""
    index: dict[str, str] = {}
    for key, topic in topics.items():
        for name in (key, topic.title, *topic.aliases):
            name = normalise(name)
            owner = index.setdefault(name, key)
            if owner != key:
                raise TopicError(f"name '{name}' is used by both '{owner}' and '{key}'")
    return index


def _need(obj: object, field: str, kind: type, where: str):
    """Return obj[field], checking it exists, has the right type and is not empty."""
    if not isinstance(obj, dict) or field not in obj:
        raise TopicError(f"{where}: missing '{field}'")
    value = obj[field]
    # bool is a subclass of int in Python, so reject it explicitly.
    if not isinstance(value, kind) or isinstance(value, bool):
        raise TopicError(f"{where}: '{field}' must be a {kind.__name__}")
    if kind in (str, list, dict) and not value:
        raise TopicError(f"{where}: '{field}' must not be empty")
    return value


def _strings(values: list, field: str, where: str) -> tuple[str, ...]:
    if not all(isinstance(v, str) and v.strip() for v in values):
        raise TopicError(f"{where}: every item in '{field}' must be non-empty text")
    return tuple(values)


def _parse_topic(key: str, body: object) -> Topic:
    where = f"topic '{key}'"
    title = _need(body, "title", str, where)
    emoji = body.get("emoji", "")
    aliases = body.get("aliases", [])
    if not isinstance(emoji, str):
        raise TopicError(f"{where}: 'emoji' must be text")
    if not isinstance(aliases, list):
        raise TopicError(f"{where}: 'aliases' must be a list")

    levels = _need(body, "levels", dict, where)
    unknown = set(levels) - set(LEVELS)
    if unknown:
        raise TopicError(f"{where}: unknown level(s) {', '.join(sorted(unknown))}")
    lessons = {}
    for level in LEVELS:
        if level not in levels:
            raise TopicError(f"{where}: missing level '{level}'")
        lessons[level] = _parse_lesson(levels[level], f"{where}, level '{level}'")

    return Topic(
        key=key,
        title=title,
        emoji=emoji,
        aliases=_strings(aliases, "aliases", where),
        lessons=lessons,
    )


def _parse_lesson(body: object, where: str) -> Lesson:
    analogy = _need(body, "analogy", str, where)
    steps = _strings(_need(body, "steps", list, where), "steps", where)
    quiz = tuple(
        _parse_question(q, f"{where}, question {i}")
        for i, q in enumerate(_need(body, "quiz", list, where), start=1)
    )
    return Lesson(analogy=analogy, steps=steps, quiz=quiz)


def _parse_question(body: object, where: str) -> Question:
    text = _need(body, "question", str, where)
    choices = _strings(_need(body, "choices", list, where), "choices", where)
    if not 2 <= len(choices) <= MAX_CHOICES:
        raise TopicError(f"{where}: needs between 2 and {MAX_CHOICES} choices")
    answer = _need(body, "answer", int, where)
    if not 0 <= answer < len(choices):
        raise TopicError(f"{where}: 'answer' {answer} is not one of the choices (0-{len(choices) - 1})")
    remember = _need(body, "remember", str, where)
    return Question(text=text, choices=choices, answer=answer, remember=remember)
