from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Video Downloader API is running",
        "endpoints": {
            "/download": "GET with ?url=VIDEO_URL"
        }
    })

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "Link kosong"}), 400

    try:
        # Opsi lengkap untuk yt-dlp
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prioritaskan MP4
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'extract_flat': False,
            'force_generic_extractor': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ekstrak info
            info = ydl.extract_info(video_url, download=False)
            
            # Cari URL video terbaik
            direct_link = None
            
            # Cek berbagai kemungkinan format
            if 'url' in info:
                direct_link = info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                # Ambil format dengan video+audio
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        direct_link = f.get('url')
                        break
                if not direct_link:
                    direct_link = info['formats'][-1].get('url')
            
            if not direct_link:
                return jsonify({
                    "status": "error", 
                    "message": "Tidak dapat menemukan URL video"
                }), 404
            
            # Dapatkan info tambahan
            video_info = {
                "status": "success",
                "direct_link": direct_link,
                "title": info.get('title', 'Video'),
                "duration": info.get('duration'),
                "platform": info.get('extractor_key', 'unknown'),
                "thumbnail": info.get('thumbnail')
            }
            
            return jsonify(video_info)
            
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e),
            "type": type(e).__name__
        }), 500

# Untuk Vercel serverless
def handler(request):
    return app(request)

# Untuk local development
if __name__ == '__main__':
    app.run(debug=True, port=5000)
