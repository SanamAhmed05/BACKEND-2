// DOM Elements
const videoUrlInput = document.getElementById('videoUrl');
const downloadBtn = document.getElementById('downloadBtn');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const videoInfoSection = document.getElementById('videoInfoSection');
const videoPlayerSection = document.getElementById('videoPlayerSection');

// Video info elements
const videoThumbnail = document.getElementById('videoThumbnail');
const videoTitle = document.getElementById('videoTitle');
const videoUploader = document.getElementById('videoUploader');
const videoDuration = document.getElementById('videoDuration');
const videoViews = document.getElementById('videoViews');
const formatSelect = document.getElementById('formatSelect');
const playBtn = document.getElementById('playBtn');
const confirmDownloadBtn = document.getElementById('confirmDownloadBtn');

// Video player elements
const videoPlayer = document.getElementById('videoPlayer');
const closePlayerBtn = document.getElementById('closePlayerBtn');

// Global variables
let currentVideoInfo = null;
let currentDownloadedFile = null;

// Event Listeners
downloadBtn.addEventListener('click', handleDownload);
playBtn.addEventListener('click', handlePlay);
confirmDownloadBtn.addEventListener('click', handleConfirmDownload);
closePlayerBtn.addEventListener('click', closeVideoPlayer);

// Handle Enter key in URL input
videoUrlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleDownload();
    }
});

// Main download handler
async function handleDownload() {
    const url = videoUrlInput.value.trim();
    
    if (!url) {
        showError('Please enter a video URL');
        return;
    }
    
    if (!isValidUrl(url)) {
        showError('Please enter a valid URL');
        return;
    }
    
    showLoading();
    hideError();
    hideVideoInfo();
    hideVideoPlayer();
    
    try {
        // Get video information
        const response = await fetch('/api/video/info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        let data;
        try {
            // Clone the response to avoid "body stream already read" error
            const responseClone = response.clone();
            data = await response.json();
        } catch (jsonError) {
            // If JSON parsing fails, read the response as text
            try {
                const textResponse = await response.clone().text();
                console.error('Non-JSON response:', textResponse);
                throw new Error('Server returned an invalid response. Please try again later.');
            } catch (textError) {
                console.error('Failed to read response:', textError);
                throw new Error('Failed to communicate with server. Please try again later.');
            }
        }
        
        if (!response.ok) {
            if (response.status === 429) {
                // Handle bot detection specifically
                showBotDetectionError(data.error, data.suggestion);
            } else {
                throw new Error(data.error || 'Failed to get video information');
            }
            hideLoading();
            return;
        }
        
        currentVideoInfo = data;
        displayVideoInfo(data);
        hideLoading();
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to process video URL');
        hideLoading();
    }
}

// Handle video playback
async function handlePlay() {
    if (!currentVideoInfo) return;
    
    showLoading();
    
    try {
        // Download video for streaming
        const response = await fetch('/api/video/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: videoUrlInput.value.trim(),
                format_id: formatSelect.value 
            })
        });
        
        let data;
        try {
            // Clone the response to avoid "body stream already read" error
            const responseClone = response.clone();
            data = await response.json();
        } catch (jsonError) {
            // If JSON parsing fails, read the response as text
            try {
                const textResponse = await response.clone().text();
                console.error('Non-JSON response:', textResponse);
                throw new Error('Server returned an invalid response. Please try again later.');
            } catch (textError) {
                console.error('Failed to read response:', textError);
                throw new Error('Failed to communicate with server. Please try again later.');
            }
        }
        
        if (!response.ok) {
            if (response.status === 429) {
                showBotDetectionError(data.error, data.suggestion);
            } else {
                throw new Error(data.error || 'Failed to download video');
            }
            hideLoading();
            return;
        }
        
        currentDownloadedFile = data.filename;
        
        // Set video source and show player
        const streamUrl = `/api/video/stream/${data.filename}`;
        videoPlayer.src = streamUrl;
        
        showVideoPlayer();
        hideLoading();
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to load video for playback');
        hideLoading();
    }
}

// Handle download confirmation
async function handleConfirmDownload() {
    if (!currentVideoInfo) return;
    
    showLoading();
    
    try {
        const response = await fetch('/api/video/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: videoUrlInput.value.trim(),
                format_id: formatSelect.value 
            })
        });
        
        let data;
        try {
            // Clone the response to avoid "body stream already read" error
            const responseClone = response.clone();
            data = await response.json();
        } catch (jsonError) {
            // If JSON parsing fails, read the response as text
            try {
                const textResponse = await response.clone().text();
                console.error('Non-JSON response:', textResponse);
                throw new Error('Server returned an invalid response. Please try again later.');
            } catch (textError) {
                console.error('Failed to read response:', textError);
                throw new Error('Failed to communicate with server. Please try again later.');
            }
        }
        
        if (!response.ok) {
            if (response.status === 429) {
                showBotDetectionError(data.error, data.suggestion);
            } else {
                throw new Error(data.error || 'Failed to download video');
            }
            hideLoading();
            return;
        }
        
        // Trigger download
        const downloadUrl = data.download_url;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = data.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        hideLoading();
        showSuccess('Video downloaded successfully!');
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to download video');
        hideLoading();
    }
}

// Display video information
function displayVideoInfo(info) {
    videoTitle.textContent = info.title;
    videoUploader.textContent = `By: ${info.uploader}`;
    videoDuration.textContent = formatDuration(info.duration);
    videoViews.textContent = formatViews(info.view_count);
    
    if (info.thumbnail) {
        videoThumbnail.src = info.thumbnail;
        videoThumbnail.alt = info.title;
    }
    
    // Populate format options
    formatSelect.innerHTML = '<option value="best">Best Quality</option>';
    if (info.formats && info.formats.length > 0) {
        info.formats.forEach(format => {
            if (format.quality && format.quality !== 'Unknown') {
                const option = document.createElement('option');
                option.value = format.format_id;
                option.textContent = `${format.quality}p (${format.ext.toUpperCase()})`;
                formatSelect.appendChild(option);
            }
        });
    }
    
    showVideoInfo();
}

// Show bot detection specific error
function showBotDetectionError(message, suggestion) {
    const errorDiv = document.getElementById('errorState');
    errorDiv.innerHTML = `
        <i class="fas fa-robot" style="color: #ff6b6b; font-size: 24px; margin-bottom: 10px;"></i>
        <h3 style="color: #ff6b6b; margin-bottom: 10px;">Bot Detection Alert</h3>
        <p style="margin-bottom: 15px;">${message}</p>
        <p style="color: #b8b8b8; font-size: 14px; margin-bottom: 15px;">${suggestion}</p>
        <div style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 8px; margin-top: 15px;">
            <h4 style="color: #667eea; margin-bottom: 10px;">Alternative Options:</h4>
            <ul style="text-align: left; color: #b8b8b8; font-size: 14px;">
                <li>Try videos from Vimeo, Dailymotion, or TikTok</li>
                <li>Wait a few minutes and try again</li>
                <li>Try a different YouTube video</li>
            </ul>
            <button onclick="showSupportedSites()" style="margin-top: 10px; background: #667eea; border: none; color: white; padding: 8px 15px; border-radius: 5px; cursor: pointer;">
                View Supported Sites
            </button>
        </div>
    `;
    errorDiv.classList.remove('hidden');
}

// Show supported sites
async function showSupportedSites() {
    try {
        const response = await fetch('/api/video/supported-sites');
        
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            try {
                const textResponse = await response.clone().text();
                console.error('Failed to parse JSON response:', textResponse);
                throw new Error('Server returned an invalid response. Please try again later.');
            } catch (textError) {
                console.error('Failed to read response:', textError);
                throw new Error('Failed to communicate with server. Please try again later.');
            }
        }
        
        if (response.ok) {
            let sitesHtml = '<div style="max-height: 200px; overflow-y: auto; text-align: left;">';
            data.supported_sites.forEach(site => {
                const statusColor = site.status.includes('Limited') ? '#ff6b6b' : '#4ade80';
                sitesHtml += `
                    <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <span>${site.name} (${site.domain})</span>
                        <span style="color: ${statusColor}; font-size: 12px;">${site.status}</span>
                    </div>
                `;
            });
            sitesHtml += '</div>';
            
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                background: rgba(0,0,0,0.8); z-index: 1000; 
                display: flex; align-items: center; justify-content: center;
            `;
            modal.innerHTML = `
                <div style="background: #1a1a2e; padding: 30px; border-radius: 15px; max-width: 500px; width: 90%;">
                    <h3 style="color: #667eea; margin-bottom: 20px;">Supported Video Sites</h3>
                    ${sitesHtml}
                    <button onclick="this.closest('div').parentElement.remove()" 
                            style="margin-top: 20px; background: #667eea; border: none; color: white; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                        Close
                    </button>
                </div>
            `;
            document.body.appendChild(modal);
        }
    } catch (error) {
        console.error('Failed to load supported sites:', error);
    }
}

// Utility functions
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

function formatDuration(seconds) {
    if (!seconds) return 'Unknown';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

function formatViews(views) {
    if (!views) return 'Unknown views';
    
    if (views >= 1000000) {
        return `${(views / 1000000).toFixed(1)}M views`;
    } else if (views >= 1000) {
        return `${(views / 1000).toFixed(1)}K views`;
    } else {
        return `${views} views`;
    }
}

// UI State Management
function showLoading() {
    loadingState.classList.remove('hidden');
}

function hideLoading() {
    loadingState.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
}

function hideError() {
    errorState.classList.add('hidden');
}

function showVideoInfo() {
    videoInfoSection.classList.remove('hidden');
}

function hideVideoInfo() {
    videoInfoSection.classList.add('hidden');
}

function showVideoPlayer() {
    videoPlayerSection.classList.remove('hidden');
    videoPlayer.scrollIntoView({ behavior: 'smooth' });
}

function hideVideoPlayer() {
    videoPlayerSection.classList.add('hidden');
    videoPlayer.pause();
    videoPlayer.src = '';
}

function closeVideoPlayer() {
    hideVideoPlayer();
}

function showSuccess(message) {
    // Create a temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <p>${message}</p>
    `;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(0, 255, 0, 0.1);
        border: 1px solid rgba(0, 255, 0, 0.3);
        border-radius: 10px;
        padding: 15px 20px;
        color: #00ff00;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
    `;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        document.body.removeChild(successDiv);
    }, 3000);
}

