from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    if not video_url or video_url == "TEST":
        return jsonify({"status": "error", "message": "Link video tidak ada"}), 400

    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            # Menghindari error di serverless
            'nocheckcertificate': True,
            'extract_flat': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "status": "success",
                "video_url": info.get('url')
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Baris ini SANGAT PENTING untuk Vercel
def handler(event, context):
    return app(event, context)
