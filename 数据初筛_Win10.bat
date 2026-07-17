@echo off
setlocal EnableExtensions
chcp 65001 >nul

rem 此文件可直接复制到任意 <项目代码>\<集号(场号)> 目录后双击运行。
set "SCENE_DIR=%~dp0"
set "TEMP_PY=%TEMP%\data_filter_%RANDOM%_%RANDOM%.py"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$lines = Get-Content -LiteralPath '%~f0'; $marker = [Array]::IndexOf([string[]]$lines, '# ==PYTHON=='); if ($marker -lt 0) { exit 1 }; $lines[($marker + 1)..($lines.Length - 1)] | Set-Content -LiteralPath '%TEMP_PY%' -Encoding UTF8"
if errorlevel 1 (
    echo 无法准备数据初筛程序。
    goto :error
)

py -3 "%TEMP_PY%" "%SCENE_DIR%"
if errorlevel 1 (
    python "%TEMP_PY%" "%SCENE_DIR%"
)
if errorlevel 1 (
    echo.
    echo 未找到可用的 Python 3，或数据目录不符合规范。
    echo 请安装 Python 3 后重试，并确认脚本位于 ^<项目代码^>\^<三位集号(场号)^> 目录。
    goto :error
)

del "%TEMP_PY%" >nul 2>nul
echo.
echo 数据初筛完成。
pause
exit /b 0

:error
del "%TEMP_PY%" >nul 2>nul
echo.
pause
exit /b 1

# ==PYTHON==
from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")
EPISODE_PATTERN = re.compile(r"^\d{3}$")
SHOT_PATTERN = re.compile(r"^\d{3}(?:\d{3})?$")
VERSION_PATTERN = re.compile(r"(?:^|[_-])v(\d+)(?=$|[_\.\-])", re.IGNORECASE)
TEMPORARY_SUFFIXES = {".autosave", ".bak", ".tmp", ".swp"}


def parse_scene_directory(scene_directory: Path) -> tuple[str, str, Path]:
    scene_directory = scene_directory.resolve()
    if not scene_directory.is_dir():
        raise ValueError(f"集（场）目录不存在：{scene_directory}")
    project_code = scene_directory.parent.name
    episode = scene_directory.name
    if not PROJECT_CODE_PATTERN.fullmatch(project_code):
        raise ValueError(f"项目代码应为三位大写字母，当前为：{project_code}")
    if not EPISODE_PATTERN.fullmatch(episode):
        raise ValueError(f"集号（场号）应为三位数字，当前为：{episode}")
    return project_code, episode, scene_directory


def is_temporary_file(path: Path) -> bool:
    return (
        any(path.name.lower().endswith(suffix) for suffix in TEMPORARY_SUFFIXES)
        or path.name.startswith((".", "~$"))
    )


def version_number(path: Path) -> int | None:
    matches = VERSION_PATTERN.findall(path.stem)
    return int(matches[-1]) if matches else None


def highest_version_task_file(task_directory: Path) -> Path | None:
    candidates: list[tuple[int, Path]] = []
    for path in task_directory.iterdir():
        if not path.is_file() or is_temporary_file(path):
            continue
        version = version_number(path)
        if version is not None:
            candidates.append((version, path))
    if not candidates:
        return None
    highest_version = max(version for version, _ in candidates)
    return min(
        (path for version, path in candidates if version == highest_version),
        key=lambda path: path.name.lower(),
    )


def main() -> int:
    try:
        project_code, episode, scene_directory = parse_scene_directory(Path(sys.argv[1]))
    except (IndexError, ValueError) as error:
        print(f"错误：{error}")
        return 1

    latest_files: list[Path] = []
    shot_directories = sorted(
        (path for path in scene_directory.iterdir() if path.is_dir() and SHOT_PATTERN.fullmatch(path.name)),
        key=lambda path: (int(path.name), path.name),
    )
    for shot_directory in shot_directories:
        task_directory = shot_directory / "cmp" / "task"
        if task_directory.is_dir():
            latest_file = highest_version_task_file(task_directory)
            if latest_file:
                latest_files.append(latest_file)

    output_path = scene_directory / f"{project_code}_{episode}_DataFilter.txt"
    output_path.write_text(
        "\n".join(path.name for path in latest_files) + ("\n" if latest_files else ""),
        encoding="utf-8",
    )
    print(f"已生成：{output_path}")
    print(f"共提取 {len(latest_files)} 个镜头的最高版本合成工程文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
