# api/index.py
from http.server import BaseHTTPRequestHandler
import json
import yt_dlp
import certifi
import os
from urllib.parse import urlparse, parse_qs
import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Parse URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # Root endpoint
        if parsed.path == '/' or parsed.path == '':
            response = {
                "status": "online",
                "message": "Video Downloader API is running",
                "version": "2.1",
                "endpoints": {
                    "/download": "GET with ?url=VIDEO_URL (TikTok & Instagram)",
                    "/health": "GET - Check API health",
                    "/platforms": "GET - List supported platforms"
                }
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Health endpoint
        if parsed.path == '/health':
            response = {
                "status": "healthy",
                "timestamp": str(datetime.datetime.now()),
                "uptime": "OK"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Platforms endpoint
        if parsed.path == '/platforms':
            response = {
                "status": "success",
                "platforms": [
                    "tiktok",
                    "instagram", 
                    "youtube",
                    "twitter",
                    "facebook"
                ],
                "note": "Powered by yt-dlp"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Download endpoint
        if parsed.path == '/download':
            video_url = params.get('url', [None])[0]
            
            if not video_url:
                response = {
                    "status": "error", 
                    "message": "URL parameter required. Contoh: ?url=https://vt.tiktok.com/xxx"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # PROSES DOWNLOAD
            try:
                # Set SSL certificate for Vercel
                os.environ['SSL_CERT_FILE'] = certifi.where()
                
                # Base options untuk yt-dlp
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',  # Prioritaskan MP4
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,  # Penting untuk Vercel!
                    'ignoreerrors': True,
                    'no_color': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
                
                # Deteksi platform dan tambahkan opsi khusus
                if 'instagram.com' in video_url:
                    ydl_opts.update({
                        'force_generic_extractor': True,
                        'extract_flat': False,
                        'cookiefile': None,
                    })
                elif 'tiktok.com' in video_url:
                    ydl_opts.update({
                        'extract_flat': False,
                    })
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Ekstrak info video
                    try:
                        info = ydl.extract_info(video_url, download=False)
                    except Exception as e:
                        response = {
                            "status": "error",
                            "message": f"Gagal mengekstrak video: {str(e)}",
                            "type": "ExtractError",
                            "suggestion": "Coba gunakan link langsung (bukan short link) atau cek apakah video masih tersedia"
                        }
                        self.wfile.write(json.dumps(response).encode())
                        return
                    
                    # CEK APAKAH INFO NONE
                    if info is None:
                        response = {
                            "status": "error",
                            "message": "Tidak dapat mengambil info video. Link mungkin private, perlu login, atau tidak valid.",
                            "type": "EmptyInfoError",
                            "suggestion": "Coba buka link di browser dulu untuk memastikan video bisa diakses"
                        }
                        self.wfile.write(json.dumps(response).encode())
                        return
                    
                    # AMBIL DIRECT LINK DENGAN AMAN
                    direct_link = None
                    
                    # Pastikan info adalah dictionary
                    if isinstance(info, dict):
                        # Method 1: Langsung dari 'url'
                        direct_link = info.get('url')
                        
                        # Method 2: Cari dari 'formats'
                        if not direct_link and info.get('formats'):
                            formats = info['formats']
                            if isinstance(formats, list):
                                # Cari format dengan video + audio
                                for f in formats:
                                    if isinstance(f, dict):
                                        if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                            direct_link = f.get('url')
                                            break
                                
                                # Fallback ke format terakhir
                                if not direct_link and formats and isinstance(formats[-1], dict):
                                    direct_link = formats[-1].get('url')
                        
                        # Method 3: Untuk playlist
                        if not direct_link and info.get('entries'):
                            entries = info['entries']
                            if entries and isinstance(entries, list) and len(entries) > 0:
                                first_entry = entries[0]
                                if isinstance(first_entry, dict):
                                    direct_link = first_entry.get('url')
                                    
                                    # Coba cari di formats entry pertama
                                    if not direct_link and first_entry.get('formats'):
                                        for f in first_entry['formats']:
                                            if isinstance(f, dict):
                                                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                                    direct_link = f.get('url')
                                                    break
                    
                    # CEK APAKAH DAPAT DIRECT LINK
                    if not direct_link:
                        response = {
                            "status": "error",
                            "message": "Tidak dapat menemukan URL video dari link tersebut.",
                            "type": "NoURLError",
                            "suggestion": "Platform mungkin tidak didukung atau video dalam format yang tidak bisa diekstrak"
                        }
                        self.wfile.write(json.dumps(response).encode())
                        return
                    
                    # Siapkan response sukses
                    response = {
                        "status": "success",
                        "direct_link": direct_link,
                        "title": info.get('title', 'Video') if isinstance(info, dict) else 'Video',
                        "platform": info.get('extractor_key', 'unknown') if isinstance(info, dict) else 'unknown',
                        "thumbnail": info.get('thumbnail') if isinstance(info, dict) else None,
                        "duration": info.get('duration') if isinstance(info, dict) else None,
                        "uploader": info.get('uploader') if isinstance(info, dict) else None
                    }
                    
                    self.wfile.write(json.dumps(response).encode())
                    return
                    
            except Exception as e:
                # Handle unexpected errors
                error_message = str(e)
                error_type = type(e).__name__
                
                # Cek error spesifik
                if 'SSL' in error_message:
                    response = {
                        "status": "error",
                        "message": "SSL Certificate Error. Mencoba tanpa verifikasi...",
                        "type": error_type,
                        "retry": True
                    }
                elif '404' in error_message:
                    response = {
                        "status": "error",
                        "message": "Video tidak ditemukan (404). Link mungkin sudah dihapus.",
                        "type": error_type
                    }
                elif 'private' in error_message.lower():
                    response = {
                        "status": "error",
                        "message": "Video ini private atau memerlukan login.",
                        "type": error_type
                    }
                else:
                    response = {
                        "status": "error",
                        "message": error_message,
                        "type": error_type,
                        "note": "Kalau terus error, coba link lain atau laporkan ke developer"
                    }
                
                self.wfile.write(json.dumps(response).encode())
                return
        
        # 404 for other paths
        self.send_response(404)
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": "Endpoint not found",
            "available": ["/", "/health", "/platforms", "/download"]
        }).encode())
    
    def do_OPTIONS(self):
        # Handle preflight CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
