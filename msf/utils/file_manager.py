"""MSF Project File Manager Utility.

Provides ProjectFileManager for managing directory layouts and persisting/loading
domain contract dataclasses as JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Type, TypeVar

from msf.contracts.models import BaseContract, ProjectState

T = TypeVar("T", bound=BaseContract)


class ProjectFileManager:
    """Manages project directory structures and JSON persistence of domain models."""

    def __init__(self, base_dir: str | Path = "./output"):
        self.base_dir = Path(base_dir).resolve()

    def get_project_dir(self, project_id: str) -> Path:
        """Get root path for a given project ID."""
        return self.base_dir / project_id

    def create_project_dirs(self, project_id: str) -> dict[str, Path]:
        """Create standard directory hierarchy for a project."""
        proj_dir = self.get_project_dir(project_id)
        dirs = {
            "root": proj_dir,
            "assets": proj_dir / "assets",
            "audio": proj_dir / "audio",
            "scenes": proj_dir / "scenes",
            "reviews": proj_dir / "reviews",
            "output": proj_dir / "output",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        return dirs

    def save_contract(
        self, project_id: str, relative_path: str | Path, contract: BaseContract
    ) -> Path:
        """Serialize and save any domain model contract to JSON within the project directory."""
        proj_dir = self.get_project_dir(project_id)
        target_path = proj_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        data = contract.to_dict()
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return target_path

    def load_contract(
        self, project_id: str, relative_path: str | Path, contract_cls: Type[T]
    ) -> T:
        """Load and deserialize a JSON file into a specific domain model contract class."""
        proj_dir = self.get_project_dir(project_id)
        target_path = proj_dir / relative_path
        if not target_path.exists():
            raise FileNotFoundError(f"Contract file not found: {target_path}")
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return contract_cls.from_dict(data)

    def save_project_state(self, state: ProjectState) -> Path:
        """Convenience method to save root ProjectState."""
        self.create_project_dirs(state.project_id)
        return self.save_contract(state.project_id, "state.json", state)

    def load_project_state(self, project_id: str) -> ProjectState:
        """Convenience method to load root ProjectState."""
        return self.load_contract(project_id, "state.json", ProjectState)
