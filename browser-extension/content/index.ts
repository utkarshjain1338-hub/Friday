import { getPageContext } from '../context/analyzer';

console.log("Friday Browser Extension Content Script Initialized");

// Listen for extraction requests from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "EXTRACT_CONTEXT") {
        const context = getPageContext();
        chrome.runtime.sendMessage({
            type: "PAGE_CONTEXT",
            payload: context
        });
    }
});

// Auto-extract context on load
const context = getPageContext();
chrome.runtime.sendMessage({
    type: "PAGE_CONTEXT",
    payload: context
});
