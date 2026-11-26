# Регламент создания и применения автопатчей (HomeGrid Backup)

## 1. Контекст проекта и целевые платформы
* **Структура репозитория:** `main.py`, `core/`, `gui/`, `console/`, `mobile/`, `.github/workflows/*.yml`.
* **Кроссплатформенность:** Windows 7 (32-bit x86), Windows 10/11, Linux/Ubuntu, macOS и Android.
* **Жёсткое ограничение синтаксиса — Python 3.8:** сборка `build_windows7.yml` компилируется на Python 3.8.10 (x86). Запрещены вложенные однотипные кавычки в f-строках (PEP 701). Внутри `f"..."` использовать только одинарные кавычки `'...'`.
* **Системные фолбэки:** `wmic` помимо `Get-NetAdapter` для Windows 7; `parent=self.root` для `filedialog` на Ubuntu/macOS.

## 2. Правила оформления патча (PowerShell)
* **Обёртка запуска:** `@' ... '@ | python -`.
* **Защита от обрезки буфера:** строки до 140–160 символов, объём части до 6 КБ, без `"""` и `'''` внутри скрипта, кириллица через `\uXXXX`, без `input(...)`.

## 3. Надёжность и проверки
* **Атомарность и бэкап:** проверка всех якорей в памяти до записи, бэкап в `.patch_bak/`, запись в UTF-8 без BOM (`newline="\n"`).
* **Валидация:** `ast.parse(src, filename=fp, feature_version=(3, 8))` и `py_compile.compile(fp, doraise=True)`.

## 4. Обязательное обновление версии и GitHub Actions
* **Локальный конфиг:** при каждом функциональном патче повышать `SCRIPT_VER` (+0.01) и обновлять `BUILD_DATE` в `core/config.py`.
* **Синхронизация с GitHub:** одновременно обновлять номер версии во всех файлах сборки `.github/workflows/*.yml` (параметры `--file-version`, `--product-version`, `/DAppVersion`, `tag_name`, `name` релиза), а также в `.spec` / `.iss` файлах.
* **Целостность YAML:** при изменении `.github/workflows/*.yml` сохранять строго UTF-8 без BOM, без отступа в первой строке `name:` и с проверкой шага `Publish GitHub Release`.
