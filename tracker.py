from flask import Flask, redirect, request, jsonify
import time
import os

app = Flask(__name__)

# Simpan user yang sudah klik {user_id: timestamp}
clicked_users = {}

# Ganti dengan link Shopee affiliate kamu
SHOPEE_AFFILIATE_URL = "https://shope.ee/XXXXXXXX"

# Token expire 10 menit
EXPIRE_SECONDS = 600

@app.route("/click/<int:user_id>")
def track_click(user_id):
    """User klik link ini → dicatat → redirect ke Shopee"""
    clicked_users[user_id] = time.time()
    return redirect(SHOPEE_AFFILIATE_URL)

@app.route("/check/<int:user_id>")
def check_click(user_id):
    """Bot cek apakah user sudah klik"""
    ts = clicked_users.get(user_id)
    if ts and (time.time() - ts) < EXPIRE_SECONDS:
        return jsonify({"clicked": True})
    return jsonify({"clicked": False})

@app.route("/reset/<int:user_id>")
def reset_click(user_id):
    """Reset status user setelah download selesai"""
    clicked_users.pop(user_id, None)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
