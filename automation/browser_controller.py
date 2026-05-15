import webbrowser
from urllib.parse import quote_plus


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def open_website(url: str) -> str:
    if not url:
        return "Please specify a website to open."
    webbrowser.open_new_tab(_normalize_url(url))
    return f"Opening {url}."


def search_google(query: str) -> str:
    if not query:
        return "Please provide search terms for Google."
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    webbrowser.open_new_tab(url)
    return f"Searching Google for '{query}'."


def open_youtube(query: str = None) -> str:
    if query:
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        webbrowser.open_new_tab(url)
        return f"Searching YouTube for '{query}'."

    webbrowser.open_new_tab("https://www.youtube.com")
    return "Opening YouTube."
