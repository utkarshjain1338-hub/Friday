import asyncio
import websockets
import json

async def test_browser_extension():
    uri = "ws://127.0.0.1:5556"
    print(f"Connecting to Friday Orchestrator at {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Sending mock BrowserTabChanged event...")
            
            # Send a tab change event
            tab_event = {
                "event": "BrowserTabChanged",
                "payload": {
                    "url": "https://github.com",
                    "title": "GitHub: Let's build from here"
                }
            }
            await websocket.send(json.dumps(tab_event))
            
            await asyncio.sleep(1)
            
            print("Sending mock BrowserContextUpdated event...")
            context_event = {
                "event": "BrowserContextUpdated",
                "payload": {
                    "url": "https://github.com",
                    "content": "This is a mock repository page. It contains lots of code.",
                    "hasPlayingMedia": False,
                    "inputs": 2
                }
            }
            await websocket.send(json.dumps(context_event))
            
            print("Events sent successfully. Check the Orchestrator logs!")
            
    except ConnectionRefusedError:
        print("Error: Friday Orchestrator is not running on port 5556. Please start it first.")

if __name__ == "__main__":
    asyncio.run(test_browser_extension())
