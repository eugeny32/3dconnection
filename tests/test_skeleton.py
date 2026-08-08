import spacemouse_bridge
from spacemouse_bridge.app.cli import main


def test_package_importable():
    assert spacemouse_bridge.__version__ == "0.1.0"


def test_cli_main_runs(capsys):
    main([])
    captured = capsys.readouterr()
    assert "spacemouse-bridge" in captured.out
