"""按集（场）目录汇总各镜头最高版本的合成工程文件。

目录约定::

    <项目代码>/<集号或场号>/<镜头号>/cmp/task/<工程文件>

例如在 ``TLP/002`` 目录中执行 ``python /path/to/data_filter.py``，会生成
``TLP_002_DataFilter.txt``。也可以显式传入集（场）目录：
``python data_filter.py /show/TLP/002``。
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")
EPISODE_PATTERN = re.compile(r"^\d{3}$")
SHOT_PATTERN = re.compile(r"^\d{3}(?:\d{3})?$")
VERSION_PATTERN = re.compile(r"(?:^|[_-])v(\d+)(?=$|[_\.\-])", re.IGNORECASE)
TEMPORARY_SUFFIXES = {".autosave", ".bak", ".tmp", ".swp"}

# 用于后续扩展数据初筛时复用的流程与数据属性释义。
PROCESS_CODE_MEANINGS = {
    "ani": "动画",
    "cmp": "合成",
    "editorial": "剪辑",
    "edtorial": "剪辑（editorial 的常见拼写变体）",
    "rotopaint": "擦除",
}
DATA_ATTRIBUTE_MEANINGS = {
    "img": "渲染结构",
    "images": "渲染结构",
    "task": "工程文件",
}


@dataclass(frozen=True)
class SceneLocation:
    """从集（场）目录识别出的项目、集（场）信息。"""

    project_code: str
    episode: str
    directory: Path


def parse_scene_directory(scene_directory: Path) -> SceneLocation:
    """验证并解析 ``<项目代码>/<三位集号>`` 集（场）目录。"""
    scene_directory = scene_directory.resolve()
    if not scene_directory.is_dir():
        raise ValueError(f"集（场）目录不存在：{scene_directory}")

    project_code = scene_directory.parent.name
    episode = scene_directory.name
    if not PROJECT_CODE_PATTERN.fullmatch(project_code):
        raise ValueError(f"项目代码应为三位大写字母，当前为：{project_code}")
    if not EPISODE_PATTERN.fullmatch(episode):
        raise ValueError(f"集号（场号）应为三位数字，当前为：{episode}")
    return SceneLocation(project_code=project_code, episode=episode, directory=scene_directory)


def is_temporary_file(path: Path) -> bool:
    """排除 Nuke autosave、备份和编辑器临时文件。"""
    return (
        any(path.name.lower().endswith(suffix) for suffix in TEMPORARY_SUFFIXES)
        or path.name.startswith((".", "~$"))
    )


def version_number(path: Path) -> int | None:
    """取得文件名中的版本号，例如 ``*_v001.nk`` 返回 1。"""
    matches = VERSION_PATTERN.findall(path.stem)
    return int(matches[-1]) if matches else None


def shot_sort_key(path: Path) -> tuple[int, str]:
    return (int(path.name), path.name)


def highest_version_task_file(task_directory: Path) -> Path | None:
    """返回 task 目录中版本最高的正式工程文件。

    同一最高版本有多个文件时，按文件名不区分大小写排序，稳定地选择第一个。
    """
    candidates: list[tuple[int, str, Path]] = []
    for path in task_directory.iterdir():
        if not path.is_file() or is_temporary_file(path):
            continue
        version = version_number(path)
        if version is not None:
            candidates.append((version, path.name.lower(), path))
    if not candidates:
        return None
    highest_version = max(item[0] for item in candidates)
    return min(
        (item[2] for item in candidates if item[0] == highest_version),
        key=lambda path: path.name.lower(),
    )


def collect_latest_cmp_tasks(scene_directory: Path) -> list[Path]:
    """收集该集（场）全部有效镜头的最高版本 ``cmp/task`` 工程文件。"""
    selected: list[Path] = []
    shot_directories = sorted(
        (path for path in scene_directory.iterdir() if path.is_dir() and SHOT_PATTERN.fullmatch(path.name)),
        key=shot_sort_key,
    )
    for shot_directory in shot_directories:
        task_directory = shot_directory / "cmp" / "task"
        if not task_directory.is_dir():
            continue
        latest_file = highest_version_task_file(task_directory)
        if latest_file:
            selected.append(latest_file)
    return selected


def write_data_filter_file(scene_directory: Path) -> Path:
    """生成 ``<项目代码>_<集号>_DataFilter.txt`` 并返回其路径。"""
    scene = parse_scene_directory(scene_directory)
    output_path = scene.directory / f"{scene.project_code}_{scene.episode}_DataFilter.txt"
    filenames = [path.name for path in collect_latest_cmp_tasks(scene.directory)]
    output_path.write_text("\n".join(filenames) + ("\n" if filenames else ""), encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="提取当前集（场）所有镜头 cmp/task 中版本最高的工程文件名。"
    )
    parser.add_argument(
        "scene_directory",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="集（场）目录；省略时使用当前目录。",
    )
    args = parser.parse_args(argv)
    try:
        output_path = write_data_filter_file(args.scene_directory)
    except ValueError as error:
        parser.error(str(error))

    print(f"已生成：{output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
