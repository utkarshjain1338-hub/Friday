import subprocess
import psutil

APP_SHORTCUTS = {
    "firefox": ["firefox"],
    "code": ["code"],
    "terminal": ["gnome-terminal"],
    "browser": ["firefox"],
    "files": ["nautilus"],
}


def open_application(app_name: str) -> str:
    app_name = app_name.lower().strip()
    if app_name not in APP_SHORTCUTS:
        return f"I do not have a launcher configured for '{app_name}'."

    try:
        subprocess.Popen(APP_SHORTCUTS[app_name])
        return f"Launching {app_name}."
    except FileNotFoundError:
        return f"Application '{app_name}' is not installed or not found in PATH."
    except Exception as exc:
        return f"Could not launch '{app_name}': {exc}"


def kill_process(process_name: str) -> str:
    process_name = process_name.lower().strip()
    matches = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        name = proc.info.get("name") or ""
        cmdline = " ".join(proc.info.get("cmdline") or [])
        if process_name in name.lower() or process_name in cmdline.lower():
            try:
                proc.kill()
                matches.append(f"{name} ({proc.pid})")
            except Exception:
                pass

    if not matches:
        return f"No processes matching '{process_name}' were found."
    return f"Killed processes: {', '.join(matches)}"


def list_processes(limit: int = 10) -> str:
    processes = []
    for proc in psutil.process_iter(["pid", "name"]):
        name = proc.info.get("name") or ""
        processes.append((proc.info["pid"], name))

    processes = sorted(processes, key=lambda item: item[0])[:limit]
    return "\n".join(f"{pid}: {name}" for pid, name in processes)


def focus_window(window_hint: str) -> str:
    return "Window focus support will be added in a later phase."
