<div id="downloader-app" style="max-width: 500px; margin: 20px auto; padding: 25px; border-radius: 15px; background: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.1); font-family: sans-serif; text-align: center; border: 1px solid #eee;">
    <h2 style="color: #333; margin-bottom: 5px;">Video Downloader</h2>
    <p style="color: #666; font-size: 14px; margin-bottom: 20px;">TikTok & Instagram No Watermark</p>

    <input type="text" id="videoLink" placeholder="Tempel link video di sini..." 
        style="width: 100%; padding: 12px; border: 2px solid #000; border-radius: 8px; box-sizing: border-box; outline: none; font-size: 14px;">
    
    <button onclick="processDownload()" id="btnDownload" 
        style="width: 100%; margin-top: 15px; padding: 12px; background: #000; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.3s;">
        AMBIL VIDEO
    </button>

    <div id="loader" style="display:none; margin-top: 20px;">
        <div style="border: 4px solid #f3f3f3; border-top: 4px solid #000; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
        <p style="color: #888; font-size: 13px; margin-top: 10px;">Menghubungkan ke API kamu...</p>
    </div>

    <div id="resultArea" style="display: none; margin-top: 25px; border-top: 1px solid #eee; padding-top: 20px;">
        <video id="player" controls style="width: 100%; border-radius: 10px; background: #000; box-shadow: 0 5px 15px rgba(0,0,0,0.2);"></video>
        <div style="margin-top: 20px;">
            <a id="downloadBtn" href="#" rel="noreferrer" target="_blank" style="display: block; background: #25d366; color: white; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                DOWNLOAD VIDEO SEKARANG
            </a>
            <p style="font-size: 11px; color: #999; margin-top: 10px;">Tips: Jika tidak otomatis mendownload, tahan lama tombol lalu pilih "Download Link".</p>
        </div>
    </div>
</div>

<style>
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
#btnDownload:hover { background: #333; }
#btnDownload:disabled { background: #ccc; cursor: not-allowed; }
</style>

<script>
async function processDownload() {
    const linkInput = document.getElementById('videoLink');
    const btn = document.getElementById('btnDownload');
    const resArea = document.getElementById('resultArea');
    const loader = document.getElementById('loader');
    const player = document.getElementById('player');
    const downloadBtn = document.getElementById('downloadBtn');

    if (!linkInput.value) {
        alert("Masukkan link video dulu!");
        return;
    }

    // Reset Tampilan
    loader.style.display = "block";
    resArea.style.display = "none";
    btn.disabled = true;
    btn.innerText = "SEDANG BERPROSES...";

    try {
        // --- GANTI DENGAN LINK VERCEL KAMU ---
        const myApiUrl = "https://my-video-ap.vercel.app/download"; 
        
        const response = await fetch(`${myApiUrl}?url=${encodeURIComponent(linkInput.value)}`);
        const result = await response.json();

        if (result.status === "success") {
            const videoUrl = result.direct_link;
            
            // Masukkan link ke player dan tombol download
            player.src = videoUrl;
            downloadBtn.href = videoUrl;
            
            // Tampilkan area hasil
            resArea.style.display = "block";
        } else {
            alert("Gagal mengambil video: " + result.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Terjadi kesalahan. Pastikan API Vercel kamu sudah ter-deploy dengan benar.");
    } finally {
        loader.style.display = "none";
        btn.disabled = false;
        btn.innerText = "AMBIL VIDEO";
    }
}
</script>
