"""`tools/build.py` 단위 테스트.

보드나 arduino-cli 없이 돈다. tools/build.py는 실행 파일이 아니라
`python tools/build.py`로 부르는 스크립트라 import 경로에 없으므로,
파일 경로로 직접 불러온다. (PyPI의 `build` 패키지와 이름이 겹치지 않게
모듈 이름은 `lab_build`로 둔다.)
"""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def lab_build():
    spec = importlib.util.spec_from_file_location(
        "lab_build", REPO_ROOT / "tools" / "build.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_make_fqbn_without_partition(lab_build):
    assert lab_build.make_fqbn(None) == lab_build.BASE_FQBN
    assert "PartitionScheme" not in lab_build.make_fqbn(None)


def test_make_fqbn_with_partition(lab_build):
    fqbn = lab_build.make_fqbn("app3M_fat9M_16MB")
    assert fqbn == lab_build.BASE_FQBN + ",PartitionScheme=app3M_fat9M_16MB"
    assert fqbn.endswith(",PartitionScheme=app3M_fat9M_16MB")


def test_build_commands_compile_only(lab_build, tmp_path):
    commands = lab_build.build_commands(
        tmp_path / "arduino-cli.exe",
        tmp_path / "00_first_task",
        tmp_path / ".build" / "00_first_task",
        lab_build.BASE_FQBN,
        tmp_path / "arduino-cli.yaml",
        False,
        "COM9",
    )
    assert len(commands) == 1
    command = commands[0]
    assert all(isinstance(part, str) for part in command)
    assert "compile" in command
    assert command[command.index("--fqbn") + 1] == lab_build.BASE_FQBN
    assert "--build-path" in command
    assert str(tmp_path / "00_first_task") in command
    assert "--config-file" in command


def test_build_commands_upload_and_no_config(lab_build, tmp_path):
    sketch = tmp_path / "00_first_task"
    build_dir = tmp_path / ".build" / "00_first_task"
    commands = lab_build.build_commands(
        tmp_path / "arduino-cli.exe",
        sketch,
        build_dir,
        lab_build.BASE_FQBN,
        None,
        True,
        "COM9",
    )
    assert len(commands) == 2
    compile_command, upload_command = commands
    assert "--config-file" not in compile_command
    assert "upload" in upload_command
    assert upload_command[upload_command.index("-p") + 1] == "COM9"
    assert upload_command[upload_command.index("--input-dir") + 1] == str(build_dir)
    assert "--config-file" not in upload_command
    assert all(isinstance(part, str) for command in commands for part in command)


def test_port_busy_hint_detects_permission_error(lab_build):
    assert lab_build.port_busy_hint("ClearCommError failed: PermissionError(13, ...)")


def test_port_busy_hint_detects_missing_port(lab_build):
    hint = lab_build.port_busy_hint("Could not open COM9, the port doesn't exist")
    assert hint is not None
    assert "Serial Monitor" in hint


def test_port_busy_hint_detects_busy_port(lab_build):
    assert lab_build.port_busy_hint("Error: the port is busy") is not None


def test_port_busy_hint_ignores_normal_output(lab_build):
    assert lab_build.port_busy_hint("Sketch uses 1234 bytes") is None


def test_find_cli_reads_env_override(lab_build, tmp_path):
    fake_cli = tmp_path / "arduino-cli.exe"
    fake_cli.write_text("", encoding="utf-8")
    assert lab_build.find_cli({"ARDUINO_CLI": str(fake_cli)}) == fake_cli


def test_main_dry_run_prints_compile_command(lab_build, tmp_path, monkeypatch, capsys):
    fake_cli = tmp_path / "arduino-cli.exe"
    fake_cli.write_text("", encoding="utf-8")
    monkeypatch.setenv("ARDUINO_CLI", str(fake_cli))
    sketch = tmp_path / "00_first_task"
    sketch.mkdir()

    result = lab_build.main([str(sketch), "--dry-run"])

    assert result == 0
    output = capsys.readouterr().out
    assert "compile" in output
    assert str(sketch) in output
