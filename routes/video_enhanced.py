from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
import yt_dlp
import os
import tempfile
import uuid
import time
import random
from urllib.parse import urlparse
from yt_dlp import YoutubeDL
import os
import pickle

def download_video(url):
    token_path = 'src/database/token.pkl'

    if not os.path.exists(token_path):
        return "Admin has not authenticated yet."

    with open(token_path, 'rb') as token_file:
        creds = pickle.load(token_file)

    # If token is expired and refreshable
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'wb') as token_file:
            pickle.dump(creds, token_file)

    # Set up yt_dlp with cookies from token (for private/auth-only videos)
    # WARNING: yt_dlp doesn't directly accept Google OAuth, so this is pseudo:
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


video_enhanced_bp = Blueprint('video_enhanced', __name__)

# Directory to store downloaded videos temporarily
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), 'video_downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_enhanced_ydl_opts(format_id='best'):
    """Get enhanced yt-dlp options to bypass bot detection"""
    return {
        'format': format_id,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'ignoreerrors': True,
        # Enhanced options to avoid bot detection
        'sleep_interval': random.uniform(1, 3),  # Random sleep between requests
        'max_sleep_interval': 5,
        'sleep_interval_requests': random.uniform(0.5, 1.5),  # Sleep between HTTP requests
        'retries': 3,
        'fragment_retries': 3,
        'extractor_retries': 3,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '300',
            'Connection': 'keep-alive',
        },
        # Additional options to appear more like a regular browser
        'geo_bypass': True,
        'geo_bypass_country': 'US',
    }

@video_enhanced_bp.route('/video/info', methods=['POST'])
@cross_origin()
def get_video_info():
    """Get video information without downloading"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Configure yt-dlp options for info extraction
        ydl_opts = get_enhanced_ydl_opts()
        ydl_opts.update({
            'simulate': True,  # Don't download, just extract info
            'skip_download': True,
        })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                video_info = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'formats': []
                }
                
                # Extract available formats
                if 'formats' in info:
                    seen_qualities = set()
                    for fmt in info['formats']:
                        if fmt.get('vcodec') != 'none' and fmt.get('height'):  # Video formats only
                            quality = fmt.get('height')
                            if quality and quality not in seen_qualities:
                                seen_qualities.add(quality)
                                video_info['formats'].append({
                                    'format_id': fmt.get('format_id'),
                                    'ext': fmt.get('ext', 'mp4'),
                                    'quality': quality,
                                    'filesize': fmt.get('filesize', 0)
                                })
                
                # Sort formats by quality (highest first)
                video_info['formats'].sort(key=lambda x: x['quality'], reverse=True)
                
                return jsonify(video_info)
                
            except yt_dlp.utils.ExtractorError as e:
                error_msg = str(e)
                if "Sign in to confirm you're not a bot" in error_msg:
                    return jsonify({
                        'error': 'YouTube is currently blocking automated access. This is a temporary restriction. Please try again later or try a different video URL.',
                        'suggestion': 'You can try videos from other platforms like Vimeo, Dailymotion, or other supported sites.'
                    }), 429  # Too Many Requests
                else:
                    return jsonify({'error': f'Failed to extract video info: {error_msg}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_enhanced_bp.route('/video/download', methods=['POST'])
@cross_origin()
def download_video():
    """Download video and return file path"""
    try:
        data = request.get_json()
        url = data.get('url')
        format_id = data.get('format_id', 'best')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        
        # Configure yt-dlp options
        ydl_opts = get_enhanced_ydl_opts(format_id)
        ydl_opts.update({
            'outtmpl': os.path.join(DOWNLOAD_DIR, f'{unique_id}.%(ext)s'),
        })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Add a small delay before download to appear more natural
                time.sleep(random.uniform(1, 2))
                
                info = ydl.extract_info(url, download=True)
                
                # Find the downloaded file
                downloaded_file = None
                for file in os.listdir(DOWNLOAD_DIR):
                    if file.startswith(unique_id):
                        downloaded_file = file
                        break
                
                if not downloaded_file:
                    return jsonify({'error': 'Download failed - file not found'}), 500
                
                file_path = os.path.join(DOWNLOAD_DIR, downloaded_file)
                file_size = os.path.getsize(file_path)
                
                return jsonify({
                    'success': True,
                    'filename': downloaded_file,
                    'title': info.get('title', 'Unknown'),
                    'file_size': file_size,
                    'download_url': f'/api/video/file/{downloaded_file}'
                })
                
            except yt_dlp.utils.ExtractorError as e:
                error_msg = str(e)
                if "Sign in to confirm you're not a bot" in error_msg:
                    return jsonify({
                        'error': 'YouTube is currently blocking automated access. This is a temporary restriction.',
                        'suggestion': 'Please try again in a few minutes, or try a different video URL from other platforms.'
                    }), 429  # Too Many Requests
                else:
                    return jsonify({'error': f'Download failed: {error_msg}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_enhanced_bp.route('/video/file/<filename>')
@cross_origin()
def serve_video_file(filename):
    """Serve downloaded video file"""
    try:
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_enhanced_bp.route('/video/stream/<filename>')
@cross_origin()
def stream_video_file(filename):
    """Stream video file for playback"""
    try:
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='video/mp4')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_enhanced_bp.route('/video/supported-sites')
@cross_origin()
def get_supported_sites():
    """Get list of supported video sites"""
    try:
        # Return a curated list of popular supported sites
        supported_sites = [
            {'name': 'YouTube', 'domain': 'youtube.com', 'status': 'Limited (due to bot detection)'},
            {'name': 'Vimeo', 'domain': 'vimeo.com', 'status': 'Supported'},
            {'name': 'Dailymotion', 'domain': 'dailymotion.com', 'status': 'Supported'},
            {'name': 'Twitch', 'domain': 'twitch.tv', 'status': 'Supported'},
            {'name': 'TikTok', 'domain': 'tiktok.com', 'status': 'Supported'},
            {'name': 'Instagram', 'domain': 'instagram.com', 'status': 'Supported'},
            {'name': 'Twitter/X', 'domain': 'twitter.com', 'status': 'Supported'},
            {'name': 'Facebook', 'domain': 'facebook.com', 'status': 'Supported'},
            {'name': 'Reddit', 'domain': 'reddit.com', 'status': 'Supported'},
            {'name': 'Streamable', 'domain': 'streamable.com', 'status': 'Supported'},
        ]
        
        return jsonify({
            'supported_sites': supported_sites,
            'total_sites': len(supported_sites),
            'note': 'yt-dlp supports over 1000 sites. This is a curated list of popular ones.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

