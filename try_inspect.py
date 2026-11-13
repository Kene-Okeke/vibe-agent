from vibe_agent.inspector.inspector import inspect

for name in ["good.zip", "monorepo.zip", "two-sites.zip", "two-libs.zip", "evidence.zip", "binary.zip", "no-apps.zip", "broken-json.zip"]:
    path = "test-zips/" + name
    try:
        manifests = inspect(path)
    except ValueError as error:
        print(name, "-> error:", error)
        continue
    print(name, "->", len(manifests), "app(s)")
    for manifest in manifests:
        print("  ", manifest.folder, manifest.app_type, "| markers:", manifest.markers)