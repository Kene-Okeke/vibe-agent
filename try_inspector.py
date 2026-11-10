from app.inspector import list_zip_files
from app.inspector import find_apps
# for name in ["good.zip", "too-many.zip", "too-big.zip", "escape.zip"]:
#     try:
#         print(name, "->", list_zip_files("test-zips/" + name))
#     except ValueError as error:
#         print(name, "-> rejected:", error)

print("good.zip:", find_apps(list_zip_files("test-zips/good.zip")))
print("my repo:", find_apps(list_zip_files("test-zips/my-repo.zip")))



from app.inspector import find_apps, find_workspace_roots

for name in ["good.zip", "monorepo.zip", "broken-json.zip"]:
    path = "test-zips/" + name
    names = list_zip_files(path)
    roots = find_workspace_roots(path, names)
    print(name, "roots:", roots)
    print("   before:", find_apps(names))
    print("   after: ", find_apps(names, roots))