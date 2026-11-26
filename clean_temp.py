import os, shutil

SKIP_DIRS = {".git", "venv", ".venv", "env"}
TARGET_DIRS = {".patch_bak", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TARGET_EXTS = (".pyc", ".pyo", ".bak", ".tmp", ".orig")

def clean_project():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    removed_dirs = 0
    removed_files = 0
    freed_bytes = 0

    for current_root, dirs, files in os.walk(root_dir, topdown=True):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for d in list(dirs):
            if d in TARGET_DIRS:
                full_d = os.path.join(current_root, d)
                try:
                    for dp, _, fns in os.walk(full_d):
                        for fn in fns:
                            try:
                                freed_bytes += os.path.getsize(os.path.join(dp, fn))
                            except OSError:
                                pass
                    shutil.rmtree(full_d, ignore_errors=True)
                    dirs.remove(d)
                    removed_dirs += 1
                except OSError:
                    pass

        for f in files:
            if f == os.path.basename(__file__):
                continue
            if f.endswith(TARGET_EXTS):
                full_f = os.path.join(current_root, f)
                try:
                    freed_bytes += os.path.getsize(full_f)
                    os.remove(full_f)
                    removed_files += 1
                except OSError:
                    pass

    freed_kb = round(freed_bytes / 1024.0, 1)
    print(f"?????? ?????????: ??????? ?????={removed_dirs}, ??????={removed_files}, ???????????={freed_kb} ")

if __name__ == "__main__":
    clean_project()
