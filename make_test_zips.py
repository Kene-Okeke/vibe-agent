import zipfile
import json
with zipfile.ZipFile("good.zip", "w") as z:
    z.writestr("my-site/index.html", "<h1>hi</h1>")
    z.writestr("my-site/style.css", "h1 { color: red }")

with zipfile.ZipFile("too-many.zip", "w") as z:
    for i in range(2001):
        z.writestr(f"f{i}.txt", "x")

with zipfile.ZipFile("too-big.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("big.txt", "0" * (201 * 1024 * 1024))

with zipfile.ZipFile("escape.zip", "w") as z:
    z.writestr("../../evil.txt", "gotcha")

with zipfile.ZipFile("monorepo.zip", "w") as z:
    z.writestr("my-project/package.json", json.dumps({"name": "my-project", "workspaces": ["apps/*", "packages/*"]}))
    z.writestr("my-project/apps/frontend/package.json", json.dumps({"name": "frontend", "dependencies": {"react": "18", "shared": "*"}, "scripts": {"build": "vite build"}}))
    z.writestr("my-project/apps/frontend/index.html", "<div id=root></div>")
    z.writestr("my-project/apps/backend/requirements.txt", "fastapi\n")
    z.writestr("my-project/apps/backend/main.py", "")
    z.writestr("my-project/packages/shared/package.json", json.dumps({"name": "shared"}))

with zipfile.ZipFile("broken-json.zip", "w") as z:
    z.writestr("site/package.json", "{ not json")
    z.writestr("site/index.html", "<h1>hi</h1>")

    

with zipfile.ZipFile("two-sites.zip", "w") as z:
    z.writestr("shop/package.json", json.dumps({"name": "shop", "dependencies": {"react": "18"}}))
    z.writestr("admin/package.json", json.dumps({"name": "admin", "dependencies": {"react": "18"}}))

print("made good.zip, too-many.zip, too-big.zip, escape.zip")