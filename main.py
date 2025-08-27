import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from models.user import db
from routes.video_enhanced import video_enhanced_bp  # import blueprint

app = Flask(__name__,
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS
CORS(app)

# Register blueprints (⚡ notice: url_prefix only here, not in video_enhanced.py)
app.register_blueprint(video_enhanced_bp, url_prefix="/api/video")

# Database setup
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()


# Serve frontend (React/HTML)
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        return send_from_directory(static_folder_path, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
