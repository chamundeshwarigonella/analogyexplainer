# Analogy Explainer

A small command-line tool that explains a concept with an everyday analogy, pitched at the
reader's age, and can finish with a short quiz.

```
$ python3 -m explainer photosynthesis --age 10

🌱 Photosynthesis  (ages 9-12)

Analogy: A leaf is a tiny kitchen. Sunlight is the cooker, water and carbon
         dioxide are the ingredients, and sugar is the meal the plant makes
         for itself. Oxygen is the steam that drifts out.

Key steps:
 1. Roots drink water
 2. Leaves breathe in carbon dioxide
 3. Sunlight powers the 'cooking'
 4. Out comes sugar (food) and oxygen
```

## Requirements

Python 3.10 or newer. There are no other dependencies.

## Usage

```bash
python3 -m explainer photosynthesis              # default age is 10
python3 -m explainer water cycle --age 14        # multi-word topics need no quotes
python3 -m explainer gravity --age 7 --quiz      # finish with a 3-question quiz
python3 -m explainer --list                      # show every topic
```

To get a plain `explain` command, install it into a virtual environment:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
explain electricity --age 12
```

## How it behaves

| Feature | Rule |
|---|---|
| Reading level | Ages 6-8 → `young`, 9-12 → `middle`, 13+ → `teen`. Under 6 or over 120 is rejected. |
| Finding a topic | Matches the topic key, its title or any alias, ignoring case, extra spaces, `-` and `_`. |
| Typos | A close match (`photosynthesys`) is used, and the tool says what it guessed. |
| Unknown topics | Suggests up to 3 near matches, otherwise points to `--list`. |
| Quiz | Accepts `a`/`b`/`c` or `1`/`2`/`3`, re-asks on anything else, then scores out of 3 and explains each wrong answer. |

Exit codes: `0` success, `1` topic not found or quiz stopped early, `2` bad input or a broken topics file.

## Adding a topic

All content lives in [`explainer/topics.json`](explainer/topics.json). Each topic needs a
`title`, optional `emoji` and `aliases`, and all three `levels`. Each level has an `analogy`,
a list of `steps` and a `quiz`:

```json
{
  "question": "Which gas do leaves take in?",
  "choices": ["Oxygen", "Carbon dioxide", "Helium"],
  "answer": 1,
  "remember": "Leaves take in carbon dioxide and give out oxygen."
}
```

`answer` is the position of the right choice, counting from 0. The file is checked when it
loads: missing levels, an `answer` outside the choices, or two topics sharing a name are all
reported with the exact place to fix.

## Project layout

```
explainer/
  cli.py        command-line options and output
  topics.py     loading, validating and finding topics
  quiz.py       asking and marking the quiz
  topics.json   the content: 5 topics x 3 levels
tests/          unit tests for each module
```

## Tests

```bash
python3 -m unittest
```
