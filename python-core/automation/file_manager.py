import shutil
from pathlib import Path


def list_home() -> str:
    home = Path.home()
    return '\n'.join(sorted(str(path.name) for path in home.iterdir()))


def search_files(query: str, root: str = None) -> str:
    root_path = Path(root or Path.home())
    if not query:
        return "Please provide a filename or pattern to search for."

    matches = []
    for path in root_path.rglob("*"):
        if query.lower() in path.name.lower():
            matches.append(str(path))
            if len(matches) >= 30:
                break

    return "\n".join(matches) if matches else f"No files found matching '{query}'."


def create_folder(path: str) -> str:
    target = Path(path).expanduser()
    if target.exists():
        return f"The folder '{target}' already exists."

    try:
        target.mkdir(parents=True, exist_ok=True)
        return f"Created folder '{target}'."
    except Exception as exc:
        return f"Could not create folder '{target}': {exc}"


def move_file(source: str, destination: str) -> str:
    src = Path(source).expanduser()
    dst = Path(destination).expanduser()

    if not src.exists():
        return f"Source path '{src}' does not exist."

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"Moved '{src}' to '{dst}'."
    except Exception as exc:
        return f"Could not move '{src}' to '{dst}': {exc}"


def delete_path(path: str) -> str:
    target = Path(path).expanduser()
    if not target.exists():
        return f"The path '{target}' does not exist."

    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return f"Deleted '{target}'."
    except Exception as exc:
        return f"Could not delete '{target}': {exc}"
