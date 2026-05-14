"""
پنل ادمین - Flask Web App
نصب: pip install flask python-telegram-bot
اجرا: python admin_panel.py
"""

import os
import json
import asyncio
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from db import Database
import requests as req

app = Flask(__name__)
app.secret_key = os.getenv("ADMIN_SECRET", "change_this_secret_key_123")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

db = Database()

# ── Auth ──────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────
# HTML Template (Space Blue Theme)
# ─────────────────────────────────────────────────────
BASE_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🚀 پنل ادمین Space Coin</title>
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #020817;
    --bg2: #0a1628;
    --bg3: #0f2040;
    --accent: #00d4ff;
    --accent2: #7c3aed;
    --accent3: #06b6d4;
    --text: #e2e8f0;
    --text2: #94a3b8;
    --border: #1e3a5f;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --card-bg: #0d1f3c;
    --glow: 0 0 20px rgba(0, 212, 255, 0.15);
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Vazirmatn', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    background-image:
      radial-gradient(ellipse at 20% 50%, rgba(124,58,237,0.08) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 20%, rgba(0,212,255,0.06) 0%, transparent 40%),
      url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='2' cy='2' r='1' fill='%23ffffff08'/%3E%3C/svg%3E");
  }
  .sidebar {
    position: fixed; right: 0; top: 0; width: 260px; height: 100vh;
    background: var(--bg2);
    border-left: 1px solid var(--border);
    padding: 24px 0;
    z-index: 100;
    box-shadow: -4px 0 30px rgba(0,0,0,0.5);
  }
  .sidebar-logo {
    padding: 0 24px 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
  }
  .sidebar-logo h2 {
    font-size: 1.2rem;
    font-weight: 900;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .sidebar-logo p { font-size: 0.75rem; color: var(--text2); margin-top: 4px; }
  .nav-item {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 24px;
    color: var(--text2);
    text-decoration: none;
    font-size: 0.9rem;
    transition: all 0.2s;
    border-right: 3px solid transparent;
  }
  .nav-item:hover, .nav-item.active {
    color: var(--accent);
    background: rgba(0,212,255,0.06);
    border-right-color: var(--accent);
  }
  .nav-item .icon { font-size: 1.2rem; width: 24px; text-align: center; }
  .nav-section { padding: 16px 24px 8px; font-size: 0.7rem; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; }
  .main { margin-right: 260px; padding: 32px; min-height: 100vh; }
  .page-header { margin-bottom: 32px; }
  .page-header h1 { font-size: 1.8rem; font-weight: 900; color: var(--text); }
  .page-header p { color: var(--text2); margin-top: 4px; }
  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 32px; }
  .stat-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--glow);
  }
  .stat-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 60px; height: 60px;
    background: radial-gradient(circle, rgba(0,212,255,0.15), transparent);
  }
  .stat-card .label { font-size: 0.8rem; color: var(--text2); margin-bottom: 8px; }
  .stat-card .value { font-size: 2rem; font-weight: 900; color: var(--accent); }
  .stat-card .icon { font-size: 2rem; position: absolute; top: 16px; left: 20px; opacity: 0.5; }
  .card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: var(--glow);
  }
  .card-title {
    font-size: 1.1rem; font-weight: 700;
    color: var(--text);
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 8px;
  }
  .form-group { margin-bottom: 16px; }
  .form-group label { display: block; font-size: 0.85rem; color: var(--text2); margin-bottom: 6px; }
  .form-control {
    width: 100%;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    color: var(--text);
    font-family: 'Vazirmatn', sans-serif;
    font-size: 0.9rem;
    outline: none;
    transition: border-color 0.2s;
  }
  .form-control:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(0,212,255,0.1); }
  .form-control select, select.form-control {
    background: var(--bg3);
    color: var(--text);
  }
  .btn {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 20px;
    border: none; border-radius: 10px;
    font-family: 'Vazirmatn', sans-serif;
    font-size: 0.9rem; font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
  }
  .btn-primary { background: linear-gradient(135deg, var(--accent3), var(--accent)); color: #000; }
  .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,212,255,0.4); }
  .btn-danger { background: var(--danger); color: #fff; }
  .btn-danger:hover { background: #dc2626; }
  .btn-success { background: var(--success); color: #fff; }
  .btn-warning { background: var(--warning); color: #000; }
  .btn-secondary { background: var(--bg3); color: var(--text2); border: 1px solid var(--border); }
  .btn-sm { padding: 6px 12px; font-size: 0.8rem; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: right; padding: 12px 16px; font-size: 0.8rem; color: var(--text2); border-bottom: 1px solid var(--border); font-weight: 600; }
  td { padding: 12px 16px; font-size: 0.85rem; border-bottom: 1px solid rgba(30,58,95,0.5); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(0,212,255,0.03); }
  .badge {
    display: inline-block;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
  }
  .badge-blue { background: rgba(0,212,255,0.15); color: var(--accent); }
  .badge-green { background: rgba(16,185,129,0.15); color: var(--success); }
  .badge-purple { background: rgba(124,58,237,0.15); color: #a78bfa; }
  .alert { padding: 12px 16px; border-radius: 10px; margin-bottom: 20px; font-size: 0.9rem; }
  .alert-success { background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: var(--success); }
  .alert-danger { background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: var(--danger); }
  .tabs { display: flex; gap: 4px; margin-bottom: 20px; background: var(--bg3); padding: 4px; border-radius: 12px; width: fit-content; }
  .tab-btn {
    padding: 8px 18px; border: none; border-radius: 9px;
    background: transparent; color: var(--text2);
    font-family: 'Vazirmatn', sans-serif; cursor: pointer;
    font-size: 0.85rem; transition: all 0.2s;
  }
  .tab-btn.active { background: var(--accent); color: #000; font-weight: 700; }
  .image-upload-area {
    border: 2px dashed var(--border); border-radius: 12px;
    padding: 30px; text-align: center; cursor: pointer;
    transition: all 0.2s; color: var(--text2);
  }
  .image-upload-area:hover { border-color: var(--accent); color: var(--accent); }
  .image-preview { width: 80px; height: 80px; border-radius: 12px; object-fit: cover; }
  .login-page {
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh;
  }
  .login-card {
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 24px; padding: 48px 40px; width: 380px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5), var(--glow);
    text-align: center;
  }
  .login-card h1 { font-size: 2rem; font-weight: 900; margin-bottom: 8px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .stars {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;
    background-image:
      radial-gradient(1px 1px at 10% 20%, white, transparent),
      radial-gradient(1px 1px at 30% 60%, white, transparent),
      radial-gradient(1px 1px at 50% 10%, white, transparent),
      radial-gradient(1px 1px at 70% 80%, white, transparent),
      radial-gradient(1px 1px at 90% 40%, white, transparent),
      radial-gradient(1.5px 1.5px at 20% 85%, rgba(255,255,255,0.6), transparent),
      radial-gradient(1.5px 1.5px at 60% 35%, rgba(255,255,255,0.6), transparent),
      radial-gradient(1.5px 1.5px at 80% 65%, rgba(255,255,255,0.6), transparent);
    opacity: 0.6;
  }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="stars"></div>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div style="position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:9999;min-width:300px;">
    {% for cat, msg in messages %}
      <div class="alert alert-{{ 'success' if cat == 'success' else 'danger' }}">{{ msg }}</div>
    {% endfor %}
    </div>
  {% endif %}
{% endwith %}
"""

NAV_HTML = """
<div class="sidebar">
  <div class="sidebar-logo">
    <h2>🚀 Space Coin</h2>
    <p>پنل مدیریت</p>
  </div>
  <div class="nav-section">عمومی</div>
  <a href="/" class="nav-item {{ 'active' if active=='dashboard' }}"><span class="icon">📊</span> داشبورد</a>
  <a href="/users" class="nav-item {{ 'active' if active=='users' }}"><span class="icon">👥</span> کاربران</a>
  <div class="nav-section">محتوا</div>
  <a href="/characters" class="nav-item {{ 'active' if active=='characters' }}"><span class="icon">🎮</span> شخصیت‌ها</a>
  <a href="/categories" class="nav-item {{ 'active' if active=='categories' }}"><span class="icon">📦</span> دسته‌بندی‌ها</a>
  <a href="/cards" class="nav-item {{ 'active' if active=='cards' }}"><span class="icon">🃏</span> کارت‌ها</a>
  <div class="nav-section">تنظیمات</div>
  <a href="/settings" class="nav-item {{ 'active' if active=='settings' }}"><span class="icon">⚙️</span> تنظیمات</a>
  <a href="/broadcast" class="nav-item {{ 'active' if active=='broadcast' }}"><span class="icon">📢</span> پیام همگانی</a>
  <a href="/logout" class="nav-item" style="margin-top:auto;color:var(--danger)"><span class="icon">🚪</span> خروج</a>
</div>
"""

FOOTER_HTML = """
</body>
</html>
"""

# ── Login ──────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/")
        flash("رمز عبور اشتباه است", "danger")

    html = BASE_HTML + """
    <div class="login-page" style="position:relative;z-index:1;">
      <div class="login-card">
        <div style="font-size:3rem;margin-bottom:16px;">🚀</div>
        <h1>Space Coin</h1>
        <p style="color:var(--text2);margin-bottom:32px;font-size:0.9rem;">پنل مدیریت</p>
        <form method="POST">
          <div class="form-group" style="text-align:right;">
            <label>رمز عبور ادمین</label>
            <input type="password" name="password" class="form-control" placeholder="رمز عبور را وارد کنید" autofocus>
          </div>
          <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px;">
            🔐 ورود
          </button>
        </form>
      </div>
    </div>
    """ + FOOTER_HTML
    return html


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ── Dashboard ──────────────────────────────────────────
@app.route("/")
@login_required
def dashboard():
    user_count = db.get_user_count()
    total_coins = db.get_total_coins()
    card_count = len(db.get_all_cards())
    cat_count = len(db.get_categories())
    top_users = db.get_leaderboard(5)

    rows = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, u in enumerate(top_users):
        name = u["first_name"] or u["username"] or "ناشناس"
        rows += f"""<tr>
          <td>{medals[i]}</td>
          <td>{name}</td>
          <td><span class="badge badge-blue">{u['coins']:,}</span></td>
          <td><span class="badge badge-green">@{u['username'] or '-'}</span></td>
        </tr>"""

    html = BASE_HTML + NAV_HTML.replace("{{ 'active' if active=='dashboard' }}", "active") \
        .replace("{{ 'active' if active=='users' }}", "") \
        .replace("{{ 'active' if active=='characters' }}", "") \
        .replace("{{ 'active' if active=='categories' }}", "") \
        .replace("{{ 'active' if active=='cards' }}", "") \
        .replace("{{ 'active' if active=='settings' }}", "") \
        .replace("{{ 'active' if active=='broadcast' }}", "") + f"""
    <div class="main">
      <div class="page-header">
        <h1>📊 داشبورد</h1>
        <p>خلاصه وضعیت ربات</p>
      </div>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="label">کل کاربران</div>
          <div class="value">{user_count:,}</div>
          <div class="icon">👥</div>
        </div>
        <div class="stat-card">
          <div class="label">کل سکه‌های منتشر شده</div>
          <div class="value">{total_coins:,}</div>
          <div class="icon">🪙</div>
        </div>
        <div class="stat-card">
          <div class="label">تعداد کارت‌ها</div>
          <div class="value">{card_count}</div>
          <div class="icon">🃏</div>
        </div>
        <div class="stat-card">
          <div class="label">دسته‌بندی‌ها</div>
          <div class="value">{cat_count}</div>
          <div class="icon">📦</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">🏆 برترین کاربران</div>
        <table>
          <thead><tr><th>رتبه</th><th>نام</th><th>سکه</th><th>یوزرنیم</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>
    """ + FOOTER_HTML
    return html


# ── Users ──────────────────────────────────────────────
@app.route("/users")
@login_required
def users():
    all_users = db.get_all_users()
    rows = ""
    for u in all_users[:100]:
        name = u["first_name"] or "ناشناس"
        rows += f"""<tr>
          <td>{u['user_id']}</td>
          <td>{name}</td>
          <td>@{u['username'] or '-'}</td>
          <td><span class="badge badge-blue">{u['coins']:,}</span></td>
          <td>
            <a href="/user/{u['user_id']}/edit" class="btn btn-sm btn-secondary">ویرایش</a>
          </td>
        </tr>"""

    content = f"""
    <div class="main">
      <div class="page-header">
        <h1>👥 کاربران</h1>
        <p>مدیریت کاربران ربات</p>
      </div>
      <div class="card">
        <div class="card-title">📋 لیست کاربران ({len(all_users)} نفر)</div>
        <table>
          <thead><tr><th>آیدی</th><th>نام</th><th>یوزرنیم</th><th>سکه</th><th>عملیات</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>
    """
    return render_page(content, "users")


@app.route("/user/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    user = db.get_user(user_id)
    if not user:
        flash("کاربر پیدا نشد", "danger")
        return redirect("/users")

    if request.method == "POST":
        new_coins = int(request.form.get("coins", user["coins"]))
        db.conn.execute("UPDATE users SET coins=? WHERE user_id=?", (new_coins, user_id))
        db.conn.commit()
        flash("✅ تغییرات ذخیره شد", "success")
        return redirect("/users")

    content = f"""
    <div class="main">
      <div class="page-header">
        <h1>✏️ ویرایش کاربر</h1>
        <p>{user['first_name']} - @{user['username']}</p>
      </div>
      <div class="card" style="max-width:500px;">
        <div class="card-title">💰 ویرایش سکه</div>
        <form method="POST">
          <div class="form-group">
            <label>تعداد سکه</label>
            <input type="number" name="coins" class="form-control" value="{user['coins']}">
          </div>
          <button type="submit" class="btn btn-primary">💾 ذخیره</button>
          <a href="/users" class="btn btn-secondary" style="margin-right:8px;">انصراف</a>
        </form>
      </div>
    </div>
    """
    return render_page(content, "users")


# ── Characters ─────────────────────────────────────────
@app.route("/characters", methods=["GET", "POST"])
@login_required
def characters():
    if request.method == "POST":
        level_key = request.form.get("level_key")
        file_id = request.form.get("file_id", "").strip()
        if level_key and file_id:
            db.set_character_image(level_key, file_id)
            flash(f"✅ عکس شخصیت سطح {level_key} ذخیره شد", "success")
        return redirect("/characters")

    char_images = db.get_all_character_images()
    rows = ""
    for i in range(1, 11):
        key = f"level_{i}"
        file_id = char_images.get(key, "")
        rows += f"""
        <tr>
          <td><span class="badge badge-purple">سطح {i}</span></td>
          <td style="font-size:0.75rem;color:var(--text2);max-width:200px;overflow:hidden;text-overflow:ellipsis;">{file_id or '—'}</td>
          <td>
            <form method="POST" style="display:flex;gap:8px;align-items:center;">
              <input type="hidden" name="level_key" value="{key}">
              <input type="text" name="file_id" class="form-control" style="max-width:300px;" 
                     placeholder="File ID عکس تلگرام" value="{file_id}">
              <button type="submit" class="btn btn-sm btn-primary">💾</button>
            </form>
          </td>
        </tr>"""

    content = f"""
    <div class="main">
      <div class="page-header">
        <h1>🎮 شخصیت‌ها</h1>
        <p>عکس شخصیت برای هر سطح - File ID را از تلگرام وارد کنید</p>
      </div>
      <div class="card">
        <div class="card-title">💡 راهنما</div>
        <p style="color:var(--text2);font-size:0.85rem;line-height:1.8;">
          برای دریافت File ID عکس: عکس را به ربات @RawDataBot بفرستید. در پاسخ، photo > file_id را کپی کنید.<br>
          هر سطح می‌تواند عکس متفاوتی داشته باشد. وقتی کاربر به آن سطح رسید، عکس شخصیت تغییر می‌کند.
        </p>
      </div>
      <div class="card">
        <div class="card-title">🖼️ عکس‌های شخصیت (۱۰ سطح)</div>
        <table>
          <thead><tr><th>سطح</th><th>File ID فعلی</th><th>تغییر</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>
    """
    return render_page(content, "characters")


# ── Categories ─────────────────────────────────────────
@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            name = request.form.get("name", "").strip()
            icon = request.form.get("icon", "📦").strip()
            if name:
                db.create_category(name, icon)
                flash("✅ دسته‌بندی ایجاد شد", "success")
        elif action == "update":
            cat_id = int(request.form.get("cat_id"))
            name = request.form.get("name", "").strip()
            icon = request.form.get("icon", "📦").strip()
            db.update_category(cat_id, name, icon)
            flash("✅ دسته‌بندی ویرایش شد", "success")
        elif action == "delete":
            cat_id = int(request.form.get("cat_id"))
            db.delete_category(cat_id)
            flash("✅ دسته‌بندی حذف شد", "success")
        return redirect("/categories")

    cats = db.get_categories()
    rows = ""
    for cat in cats:
        rows += f"""
        <tr>
          <td>{cat['icon']} {cat['name']}</td>
          <td>{cat['id']}</td>
          <td>
            <button onclick="editCat({cat['id']}, '{cat['name']}', '{cat['icon']}')" class="btn btn-sm btn-secondary">✏️ ویرایش</button>
            <form method="POST" style="display:inline;" onsubmit="return confirm('حذف شود؟')">
              <input type="hidden" name="action" value="delete">
              <input type="hidden" name="cat_id" value="{cat['id']}">
              <button type="submit" class="btn btn-sm btn-danger">🗑️</button>
            </form>
          </td>
        </tr>"""

    content = f"""
    <div class="main">
      <div class="page-header">
        <h1>📦 دسته‌بندی‌ها</h1>
        <p>مدیریت دسته‌بندی کارت‌ها</p>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-title">➕ دسته‌بندی جدید</div>
          <form method="POST" id="catForm">
            <input type="hidden" name="action" id="catAction" value="create">
            <input type="hidden" name="cat_id" id="catId" value="">
            <div class="form-group">
              <label>نام دسته‌بندی</label>
              <input type="text" name="name" id="catName" class="form-control" placeholder="مثلا: فناوری" required>
            </div>
            <div class="form-group">
              <label>آیکون (ایموجی)</label>
              <input type="text" name="icon" id="catIcon" class="form-control" placeholder="💻" value="📦">
            </div>
            <button type="submit" class="btn btn-primary" id="catSubmitBtn">➕ ایجاد</button>
            <button type="button" onclick="resetCatForm()" class="btn btn-secondary" style="margin-right:8px;">انصراف</button>
          </form>
        </div>
        <div class="card">
          <div class="card-title">📋 دسته‌بندی‌های موجود ({len(cats)} عدد)</div>
          <table>
            <thead><tr><th>نام</th><th>آیدی</th><th>عملیات</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
      </div>
    </div>
    <script>
    function editCat(id, name, icon) {{
      document.getElementById('catAction').value = 'update';
      document.getElementById('catId').value = id;
      document.getElementById('catName').value = name;
      document.getElementById('catIcon').value = icon;
      document.getElementById('catSubmitBtn').textContent = '💾 ذخیره';
    }}
    function resetCatForm() {{
      document.getElementById('catAction').value = 'create';
      document.getElementById('catId').value = '';
      document.getElementById('catName').value = '';
      document.getElementById('catIcon').value = '📦';
      document.getElementById('catSubmitBtn').textContent = '➕ ایجاد';
    }}
    </script>
    """
    return render_page(content, "categories")


# ── Cards ──────────────────────────────────────────────
@app.route("/cards", methods=["GET", "POST"])
@login_required
def cards():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            db.create_card(
                cat_id=int(request.form.get("cat_id")),
                name=request.form.get("name", "").strip(),
                base_profit=int(request.form.get("base_profit", 100)),
                base_cost=int(request.form.get("base_cost", 1000)),
            )
            flash("✅ کارت ایجاد شد", "success")
        elif action == "update":
            db.update_card(
                card_id=int(request.form.get("card_id")),
                name=request.form.get("name", "").strip(),
                base_profit=int(request.form.get("base_profit", 100)),
                base_cost=int(request.form.get("base_cost", 1000)),
                cat_id=int(request.form.get("cat_id")),
            )
            flash("✅ کارت ویرایش شد", "success")
        elif action == "delete":
            db.delete_card(int(request.form.get("card_id")))
            flash("✅ کارت حذف شد", "success")
        elif action == "set_image":
            db.set_card_image(
                card_id=int(request.form.get("card_id")),
                level=int(request.form.get("level")),
                file_id=request.form.get("file_id", "").strip()
            )
            flash("✅ عکس کارت ذخیره شد", "success")
        return redirect("/cards")

    all_cards = db.get_all_cards()
    cats = db.get_categories()
    cat_options = "".join(f'<option value="{c["id"]}">{c["icon"]} {c["name"]}</option>' for c in cats)

    rows = ""
    for card in all_cards:
        rows += f"""
        <tr>
          <td>{card['id']}</td>
          <td><strong>{card['name']}</strong></td>
          <td><span class="badge badge-blue">{card['cat_name']}</span></td>
          <td>{card['base_profit']:,}/ساعت</td>
          <td>{card['base_cost']:,}</td>
          <td>
            <button onclick="editCard({card['id']}, '{card['name']}', {card['cat_id']}, {card['base_profit']}, {card['base_cost']})" 
                    class="btn btn-sm btn-secondary">✏️</button>
            <button onclick="openImageModal({card['id']}, '{card['name']}')" 
                    class="btn btn-sm btn-warning">🖼️</button>
            <form method="POST" style="display:inline;" onsubmit="return confirm('حذف شود؟')">
              <input type="hidden" name="action" value="delete">
              <input type="hidden" name="card_id" value="{card['id']}">
              <button type="submit" class="btn btn-sm btn-danger">🗑️</button>
            </form>
          </td>
        </tr>"""

    content = f"""
    <div class="main">
      <div class="page-header">
        <h1>🃏 کارت‌ها</h1>
        <p>مدیریت کارت‌ها - هر کارت ۱۰ سطح دارد</p>
      </div>
      <div class="card">
        <div class="card-title" id="formTitle">➕ کارت جدید</div>
        <form method="POST" id="cardForm">
          <input type="hidden" name="action" id="cardAction" value="create">
          <input type="hidden" name="card_id" id="cardIdHidden" value="">
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr auto;gap:12px;align-items:end;">
            <div class="form-group" style="margin:0;">
              <label>نام کارت</label>
              <input type="text" name="name" id="cardName" class="form-control" placeholder="ماهواره" required>
            </div>
            <div class="form-group" style="margin:0;">
              <label>دسته‌بندی</label>
              <select name="cat_id" id="cardCat" class="form-control">{cat_options}</select>
            </div>
            <div class="form-group" style="margin:0;">
              <label>سود پایه (در ساعت)</label>
              <input type="number" name="base_profit" id="cardProfit" class="form-control" value="500" required>
            </div>
            <div class="form-group" style="margin:0;">
              <label>هزینه پایه ارتقا</label>
              <input type="number" name="base_cost" id="cardCost" class="form-control" value="5000" required>
            </div>
            <div style="display:flex;gap:8px;">
              <button type="submit" class="btn btn-primary" id="cardSubmitBtn">➕</button>
              <button type="button" onclick="resetCardForm()" class="btn btn-secondary">↩️</button>
            </div>
          </div>
        </form>
      </div>
      <div class="card">
        <div class="card-title">📋 کارت‌های موجود ({len(all_cards)} عدد)</div>
        <table>
          <thead><tr><th>آیدی</th><th>نام</th><th>دسته‌بندی</th><th>سود</th><th>هزینه</th><th>عملیات</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>

    <!-- Modal عکس -->
    <div id="imageModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:1000;align-items:center;justify-content:center;">
      <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:16px;padding:32px;width:500px;max-width:90%;">
        <h3 style="margin-bottom:20px;color:var(--accent);" id="modalCardName">عکس کارت</h3>
        <form method="POST" id="imageForm">
          <input type="hidden" name="action" value="set_image">
          <input type="hidden" name="card_id" id="modalCardId">
          <div class="form-group">
            <label>سطح کارت</label>
            <select name="level" class="form-control">
              {"".join(f'<option value="{i}">سطح {i}</option>' for i in range(1,11))}
            </select>
          </div>
          <div class="form-group">
            <label>File ID عکس تلگرام</label>
            <input type="text" name="file_id" class="form-control" placeholder="AgACAgIAAxkBAAI..." required>
          </div>
          <p style="color:var(--text2);font-size:0.8rem;margin-bottom:16px;">
            💡 عکس را به @RawDataBot بفرستید و file_id را کپی کنید
          </p>
          <button type="submit" class="btn btn-primary">💾 ذخیره</button>
          <button type="button" onclick="closeModal()" class="btn btn-secondary" style="margin-right:8px;">انصراف</button>
        </form>
      </div>
    </div>

    <script>
    function editCard(id, name, catId, profit, cost) {{
      document.getElementById('cardAction').value = 'update';
      document.getElementById('cardIdHidden').value = id;
      document.getElementById('cardName').value = name;
      document.getElementById('cardCat').value = catId;
      document.getElementById('cardProfit').value = profit;
      document.getElementById('cardCost').value = cost;
      document.getElementById('cardSubmitBtn').textContent = '💾';
      document.getElementById('formTitle').textContent = '✏️ ویرایش کارت';
    }}
    function resetCardForm() {{
      document.getElementById('cardAction').value = 'create';
      document.getElementById('cardIdHidden').value = '';
      document.getElementById('cardName').value = '';
      document.getElementById('cardProfit').value = '500';
      document.getElementById('cardCost').value = '5000';
      document.getElementById('cardSubmitBtn').textContent = '➕';
      document.getElementById('formTitle').textContent = '➕ کارت جدید';
    }}
    function openImageModal(id, name) {{
      document.getElementById('modalCardId').value = id;
      document.getElementById('modalCardName').textContent = '🖼️ عکس کارت: ' + name;
      document.getElementById('imageModal').style.display = 'flex';
    }}
    function closeModal() {{
      document.getElementById('imageModal').style.display = 'none';
    }}
    </script>
    """
    return render_page(content, "cards")


# ── Settings ───────────────────────────────────────────
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        db.set_setting("bot_name", request.form.get("bot_name", "Space Coin"))
        db.set_setting("coins_per_tap", request.form.get("coins_per_tap", "1"))
        flash("✅ تنظیمات ذخیره شد", "success")
        return redirect("/settings")

    s = db.get_settings()
    content = f"""
    <div class="main">
      <div class="page-header">
        <h1>⚙️ تنظیمات</h1>
        <p>تنظیمات کلی ربات</p>
      </div>
      <div class="card" style="max-width:500px;">
        <div class="card-title">🔧 تنظیمات عمومی</div>
        <form method="POST">
          <div class="form-group">
            <label>نام ربات</label>
            <input type="text" name="bot_name" class="form-control" value="{s.get('bot_name','Space Coin')}">
          </div>
          <div class="form-group">
            <label>سکه به ازای هر کلیک</label>
            <input type="number" name="coins_per_tap" class="form-control" value="{s.get('coins_per_tap','1')}" min="1">
          </div>
          <button type="submit" class="btn btn-primary">💾 ذخیره تنظیمات</button>
        </form>
      </div>
    </div>
    """
    return render_page(content, "settings")


# ── Broadcast ──────────────────────────────────────────
@app.route("/broadcast", methods=["GET", "POST"])
@login_required
def broadcast():
    result_msg = ""
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
            users = db.get_all_users()
            sent = 0
            for u in users:
                try:
                    resp = req.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={"chat_id": u["user_id"], "text": message, "parse_mode": "Markdown"},
                        timeout=5
                    )
                    if resp.status_code == 200:
                        sent += 1
                except:
                    pass
            flash(f"✅ پیام به {sent} کاربر ارسال شد", "success")
        else:
            flash("پیام خالی یا توکن ربات تنظیم نشده", "danger")
        return redirect("/broadcast")

    content = f"""
    <div class="main">
      <div class="page-header">
        <h1>📢 پیام همگانی</h1>
        <p>ارسال پیام به همه کاربران</p>
      </div>
      <div class="card" style="max-width:600px;">
        <div class="card-title">✍️ متن پیام</div>
        <form method="POST">
          <div class="form-group">
            <label>پیام (از Markdown پشتیبانی می‌کند)</label>
            <textarea name="message" class="form-control" rows="6" placeholder="*سلام* به همه!&#10;&#10;یک خبر مهم داریم..."></textarea>
          </div>
          <button type="submit" class="btn btn-primary" onclick="return confirm('ارسال به همه کاربران؟')">
            📤 ارسال به همه
          </button>
        </form>
      </div>
    </div>
    """
    return render_page(content, "broadcast")


# ── Helper ─────────────────────────────────────────────
def render_page(content, active_page):
    nav = NAV_HTML
    for page in ["dashboard","users","characters","categories","cards","settings","broadcast"]:
        placeholder = "{{ 'active' if active=='" + page + "' }}"
        nav = nav.replace(placeholder, "active" if active_page == page else "")
    return BASE_HTML + nav + content + FOOTER_HTML


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
