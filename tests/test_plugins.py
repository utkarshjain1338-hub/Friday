import asyncio
from skills.registry import SkillRegistry
from skills.loader import discover_plugins


def test_discover_and_run():
    registry = SkillRegistry()
    discover_plugins(registry)
    skills = registry.all_skills()
    print("Discovered skills:", [s.name for s in skills])
    if skills:
        # run the first skill's execute if async
        skill = skills[0]
        if hasattr(skill, "execute"):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(skill.execute("test", {}))
            print("Skill result:", result)


if __name__ == "__main__":
    test_discover_and_run()
