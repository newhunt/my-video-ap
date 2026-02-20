from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app) # Penting agar bisa diakses dari Blogspot kamu

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_direct_url = info.get('url')
            return jsonify({
                "status": "success",
                "video_url": video_direct_url
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
