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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Referer': 'https://www.tiktok.com/'
    }
    
    # Menggunakan stream=True dan meneruskan data secara langsung
    req = requests.get(target_url, headers=headers, stream=True, timeout=10)
    
    def generate():
        for chunk in req.iter_content(chunk_size=4096):
            yield chunk

    return Response(generate(), 
                    content_type=req.headers.get('Content-Type', 'video/mp4'),
                    headers={
                        "Content-Disposition": "attachment; filename=video.mp4",
                        "Access-Control-Allow-Origin": "*"
                    })
