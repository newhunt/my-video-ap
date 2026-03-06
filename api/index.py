# api/index.py
from http.server import BaseHTTPRequestHandler
import json
import yt_dlp
import certifi
import os
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Handle OPTIONS request for CORS preflight
        if self.command == 'OPTIONS':
            self.send_response(200)
            self.end_headers()
            return
        
        # Parse URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # Root endpoint
        if parsed.path == '/' or parsed.path == '':
            response = {
                "status": "online",
                "message": "Video Downloader API is running",
                "version": "2.0",
                "endpoints": {
                    "/download": "GET with ?url=VIDEO_URL"
                }
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Download endpoint
        if parsed.path == '/download':
            video_url = params.get('url', [None])[0]
            
            if not video_url:
                response = {"status": "error", "message": "URL parameter required"}
                self.wfile.write(json.dumps(response).encode())
                return
            
            try:
                # Set SSL certificate
                os.environ['SSL_CERT_FILE'] = certifi.where()
                
                # yt-dlp options
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'ignoreerrors': True,
                    'no_color': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info
                    info = ydl.extract_info(video_url, download=False)
                    
                    # Get direct link
                    direct_link = None
                    
                    if info.get('url'):
                        direct_link = info['url']
                    elif info.get('formats'):
                        for f in info['formats']:
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                direct_link = f.get('url')
                                break
                        if not direct_link and info['formats']:
                            direct_link = info['formats'][-1].get('url')
                    
                    if not direct_link:
                        response = {"status": "error", "message": "No video URL found"}
                        self.wfile.write(json.dumps(response).encode())
                        return
                    
                    # Success response
                    response = {
                        "status": "success",
                        "direct_link": direct_link,
                        "title": info.get('title', 'Video'),
                        "platform": info.get('extractor_key', 'unknown'),
                        "thumbnail": info.get('thumbnail')
                    }
                    
            except Exception as e:
                response = {
                    "status": "error",
                    "message": str(e),
                    "type": type(e).__name__
                }
            
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Health endpoint
        if parsed.path == '/health':
            response = {
                "status": "healthy",
                "timestamp": str(__import__('datetime').datetime.now())
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # 404 for other paths
        self.send_response(404)
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_OPTIONS(self):
        # Handle preflight CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
