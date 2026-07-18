"""Create Hiero projects from the latest compositing tasks in a scene."""

from __future__ import annotations

from pathlib import Path

from scene_filter import (
    collect_latest_cmp_tasks,
    latest_review_media,
    project_stem,
    write_data_filter_file,
)

import os

try:
    import hiero.core
except ImportError as error:
    raise RuntimeError(
        "data_management.py must run inside Hiero or Nuke Studio; "
        "hiero.core is provided by the host application."
    ) from error


def report(message: str) -> None:
    """Write progress to both the launch terminal and the persistent log."""
    print(message, flush=True)
    log_path = os.environ.get("HIERO_BUILDER_LOG")
    if log_path:
        destination = Path(log_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as log_file:
            log_file.write(message + "\n")

def create_project(save_path: str | Path | None = None):
    """Create a new Hiero project and optionally save it as a .hrox file.

    Args:
        save_path: Destination for the new project. When omitted, the project
            remains unsaved in the current Hiero session.
    """
    if save_path is not None:
        destination = Path(save_path).expanduser().resolve()

        if destination.suffix.lower() != ".hrox":
            raise ValueError("Hiero project files must use the .hrox extension.")
        if destination.exists():
            raise FileExistsError(
                "Refusing to overwrite existing Hiero project: {}".format(
                    destination
                )
            )
        destination.parent.mkdir(parents=True, exist_ok=True)

    project = hiero.core.newProject()

    if save_path is not None:
        project.saveAs(str(destination))

    return project


def import_review_media(project, media_paths: list[Path]) -> list[Path]:
    """Import media directly into the project's root Clips Bin."""
    imported: list[Path] = []
    clips_bin = project.clipsBin()
    for media_path in media_paths:
        report("Importing: {}".format(media_path))
        clips_bin.createClip(media_path.as_posix())
        imported.append(media_path)
    return imported


def create_scene_projects(scene_directory: str | Path, output_directory: str | Path) -> dict:
    """Build one saved Hiero project per latest compositing task.

    Existing .hrox files are skipped to protect prior work. A media-import
    failure only affects its own project and is reported in the result.
    """
    scene_directory = Path(scene_directory).resolve()
    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    report("Filtering scene: {}".format(scene_directory))
    tasks = collect_latest_cmp_tasks(scene_directory)
    filter_file = write_data_filter_file(scene_directory, tasks, output_directory)
    result = {"filter_file": filter_file, "created": [], "skipped": [], "failed": []}

    for task_file in tasks:
        stem = project_stem(task_file)
        if stem is None:
            result["skipped"].append((task_file, "missing _cmp_ process token"))
            continue

        project_path = output_directory / "{}.hrox".format(stem)
        if project_path.exists():
            result["skipped"].append((task_file, "project already exists"))
            continue

        try:
            report("Creating project: {}".format(project_path))
            project = create_project()
            imported = import_review_media(project, latest_review_media(task_file))
            report("Saving project: {}".format(project_path))
            project.saveAs(str(project_path))
            result["created"].append((project_path, imported))
        except Exception as error:
            result["failed"].append((task_file, str(error)))

    return result


def main() -> None:
    """Create an unsaved project for a quick interactive smoke test."""
    create_project()
    print("Created an unsaved Hiero project.")


if __name__ == "__main__":
    main()
