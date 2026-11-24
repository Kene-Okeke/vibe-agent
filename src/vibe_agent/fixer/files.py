# always useful context, if the project has them
CONTEXT_FILES = ["package.json", "requirements.txt"]

# never send these to the LLM
SECRET_ENDINGS = [".env", ".pem", ".key", ".sql", ".db", ".sqlite"]

MAX_FILES = 5


def is_secret(path: str) -> bool:
    for ending in SECRET_ENDINGS:
        if path.endswith(ending) or "/.env" in path or path.startswith(".env"):
            return True
    return False


def pick_relevant_files(log: str, files: list[str]) -> list[str]:
    picked = []

    # 1. files the error log mentions
    for path in files:
        if path in log and not is_secret(path):
            picked.append(path)

    # 2. context files, if not already picked
    for path in CONTEXT_FILES:
        if path in files and path not in picked:
            picked.append(path)

    # 3. keep it small
    return picked[:MAX_FILES]