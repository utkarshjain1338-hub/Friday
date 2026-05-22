console.log("Friday Browser Extension Background Script Initialized");

let socket: WebSocket | null = null;
const WS_URL = "ws://127.0.0.1:5556";

function connect() {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
        console.log("Connected to Friday Cognitive Orchestrator");
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleCommand(data);
        } catch (e) {
            console.error("Failed to parse message:", e);
        }
    };

    socket.onclose = () => {
        console.log("Disconnected from Friday, retrying in 2 seconds...");
        setTimeout(connect, 2000);
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

function handleCommand(command: any) {
    if (command.action === "get_context") {
        // Ask the active tab for its context
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0] && tabs[0].id) {
                chrome.tabs.sendMessage(tabs[0].id, { type: "EXTRACT_CONTEXT" });
            }
        });
    } else if (command.action === "execute_script") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0] && tabs[0].id) {
                chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    func: new Function(command.code) as any
                });
            }
        });
    }
}

// Listen for context payloads from content scripts and forward to Python
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "PAGE_CONTEXT" && socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            event: "BrowserContextUpdated",
            payload: message.payload
        }));
    }
});

// Start connection
connect();

// Track active tab changes
chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                event: "BrowserTabChanged",
                payload: { url: tab.url, title: tab.title }
            }));
        }
    });
});
