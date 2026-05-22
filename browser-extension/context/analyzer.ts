export const getPageContext = () => {
    // Extract meaningful text, skipping massive scripts or hidden elements
    const getVisibleText = () => {
        return document.body.innerText.substring(0, 2000); // Send up to 2000 chars for semantic memory
    };

    // Find any playing media
    const mediaElements = Array.from(document.querySelectorAll('video, audio')) as HTMLMediaElement[];
    const playingMedia = mediaElements.find(m => !m.paused && !m.muted);

    return {
        title: document.title,
        url: window.location.href,
        content: getVisibleText(),
        hasPlayingMedia: !!playingMedia,
        inputs: Array.from(document.querySelectorAll('input, textarea')).length,
    };
};
