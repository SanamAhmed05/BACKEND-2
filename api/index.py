import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from models.user import db
from routes.video_enhanced import video_enhanced_bp

# Flask app
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), '../static/build'),
    template_folder=os.path.join(os.path.dirname(__file__), '../templates')
)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS
CORS(app)

# Register Blueprints
app.register_blueprint(video_enhanced_bp, url_prefix="/api/video")

# Database setup
app.config[
    'SQLALCHEMY_DATABASE_URI'
] = f"sqlite:///{os.path.join(os.path.dirname(__file__), '../database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# Serve React frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        return send_from_directory(static_folder_path, "index.html")

# Serve videos
@app.route("/videos/<filename>")
def serve_video(filename):
    video_folder = os.path.join(os.path.dirname(__file__), '../static/videos')
    if os.path.exists(os.path.join(video_folder, filename)):
        return send_from_directory(video_folder, filename)
    else:
        return jsonify({"error": "Video not found"}), 404

# Vercel serverless handler
def handler(environ, start_response):
    from werkzeug.wrappers import Request, Response
    request = Request(environ)
    response = Response()
    return app(environ, start_response)
