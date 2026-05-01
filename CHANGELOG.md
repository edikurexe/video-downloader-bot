# Changelog

Semua perubahan penting pada project ini didokumentasikan di sini.

---

## [1.2.0] - 2026-05-01

### ✨ Added
- **Download foto/slideshow** dari TikTok, Instagram, dan Facebook menggunakan `gallery-dl`
- Auto-detect TikTok slideshow (URL `/photo/`)
- Auto-detect Instagram post (URL `/p/`) — coba foto dulu, fallback ke video
- Auto-detect Facebook photo — coba foto dulu, fallback ke video
- Foto dikirim sebagai **album** (media group) di Telegram, max 10 foto
- **VIP system**: `/addvip`, `/delvip`, `/listvip` — VIP skip sponsor & langsung download best quality
- Fallback otomatis: jika yt-dlp gagal "Unsupported URL" pada TikTok, otomatis coba `gallery-dl`
- Resolve short URL TikTok (`vm.tiktok.com`, `vt.tiktok.com`) sebelum proses

### 📦 Dependencies
- Tambah `gallery-dl` di requirements.txt

---

## [1.1.0] - 2026-04-23

### 🔧 Fixed
- Hapus unused `TRACKER_URL` variable

---

## [1.0.0] - 2026-04-22

### 🎉 Initial Release
- Download video dari 1000+ platform (TikTok, YouTube, Instagram, Twitter, Facebook, dll)
- Pilih kualitas: 360p, 720p, 1080p, best
- Download audio MP3
- Rate limit 5x/jam per user
- Riwayat download (`/history`)
- Statistik bot (`/stats`) — owner only
- Broadcast pesan (`/broadcast`) — owner only
- Tombol donasi QRIS
- Gatcha sponsor (tombol acak affiliate Shopee)
