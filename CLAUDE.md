# SpaceMouse Universal Bridge

## Контекст
Мост между HID-устройством 3Dconnexion SpaceMouse и приложениями без официальной
поддержки. Реализация — Python 3.11, Windows-first.

## Железные правила
- Никаких обращений к SDK или службам 3Dconnexion. Только сырой HID.
- Слой инъекции — строго за интерфейсом Injector. Никаких вызовов win32 вне inject/win32.py.
- Любая новая логика фильтрации/маппинга должна быть покрыта тестом на записанном дампе.
- Не хардкодить PID устройств: только через конфиг device_ids.toml.
- Все величины движения — float до самого SendInput.

## Команды
- `python -m spacemouse_bridge.app.cli --dump` — сырые репорты
- `python -m spacemouse_bridge.app.cli --viz` — визуализация осей
- `python -m spacemouse_bridge.app.cli --profile blender`
- `pytest -q`

## Не делать
- Не запускать реальную инъекцию ввода в тестах — только FakeInjector.
- Не добавлять GUI-зависимости до фазы 4.

## План
Полный план разработки — в `docs/PLAN.md`.
