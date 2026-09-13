"""Find the latest compositing tasks and review media in a scene directory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,31}$")
EPISODE_PATTERN = re.compile(r"^\d{1,3}$")
SHOT_PATTERN = re.compile(r"^(?:\d{3}(?:\d{3})?|C\d{2,3})$", re.IGNORECASE)
VERSION_PATTERN = re.compile(r"(?:^|[_-])v(\d+)(?=$|[_\.\-])", re.IGNORECASE)
FRAME_PATTERN = re.compile(r"^(.*?)(\d+)$")
TEMPORARY_SUFFIXES = {".autosave", ".bak", ".tmp", ".swp"}
IMAGE_SEQUENCE_EXTENSIONS = {".dpx", ".exr", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
MEDIA_DIRECTORIES = (
    ("cmp", "img"),
    ("cmp", "images"),
    ("cmp", "preview"),
    ("editorial", "plate"),
    ("edtorial", "plate"),
    ("rotopaint", "preview"),
)


@dataclass(frozen=True)
class SceneLocation:
    project_code: str
    episode: str
    directory: Path


def parse_scene_directory(scene_directory: Path) -> SceneLocation:
    """Validate a scene directory and locate its project code."""
    scene_directory = scene_directory.resolve()
    if not scene_directory.is_dir():
        raise ValueError("Scene directory does not exist: {}".format(scene_directory))
    if not EPISODE_PATTERN.fullmatch(scene_directory.name):
        raise ValueError(
            "Scene directory must have a one- to three-digit name: {}".format(
                scene_directory
            )
        )
    episode = scene_directory.name.zfill(3)

    project_code = next(
        (
            parent.name
            for parent in scene_directory.parents
            if PROJECT_CODE_PATTERN.fullmatch(parent.name)
        ),
        None,
    )
    if project_code is None:
        raise ValueError(
            "No uppercase project code found above: {}".format(scene_directory)
        )
    return SceneLocation(project_code, episode, scene_directory)


def is_temporary_file(path: Path) -> bool:
    return (
        any(path.name.lower().endswith(suffix) for suffix in TEMPORARY_SUFFIXES)
        or path.name.startswith((".", "~$"))
    )


def version_number(path: Path) -> int:
    """Return the final v### token, or -1 for files without a version token."""
    matches = VERSION_PATTERN.findall(path.stem)
    return int(matches[-1]) if matches else -1


def latest_file(directory: Path, extension: str) -> Path | None:
    """Select the highest-version matching file in one directory."""
    if not directory.is_dir():
        return None
    candidates = [
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.lower() == extension
        and not is_temporary_file(path)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda path: (-version_number(path), path.name.lower()))


def image_sequence_key(path: Path) -> tuple[str, str, int]:
    match = FRAME_PATTERN.match(path.stem)
    if match is None:
        return (path.stem.lower(), path.suffix.lower(), 0)
    prefix, frame = match.groups()
    return (prefix.lower(), path.suffix.lower(), len(frame))


def image_sequence_sort_key(path: Path) -> tuple[int, str]:
    match = FRAME_PATTERN.match(path.stem)
    frame = int(match.group(2)) if match else -1
    return (frame, path.name.lower())


def image_sequence_heads(directory: Path) -> list[Path]:
    """Return the first existing frame for each image sequence in a directory."""
    if not directory.is_dir():
        return []
    sequences: dict[tuple[str, str, int], list[Path]] = {}
    for path in directory.iterdir():
        if (
            path.is_file()
            and path.suffix.lower() in IMAGE_SEQUENCE_EXTENSIONS
            and FRAME_PATTERN.match(path.stem)
            and not is_temporary_file(path)
        ):
            sequences.setdefault(image_sequence_key(path), []).append(path)
    return [
        min(paths, key=image_sequence_sort_key)
        for _, paths in sorted(sequences.items(), key=lambda item: item[0])
    ]


def editorial_plate_sequence_heads(plate_directory: Path) -> list[Path]:
    """Return sequence head frames from first-level folders under a plate folder."""
    if not plate_directory.is_dir():
        return []
    heads: list[Path] = []
    for child in sorted(
        (path for path in plate_directory.iterdir() if path.is_dir()),
        key=lambda path: path.name.lower(),
    ):
        heads.extend(image_sequence_heads(child))
    return heads


def shot_directories(scene_directory: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in scene_directory.iterdir()
            if path.is_dir() and SHOT_PATTERN.fullmatch(path.name)
        ),
        key=shot_sort_key,
    )


def shot_sort_key(path: Path) -> tuple[int, int, str]:
    if path.name.isdigit():
        return (0, int(path.name), path.name)
    return (1, int(path.name[1:]), path.name.lower())


def collect_latest_cmp_tasks(scene_directory: Path) -> list[Path]:
    """Return the highest-version .nk file from every shot's cmp/task folder."""
    selected: list[Path] = []
    for shot_directory in shot_directories(scene_directory):
        task = latest_file(shot_directory / "cmp" / "task", ".nk")
        if task is not None:
            selected.append(task)
    return selected


def write_data_filter_file(
    scene_directory: Path,
    tasks: list[Path] | None = None,
    output_directory: Path | None = None,
) -> Path:
    """Write the selected compositing filenames to the requested output directory."""
    scene = parse_scene_directory(scene_directory)
    if tasks is None:
        tasks = collect_latest_cmp_tasks(scene.directory)
    if output_directory is None:
        output_directory = scene.directory
    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / "{}_{}_DataFilter.txt".format(
        scene.project_code, scene.episode
    )
    output_path.write_text(
        "\n".join(task.name for task in tasks) + ("\n" if tasks else ""),
        encoding="utf-8",
    )
    return output_path


def project_stem(task_file: Path) -> str | None:
    """Return the filename portion before the compositing process token."""
    match = re.match(r"(.+?)_cmp(?:_|$)", task_file.stem, re.IGNORECASE)
    return match.group(1) if match else None


def latest_review_media(task_file: Path) -> list[Path]:
    """Return selected review media from each configured folder."""
    shot_directory = task_file.parents[2]
    media: list[Path] = []
    seen_categories: set[str] = set()
    for process, attribute in MEDIA_DIRECTORIES:
        if process in {"editorial", "edtorial"}:
            category = "editorial"
        elif process == "cmp" and attribute in {"img", "images"}:
            category = "cmp/images"
        else:
            category = "{}/{}".format(process, attribute)
        if category in seen_categories:
            continue
        found: list[Path] = []
        candidate = latest_file(shot_directory / process / attribute, ".mov")
        if candidate is not None:
            found.append(candidate)
        if process in {"editorial", "edtorial"} and attribute == "plate":
            found.extend(
                editorial_plate_sequence_heads(shot_directory / process / attribute)
            )
        if found:
            media.extend(found)
            seen_categories.add(category)
    return media
