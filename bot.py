import os
import re
import tempfile
import random
import time
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
TRACKER_URL = "http://localhost:5000"
SHOPEE_URLS = [
    "https://s.shopee.co.id/8fOSavcGG9",   # Wipol Karbol
    "https://s.shopee.co.id/2qQfeIgImI",   # Kopi Kapal Api
    "https://s.shopee.co.id/8V52OlZKSQ",   # Kabel Baseus
    "https://s.shopee.co.id/70GEc3969V",   # Vitamin C Blackmores
    "https://s.shopee.co.id/5AoaQilmod",   # Pulpen Pilot G2
]

# Rate limit: max download per jam per user
RATE_LIMIT = 5

URL_PATTERN = re.compile(r'https?://\S+')
pending_downloads = {}  # {user_id: url}
rate_tracker = {}       # {user_id: [timestamps]}

DB_PATH = Path(__file__).parent / "bot.db"

# ─── Database ────────────────────────────────────────────────────────────────

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT,
            title TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    con.commit()
    con.close()

def register_user(user):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (user.id, user.username, user.first_name, datetime.now().isoformat()))
    con.commit()
    con.close()

def log_download(user_id, url, title, status):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO downloads (user_id, url, title, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, url, title, status, datetime.now().isoformat()))
    con.commit()
    con.close()

def get_stats():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    total_users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_downloads = cur.execute("SELECT COUNT(*) FROM downloads WHERE status='success'").fetchone()[0]
    total_failed = cur.execute("SELECT COUNT(*) FROM downloads WHERE status='failed'").fetchone()[0]
    con.close()
    return total_users, total_downloads, total_failed

def get_all_users():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    rows = cur.execute("SELECT user_id FROM users").fetchall()
    con.close()
    return [r[0] for r in rows]

def get_user_history(user_id, limit=5):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    rows = cur.execute("""
        SELECT title, url, status, created_at FROM downloads
        WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    con.close()
    return rows

# ─── Rate Limit ──────────────────────────────────────────────────────────────

def check_rate_limit(user_id: int) -> tuple[bool, int]:
    """Return (allowed, remaining)"""
    now = time.time()
    timestamps = rate_tracker.get(user_id, [])
    # Hapus yang lebih dari 1 jam
    timestamps = [t for t in timestamps if now - t < 3600]
    rate_tracker[user_id] = timestamps
    remaining = RATE_LIMIT - len(timestamps)
    if len(timestamps) >= RATE_LIMIT:
        return False, 0
    return True, remaining - 1

def add_rate_entry(user_id: int):
    rate_tracker.setdefault(user_id, []).append(time.time())

# ─── yt-dlp opts ─────────────────────────────────────────────────────────────

def get_ydl_opts(output_dir, quality="best", audio_only=False):
    if audio_only:
        return {
            'format': 'bestaudio/best',
            'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
    fmt = {
        "360": "bestvideo[height<=360][ext=mp4]+bestaudio/best[height<=360]",
        "720": "bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]",
        "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]",
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
    }.get(quality, "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best")
    return {
        'format': fmt,
        'merge_output_format': 'mp4',
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

# ─── Commands ────────────────────────────────────────────────────────────────

SUPPORTED_PLATFORMS = """
📱 *Platform yang didukung:*

• TikTok
• YouTube & YouTube Shorts
• Instagram (Reels, Post)
• Twitter / X
• Facebook
• Reddit
• Twitch (clips & VOD)
• Bilibili, Dailymotion, Vimeo
• Dan 1000+ platform lainnya\\!

❌ *Tidak didukung:*
• Netflix, Disney\\+, Spotify \\(DRM\\)
• Video private/akun private
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)
    await update.message.reply_text(
        "👋 Heyy, selamat datang!\n\n"
        "Aku siap bantu kamu download video dari mana aja —\n"
        "TikTok, YouTube, Instagram, Twitter, dan masih banyak lagi! 🎬\n\n"
        "Caranya gampang banget:\n"
        "Tinggal kirim link videonya ke sini, sisanya biar aku yang urus~ 😊\n\n"
        "Ketik /help untuk info lebih lanjut ya!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(SUPPORTED_PLATFORMS, parse_mode="MarkdownV2")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rows = get_user_history(user_id)
    if not rows:
        await update.message.reply_text("😊 Kamu belum pernah download apapun nih~")
        return
    text = "📋 *5 Download Terakhirmu:*\n\n"
    for title, url, status, created_at in rows:
        icon = "✅" if status == "success" else "❌"
        date = created_at[:10]
        title_safe = (title or "Unknown")[:40].replace("*","").replace("_","")
        text += f"{icon} {title_safe}\n_{date}_\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Kamu tidak punya akses ke sini ya~")
        return
    total_users, total_downloads, total_failed = get_stats()
    await update.message.reply_text(
        f"📊 *Statistik Bot*\n\n"
        f"👥 Total user: `{total_users}`\n"
        f"✅ Total download sukses: `{total_downloads}`\n"
        f"❌ Total gagal: `{total_failed}`",
        parse_mode="Markdown"
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Kamu tidak punya akses ke sini ya~")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <pesan>")
        return
    text = " ".join(context.args)
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, text)
            success += 1
        except:
            pass
    await update.message.reply_text(f"✅ Pesan terkirim ke {success}/{len(users)} user.")

# ─── Download Flow ────────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)
    text = update.message.text or ""
    urls = URL_PATTERN.findall(text)
    if not urls:
        return

    url = urls[0]
    user_id = update.effective_user.id

    # Rate limit (skip untuk owner)
    if user_id != OWNER_ID:
        allowed, remaining = check_rate_limit(user_id)
        if not allowed:
            await update.message.reply_text(
                "😅 Wah, kamu sudah download terlalu banyak nih!\n"
                "Tunggu sekitar 1 jam ya sebelum download lagi~ 🙏"
            )
            return

    # Owner: langsung download best quality, skip semua step
    if user_id == OWNER_ID:
        pending_downloads[user_id] = {"url": url, "quality": "best", "audio_only": False}
        msg = await update.message.reply_text("⏳ Mendownload...")
        await do_download(msg, pending_downloads[user_id], user_id, edit=True, owner=True)
        return

    # Simpan URL + tampilkan pilihan kualitas
    pending_downloads[user_id] = {"url": url, "quality": "best", "audio_only": False}

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"quality_{user_id}_audio"),
            InlineKeyboardButton("📱 360p", callback_data=f"quality_{user_id}_360"),
        ],
        [
            InlineKeyboardButton("🎬 720p", callback_data=f"quality_{user_id}_720"),
            InlineKeyboardButton("🔥 1080p", callback_data=f"quality_{user_id}_1080"),
        ],
    ])

    await update.message.reply_text(
        "🎞️ *Pilih kualitas download:*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    # Tombol donasi
    if data.startswith("donate_"):
        await query.answer()
        qris_path = Path(__file__).parent / "qris.jpg"
        with open(qris_path, 'rb') as f:
            await query.message.reply_photo(
                photo=f,
                caption="❤️ *Terima kasih atas dukunganmu!*\n\nScan QRIS di atas untuk donasi ya~ 🙏\n_EDIKUR.EXE STORE_",
                parse_mode="Markdown"
            )
        return

    # Pilih kualitas
    if data.startswith("quality_"):
        _, uid, quality = data.split("_", 2)
        if int(uid) != user_id:
            await query.answer("❌ Bukan requestmu!", show_alert=True)
            return

        pending = pending_downloads.get(user_id)
        if not pending:
            await query.edit_message_text("😔 Request expired, kirim ulang linknya ya~")
            return

        if quality == "audio":
            pending["audio_only"] = True
        else:
            pending["quality"] = quality

        await query.answer()

        # Owner skip sponsor
        if user_id == OWNER_ID:
            await query.edit_message_text("⏳ Mendownload...")
            await do_download(query.message, pending, user_id, edit=True)
            return

        # Tampilkan gatcha sponsor
        btn_download = InlineKeyboardButton("⚡ Tombol 1", callback_data=f"download_{user_id}")
        btn_affiliate = InlineKeyboardButton("⚡ Tombol 2", url=random.choice(SHOPEE_URLS))
        buttons = [btn_download, btn_affiliate]
        random.shuffle(buttons)

        await query.edit_message_text(
            "⚡ *Download siap\\!*\n\n"
            "Di antara dua tombol ini,\n"
            "tersembunyi satu jalan menuju videomu\\.\\.\\.\n\n"
            "Mana pilihanmu? 🤔",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([buttons])
        )
        return

    # Tombol download dipilih
    if data.startswith("download_"):
        _, uid = data.split("_", 1)
        if int(uid) != user_id:
            await query.answer("❌ Bukan requestmu!", show_alert=True)
            return

        pending = pending_downloads.get(user_id)
        if not pending:
            await query.edit_message_text("😔 Request expired, kirim ulang linknya ya~")
            return

        await query.answer()
        await query.edit_message_text("⏳ Mendownload...")
        await do_download(query.message, pending, user_id, edit=True)

async def do_download(message, pending: dict, user_id: int, edit=False, owner=False):
    url = pending["url"]
    quality = pending.get("quality", "best")
    audio_only = pending.get("audio_only", False)

    async def update_text(text):
        if edit:
            await message.edit_text(text)
        else:
            await message.reply_text(text)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            opts = get_ydl_opts(tmppath, quality, audio_only)

            await update_text("⏳ Mendownload... 0%")

            last_update = [0]

            def progress_hook(d):
                if d['status'] == 'downloading':
                    pct = d.get('_percent_str', '?').strip()
                    now = time.time()
                    if now - last_update[0] > 3:
                        last_update[0] = now
                        import asyncio
                        asyncio.get_event_loop().create_task(
                            update_text(f"⏳ Mendownload... {pct}")
                        )

            opts['progress_hooks'] = [progress_hook]

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Video')

                if audio_only:
                    files = list(tmppath.glob("*.mp3"))
                else:
                    files = list(tmppath.glob("*.mp4")) or list(tmppath.glob("*.*"))

                if not files:
                    await update_text("😔 Maaf, file tidak ditemukan setelah download~")
                    log_download(user_id, url, title, "failed")
                    return

                filepath = files[0]
                filesize = filepath.stat().st_size

                if filesize > 50 * 1024 * 1024:
                    await update_text("😔 Maaf ya, videonya terlalu besar untuk dikirim lewat Telegram (max 50MB)~")
                    log_download(user_id, url, title, "failed")
                    return

                await update_text("📤 Mengirim...")

                add_rate_entry(user_id)
                pending_downloads.pop(user_id, None)

                with open(filepath, 'rb') as f:
                    if audio_only:
                        await message.reply_audio(
                            audio=f,
                            caption=f"🎵 {title[:200]}",
                        )
                    else:
                        await message.reply_video(
                            video=f,
                            caption=f"✅ {title[:200]}",
                            supports_streaming=True
                        )

                await message.delete()

                # Kirim button donasi (skip untuk owner)
                if not owner:
                    donate_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("❤️ Donasi via QRIS", callback_data=f"donate_{user_id}")]
                    ])
                    await message.reply_text(
                        "🙏 Terima kasih sudah menggunakan bot ini!\n"
                        "Kalau berkenan, boleh donasi buat bantu biaya server ya~ 😊",
                        reply_markup=donate_keyboard
                    )
                log_download(user_id, url, title, "success")

    except yt_dlp.utils.DownloadError as e:
        err = str(e)
        if "Unsupported URL" in err:
            await update_text("😔 Maaf, platform ini belum didukung ya...")
        elif "private" in err.lower():
            await update_text("🔒 Sepertinya videonya private, jadi aku tidak bisa mengaksesnya. Coba link lain ya~")
        elif "429" in err:
            await update_text("😅 Waduh, terlalu banyak request nih. Tunggu sebentar ya, lalu coba lagi~")
        else:
            await update_text(f"🙏 Maaf ya, ada kendala saat download:\n{err[:200]}")
        log_download(user_id, url, "", "failed")
    except Exception as e:
        await update_text(f"😢 Ups, ada yang tidak beres nih...\nCoba lagi ya~ {str(e)[:150]}")
        log_download(user_id, url, "", "failed")

# ─── Main ─────────────────────────────────────────────────────────────────────

async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "Mulai bot"),
        BotCommand("help", "Platform yang didukung"),
        BotCommand("history", "5 download terakhirmu"),
        BotCommand("stats", "Statistik bot (owner only)"),
        BotCommand("broadcast", "Kirim pesan ke semua user (owner only)"),
    ])

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
