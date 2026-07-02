#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import time
import os
import requests
import re
from pathlib import Path

# ===================== RENKLİ ÇIKTI =====================
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_colored(color, text):
    print(f"{color}{text}{Colors.NC}")

# ===================== SSH101.com AYARLARI =====================
RTMP_URL = "rtmp://ssh101.bozztv.com:1935/ssh101"
STREAM_KEY = "tvgo2"
rtmp_server = f"{RTMP_URL}/{STREAM_KEY}"

# ===================== M3U KAYNAĞI =====================
M3U_SOURCE = "https://raw.githubusercontent.com/ibrahirahim/yayin/refs/heads/main/playlist.m3u"
LOGO_URL = "https://i.hizliresim.com/rq6o3ie.png"

def is_github_actions():
    return 'GITHUB_ACTIONS' in os.environ

def check_dependencies():
    print_colored(Colors.YELLOW, "[1/5] Bağımlılıklar kontrol ediliyor...")
    try:
        import requests
        print_colored(Colors.GREEN, "✅ requests paketi yüklü")
    except ImportError:
        print_colored(Colors.RED, "❌ requests paketi yüklü değil, yükleniyor...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print_colored(Colors.GREEN, "✅ FFmpeg yüklü")
    except:
        print_colored(Colors.RED, "❌ FFmpeg bulunamadı!")

def m3u_dan_linkleri_cek(m3u_url):
    print_colored(Colors.YELLOW, "[2/5] M3U dosyası işleniyor...")
    try:
        if m3u_url.startswith('http'):
            print_colored(Colors.BLUE, f"📥 M3U indiriliyor: {m3u_url}")
            response = requests.get(m3u_url, timeout=30)
            response.raise_for_status()
            m3u_icerik = response.text
        else:
            with open(m3u_url, 'r', encoding='utf-8') as f:
                m3u_icerik = f.read()
        
        video_linkleri = []
        for satir in m3u_icerik.split('\n'):
            satir = satir.strip()
            if satir.startswith('#EXTINF'):
                continue
            if satir.startswith('http'):
                video_linkleri.append(satir)
        
        if len(video_linkleri) == 0:
            tum_linkler = re.findall(r'https?://[^\s"]+', m3u_icerik)
            video_linkleri = [link for link in tum_linkler if not link.endswith('.m3u')]
        
        print_colored(Colors.GREEN, f"✅ {len(video_linkleri)} video linki bulundu!")
        return video_linkleri
    except Exception as e:
        print_colored(Colors.RED, f"❌ M3U işleme hatası: {e}")
        return []

def download_logo():
    print_colored(Colors.YELLOW, "[3/5] Logo indiriliyor...")
    try:
        if LOGO_URL.startswith('http'):
            response = requests.get(LOGO_URL, timeout=30)
            response.raise_for_status()
            with open('logo.png', 'wb') as f:
                f.write(response.content)
            print_colored(Colors.GREEN, "✅ Logo indirildi")
            return True
    except Exception as e:
        print_colored(Colors.RED, f"❌ Logo indirme hatası: {e}")
        return False

def start_stream(video_list):
    print_colored(Colors.YELLOW, "[4/5] Yayın hazırlanıyor...")
    
    if len(video_list) == 0:
        print_colored(Colors.RED, "❌ Yayın için video bulunamadı!")
        return False
    
    print_colored(Colors.BLUE, "=" * 50)
    print_colored(Colors.GREEN, "  SSH101.com Yayın Başlatılıyor")
    print_colored(Colors.BLUE, "=" * 50)
    print_colored(Colors.BLUE, f"📡 RTMP: {rtmp_server}")
    print_colored(Colors.BLUE, f"🎬 Video Sayısı: {len(video_list)}")
    print_colored(Colors.BLUE, f"🌐 İzleme: https://ssh101.com/live/{STREAM_KEY}")
    print_colored(Colors.BLUE, "=" * 50)
    
    video_index = 0
    while True:
        try:
            video_url = video_list[video_index]
            print_colored(Colors.GREEN, f"▶ Yayınlanıyor [{video_index+1}/{len(video_list)}]: {video_url}")
            
            command = [
                'ffmpeg',
                '-re',
                '-i', video_url,
                '-i', 'logo.png',
                '-filter_complex',
                '[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black[v0];'
                '[1:v]scale=230:90[logo];'
                '[v0][logo]overlay=W-w-10:3,'
                'drawtext=text=\'SSH101.com\':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.6:boxborderw=5:x=(w-text_w)/2:y=h-text_h-20[v]',
                '-map', '[v]',
                '-map', '0:a?',
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-pix_fmt', 'yuv420p',
                '-b:v', '4000k',
                '-maxrate', '4000k',
                '-bufsize', '8000k',
                '-g', '50',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',
                '-f', 'flv',
                rtmp_server
            ]
            
            process = subprocess.Popen(command)
            process.wait()
            
            video_index = (video_index + 1) % len(video_list)
            print_colored(Colors.BLUE, "⏳ Sıradaki videoya geçiliyor...")
            time.sleep(2)
            
        except KeyboardInterrupt:
            print_colored(Colors.RED, "\n⛔ Yayın durduruluyor...")
            if 'process' in locals():
                process.terminate()
                process.wait()
            print_colored(Colors.GREEN, "✅ Yayın sonlandırıldı.")
            break
        except Exception as e:
            print_colored(Colors.RED, f"❌ Yayın hatası: {e}")
            time.sleep(5)
            video_index = (video_index + 1) % len(video_list)

def main():
    print_colored(Colors.BLUE, "=" * 50)
    print_colored(Colors.GREEN, "  SSH101.com Yayın Sistemi")
    print_colored(Colors.BLUE, "=" * 50)
    
    if is_github_actions():
        print_colored(Colors.BLUE, "☁️ GitHub Actions ortamı tespit edildi")
    
    check_dependencies()
    
    playlist = []
    if M3U_SOURCE:
        playlist = m3u_dan_linkleri_cek(M3U_SOURCE)
    
    if len(playlist) == 0 and os.path.exists('playlist.m3u'):
        print_colored(Colors.YELLOW, "⚠️ Yerel playlist.m3u deneniyor...")
        playlist = m3u_dan_linkleri_cek('playlist.m3u')
    
    if len(playlist) == 0:
        print_colored(Colors.RED, "❌ Yayın için hiç video bulunamadı!")
        sys.exit(1)
    
    download_logo()
    
    print_colored(Colors.YELLOW, "[5/5] Yayın başlatılıyor...")
    print_colored(Colors.BLUE, "=" * 50)
    print_colored(Colors.GREEN, "✨ Yayın başlıyor! (Durdurmak için: Ctrl+C)")
    print_colored(Colors.BLUE, "=" * 50)
    
    start_stream(playlist)

if __name__ == "__main__":
    main()
