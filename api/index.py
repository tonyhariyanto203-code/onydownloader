from flask import Flask, render_template_string, request, jsonify
import yt_dlp
import os
import tempfile

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ony Downloader - Glassmorphism</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, sans-serif; }
        body {
            background: linear-gradient(135deg, #0f172a, #1e1b4b, #311042);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #fff;
            padding: 20px;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            width: 100%;
            max-width: 480px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            text-align: center;
        }
        h2 {
            margin-bottom: 8px;
            font-size: 26px;
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        p { color: #94a3b8; font-size: 13px; margin-bottom: 25px; }
        .input-group { display: flex; flex-direction: column; gap: 15px; }
        input[type="text"] {
            width: 100%;
            padding: 14px 16px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            color: #fff;
            font-size: 14px;
            outline: none;
            transition: 0.3s;
        }
        input[type="text"]:focus { border-color: #38bdf8; box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }
        button {
            padding: 14px;
            background: linear-gradient(to right, #0284c7, #4f46e5);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
        }
        button:hover { opacity: 0.9; transform: translateY(-2px); }
        #result { margin-top: 20px; text-align: left; font-size: 14px; }
        .download-link {
            display: block;
            margin-top: 10px;
            padding: 10px;
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid #10b981;
            color: #34d399;
            text-align: center;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
        }
        .loading { color: #38bdf8; font-style: italic; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="glass-card">
        <h2>✨ Ony Downloader</h2>
        <p>Minimalist YouTube Downloader & Glass UI</p>
        
        <div class="input-group">
            <input type="text" id="urlInput" placeholder="Tempel link YouTube di sini...">
            <button onclick="fetchVideo()">Ambil Link Download</button>
        </div>

        <div id="status"></div>
        <div id="result"></div>
    </div>

    <script>
        async function fetchVideo() {
            const url = document.getElementById('urlInput').value;
            const status = document.getElementById('status');
            const result = document.getElementById('result');

            if (!url) {
                status.innerHTML = '<span style="color: #f87171;">Masukkan URL YouTube dulu bro!</span>';
                return;
            }

            status.innerHTML = '<div class="loading">Sedang memproses video... Sabar ya...</div>';
            result.innerHTML = '';

            try {
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                const data = await response.json();

                if (data.error) {
                    status.innerHTML = `<span style="color: #f87171;">Error: ${data.error}</span>`;
                } else {
                    status.innerHTML = '';
                    result.innerHTML = `
                        <b style="color: #f1f5f9;">${data.title}</b>
                        <a href="${data.download_url}" class="download-link" target="_blank">📥 Download Video Sekarang</a>
                    `;
                }
            } catch (err) {
                status.innerHTML = '<span style="color: #f87171;">Terjadi kesalahan sistem!</span>';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/index', methods=['GET', 'POST'])
def api_index():
    if request.method == 'POST':
        data = request.get_json() or {}
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL tidak boleh kosong'}), 400

        cookie_content = os.environ.get('YOUTUBE_COOKIES')
        cookie_file_path = None

        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

        # Jika cookie tersedia di Environment Variables, buat file temporary otomatis
        if cookie_content:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(cookie_content)
                cookie_file_path = f.name
            ydl_opts['cookiefile'] = cookie_file_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return jsonify({'error': 'Gagal mengambil data video.'}), 500
                    
                video_title = info.get('title', 'Video YouTube')
                download_url = info.get('url')
                return jsonify({
                    'title': video_title,
                    'download_url': download_url
                })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Hapus file temporary setelah selesai dipakai untuk keamanan server
            if cookie_file_path and os.path.exists(cookie_file_path):
                os.remove(cookie_file_path)

    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)
