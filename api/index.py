from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "No URL provided"}), 400
    try:
        ydl_opts = {'format': 'best', 'quiet': True, 'nocheckcertificate': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            original_url = info.get('url')
            # Kita arahkan ke rute proxy buatan kita sendiri
            proxy_url = f"{request.host_url}proxy?url={original_url}"
            return jsonify({
                "status": "success", 
                "video_url": proxy_url,
                "direct_link": original_url
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/proxy')
def proxy():
    target_url = request.args.get('url')
    # Meniru browser asli agar tidak kena 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    req = requests.get(target_url, headers=headers, stream=True)
    return Response(req.iter_content(chunk_size=1024), 
                    content_type=req.headers['Content-Type'],
                    headers={"Content-Disposition": "attachment; filename=video.mp4"})
