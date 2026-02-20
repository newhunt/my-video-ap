from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "Link tidak boleh kosong"}), 400

    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "status": "success",
                "direct_link": info.get('url'),
                "title": info.get('title', 'Video')
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Opsional: Hanya untuk testing lokal, tidak akan mengganggu Vercel
if __name__ == "__main__":
    app.run(debug=True)
