from vibe_agent.fixer.fix_suggestion import FixSuggestion, CodeEdit
from vibe_agent.fixer.check import check_fix

files = ["package.json", "package-lock.json", "src/App.tsx", "src/header.tsx", ".env"]
file_contents = {
    "src/App.tsx": "import Header from './Header'\nimport type { HeaderProps } from './Header'\n",
    "package.json": '{"name": "shop"}',
}

def code_fix(file, find):
    return FixSuggestion(kind="code", explanation="test",
                         edits=[CodeEdit(file=file, find=find, replace="x")])

tests = [
    ("good fix",              code_fix("src/App.tsx", "import Header from './Header'")),
    ("file doesn't exist",    code_fix("src/Nope.tsx", "anything")),
    ("secret file",           code_fix(".env", "SECRET=1")),
    ("lockfile",              code_fix("package-lock.json", "{")),
    ("file LLM never saw",    code_fix("src/header.tsx", "export")),
    ("find appears 0 times",  code_fix("src/App.tsx", "import Footer")),
    ("find appears 2 times",  code_fix("src/App.tsx", "./Header")),
    ("too many edits",        FixSuggestion(kind="code", explanation="test",
                                  edits=[CodeEdit(file="src/App.tsx", find="a", replace="b")] * 6)),
    ("bad plan field",        FixSuggestion(kind="plan", explanation="test",
                                  plan_changes={"confidence": "high"})),
    ("good plan fix",         FixSuggestion(kind="plan", explanation="test",
                                  plan_changes={"runtime_version": "20"})),
]

for label, fix in tests:
    try:
        check_fix(fix, files, file_contents)
        print(f"PASSED   {label}")
    except ValueError as error:
        print(f"REJECTED {label}: {error}")