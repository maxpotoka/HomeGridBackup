import os, re, shutil, sys
from python_minifier import minify

BACKUP_DIR_NAME = "_backup_orig"
RX_PATCH = re.compile(r"^\s*#.*\bpatch\b", re.IGNORECASE)
RX_VER = re.compile(r"(\d+(?:\.\d+)+)")
KEEP_OTHER = [
    re.compile(r"^\s*#\s*\[ФАЙЛ:"),
    re.compile(r"^#!"),
]

def _freshest_patch_idx(lines):
    matches = [(i, ln) for i, ln in enumerate(lines) if RX_PATCH.search(ln)]
    if not matches:
        return -1
    def score(item):
        idx, text = item
        m = RX_VER.search(text)
        ver_t = tuple(int(x) for x in m.group(1).split(".")) if m else (0,)
        return (ver_t, -idx)
    return max(matches, key=score)[0]

def extract_headers(source):
    lines = source.splitlines()
    best_i = _freshest_patch_idx(lines)
    kept = []
    for i, line in enumerate(lines):
        if i == best_i or any(p.search(line) for p in KEEP_OTHER):
            kept.append(line.rstrip())
    return "\n".join(kept)

def clean_old_patches_in_tree(dirpath):
    skip_dirs = {"__pycache__", ".git", ".venv", "venv", BACKUP_DIR_NAME, ".patch_bak"}
    skip_files = {"minify_py.py", "run_pyminify.py"}
    cleaned = 0
    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in sorted(files):
            if f.endswith(".py") and f not in skip_files:
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as fp:
                    src = fp.read()
                lines = src.splitlines()
                matches = [i for i, ln in enumerate(lines) if RX_PATCH.search(ln)]
                if len(matches) > 1:
                    best_i = _freshest_patch_idx(lines)
                    out_lines = [ln for i, ln in enumerate(lines) if not RX_PATCH.search(ln) or i == best_i]
                    with open(path, "w", encoding="utf-8", newline="\n") as fp:
                        fp.write("\n".join(out_lines) + ("\n" if src.endswith("\n") else ""))
                    cleaned += 1
                    print(f"[PATCH CLEAN] {os.path.relpath(path, dirpath)} -> {lines[best_i].strip()}")
    print(f"Очищено файлов от старых patch-заголовков: {cleaned}")

def process(dirpath, apply=False):
    skip_dirs = {"__pycache__", ".git", ".venv", "venv", BACKUP_DIR_NAME, ".patch_bak"}
    skip_files = {"minify_py.py", "run_pyminify.py"}
    backup_root = os.path.join(dirpath, BACKUP_DIR_NAME)
    total_b, total_a = 0, 0

    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in sorted(files):
            if f.endswith(".py") and f not in skip_files:
                path = os.path.join(root, f)
                rel = os.path.relpath(path, dirpath)
                with open(path, "r", encoding="utf-8") as fp:
                    src = fp.read()
                headers = extract_headers(src)
                compact = minify(src, remove_literal_statements=True, rename_globals=False)
                if headers:
                    compact = headers + "\n" + compact
                bb = len(src.encode("utf-8"))
                ba = len(compact.encode("utf-8"))
                total_b += bb
                total_a += ba
                print(f"{rel:<45} {bb:>8} -> {ba:>8} байт (-{bb-ba})")
                if apply and (bb != ba or len([ln for ln in src.splitlines() if RX_PATCH.search(ln)]) > 1):
                    bk = os.path.join(backup_root, rel)
                    os.makedirs(os.path.dirname(bk), exist_ok=True)
                    shutil.copy2(path, bk)
                    with open(path, "w", encoding="utf-8", newline="\n") as fp:
                        fp.write(compact + "\n")

    pct = 100 - 100 * total_a // max(1, total_b)
    print(f"\nИТОГО: {total_b} -> {total_a} байт (сжато на {pct}%)")
    if not apply:
        print("[Режим просмотра] Для применения запустите: python run_pyminify.py --apply")
        print("Для очистки только заголовков без сжатия: python run_pyminify.py --clean-headers")
    else:
        print(f"Оригиналы сохранены в {backup_root}")

if __name__ == "__main__":
    target = next((a for a in sys.argv[1:] if not a.startswith("-")), os.getcwd())
    if "--clean-headers" in sys.argv:
        clean_old_patches_in_tree(target)
    else:
        process(target, apply="--apply" in sys.argv)
