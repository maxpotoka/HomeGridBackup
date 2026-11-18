# [ФАЙЛ: core/i18n.py — ПЕРЕВОД ИНТЕРФЕЙСА И СООБЩЕНИЙ (EN / UK)]
import re

EN_EXACT = {
    "Готовий до резервного копіювання": "Ready for backup",
    "Очікування": "Idle",
    "Не перевірено": "Not checked",
    "Перевірка...": "Checking...",
    "Підключення до сервера та папки збереження": "Server connection and backup folders",
    "Адреса:": "Server:",
    "🕘 Історія": "🕘 History",
    "🔌 Підключити": "🔌 Connect",
    "🔍 Автопошук по LAN": "🔍 Auto-scan LAN",
    "📡 Обрати виявлений (0)": "📡 Select found (0)",
    "Папка:": "Folder:",
    "📁 Папка архівів...": "📁 Backup folder...",
    "📂 Відкрити папку": "📂 Open folder",
    "Дзеркало:": "Mirror:",
    "🪞 Папка дзеркала...": "🪞 Mirror folder...",
    "Увімкнено": "Enabled",
    "Не задано": "Not set",
    "ЛОКАЛЬНЕ СХОВИЩЕ": "LOCAL STORAGE",
    "ОСТАННІЙ АРХІВ": "LAST ARCHIVE",
    "Ще немає створених копій": "No backups created yet",
    "Невідомо": "Unknown",
    "📊 Статистика": "📊 Statistics",
    "📜 Журнал операцій": "📜 Operations log",
    "🔍 Аналіз GFS / SHA-256": "🔍 GFS / SHA-256 Analysis",
    "Системний лог": "System log",
    "🗑 Очистити лог": "🗑 Clear log",
    "▶ ЗАПУСТИТИ БЕКАП": "▶ START BACKUP",
    "⚙️ Налаштування": "⚙️ Settings",
    "ℹ️ Про програму": "ℹ️ About",
    "✖ Вихід": "✖ Exit",
    "☀️ Світла тема": "☀️ Light theme",
    "🌙 Темна тема": "🌙 Dark theme",
    "Закрити": "Close",
    "Скасувати": "Cancel",
    "Підтвердити": "Confirm",
    "Обрати": "Select",
    "Так": "Yes",
    "Ні": "No",
    "Успішно": "Success",
    "Помилка": "Error",
    "Підтвердження виходу": "Confirm Exit",
    "Ви дійсно бажаєте завершити роботу HomeGrid Backup та закрити програму?": "Are you sure you want to close HomeGrid Backup?",
    "✖ Так, вийти": "✖ Yes, Exit",
    "Історія адрес серверів": "Server Address History",
    "Оберіть раніше збережену адресу або видаліть зайву:": "Select a saved address or remove an old one:",
    "Історія адрес порожня.": "Server history is empty.",
    "Налаштування програми, тем, масштабу, GFS та Планувальника": "Application, Theme, Scale, GFS & Scheduler Settings",
    " 1. Стратегія збереження файлів (GFS) ": " 1. File Retention Strategy (GFS) ",
    "Щоденні (дн.):": "Daily (days):",
    "За сьогодні:": "Today max:",
    "Тижневі (шт.):": "Weekly (pcs):",
    "Місячні (шт.):": "Monthly (pcs):",
    "Річні (архів):": "Yearly (archive):",
    "🗑️ У Кошик (замість назавжди)": "🗑️ Move to Trash (instead of permanent)",
    " 2. Системний трей та тихий режим ": " 2. System Tray, Language & Silent Mode ",
    "📌 Згортати у системний трей при закритті [X]": "📌 Minimize to system tray on close [X]",
    "🧹 Очищати старі копії у тихому режиме (GFS)": "🧹 Clean old backups in silent mode (GFS)",
    "🧹 Очищати старі копії у тихому режимі (GFS)": "🧹 Clean old backups in silent mode (GFS)",
    "Мова / Language:": "Language:",
    " 3. Автозапуск за розкладом (Планувальник завдань Windows) ": " 3. Scheduled Autostart (Task Scheduler) ",
    "Час щодня:": "Daily time:",
    "У фоні через трей (--hidden)": "Background in tray (--hidden)",
    "З вікном консолі (--silent)": "With console window (--silent)",
    "Пріоритет (2-9):": "Priority (2-9):",
    "Запускати пропущене": "Run missed task",
    "Розбудити ПК зі сну": "Wake PC from sleep",
    "📅 Додати в Планувальник": "📅 Add to Scheduler",
    "🗑️ Видалити задачу": "🗑️ Delete Task",
    "📋 Копіювати --hidden": "📋 Copy --hidden",
    "📋 Копіювати --silent": "📋 Copy --silent",
    " 4. Тема (7 стилів), роздільна здатність та шрифт ": " 4. Theme, Resolution & Font ",
    "Тема:": "Theme:",
    "Екран:": "Screen:",
    "Шрифт:": "Font:",
    " 5. Стиль індикатора прогресу (12 стилів) ": " 5. Progress Bar Style ",
    "🔑 Скинути PIN": "🔑 Reset PINs",
    "💾 Зберегти та закрити": "💾 Save & Close",
    "✅ Застосувати": "✅ Apply",
    "Аналіз локального сховища (GFS та SHA-256)": "Local Storage Analysis (GFS & SHA-256)",
    "У папці поки немає ZIP-архівів.": "No ZIP archives in the folder yet.",
    "Перевірка не запущена": "Verification not started",
    "🛡️ Перевірити SHA-256 + CRC32": "🛡️ Verify SHA-256 + CRC32",
    "Буфер:": "Buffer:",
    "🗑️ Очистити застарілі зараз": "🗑️ Clean Expired Now",
    "Статистика резервного копіювання": "Backup Statistics",
    "Зведена аналітика за періодами та структурою локального сховища:": "Summary analytics by period and local storage structure:",
    "СЬОГОДНІ": "TODAY",
    "ЗА ТИЖДЕНЬ (7 ДН.)": "LAST 7 DAYS",
    "ЗА МІСЯЦЬ (30 ДН.)": "LAST 30 DAYS",
    "ЗА ВЕСЬ ЧАС": "ALL TIME",
    "ДИНАМІКА СТВОРЕННЯ АРХІВІВ ЗА ОСТАННІ 6 МІСЯЦІВ": "ARCHIVE CREATION DYNAMICS (LAST 6 MONTHS)",
    "Журнал останніх операцій архівування": "Recent Backup Operations Log",
    "Останні 25 операцій створення резервних копій (дата, розмір та підсумок):": "Last 25 backup operations (date, size, and status):",
    "Журнал операцій поки порожній. Запустіть резервне копіювання.": "Operations log is empty. Run a backup first.",
}

EN_SUBSTR = sorted([
    ("Обрати виявлений", "Select found"),
    ("Графіка", "Graphics"),
    ("Готовий до резервного копіювання", "Ready for backup"),
    (" від ", " from "),
    ("(від ", "(from "),
    ("Систему запущено", "System started"), ("сховище:", "storage:"), ("Каталог:", "Dir:"),
    ("ОС та залізо:", "OS & Hardware:"), ("Перевірку сайту/порту пропущено для", "Host/port check skipped for"),
    ("Перевірка сайту та сервера HGM...", "Checking HGM host and server..."),
    ("Перевірка сесії та авторизація...", "Checking session and auth..."),
    ("Запит на підготовку бекапу...", "Requesting backup preparation..."),
    ("Підготовка на сервері", "Preparing on server"), ("Копіювання бази та файлів", "Copying DB & files"),
    ("Перевірка файлів", "Checking files"), ("Стиснення ZIP-архіву", "Packing ZIP"),
    ("Архів готовий (75%). Завантаження...", "Archive ready (75%). Downloading..."),
    ("Завантаження ZIP-архіву з", "Downloading ZIP archive from"), ("Завантаження", "Downloading"),
    ("Швидкість:", "Speed:"), ("Архів завантажено:", "Archive downloaded:"),
    ("Цілісність перевірено", "Integrity verified"), ("Цілісність 100% підтверджена", "Integrity 100% verified"),
    ("файлів", "files"), ("файл(ів)", "file(s)"), ("Збережено", "Saved"),
    ("Дзеркальну копію збережено у:", "Mirror copy saved to:"),
    ("Налаштування та ключі захищено збережено.", "Settings and keys securely saved."),
    ("Налаштування програми, теми, шрифту та стратегії GFS застосовано.", "Application, theme, font, and GFS settings applied."),
    ("Ротація бекапів за обраною стратегією...", "Running GFS backup rotation..."),
    ("Переміщено у Кошик:", "Moved to Recycle Bin:"), ("Видалено з диска назавжди:", "Deleted permanently:"),
    ("Готово! Архів збережено", "Done! Archive saved"), ("УСПІХ! Резервне копіювання завершено за", "SUCCESS! Backup completed in"),
    ("ПОМИЛКА:", "ERROR:"), ("Помилка:", "Error:"), ("Сканування підмереж:", "Scanning subnets:"),
    ("Сканування", "Scanning"), ("Автоматично обрано сервер:", "Auto-selected server:"),
    ("Знайдено сервер:", "Server found:"), ("Підключено до HomeGrid Monitor:", "Connected to HomeGrid Monitor:"),
    ("Активну сесію підтверджено.", "Active session confirmed."), ("Авторизація успішна!", "Authorization successful!"),
    ("Збірка архіву на сервері", "Building archive on server"), ("Етап сервера", "Server stage"),
    ("Перевірка CRC32", "Verifying CRC32"), ("Розрахунок SHA-256:", "Calculating SHA-256:"),
    ("справних", "valid"), ("без .sha256:", "no .sha256:"), ("пошкоджених:", "corrupted:"),
    ("Час:", "Time:"), ("буфер", "buffer"), ("Завершено за", "Completed in"),
    ("архівів", "archives"), ("Вільно:", "Free:"), ("Без .sha256", "No .sha256"),
    ("знайдено на диску", "found on disk"), ("Структура GFS:", "GFS Structure:"),
    ("Щоденних:", "Daily:"), ("Тижневих", "Weekly"), ("Місячних", "Monthly"),
    ("Середній розмір архіву:", "Average archive size:"), ("Захист SHA-256:", "SHA-256 protection:"),
    ("Успішність запусків:", "Success rate:"), ("Глибина архіву:", "Archive depth:"),
    ("дн.", "days"), ("шт.", "pcs"), ("Всього:", "Total:"), ("Залишиться:", "Keep:"),
    ("Застарілих:", "Expired:"), ("[ВИДАЛИТИ]", "[DELETE]"), ("Версія", "Version"), ("оновлено:", "updated:"),
    ("Січень", "January"), ("Лютий", "February"), ("Березень", "March"), ("Квітень", "April"),
    ("Травень", "May"), ("Червень", "June"), ("Липень", "July"), ("Серпень", "August"),
    ("Вересень", "September"), ("Жовтень", "October"), ("Листопад", "November"), ("Грудень", "December"),
    ("МБ/с", "MB/s"), ("КБ/с", "KB/s"), ("МБ", "MB"), ("КБ", "KB"), ("ГБ", "GB"), ("мс", "ms"),
], key=lambda x: len(x), reverse=True)

UK_EXACT = {v: k for k, v in EN_EXACT.items()}

def tr(text, lang="en"):
    if not text:
        return text
    s = str(text)
    if lang == "uk":
        if s in UK_EXACT:
            return UK_EXACT[s]
        for uk, en in EN_SUBSTR:
            if len(en) > 3 and en in s:
                s = s.replace(en, uk)
        return s
    if s in EN_EXACT:
        return EN_EXACT[s]
    for uk, en in EN_SUBSTR:
        if uk in s:
            s = s.replace(uk, en)
    s = re.sub(r"(?<=\d)\s*с(?=\b|\)|\.)", " s", s)
    s = re.sub(r"\bза\s+(?=\d)", "in ", s)
    s = re.sub(r"\bіз\s+(?=\d)", "of ", s)
    s = re.sub(r"\bо\s+(?=\d{2}:\d{2})", "at ", s)
    return s

def apply_widget_i18n(widget, lang="en"):
    try:
        if "text" in widget.keys():
            cur = widget.cget("text")
            if isinstance(cur, str) and cur.strip():
                t_val = tr(cur, lang)
                if t_val != cur:
                    widget.configure(text=t_val)
    except Exception:
        pass
    try:
        for ch in widget.winfo_children():
            apply_widget_i18n(ch, lang)
    except Exception:
        pass
