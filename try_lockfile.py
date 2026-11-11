from vibe_agent.inspector.inspector import find_apps, add_lockfiles

samples = {
    "npm app": ["shop/package.json", "shop/package-lock.json"],
    "yarn app": ["shop/package.json", "shop/yarn.lock"],
    "no lock file": ["shop/package.json"],
    "python poetry": ["api/pyproject.toml", "api/poetry.lock"],
    "python pip": ["api/requirements.txt"],
    "static": ["site/index.html"],
    "lock in junk": ["w/package.json", "w/node_modules/x/yarn.lock"],
    "lock next door": ["a/package.json", "b/package.json", "b/yarn.lock"],
    "mixed folder": ["x/package.json", "x/requirements.txt", "x/package-lock.json"],
    "your repo": ["vibe-deploy/backend/requirements.txt", "vibe-deploy/frontend/package.json",
                  "vibe-deploy/frontend/package-lock.json", "vibe-deploy/frontend/index.html"],
}

for label, names in samples.items():
    print(label, "->", add_lockfiles(find_apps(names), names))

names = ["m/package.json", "m/pnpm-lock.yaml", "m/apps/web/package.json", "m/apps/api/requirements.txt"]
print("monorepo ->", add_lockfiles(find_apps(names, ["m/"]), names))