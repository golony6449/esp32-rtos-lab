#!/usr/bin/env python3
"""Arduino 스케치 빌드·업로드 진입점.

사용법:
    python tools/build.py <스케치 폴더> [--upload] [--port COM9]
                          [--partition app3M_fat9M_16MB] [--dry-run]

Arduino IDE 2.x에 들어 있는 arduino-cli를 찾아 esp32-s3 보드용으로
컴파일하고, --upload면 같은 빌드 산출물을 보드에 올린다.
표준 라이브러리만 쓰고, subprocess는 인자 리스트로 부른다(shell=False).

비유: Makefile의 진입점 타깃. 빌드 폴더(.build/)는 증분 빌드 캐시다.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

# docs/arduino-board-settings.md의 Tools 설정과 같은 값. FQBN = 보드 설정 프로필.
BASE_FQBN = "esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,FlashSize=16M,PSRAM=opi"

# 이 파일은 <레포>/tools/build.py에 있으므로 부모의 부모가 레포 루트다.
REPO_ROOT = Path(__file__).resolve().parent.parent

# Arduino IDE 2.x가 함께 설치하는 arduino-cli (PATH에 없을 때의 마지막 후보).
IDE_CLI_WINDOWS = Path(
    r"C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"
)

PORT_BUSY_HINT = (
    "포트를 다른 프로그램(Arduino IDE의 Serial Monitor 등)이 잡고 있을 수 있다. "
    "닫고 다시 올린다."
)


def make_fqbn(partition: str | None) -> str:
    """기본 FQBN에 파티션 스킴을 덧붙인다."""
    if partition:
        return BASE_FQBN + ",PartitionScheme=" + partition
    return BASE_FQBN


def find_cli(env: Mapping[str, str] = os.environ) -> Path | None:
    """arduino-cli 실행 파일을 찾는다. 없으면 None."""
    override = env.get("ARDUINO_CLI")
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return candidate

    found = shutil.which("arduino-cli")
    if found:
        return Path(found)

    if sys.platform == "win32" and IDE_CLI_WINDOWS.is_file():
        return IDE_CLI_WINDOWS

    return None


def find_config() -> Path | None:
    """Arduino IDE의 arduino-cli.yaml이 있으면 쓴다.

    IDE와 같은 보드 패키지·라이브러리 위치를 보게 하기 위해서다.
    """
    config = Path.home() / ".arduinoIDE" / "arduino-cli.yaml"
    if config.is_file():
        return config
    return None


def build_commands(
    cli: Path,
    sketch: Path,
    build_dir: Path,
    fqbn: str,
    config: Path | None,
    upload: bool,
    port: str,
) -> list[list[str]]:
    """실행할 명령 목록을 만든다. 모든 원소는 str이다."""
    prefix = [str(cli)]
    if config is not None:
        prefix += ["--config-file", str(config)]

    commands = [
        prefix
        + ["compile", "--fqbn", fqbn, "--build-path", str(build_dir), str(sketch)]
    ]
    if upload:
        commands.append(
            prefix
            + [
                "upload",
                "-p",
                str(port),
                "--fqbn",
                fqbn,
                "--input-dir",
                str(build_dir),
                str(sketch),
            ]
        )
    return commands


def port_busy_hint(output: str) -> str | None:
    """arduino-cli 출력이 포트 점유 문제를 가리키면 한국어 안내를 돌려준다."""
    markers = ("PermissionError", "port doesn't exist", "port is busy")
    if any(marker in output for marker in markers):
        return PORT_BUSY_HINT
    return None


def _run_command(command: list[str]) -> tuple[int, str]:
    """명령을 실행하고 출력을 그대로 흘려보낸다.

    종료 코드와, 안내 판단용으로 모은 출력 전체를 돌려준다.
    """
    print("$ " + " ".join(command), flush=True)
    chunks: list[str] = []
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
        chunks.append(line)
    return process.wait(), "".join(chunks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="arduino-cli로 스케치를 빌드하고(원하면 업로드하고) 종료 코드를 돌려준다."
    )
    parser.add_argument("sketch", help="스케치 폴더 (예: experiments/00_first_task)")
    parser.add_argument("--upload", action="store_true", help="빌드 후 보드에 업로드한다")
    parser.add_argument("--port", default="COM9", help="업로드 포트 (기본: COM9)")
    parser.add_argument(
        "--partition",
        default=None,
        help="PartitionScheme 값 (예: app3M_fat9M_16MB). 생략하면 보드 기본값",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="명령만 출력하고 실행하지 않는다"
    )
    args = parser.parse_args(argv)

    cli = find_cli()
    if cli is None:
        print(
            "arduino-cli를 찾지 못했다. Arduino IDE 2.x를 설치하거나 "
            "환경변수 ARDUINO_CLI에 실행 파일 경로를 넣는다.",
            file=sys.stderr,
        )
        return 2

    sketch = Path(args.sketch)
    build_dir = REPO_ROOT / ".build" / sketch.name
    fqbn = make_fqbn(args.partition)
    commands = build_commands(
        cli, sketch, build_dir, fqbn, find_config(), args.upload, args.port
    )

    if args.dry_run:
        for command in commands:
            print(" ".join(command))
        return 0

    for command in commands:
        code, output = _run_command(command)
        if code != 0:
            hint = port_busy_hint(output)
            if hint:
                print(hint, file=sys.stderr)
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main())
