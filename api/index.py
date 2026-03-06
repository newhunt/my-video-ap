# api/index.py
from http.server import BaseHTTPRequestHandler
import json
import yt_dlp
import certifi
import os
import sys
import requests
import datetime
from urllib.parse import urlparse, parse_qs

# Nonaktifkan warning SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
                "version": "3.0",
                "features": [
                    "Support TikTok & Instagram",
                    "Auto fallback to multiple APIs",
                    "SSL verification disabled for Vercel"
                ],
                "endpoints": {
                    "/download": "GET with ?url=VIDEO_URL",
                    "/health": "GET - Check API health",
                    "/platforms": "GET - List supported platforms",
                    "/debug": "GET with ?url=VIDEO_URL - Debug info"
                }
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            return
        
        # Health endpoint
        if parsed.path == '/health':
            response = {
                "status": "healthy",
                "timestamp": str(datetime.datetime.now()),
                "yt_dlp_version": yt_dlp.version.__version__,
                "python_version": sys.version
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
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
                "note": "Powered by yt-dlp with multiple fallback APIs"
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            return
        
        # Debug endpoint
        if parsed.path == '/debug':
            video_url = params.get('url', [None])[0]
            
            if not video_url:
                response = {"status": "error", "message": "URL parameter required"}
                self.wfile.write(json.dumps(response, indent=2).encode())
                return
            
            debug_info = {
                "url": video_url,
                "platform": self.detect_platform(video_url),
                "timestamp": str(datetime.datetime.now()),
                "tests": {}
            }
            
            # Test yt-dlp
            try:
                ydl_opts = {
                    'format': 'best',
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'ignoreerrors': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    debug_info["tests"]["yt_dlp"] = {
                        "success": info is not None,
                        "title": info.get('title') if info else None,
                        "extractor": info.get('extractor_key') if info else None
                    }
            except Exception as e:
                debug_info["tests"]["yt_dlp"] = {
                    "success": False,
                    "error": str(e)[:200]
                }
            
            self.wfile.write(json.dumps(debug_info, indent=2).encode())
            return
        
        # DOWNLOAD ENDPOINT - MAIN FUNCTION
        if parsed.path == '/download':
            video_url = params.get('url', [None])[0]
            
            if not video_url:
                response = {
                    "status": "error", 
                    "message": "URL parameter required. Contoh: ?url=https://vt.tiktok.com/xxx"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Set environment untuk SSL
            os.environ['SSL_CERT_FILE'] = certifi.where()
            os.environ['PYTHONHTTPSVERIFY'] = '0'
            
            # Deteksi platform
            platform = self.detect_platform(video_url)
            
            # METHOD 1: Coba dengan yt-dlp (dengan berbagai opsi)
            result = self.try_yt_dlp(video_url, platform)
            if result and result.get('direct_link'):
                self.wfile.write(json.dumps(result).encode())
                return
            
            # METHOD 2: Fallback untuk TikTok
            if 'tiktok' in platform:
                result = self.try_tiktok_fallback(video_url)
                if result and result.get('direct_link'):
                    self.wfile.write(json.dumps(result).encode())
                    return
            
            # METHOD 3: Fallback untuk Instagram
            if 'instagram' in platform:
                result = self.try_instagram_fallback(video_url)
                if result and result.get('direct_link'):
                    self.wfile.write(json.dumps(result).encode())
                    return
            
            # METHOD 4: Coba dengan requests langsung (untuk video sederhana)
            result = self.try_direct_request(video_url)
            if result and result.get('direct_link'):
                self.wfile.write(json.dumps(result).encode())
                return
            
            # SEMUA METHOD GAGAL
            response = {
                "status": "error",
                "message": "Gagal mengambil video setelah mencoba semua metode",
                "platform": platform,
                "suggestions": [
                    "Coba gunakan link langsung (bukan short link)",
                    "Pastikan video tidak private",
                    "Coba link TikTok/Instagram lain",
                    "Coba lagi nanti (mungkin rate limited)"
                ]
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # 404 for other paths
        self.send_response(404)
        self.end_headers()
        self.wfile.write(json.dumps({
            "error": "Endpoint not found",
            "available": ["/", "/health", "/platforms", "/download", "/debug"]
        }).encode())
    
    def do_OPTIONS(self):
        # Handle preflight CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def detect_platform(self, url):
        """Deteksi platform dari URL"""
        url_lower = url.lower()
        if 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'facebook'
        else:
            return 'unknown'
    
    def try_yt_dlp(self, url, platform):
        """Method 1: Coba dengan yt-dlp dengan berbagai opsi"""
        try:
            # Variasi opsi untuk mencoba berbagai cara
            options_list = [
                # Opsi 1: Standard
                {
                    'format': 'best[ext=mp4]/best',
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                    'ignoreerrors': True,
                    'no_color': True,
                    'ssl_verify': False,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                # Opsi 2: Dengan cookies simulator
                {
                    'format': 'best',
                    'quiet': True,
                    'nocheckcertificate': True,
                    'ignoreerrors': True,
                    'cookiefile': None,
                    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
                },
                # Opsi 3: Generic extractor
                {
                    'format': 'best',
                    'quiet': True,
                    'nocheckcertificate': True,
                    'force_generic_extractor': True,
                    'ignoreerrors': True,
                }
            ]
            
            # Tambah opsi khusus platform
            if platform == 'instagram':
                for opts in options_list:
                    opts['force_generic_extractor'] = True
                    opts['extract_flat'] = False
            
            # Coba setiap opsi
            for i, ydl_opts in enumerate(options_list):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        
                        if info and isinstance(info, dict):
                            # Coba ambil direct link
                            direct_link = None
                            
                            # Method A: Langsung dari 'url'
                            direct_link = info.get('url')
                            
                            # Method B: Dari 'formats'
                            if not direct_link and info.get('formats'):
                                formats = info['formats']
                                if isinstance(formats, list):
                                    for f in formats:
                                        if isinstance(f, dict):
                                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                                direct_link = f.get('url')
                                                break
                                    if not direct_link and formats and isinstance(formats[-1], dict):
                                        direct_link = formats[-1].get('url')
                            
                            # Method C: Dari 'entries' (playlist)
                            if not direct_link and info.get('entries'):
                                entries = info['entries']
                                if entries and isinstance(entries, list) and len(entries) > 0:
                                    first = entries[0]
                                    if isinstance(first, dict):
                                        direct_link = first.get('url')
                            
                            if direct_link:
                                return {
                                    "status": "success",
                                    "direct_link": direct_link,
                                    "title": info.get('title', 'Video'),
                                    "platform": info.get('extractor_key', platform),
                                    "thumbnail": info.get('thumbnail'),
                                    "method": f"yt-dlp_option_{i+1}"
                                }
                except Exception as e:
                    continue  # Coba opsi berikutnya
            
            return None
        except Exception as e:
            return None
    
    def try_tiktok_fallback(self, url):
        """Method 2: Fallback khusus TikTok"""
        try:
            # Bersihkan URL dari parameter tracking
            import re
            clean_url = re.sub(r'\?.*$', '', url)
            
            # Daftar API TikTok publik
            apis = [
                {
                    "url": f"https://www.tikwm.com/api/",
                    "method": "POST",
                    "data": {"url": clean_url, "hd": 1},
                    "parse": lambda x: x.get('data', {}).get('play')
                },
                {
                    "url": f"https://api.tikmate.cc/api",
                    "method": "POST", 
                    "data": {"url": clean_url},
                    "parse": lambda x: f"https://tikmate.cc/download/{x.get('token', '')}/{x.get('vid', '')}.mp4"
                },
                {
                    "url": f"https://tiktok-video-no-watermark2.p.rapidapi.com/",
                    "method": "GET",
                    "headers": {
                        "X-RapidAPI-Key": "demo",  # Ganti dengan API key jika punya
                        "X-RapidAPI-Host": "tiktok-video-no-watermark2.p.rapidapi.com"
                    },
                    "params": {"url": clean_url},
                    "parse": lambda x: x.get('videoUrl')
                },
                {
                    "url": f"https://api.douyin.wtf/api",
                    "method": "GET",
                    "params": {"url": clean_url},
                    "parse": lambda x: x.get('video_url')
                }
            ]
            
            for api in apis:
                try:
                    if api["method"] == "POST":
                        response = requests.post(
                            api["url"], 
                            data=api.get("data", {}),
                            timeout=10,
                            verify=False,
                            headers={"User-Agent": "Mozilla/5.0"}
                        )
                    else:
                        response = requests.get(
                            api["url"],
                            params=api.get("params", {}),
                            headers=api.get("headers", {}),
                            timeout=10,
                            verify=False
                        )
                    
                    if response.status_code == 200:
                        data = response.json()
                        direct_link = api["parse"](data)
                        if direct_link:
                            return {
                                "status": "success",
                                "direct_link": direct_link,
                                "platform": "tiktok",
                                "method": "fallback_api",
                                "title": "TikTok Video"
                            }
                except:
                    continue
            
            return None
        except Exception as e:
            return None
    
    def try_instagram_fallback(self, url):
        """Method 3: Fallback khusus Instagram"""
        try:
            import re
            clean_url = re.sub(r'\?.*$', '', url)
            
            # API Instagram
            apis = [
                {
                    "url": "https://instagram-downloader-download-instagram-videos-stories1.p.rapidapi.com/get-info-rapid",
                    "method": "POST",
                    "headers": {
                        "X-RapidAPI-Key": "demo",  # Ganti dengan API key
                        "Content-Type": "application/json"
                    },
                    "data": {"url": clean_url},
                    "parse": lambda x: x.get('video_url') or x.get('display_url')
                },
                {
                    "url": "https://api.instagram.com/oembed/",
                    "method": "GET",
                    "params": {"url": clean_url},
                    "parse": lambda x: x.get('thumbnail_url')  # Fallback ke thumbnail
                }
            ]
            
            for api in apis:
                try:
                    if api["method"] == "POST":
                        response = requests.post(
                            api["url"],
                            json=api.get("data", {}),
                            headers=api.get("headers", {}),
                            timeout=10,
                            verify=False
                        )
                    else:
                        response = requests.get(
                            api["url"],
                            params=api.get("params", {}),
                            timeout=10,
                            verify=False
                        )
                    
                    if response.status_code == 200:
                        data = response.json()
                        direct_link = api["parse"](data)
                        if direct_link:
                            return {
                                "status": "success",
                                "direct_link": direct_link,
                                "platform": "instagram",
                                "method": "fallback_api",
                                "title": "Instagram Video"
                            }
                except:
                    continue
            
            return None
        except Exception as e:
            return None
    
    def try_direct_request(self, url):
        """Method 4: Coba dengan requests langsung (untuk video sederhana)"""
        try:
            # Cek apakah URL langsung mengarah ke video
            if any(ext in url.lower() for ext in ['.mp4', '.mov', '.avi']):
                return {
                    "status": "success",
                    "direct_link": url,
                    "platform": "direct",
                    "method": "direct_url"
                }
            
            # Coba ambil dari meta tag
            response = requests.get(url, timeout=10, verify=False, headers={
                "User-Agent": "Mozilla/5.0"
            })
            
            if response.status_code == 200:
                import re
                # Cari URL video di meta tag
                video_pattern = r'(https?://[^\s"\']+\.(mp4|mov|avi))'
                matches = re.findall(video_pattern, response.text)
                if matches:
                    return {
                        "status": "success",
                        "direct_link": matches[0][0],
                        "platform": "direct",
                        "method": "meta_extract"
                    }
            
            return None
        except Exception as e:
            return None
