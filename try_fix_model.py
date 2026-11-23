from vibe_agent.fixer.fix_suggestion import FixSuggestion

# a good fix, as Gemini would send it (JSON text)
good = '''{
  "kind": "code",
  "explanation": "App.tsx imports ./Header but the file is header.tsx.",
  "edits": [{"file": "src/App.tsx", "find": "./Header", "replace": "./header"}]
}'''
fix = FixSuggestion.model_validate_json(good)
print("✅ good fix:", fix.kind, "→", fix.edits[0].file)

# two bad fixes: pydantic should reject both
bad_fixes = [
    '{"kind": "magic", "explanation": "trust me"}',                 # kind not allowed
    '{"kind": "code", "explanation": "x", "edits": [{"file": "a"}]}',  # edit missing find/replace
]
for bad in bad_fixes:
    try:
        FixSuggestion.model_validate_json(bad)
        print("❌ NOT caught:", bad)
    except ValueError as error:
        print("✅ caught:", str(error).splitlines()[0])