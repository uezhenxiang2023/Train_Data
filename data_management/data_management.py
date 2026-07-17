"""Minimal Hiero project creation helpers.

Run this module from Hiero or Nuke Studio's Script Editor.  The ``hiero``
package is provided by the host application and is not available to a normal
Python interpreter.
"""

from __future__ import annotations

from pathlib import Path

try:
    import hiero.core
except ImportError as error:
    raise RuntimeError(
        "data_management.py must run inside Hiero or Nuke Studio; "
        "hiero.core is provided by the host application."
    ) from error

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


def main() -> None:
    """Create an unsaved project for a quick interactive smoke test."""
    create_project()
    print("Created an unsaved Hiero project.")


if __name__ == "__main__":
    main()
