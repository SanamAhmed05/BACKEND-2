from flask import Blueprint, request, jsonify, send_file
import yt_dlp
import os
import uuid

# ⚡ Do NOT put url_prefix here, only in main.py
video_enhanced_bp = Blueprint("video_enhanced", __name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# Get video info
@video_enhanced_bp.route("/info", methods=["POST"])
def get_video_info():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        ydl_opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [{
                "format_id": f["format_id"],
                "ext": f.get("ext"),
                "quality": f.get("height", "Unknown")
            } for f in info.get("formats", []) if f.get("height")]
            return jsonify({
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "thumbnail": info.get("thumbnail"),
                "formats": formats
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Download video
@video_enhanced_bp.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url")
    format_id = data.get("format_id", "best")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        filename = f"{uuid.uuid4()}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        ydl_opts = {"format": format_id, "outtmpl": filepath, "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return jsonify({
            "filename": filename,
            "download_url": f"/api/video/stream/{filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Stream/serve file
@video_enhanced_bp.route("/stream/<filename>", methods=["GET"])
def stream_video(filename):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=False)
