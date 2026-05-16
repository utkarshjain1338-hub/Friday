"""Improved plugin loader with discovery and management."""
import asyncio
import importlib.util
import os
from pathlib import Path
from typing import List, Optional, Callable
from loguru import logger

from .registry import SkillRegistry, BaseSkill


class PluginLoader:
    """Loads and manages plugins/skills."""

    def __init__(self, registry: Optional[SkillRegistry] = None):
        """
        Initialize plugin loader.

        Args:
            registry: Skill registry to register plugins
        """
        self.registry = registry or SkillRegistry()
        self.loaded_plugins: List[str] = []
        self.failed_plugins: List[tuple] = []  # (name, error)

    def discover_plugins(self, plugin_dir: Optional[str] = None) -> List[str]:
        """
        Discover plugins in directory.

        Args:
            plugin_dir: Directory to search (defaults to skills/plugins)

        Returns:
            List of discovered plugin names
        """
        if plugin_dir is None:
            plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")

        if not os.path.exists(plugin_dir):
            logger.warning(f"Plugin directory not found: {plugin_dir}")
            return []

        discovered = []
        for file_path in Path(plugin_dir).glob("*_skill.py"):
            try:
                plugin_name = file_path.stem
                discovered.append(plugin_name)
                logger.debug(f"Discovered plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error discovering plugin {file_path}: {e}")

        return discovered

    def load_plugin(self, plugin_name: str, plugin_dir: Optional[str] = None) -> bool:
        """
        Load a single plugin.

        Args:
            plugin_name: Name of plugin module
            plugin_dir: Directory containing plugins

        Returns:
            True if loaded successfully
        """
        if plugin_dir is None:
            plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")

        try:
            plugin_path = os.path.join(plugin_dir, f"{plugin_name}.py")

            if not os.path.exists(plugin_path):
                logger.warning(f"Plugin file not found: {plugin_path}")
                return False

            # Dynamically import module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load spec for {plugin_name}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find skill class in module
            skill_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseSkill)
                    and attr != BaseSkill
                ):
                    skill_class = attr
                    break

            if skill_class is None:
                logger.warning(f"No BaseSkill subclass found in {plugin_name}")
                return False

            # Instantiate and register
            skill_instance = skill_class()
            self.registry.register(skill_instance)
            self.loaded_plugins.append(plugin_name)
            logger.info(f"Loaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            self.failed_plugins.append((plugin_name, str(e)))
            return False

    async def load_plugins_async(
        self, plugin_dir: Optional[str] = None, on_load: Optional[Callable] = None
    ) -> int:
        """
        Load all discovered plugins asynchronously.

        Args:
            plugin_dir: Directory containing plugins
            on_load: Callback for each loaded plugin

        Returns:
            Number of plugins loaded
        """
        discovered = self.discover_plugins(plugin_dir)
        logger.info(f"Loading {len(discovered)} discovered plugins")

        for plugin_name in discovered:
            # Run loading in thread to avoid blocking
            success = await asyncio.to_thread(self.load_plugin, plugin_name, plugin_dir)
            if success and on_load:
                if asyncio.iscoroutinefunction(on_load):
                    await on_load(plugin_name)
                else:
                    on_load(plugin_name)

        return len(self.loaded_plugins)

    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugins."""
        return self.loaded_plugins.copy()

    def get_failed_plugins(self) -> List[tuple]:
        """Get list of failed plugin loads with errors."""
        return self.failed_plugins.copy()

    def get_registry(self) -> SkillRegistry:
        """Get the skill registry."""
        return self.registry

    async def reload_plugins(self, plugin_dir: Optional[str] = None) -> int:
        """
        Reload all plugins.

        Args:
            plugin_dir: Directory containing plugins

        Returns:
            Number of plugins loaded
        """
        self.loaded_plugins.clear()
        self.failed_plugins.clear()
        return await self.load_plugins_async(plugin_dir)

    def get_statistics(self) -> dict:
        """Get loader statistics."""
        return {
            "loaded": len(self.loaded_plugins),
            "failed": len(self.failed_plugins),
            "total_skills": len(self.registry.all_skills()),
            "loaded_plugins": self.loaded_plugins,
            "failed_plugins": self.failed_plugins,
        }
