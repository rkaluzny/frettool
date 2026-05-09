import os
import sys
import json
from typing import List, Optional
from models import ProjectData

def get_base_path():
    """Get the base path for data files - works both in dev and PyInstaller exe"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

class ProjectStore:
    FILEPATH = os.path.join(get_base_path(), "projects.json")

    @staticmethod
    def load_projects() -> List[ProjectData]:
        if not os.path.exists(ProjectStore.FILEPATH):
            return []

        with open(ProjectStore.FILEPATH, "r", encoding="utf-8") as f:
            try:
                raw = json.load(f)
            except Exception as e:
                print(f"Error loading projects.json: {e}")
                raw = []

        projects: List[ProjectData] = []
        needs_migration = False
        for p in raw or []:
            if isinstance(p, dict) and "id" not in p:
                needs_migration = True
            try:
                projects.append(ProjectData.from_dict(p))
            except Exception as e:
                print(f"Error loading project: {e}")
                continue

        if needs_migration:
            ProjectStore.save_all(projects)

        return projects

    @staticmethod
    def save_all(projects: List[ProjectData]) -> None:
        with open(ProjectStore.FILEPATH, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in projects], f, indent=4)

    @staticmethod
    def upsert_project(project: ProjectData) -> None:
        projects = ProjectStore.load_projects()

        idx = None
        for i, p in enumerate(projects):
            if p.id == project.id:
                idx = i
                break

        if idx is None:
            for i, p in enumerate(projects):
                if (p.name == project.name) and (p.created_at == project.created_at):
                    idx = i
                    project.id = p.id
                    break

        if idx is None:
            for i, p in enumerate(projects):
                if p.name == project.name:
                    idx = i
                    project.id = p.id
                    break

        if idx is None:
            projects.append(project)
        else:
            projects[idx] = project

        ProjectStore.save_all(projects)

    @staticmethod
    def delete_project(project_id: str) -> None:
        projects = ProjectStore.load_projects()
        projects = [p for p in projects if p.id != project_id]
        ProjectStore.save_all(projects)

    @staticmethod
    def rename_project(project_id: str, new_name: str) -> None:
        projects = ProjectStore.load_projects()
        for p in projects:
            if p.id == project_id:
                p.name = new_name
                break
        ProjectStore.save_all(projects)
