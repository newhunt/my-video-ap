from http.server import BaseHTTPRequestHandler
import json
import yt_dlp
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Parse URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # Handle root path
        if parsed.path == '/' or parsed.path == '':
            response = {
                "status": "online",
                "message": "Video Downloader API is running",
                "endpoints": {
                    "/download": "GET with ?url=VIDEO_URL"
                }
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Handle download endpoint
        if parsed.path == '/download':
            video_url = params.get('url', [None])[0]
            
            if not video_url:
                response = {"status": "error", "message": "URL parameter required"}
                self.wfile.write(json.dumps(response).encode())
                return
            
            try:
                # yt-dlp options
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    
                    # Cari URL video
                    direct_link = info.get('url')
                    if not direct_link and 'formats' in info:
                        for f in info['formats']:
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                direct_link = f.get('url')
                                break
                    
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
        
        # 404 for other paths
        self.send_response(404)
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
