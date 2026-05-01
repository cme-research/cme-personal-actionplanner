import json

from openai import OpenAI
from django.conf import settings


def ai_sort_todos(todos: list[dict]) -> list[dict]:
    """Ask a local Ollama model to sort todos by logical urgency. Returns [{id, reasoning}, ...]."""
    client = OpenAI(base_url=settings.OLLAMA_BASE_URL + "/v1", api_key="ollama")

    task_lines = "\n".join(
        f"- ID: {t['id']} | {t['name']} | priority: {t['priority']} | "
        f"topic: {t['topic'] or '-'} | due: {t['due_date'] or '-'} | "
        f"est: {t['estimation'] or '-'} | description: {t['description'] or '-'}"
        for t in todos
    )

    response = client.chat.completions.create(
        model=settings.OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a personal productivity assistant. "
                    "Sort the given tasks from most to least urgent based on logical priority: "
                    "external deadlines (tax, legal, appointments) beat practical work, "
                    "which beats personal errands. Within same importance, use the given priority field. "
                    "Respond ONLY with a valid JSON array — no markdown, no explanation outside the array. "
                    'Format: [{"id": "...", "reasoning": "one short sentence"}, ...]'
                ),
            },
            {"role": "user", "content": f"Sort these tasks:\n\n{task_lines}"},
        ],
        temperature=0.2,
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)
