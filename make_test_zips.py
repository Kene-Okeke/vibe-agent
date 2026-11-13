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


with zipfile.ZipFile("junk.zip", "w") as z:
    z.writestr("proj/backend/requirements.txt", "fastapi\n")
    z.writestr("proj/backend/main.py", "")
    z.writestr("proj/backend/__pycache__/main.cpython-312.pyc", "x")
    z.writestr("proj/.venv/lib/site-packages/somepkg/package.json", json.dumps({"name": "somepkg"}))
    z.writestr("proj/dist/index.html", "<h1>built</h1>")
    z.writestr("proj/.git/config", "")

with zipfile.ZipFile("binary.zip", "w") as z:
    z.writestr("site/package.json", b"\xff\xfe\x00\x01")
    z.writestr("site/index.html", "<h1>hi</h1>")

with zipfile.ZipFile("evidence.zip", "w") as z:
    z.writestr("proj/web/package.json", json.dumps({"name": "web", "scripts": {"build": "vite build"}, "devDependencies": {"vite": "5"}}))
    z.writestr("proj/web/package-lock.json", "{}")
    z.writestr("proj/web/vite.config.ts", "export default {}")
    z.writestr("proj/web/index.html", "<div id=root></div>")
    z.writestr("proj/web/.env", "SECRET=xxx")
    z.writestr("proj/web/src/App.jsx", "")
    z.writestr("proj/api/requirements.txt", "fastapi\n" * 10000)
    z.writestr("proj/api/pyproject.toml", b"\xff\xfe\x00\x01")
    z.writestr("proj/api/.python-version", "3.12\n")
    z.writestr("proj/api/app/main.py", "")

with zipfile.ZipFile("no-apps.zip", "w") as z:
    z.writestr("notes/readme.md", "hi")
    z.writestr("photo.png", b"\x89PNG")

with zipfile.ZipFile("two-libs.zip", "w") as z:
    z.writestr("repo/package.json", json.dumps({"name": "repo", "workspaces": ["apps/*", "packages/*"]}))
    z.writestr("repo/apps/web/package.json", json.dumps({"name": "web", "dependencies": {"react": "18", "@repo/ui": "workspace:*"}, "devDependencies": {"@repo/utils": "workspace:*"}}))
    z.writestr("repo/apps/admin/package.json", json.dumps({"name": "admin", "dependencies": {"@repo/ui": "workspace:*"}}))
    z.writestr("repo/packages/ui/package.json", json.dumps({"name": "@repo/ui", "dependencies": {"@repo/utils": "workspace:*"}}))
    z.writestr("repo/packages/utils/package.json", json.dumps({"name": "@repo/utils"}))
    
print("made good.zip, too-many.zip, too-big.zip, escape.zip")