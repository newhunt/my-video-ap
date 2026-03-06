# api/api.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import certifi

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Video Downloader API is running",
        "version": "2.0",
        "endpoints": {
            "/download": "GET with ?url=VIDEO_URL (TikTok & Instagram)"
        }
    })

@app.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "Link kosong"}), 400

    try:
        # Set SSL certificate path for Vercel
        os.environ['SSL_CERT_FILE'] = certifi.where()
        
        # Opsi lengkap untuk yt-dlp
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prioritaskan MP4
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,  # Penting untuk Vercel!
            'ignoreerrors': True,
            'no_color': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'extract_flat': False,
            'force_generic_extractor': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ekstrak info video
            info = ydl.extract_info(video_url, download=False)
            
            # Cari direct link video
            direct_link = None
            
            # Coba ambil dari 'url' langsung
            if info.get('url'):
                direct_link = info['url']
            
            # Jika tidak ada, cari di formats
            elif info.get('formats'):
                # Cari format yang punya video dan audio
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        direct_link = f.get('url')
                        break
                
                # Jika masih tidak ada, ambil format terakhir
                if not direct_link and len(info['formats']) > 0:
                    direct_link = info['formats'][-1].get('url')
            
            # Jika masih tidak dapat, coba dari entries (untuk playlist)
            elif info.get('entries') and len(info['entries']) > 0:
                first_entry = info['entries'][0]
                direct_link = first_entry.get('url')
                
                if not direct_link and first_entry.get('formats'):
                    for f in first_entry['formats']:
                        if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                            direct_link = f.get('url')
                            break
            
            # Validasi apakah dapat link
            if not direct_link:
                return jsonify({
                    "status": "error", 
                    "message": "Tidak dapat menemukan URL video"
                }), 404
            
            # Siapkan response
            response_data = {
                "status": "success",
                "direct_link": direct_link,
                "title": info.get('title', 'Video'),
                "duration": info.get('duration'),
                "platform": info.get('extractor_key', 'unknown'),
                "thumbnail": info.get('thumbnail'),
                "uploader": info.get('uploader'),
                "view_count": info.get('view_count'),
                "like_count": info.get('like_count')
            }
            
            return jsonify(response_data)
            
    except Exception as e:
        error_message = str(e)
        error_type = type(e).__name__
        
        # Handle specific errors
        if 'copyright' in error_message.lower():
            return jsonify({
                "status": "error", 
                "message": "Video terkena copyright atau tidak tersedia",
                "type": error_type
            }), 403
        
        elif 'private' in error_message.lower():
            return jsonify({
                "status": "error", 
                "message": "Video ini private",
                "type": error_type
            }), 403
        
        elif 'rate limit' in error_message.lower():
            return jsonify({
                "status": "error", 
                "message": "Terlalu banyak request, coba lagi nanti",
                "type": error_type
            }), 429
        
        else:
            return jsonify({
                "status": "error", 
                "message": error_message,
                "type": error_type
            }), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint untuk cek kesehatan API"""
    return jsonify({
        "status": "healthy",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

@app.route('/platforms', methods=['GET'])
def platforms():
    """Endpoint untuk cek platform yang didukung"""
    return jsonify({
        "status": "success",
        "platforms": [
            "tiktok",
            "instagram",
            "youtube", 
            "twitter",
            "facebook"
        ],
        "note": "Tidak semua platform 100% work, tergantung yt-dlp"
    })

# Untuk Vercel serverless
def handler(request):
    return app(request)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
