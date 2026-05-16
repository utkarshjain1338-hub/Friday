import asyncio
from core.router import FridayRouter


async def test_basic_routing():
    router = FridayRouter()
    resp = await router.route("show battery status")
    print("Routing response:", resp)


if __name__ == "__main__":
    asyncio.run(test_basic_routing())
