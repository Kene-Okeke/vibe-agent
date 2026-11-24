from vibe_agent.llm import ask_llm
from vibe_agent.fixer.fix_suggestion import FixSuggestion

def suggest_fix(prompt: str) -> FixSuggestion:
    # 1. ask Gemini (a timeout or network error is raised as-is)
    reply = ask_llm(prompt)

    # 2. LLMs often send null for "nothing"; drop those so our defaults ([] / {}) apply
    cleaned = {}
    for key, value in reply.items():
        if value is not None:
            cleaned[key] = value

    # 2. check the reply has the FixSuggestion shape (raises ValueError if not)
    return FixSuggestion.model_validate(cleaned)