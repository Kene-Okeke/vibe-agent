from vibe_agent.inspector.inspector import find_apps

samples = {
    "static site": ["index.html", "style.css", "img/logo.png"],
    "static, in a folder": ["my-site/index.html", "my-site/style.css"],
    "node (React)": ["shop/package.json", "shop/index.html", "shop/src/App.jsx"],
    "python, 3 folders deep": ["a/b/api/requirements.txt", "a/b/api/main.py"],
    "python with templates": ["api/requirements.txt", "api/templates/index.html"],
    "site with a library": ["index.html", "vendor/chart/package.json"],
    "node_modules ignored": ["web/index.html", "web/node_modules/react/package.json"],
    "mac junk": ["site/index.html", "__MACOSX/site/._index.html", "site/.DS_Store"],
    "your repo": ["vibe-deploy/backend/requirements.txt", "vibe-deploy/backend/app/main.py",
                  "vibe-deploy/frontend/package.json", "vibe-deploy/frontend/index.html"],
    "nothing known": ["notes.txt", "photo.png"],

    "vite public folder": ["web/package.json", "web/index.html", "web/public/index.html"],
    "server inside node app": ["web/package.json", "web/index.html", "web/server/package.json"],
    "python inside node app": ["app/package.json", "app/backend/requirements.txt"],
    "site at ZIP root + api": ["index.html", "api/requirements.txt"],
}

for label, names in samples.items():
    try:
        print(label, "->", find_apps(names))
    except ValueError as error:
        print(label, "-> rejected:", error)