from vibe_agent.inspector.inspector import (list_zip_files, find_workspace_roots, read_packages, find_libraries,
                                            find_apps, add_lockfiles, add_monorepo_info, build_manifest)

for name in ["good.zip", "monorepo.zip", "evidence.zip"]:
    path = "test-zips/" + name
    names = list_zip_files(path)
    roots = find_workspace_roots(path, names)
    packages = read_packages(path, names)
    libraries = find_libraries(packages)
    apps = find_apps(names, roots + libraries)
    apps = add_lockfiles(apps, names)
    apps = add_monorepo_info(apps, roots, packages)
    print(name)
    for app in apps:
        manifest = build_manifest(app, path, names)
        print("  ", manifest.folder, manifest.app_type, "| lockfile:", manifest.lockfile,
              "| root:", manifest.workspace_root, "| shared:", manifest.shared_packages)
        print("      markers:     ", manifest.markers)
        print("      marker_files:", list(manifest.marker_files))
        print("      files:       ", manifest.files)