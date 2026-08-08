# SpaceMouse Universal Bridge

Открытый и настраиваемый мост между HID-устройством 3Dconnexion SpaceMouse и
приложениями, официально не поддерживаемыми драйвером 3DxWare. Читает сырые
HID-репорты и превращает 6DoF-отклонения в навигационные жесты (орбита /
панорама / зум) через эмуляцию мыши/клавиатуры.

Полный план разработки, архитектура и дорожная карта — в [`docs/PLAN.md`](docs/PLAN.md).
Правила работы над проектом для Claude Code — в [`CLAUDE.md`](CLAUDE.md).

## Статус

Проект в начальной стадии (Фаза 0 / задача 1 из дорожной карты): собран только
скелет пакета. Функциональность HID-чтения, фильтрации, маппинга и инъекции
ввода будет добавляться по задачам из `docs/PLAN.md`, §6.2.

## Разработка

Пакет `hid` — это ctypes-обёртка над нативной библиотекой hidapi, её нужно
поставить отдельно от pip-пакета:

- **Windows:** `hidapi.dll` обычно уже доступна вместе с `hid`; если импорт
  падает — скачать `hidapi` с https://github.com/libusb/hidapi/releases и
  положить DLL рядом с интерпретатором.
- **Linux (Debian/Ubuntu):** `sudo apt-get install libhidapi-hidraw0`
- **macOS:** `brew install hidapi`

```bash
python -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\activate на Windows
pip install -e ".[dev]"
pytest -q
```

## Определение подключённого устройства

```bash
python -m spacemouse_bridge.device.enumerate
```

Выведет таблицу всех HID-устройств (VID/PID/usage page/производитель/продукт).
Устройства с известными VID 3Dconnexion/Logitech помечаются в колонке Note —
но PID оттуда руками переносится в `device_ids.toml` (см. `CLAUDE.md`), в коде
он не хардкодится.

## Правовой аспект

Проект не использует и не включает SDK или драйверы 3Dconnexion, не использует
их торговые марки в названии продукта. Реверс HID-протокола ради совместимости
опирается на открытые прецеденты (`spacenavd`, `libspnav`, драйверы в ядре Linux).
