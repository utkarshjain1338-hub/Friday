import importlib
import pkgutil
from pathlib import Path
from .registry import SkillRegistry


def discover_plugins(registry: SkillRegistry, plugins_package: str = "skills.plugins"):
    package = importlib.import_module(plugins_package)
    package_path = Path(package.__file__).parent

    for finder, name, ispkg in pkgutil.iter_modules([str(package_path)]):
        module_name = f"{plugins_package}.{name}"
        try:
            module = importlib.import_module(module_name)
            # look for attribute `skill` in module
            if hasattr(module, "skill"):
                registry.register(module.skill)
        except Exception:
            continue
