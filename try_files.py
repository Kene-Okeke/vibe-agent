from vibe_agent.inspector.inspector import find_app_files, find_markers

samples = {
    "vite app": ("web/", ["web/package.json", "web/package-lock.json", "web/vite.config.ts", "web/index.html", "web/src/App.jsx"]),
    "secrets left out": ("api/", ["api/requirements.txt", "api/main.py", "api/.env", "api/.env.local"]),
    "junk left out": ("web/", ["web/package.json", "web/node_modules/react/package.json", "web/dist/index.html"]),
    "marker in a subfolder": ("web/", ["web/package.json", "web/server/package.json", "web/server/index.js"]),
    "other apps left out": ("shop/", ["shop/package.json", "admin/package.json", "admin/index.html"]),
    "app at ZIP root": ("", ["index.html", "style.css", ".nvmrc"]),
}

for label, (folder, names) in samples.items():
    files = find_app_files({"folder": folder}, names)
    print(label)
    print("   files:  ", files)
    print("   markers:", find_markers(files))

many = ["big/package.json"]
for number in range(600):
    many.append("big/src/file" + str(number) + ".js")
print("600 files ->", len(find_app_files({"folder": "big/"}, many)))