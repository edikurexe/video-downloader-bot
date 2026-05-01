# 🎬 Video & Photo Downloader Bot

Bot Telegram untuk download video dan foto dari TikTok, YouTube, Instagram, Twitter, Facebook, dan 1000+ platform lainnya.

## Fitur

- ✅ Download video dari 1000+ platform (TikTok, YouTube, Instagram, Twitter, Facebook, dll)
- 📸 Download foto/slideshow dari TikTok, Instagram, Facebook
- 🎵 Download audio MP3
- 🎬 Pilih kualitas: 360p, 720p, 1080p, atau terbaik
- 👑 VIP system (skip sponsor, langsung download)
- ⏱️ Rate limit per user (5x/jam)
- 📋 Riwayat download (/history)
- 📊 Statistik bot (/stats) — owner only
- 📢 Broadcast pesan ke semua user (/broadcast) — owner only
- ❤️ Tombol donasi QRIS

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

3. Install gallery-dl (untuk foto/slideshow)
```bash
pip install gallery-dl
```

4. Salin .env.example ke .env lalu isi
```bash
cp .env.example .env
nano .env
```

5. Taruh file QRIS kamu dengan nama `qris.jpg` di folder yang sama

6. Jalankan bot
```bash
python bot.py
```

## Cara pakai

- **Video**: Kirim link video → pilih kualitas → tunggu dikirim
- **Foto/Slideshow**: Kirim link foto TikTok/IG/FB → otomatis dikirim sebagai album

## Command

| Command | Keterangan |
|---|---|
| /start | Mulai bot |
| /help | Platform yang didukung |
| /history | 5 download terakhir |
| /stats | Statistik bot (owner) |
| /broadcast | Kirim pesan ke semua user (owner) |
| /addvip | Tambah user VIP (owner) |
| /delvip | Hapus user VIP (owner) |
| /listvip | Lihat daftar VIP (owner) |

## Platform yang didukung (Foto)

| Platform | Foto/Slideshow | Video |
|----------|:-:|:-:|
| TikTok | ✅ | ✅ |
| Instagram | ✅ | ✅ |
| Facebook | ✅ | ✅ |
| YouTube | — | ✅ |
| Twitter/X | — | ✅ |

## Requirements

- Python 3.10+
- ffmpeg (untuk merge video+audio)
- gallery-dl (untuk download foto)

```bash
sudo apt install ffmpeg
pip install gallery-dl
```
