# ==============================================================================
# [ИДЕНТИФИКАЦИЯ ПАТЧА]
# Цель: полный EN-перевод интерфейса и сообщений, исправление подстановки «повтор»
# Модули: core/i18n.py (v2.05 -> v2.06), core/config.py (SCRIPT_VER 2.06 -> 2.07)
# Запуск: из корня репозитория  python patch_i18n_v2.07.py
# ==============================================================================
import os
import json
import shutil
import py_compile
import datetime
import traceback

BUILD = "21.11.2026 07:51"
I18N = os.path.join("core", "i18n.py")
CFG = os.path.join("core", "config.py")
BAK_ROOT = ".patch_bak"

# Точные строки (ключ = украинский текст из кода, значение = английский)
EXACT_ADD = {
    "Дата": "Date",
    "Статус": "Status",
    "Файл / Подія": "File / Event",
    "Розмір": "Size",
    "Час": "Time",
    "Деталі операції": "Operation details",
    "Видалення архіву": "Archive deletion",
    "Видалити архів та .sha256?": "Delete archive and .sha256?",
    "Оберіть дію для виявленого сервера в локальній мережі:": "Choose an action for the server found on the local network:",
    "Репозиторій проєкту:": "Project repository:",
    "Локальна мережа / LAN": "Local network / LAN",
    "Інтернет / Зовнішній": "Internet / External",
    "Резервне копіювання успішно завершено": "Backup completed successfully",
    "🔌 Підключити та бекап": "🔌 Connect & backup",
    "⭐ В Історію": "⭐ Add to History",
    "Останні 25 операцій створення резервних копій (подвійний клік по рядку — деталі):": "Last 25 backup operations (double-click a row for details):",
    "Резервне копіювання та Розклад": "Backup & Scheduler",
    "Вигляд та Інтерфейс": "Appearance & Interface",
    "Адресу не вказано. Запуск автопошуку в LAN...": "No address entered. Starting LAN auto-scan...",
    "Активні мережеві адаптери LAN не знайдено!": "No active LAN network adapters found!",
    "Автоматичне налаштування теми": "Automatic theme setup",
    "Вікно згорнуто у Dock (програма продовжує роботу).": "Window minimized to Dock (app keeps running).",
    "Системний трей недоступний у середовищі WSL — робота продовжується без іконки в треї.": "System tray unavailable in WSL — running without tray icon.",
    "Системний трей недоступний (потрібне розширення AppIndicator у GNOME).": "System tray unavailable (AppIndicator extension for GNOME required).",
    "Помилка мережі": "Network error",
    "Завдання Linux не знайдено або вже видалено.": "Linux task not found or already deleted.",
}

# Фрагменты (подстроки), в том числе для f-строк
SUBSTR_ADD = [
    ("Дата та час:", "Date & time:"),
    ("Статус:", "Status:"),
    ("Розмір:", "Size:"),
    ("Деталі / Файл:", "Details / File:"),
    ("Тривалість:", "Duration:"),
    ("Файл архіву:", "Archive file:"),
    ("Джерело (сервер):", "Source (server):"),
    ("Час запуску:", "Start time:"),
    ("Завершено:", "Finished:"),
    ("Підготовка та аналіз на сервері:", "Preparation & analysis on server:"),
    ("Збір та копіювання даних на сервері:", "Data collection & copying on server:"),
    ("Стиснення та пакування ZIP на сервері:", "ZIP packing on server:"),
    ("Перевірка файлів на сервері:", "File check on server:"),
    ("Перевірка архіву CRC32 (програма):", "CRC32 archive check (app):"),
    ("Розрахунок та звірка SHA-256:", "SHA-256 calculation & check:"),
    ("Дзеркальне копіювання:", "Mirror copy:"),
    ("Скачування по мережі (", "Network download ("),
    ("Видалено пошкоджений архів:", "Corrupted archive deleted:"),
    ("Видалено з диска назавжди", "Deleted permanently from disk"),
    ("Переміщено у Кошик", "Moved to Recycle Bin"),
    ("Сервер не повернув cookie сесії.", "Server returned no session cookie."),
    ("УВАГА! Контрольна сума SHA-256 не збігається", "WARNING! SHA-256 checksum mismatch"),
    ("SHA-256 не збігається з контрольним хешем сервера", "SHA-256 does not match server checksum"),
    ("Звіт про резервне копіювання", "Backup report"),
    ("Помилка читання ZIP:", "ZIP read error:"),
    ("Помилка перевірки SHA-256:", "SHA-256 check error:"),
    ("Помилка розблокування редактора:", "Editor unlock error:"),
    ("Помилка запису на диск:", "Disk write error:"),
    ("Помилка повторної підготовки:", "Re-preparation error:"),
    ("Сервер не створив завдання експорту:", "Server did not create export job:"),
    ("Сервер не створив нове завдання експорту:", "Server did not create new export job:"),
    ("Сервер повернув некоректну відповідь під час повторного запуску.", "Server returned invalid response during restart."),
    ("Пошкоджений CRC32 у файлі:", "Corrupted CRC32 in file:"),
    ("невідома помилка сервера", "unknown server error"),
    ("Помилка schtasks.exe:", "schtasks.exe error:"),
    ("Збій створення завдання:", "Task creation failed:"),
    ("Помилка видалення завдання:", "Task deletion error:"),
    ("Помилка створення LaunchAgent:", "LaunchAgent creation error:"),
    ("Помилка видалення LaunchAgent:", "LaunchAgent deletion error:"),
    ("Помилка запису crontab:", "crontab write error:"),
    ("ICMP Ping до", "ICMP Ping to"),
    ("Сайт/домен '", "Site/domain '"),
    ("' не знайдено (помилка DNS).", "' not found (DNS error)."),
    ("' існує, але порт", "' exists, but port"),
    ("закритий або недоступний.", "is closed or unreachable."),
    ("' доступний, але це НЕ сервер HomeGrid Monitor!", "' is reachable, but it is NOT a HomeGrid Monitor server!"),
    ("Хост '", "Host '"),
]
# === [КОНЕЦ ЧАСТИ 1/2 — ВСТАВЛЯТЬ ЧАСТЬ 2 НИЖЕ] ===
def J(s):
    return json.dumps(s, ensure_ascii=False)


def build_plan():
    """Фаза 1: все проверки в памяти, ничего не пишется на диск."""
    plan = {}
    errors = []
    for p in (I18N, CFG):
        with open(p, encoding="utf-8") as f:
            plan[p] = f.read()

    def rep(path, old, new):
        t = plan[path]
        n = t.count(old)
        if n != 1:
            errors.append(f"{path}: якорь найден {n} раз: {old[:60]!r}")
            return
        plan[path] = t.replace(old, new, 1)

    i18n = plan[I18N]
    rep(I18N, "core/i18n.py (v2.05 | 21.11.2026 07:18)",
        f"core/i18n.py (v2.06 | {BUILD})")

    # Добавления в EN_EXACT (только новые ключи)
    lines = []
    for k, v in EXACT_ADD.items():
        if J(k) + ": " in i18n:
            print("пропуск (уже есть):", k[:50])
            continue
        lines.append(f"    {J(k)}: {J(v)},\n")
    anchor_exact = ('    "Журнал операцій поки порожній. Запустіть резервне копіювання.": '
                    '"Operations log is empty. Run a backup first.",\n}')
    rep(I18N, anchor_exact, anchor_exact[:-1] + "".join(lines) + "}")

    # Добавления в EN_SUBSTR (перед сортировкой)
    lines = []
    for a, b in SUBSTR_ADD:
        if f"({J(a)}, " in i18n:
            print("пропуск (уже есть):", a[:50])
            continue
        lines.append(f"    ({J(a)}, {J(b)}),\n")
    rep(I18N, "], key=lambda x: len(x), reverse=True)",
        "".join(lines) + "], key=lambda x: len(x), reverse=True)")

    # Исправление подстроки: «повтор» ломал «повторної», «повторного»
    rep(I18N, '("повтор", "retry"), ("через", "in"),',
        '("повтор ", "retry "), ("Повтор ", "Retry "), ("через ", "in "),')

    # Версия программы: SCRIPT_VER +0.01 и дата сборки
    rep(CFG, 'SCRIPT_VER = "2.06"', 'SCRIPT_VER = "2.07"')
    rep(CFG, 'BUILD_DATE = "21.11.2026 07:34"', f'BUILD_DATE = "{BUILD}"')
    return plan, errors


def main():
    if not (os.path.isfile(I18N) and os.path.isfile(CFG)):
        print("Запустите из корня репозитория (не найден core/i18n.py).")
        return
    with open(I18N, encoding="utf-8") as f:
        if "core/i18n.py (v2.06 | " in f.read():
            print("Патч уже применён, ничего не делаю.")
            return

    plan, errors = build_plan()
    if errors:
        print("ОШИБКА, файлы НЕ изменены:")
        for e in errors:
            print("  -", e)
        return

    # Фаза 2: бэкап, запись, проверка синтаксиса
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = os.path.join(BAK_ROOT, stamp)
    os.makedirs(bdir, exist_ok=True)
    for p in plan:
        shutil.copy2(p, os.path.join(bdir, os.path.basename(p)))
    for p, text in plan.items():
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    ok = True
    for p in plan:
        try:
            py_compile.compile(p, doraise=True)
            print("OK синтаксис:", p)
        except py_compile.PyCompileError as e:
            ok = False
            print("ОШИБКА синтаксиса:", e)
    print("Бэкап:", bdir)
    print("Готово: SCRIPT_VER = 2.07" if ok else "Есть ошибки — откатите из бэкапа.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
    input("\nНажмите Enter для выхода...")