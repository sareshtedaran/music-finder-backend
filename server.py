from flask import Flask, request, jsonify
import subprocess
import uuid
import os
import requests

app = Flask(__name__)

ACR_HOST = "https://identify-eu-west-1.acrcloud.com"
ACR_ACCESS_KEY = "e4cc287adf8d56569db901dc4ad1c5b3"
ACR_ACCESS_SECRET = "or3cL0LweYfBX7q2XN5niu8SPvsmB1nQ9E0VakSy"

def download_instagram_video(url):
    video_id = str(uuid.uuid4())
    output_path = f"{video_id}.mp4"
    command = ["yt-dlp", "-o", output_path, url]
    subprocess.run(command, capture_output=True)
    return output_path

def extract_audio(video_path):
    audio_path = video_path.replace(".mp4", ".mp3")
    command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", audio_path]
    subprocess.run(command, capture_output=True)
    return audio_path

def identify_song(file_path):
    import hmac
    import hashlib
    import base64
    import time

    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = f"{http_method}\n{http_uri}\n{ACR_ACCESS_KEY}\n{data_type}\n{signature_version}\n{timestamp}"
    sign = base64.b64encode(
        hmac.new(ACR_ACCESS_SECRET.encode(), string_to_sign.encode(), digestmod=hashlib.sha1).digest()
    ).decode()

    files = {'sample': open(file_path, 'rb')}
    data = {
        'access_key': ACR_ACCESS_KEY,
        'data_type': data_type,
        'signature_version': signature_version,
        'signature': sign,
        'timestamp': timestamp,
    }

    response = requests.post(ACR_HOST + http_uri, files=files, data=data)
    return response.json()

@app.route('/identify', methods=['POST'])
def identify():
    data = request.json
    video_url = data.get('url')
    if not video_url:
        return jsonify({"error": "URL is required"}), 400

    video_path = download_instagram_video(video_url)
    audio_path = extract_audio(video_path)
    result = identify_song(audio_path)

    os.remove(video_path)
    os.remove(audio_path)

    return jsonify(result)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
