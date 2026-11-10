from app.inspector import find_apps, add_package_managers

samples = {
    "npm app": ["shop/package.json", "shop/package-lock.json"],
    "yarn app": ["shop/package.json", "shop/yarn.lock"],
    "no lock file": ["shop/package.json"],
    "python poetry": ["api/pyproject.toml", "api/poetry.lock"],
    "python pip": ["api/requirements.txt"],
    "static": ["site/index.html"],
    "node_modules ignored": ["w/package.json", "w/node_modules/x/yarn.lock"],
    "your repo": ["vibe-deploy/backend/requirements.txt", "vibe-deploy/frontend/package.json",
                  "vibe-deploy/frontend/package-lock.json", "vibe-deploy/frontend/index.html"],
}

for label, names in samples.items():
    print(label, "->", add_package_managers(find_apps(names), names))

# the monorepo: one pnpm lock at the root, two apps below it
names = ["m/package.json", "m/pnpm-lock.yaml", "m/apps/web/package.json", "m/apps/api/requirements.txt"]
print("monorepo ->", add_package_managers(find_apps(names, ["m/"]), names))
