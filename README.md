# 🎬 Video Downloader Bot

Bot Telegram untuk download video dari TikTok, YouTube, Instagram, Twitter, dan 1000+ platform lainnya.

## Fitur

- Download video dari 1000+ platform (TikTok, YouTube, Instagram, Twitter, Facebook, dll)
- Pilih kualitas: 360p, 720p, 1080p, atau terbaik
- Download audio MP3
- Rate limit per user (5x/jam)
- Riwayat download (/history)
- Statistik bot (/stats) — owner only
- Broadcast pesan ke semua user (/broadcast) — owner only
- Tombol donasi QRIS

## Instalasi

1. Clone repo ini
```bash
git clone https://github.com/edikurexe/video-downloader-bot
cd video-downloader-bot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Salin .env.example ke .env lalu isi
```bash
cp .env.example .env
nano .env
```

4. Taruh file QRIS kamu dengan nama `qris.jpg` di folder yang sama

5. Jalankan bot
```bash
python bot.py
```

## Cara pakai

Kirim link video ke bot, pilih kualitas, lalu tunggu video dikirim.

## Command

| Command | Keterangan |
|---|---|
| /start | Mulai bot |
| /help | Platform yang didukung |
| /history | 5 download terakhir |
| /stats | Statistik bot (owner) |
| /broadcast | Kirim pesan ke semua user (owner) |

## Requirements

- Python 3.10+
- ffmpeg (untuk merge video+audio)

```bash
sudo apt install ffmpeg
```
