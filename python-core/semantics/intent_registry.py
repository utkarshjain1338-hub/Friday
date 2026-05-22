INTENT_REGISTRY = {
    "coding_mode": [
        "start coding",
        "open development setup",
        "prepare workspace",
        "i want to code",
        "let's code"
    ],
    "focus_mode": [
        "too distracted",
        "need focus",
        "help me concentrate",
        "lock in mode"
    ],
    "relax_mode": [
        "play some music",
        "i want to chill",
        "relaxing time"
    ],
    "system_maintenance": [
        "clean up system",
        "run updates",
        "system check"
    ],
    "browser_search": [
        "search the web",
        "look this up",
        "find information about"
    ],
    "media_pause": [
        "pause this",
        "stop the music",
        "quiet"
    ],
    "media_play": [
        "resume this",
        "play it",
        "unpause"
    ]
}

def get_all_intents_and_labels():
    sentences = []
    labels = []
    for intent, phrases in INTENT_REGISTRY.items():
        for phrase in phrases:
            sentences.append(phrase)
            labels.append(intent)
    return sentences, labels
