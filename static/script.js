const API_BASE = window.location.origin + "/api/video";

// ---- Fetch Video Info ----
async function handleDownload() {
    const url = videoUrlInput.value.trim();
    if (!url) return showError('Please enter a video URL');
    if (!isValidUrl(url)) return showError('Please enter a valid URL');

    showLoading(); hideError(); hideVideoInfo(); hideVideoPlayer();

    try {
        const response = await fetch(`${API_BASE}/info`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error);

        currentVideoInfo = data;
        displayVideoInfo(data);
        hideLoading();
    } catch (error) {
        showError(error.message || 'Failed to fetch video info');
        hideLoading();
    }
}

// ---- Play Video ----
async function handlePlay() {
    if (!currentVideoInfo) return;
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: videoUrlInput.value.trim(),
                format_id: formatSelect.value
            })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);

        currentDownloadedFile = data.filename;
        videoPlayer.src = `${API_BASE}/stream/${data.filename}`;
        showVideoPlayer();
        hideLoading();
    } catch (error) {
        showError(error.message || 'Failed to play video');
        hideLoading();
    }
}

// ---- Download Video ----
async function handleConfirmDownload() {
    if (!currentVideoInfo) return;
    showLoading();
    try {
        const response = await fetch(`${API_BASE}/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: videoUrlInput.value.trim(),
                format_id: formatSelect.value
            })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);

        const link = document.createElement('a');
        link.href = `${API_BASE}/stream/${data.filename}`;
        link.download = data.filename;
        link.click();

        hideLoading();
        showSuccess('Video download started!');
    } catch (error) {
        showError(error.message || 'Failed to download video');
        hideLoading();
    }
}
