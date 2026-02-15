from flask import Flask, request, render_template_string, send_file
from flask_cors import CORS
import yt_dlp
import os
import re
import uuid

app = Flask(__name__)
CORS(app)

def get_video_id(url):
    patterns = [r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', r'(?:embed\/)([0-9A-Za-z_-]{11})', r'(?:shorts\/)([0-9A-Za-z_-]{11})', r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})']
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return None

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Sat.ytdownloader - Premium</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700;800&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Poppins', sans-serif; background: #000; color: #fff; text-align: center; padding: 20px; min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
            .card { background: #111; border: 1px solid #333; border-radius: 20px; padding: 30px; width: 100%; max-width: 500px; box-shadow: 0 10px 30px rgba(255,0,0,0.1); margin-top: 50px; }
            h1 { color: #ff0000; font-size: 28px; margin-bottom: 5px; }
            .tagline { color: #888; font-size: 12px; letter-spacing: 2px; margin-bottom: 30px; }
            input { width: 100%; padding: 15px; border-radius: 10px; border: 1px solid #333; background: #000; color: #fff; margin-bottom: 20px; }
            .btn { background: #ff0000; color: #fff; border: none; padding: 15px 25px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; transition: 0.3s; margin: 5px 0; }
            .btn-audio { background: #333; border: 1px solid #ff0000; }
            .btn:hover { transform: scale(1.02); opacity: 0.9; }
            #thumbnail { margin-top: 20px; border-radius: 10px; display: none; width: 100%; border: 2px solid #ff0000; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Sat.ytdownloader</h1>
            <p class="tagline">LUXURY VIDEO DOWNLOADER</p>
            <input type="text" id="url" placeholder="Paste YouTube Link here..." oninput="showThumb(this.value)">
            <img id="thumbnail" src="" alt="thumbnail">
            <form action="/download" method="post">
                <input type="hidden" name="url" id="formUrl">
                <input type="hidden" name="type" id="formType" value="video">
                <button type="submit" class="btn" onclick="document.getElementById('formType').value='video'">⬇️ Download Best Video</button>
                <button type="submit" class="btn btn-audio" onclick="document.getElementById('formType').value='audio'">🎵 Download MP3 Audio</button>
            </form>
        </div>
        <script>
            function showThumb(url) {
                document.getElementById('formUrl').value = url;
                const id = url.match(/(?:v=|\\/|shorts\\/)([0-9A-Za-z_-]{11})/);
                if(id) {
                    document.getElementById('thumbnail').src = "https://img.youtube.com/vi/" + id[1] + "/mqdefault.jpg";
                    document.getElementById('thumbnail').style.display = "block";
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/download', methods=['POST'])
def download():
    try:
        url = request.form['url']
        dtype = request.form.get('type')
        if not os.path.exists('downloads'): os.makedirs('downloads')
        
        uid = str(uuid.uuid4())[:8]
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': f'downloads/%(id)s_{uid}.%(ext)s',
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'extractor_args': {'youtube': {'player_client': ['ios', 'android']}},
            'http_headers': {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15'}
        }

        if dtype == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
        else:
            ydl_opts['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            title = "".join(c for c in info.get('title', 'video') if c.isalnum() or c in ' -_').strip()
            ext = 'mp3' if dtype == 'audio' else 'mp4'
            
        return send_file(path, as_attachment=True, download_name=f"{title}.{ext}")
            
    except Exception as e:
        return f"<html><body style='background:#000;color:#fff;text-align:center;'><h1>Error</h1><p>{str(e)}</p><a href='/' style='color:red;'>Back</a></body></html>"

if __name__ == '__main__':
    app.run(debug=False)
