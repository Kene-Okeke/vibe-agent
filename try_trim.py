from vibe_agent.fixer.logs import trim_log

# a fake 300-line build log with the real error buried early
fake_log = []
for number in range(1, 301):
    fake_log.append(f"line {number}: npm noise")
fake_log[49] = "src/App.tsx(3,20): error TS2307: Cannot find module './Header'"
fake_log[299] = 'ERROR: process "/bin/sh -c npm run build" did not complete successfully: exit code: 2'

trimmed = trim_log("\n".join(fake_log))
print(trimmed)
print("---")
print("lines kept:", len(trimmed.splitlines()))