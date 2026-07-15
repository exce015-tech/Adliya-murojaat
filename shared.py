# -*- coding: utf-8 -*-
"""
shared.py — ADLIYA-ALOQA uchun umumiy modul
============================================================================
Bu fayl o'zi ishga tushmaydi! U fuqaro_app.py va adliya_app.py ikkalasi
tomonidan import qilinadi va ular o'rtasida umumiy narsalarni ta'minlaydi:

  - Bitta umumiy Turso (libSQL) bulutli bazasi — ikkala sayt (garchi ular
    ikki mustaqil Streamlit Cloud ilovasi bo'lsa ham) shu bir bazaga
    yozadi/o'qiydi. Ulanish maʼlumotlari (URL, token) Streamlit "Secrets"
    orqali TURSO_DATABASE_URL va TURSO_AUTH_TOKEN nomlari bilan beriladi.
  - Umumiy konstantalar (soha ro'yxati, status bosqichlari va h.k.)
  - Umumiy CSS va vizual dizayn (regulation.gov.uz uslubiga yaqin: yuqori
    panel, loyiha-kartochka ko'rinishi, meta ma'lumotlar qatori).
  - Bir kishi bir murojaatga faqat bir marta ovoz bera olishini ta'minlovchi
    mexanizm (kontakt/telefon asosida).
  - Test murojaatlarni o'chirish funksiyalari (Adliya paneli uchun).
"""

import html
import datetime
import pandas as pd
import streamlit as st
import libsql_client

SOHALAR = [
    "Tadbirkorlik va litsenziyalash",
    "Transport va parkovka",
    "Qurilish va ko'chmas mulk",
    "Soliq va bojxona",
    "Fuqarolik holati dalolatnomalari",
    "Ijtimoiy himoya",
    "Boshqa",
]

STATUSLAR = [
    "1. Qabul qilindi",
    "2. Ko'rib chiqilmoqda",
    "3. Statistika/vazirlik ma'lumoti so'ralmoqda",
    "4. Xulosa chiqarildi",
]

XULOSA_TURLARI = ["Kutilmoqda", "ASOSSIZ (tartib to'g'ri qoldirildi)", "ASOSLI (o'zgartirish loyihasi tayyorlandi)"]

ADMIN_PAROL = "adliya2026"          # oddiy demo paroli - real loyihada almashtiring
TOZALASH_KALITI = "O'CHIRISH"       # bulk-tozalashni tasdiqlash uchun yozilishi kerak bo'lgan so'z


# --------------------------------------------------------------------------
# MA'LUMOTLAR BAZASI — Turso (libSQL), bulutda, ikkala sayt umumiy foydalanadi
# --------------------------------------------------------------------------
@st.cache_resource
def _client():
    """Turso bazasiga ulanish. URL va token Streamlit Cloud 'Secrets'
    bo'limidan olinadi (mahalliy testda .streamlit/secrets.toml orqali)."""
    try:
        url = st.secrets["TURSO_DATABASE_URL"]
        token = st.secrets["TURSO_AUTH_TOKEN"]
    except Exception:
        st.error(
            "⚠️ Turso ulanish maʼlumotlari topilmadi.\n\n"
            "Streamlit Cloud'da bu ilovaning **Settings → Secrets** bo'limiga quyidagilarni qo'shing:\n\n"
            "```\nTURSO_DATABASE_URL = \"libsql://sizning-bazangiz.turso.io\"\n"
            "TURSO_AUTH_TOKEN = \"sizning-tokeningiz\"\n```"
        )
        st.stop()

    client = libsql_client.create_client_sync(url=url, auth_token=token)
    client.execute("""
        CREATE TABLE IF NOT EXISTS murojaatlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sana TEXT,
            ism TEXT,
            kontakt TEXT,
            soha TEXT,
            sarlavha TEXT,
            tavsif TEXT,
            asos TEXT,
            status TEXT,
            xulosa_turi TEXT,
            xulosa_matni TEXT,
            ovoz INTEGER DEFAULT 0
        )
    """)
    client.execute("""
        CREATE TABLE IF NOT EXISTS ovozlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            murojaat_id INTEGER,
            voter TEXT,
            sana TEXT,
            UNIQUE(murojaat_id, voter)
        )
    """)
    return client



def yangi_murojaat_qoshish(ism, kontakt, soha, sarlavha, tavsif, asos):
    _client().execute(
        """INSERT INTO murojaatlar
           (sana, ism, kontakt, soha, sarlavha, tavsif, asos, status, xulosa_turi, xulosa_matni, ovoz)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
        [
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            ism, kontakt, soha, sarlavha, tavsif, asos,
            STATUSLAR[0], XULOSA_TURLARI[0], "",
        ],
    )


def barcha_murojaatlar():
    rs = _client().execute("SELECT * FROM murojaatlar ORDER BY id DESC")
    rows = [tuple(r) for r in rs.rows]
    df = pd.DataFrame(rows, columns=list(rs.columns))
    return df


def murojaatni_yangilash(mid, status, xulosa_turi, xulosa_matni):
    _client().execute(
        "UPDATE murojaatlar SET status=?, xulosa_turi=?, xulosa_matni=? WHERE id=?",
        [status, xulosa_turi, xulosa_matni, mid],
    )


def murojaatni_ochirish(mid):
    """Bitta murojaatni (masalan, test yozuvini) butunlay o'chiradi."""
    _client().execute("DELETE FROM murojaatlar WHERE id=?", [mid])
    _client().execute("DELETE FROM ovozlar WHERE murojaat_id=?", [mid])


def hammasini_tozalash():
    """DIQQAT: barcha murojaatlarni butunlay o'chiradi. Faqat test ma'lumotlarini
    tozalash uchun ishlatiladi."""
    _client().execute("DELETE FROM murojaatlar")
    _client().execute("DELETE FROM ovozlar")


# --------------------------------------------------------------------------
# OVOZ BERISH — bir kishi (kontakt bo'yicha) bir murojaatga faqat 1 marta
# --------------------------------------------------------------------------
def ovoz_berganmi(mid, voter):
    voter = (voter or "").strip().lower()
    if not voter:
        return False
    rs = _client().execute(
        "SELECT 1 FROM ovozlar WHERE murojaat_id=? AND voter=?", [mid, voter]
    )
    return len(rs.rows) > 0


def ovoz_qoshish(mid, voter):
    """True -> ovoz muvaffaqiyatli qo'shildi. False -> bu kontakt allaqachon ovoz bergan."""
    voter = (voter or "").strip().lower()
    if not voter:
        return False
    if ovoz_berganmi(mid, voter):
        return False
    try:
        _client().execute(
            "INSERT INTO ovozlar (murojaat_id, voter, sana) VALUES (?, ?, ?)",
            [mid, voter, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")],
        )
        _client().execute("UPDATE murojaatlar SET ovoz = ovoz + 1 WHERE id=?", [mid])
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------
# DIZAYN YORDAMCHILARI
# --------------------------------------------------------------------------
def case_id(row):
    yil = str(row["sana"])[:4] if row["sana"] else str(datetime.datetime.now().year)
    return f"ADL-{yil}-{int(row['id']):05d}"


def status_label(status_text):
    return status_text.split(". ", 1)[1] if ". " in status_text else status_text


def xulosa_badge(xulosa_turi):
    if str(xulosa_turi).startswith("ASOSLI"):
        return '<span class="adl-badge adl-badge-ok">✅ ASOSLI</span>'
    if str(xulosa_turi).startswith("ASOSSIZ"):
        return '<span class="adl-badge adl-badge-bad">✖ ASOSSIZ</span>'
    return '<span class="adl-badge adl-badge-pending">⏳ Kutilmoqda</span>'


def section_title(eyebrow, title, subtitle=None):
    sub_html = f'<div class="adl-section-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="adl-section">
            <div class="adl-eyebrow">{html.escape(eyebrow)}</div>
            <div class="adl-section-title">{html.escape(title)}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card(row, show_kontakt=False):
    """regulation.gov.uz uslubidagi 'loyiha kartochkasi' ko'rinishi:
    avatar+soha, sarlavha, ustki meta qator (sana / holat / ID / ovoz)."""
    cid = case_id(row)
    status_txt = html.escape(status_label(row["status"]))
    xb = xulosa_badge(row["xulosa_turi"])
    sarlavha = html.escape(str(row["sarlavha"]))
    soha = html.escape(str(row["soha"]))
    tavsif = html.escape(str(row["tavsif"])).replace("\n", "<br>")
    sana = html.escape(str(row["sana"]))
    ovoz = int(row["ovoz"])

    kontakt_html = ""
    if show_kontakt:
        kontakt_html = (
            f'<div class="adl-meta">Fuqaro: {html.escape(str(row["ism"]))} '
            f'&nbsp;·&nbsp; Kontakt: {html.escape(str(row["kontakt"]))}</div>'
        )

    matn_html = ""
    if row["xulosa_matni"]:
        matn_html = f'<div class="adl-note">{html.escape(str(row["xulosa_matni"])).replace(chr(10), "<br>")}</div>'

    card_class = "pending"
    if str(row["xulosa_turi"]).startswith("ASOSLI"):
        card_class = "ok"
    elif str(row["xulosa_turi"]).startswith("ASOSSIZ"):
        card_class = "bad"

    st.markdown(
        f"""
        <div class="adl-card {card_class}">
            <div class="adl-card-head">
                <div class="adl-card-agency">
                    <div class="adl-avatar">⚖️</div>
                    <div>
                        <div class="adl-agency-name">{soha}</div>
                        <div class="adl-case">{cid}</div>
                    </div>
                </div>
                <div class="adl-like-chip">👍 {ovoz}</div>
            </div>
            <div class="adl-card-title">{sarlavha}</div>
            <div class="adl-meta-row">
                <span>📅 {sana}</span>
                <span class="adl-meta-sep">|</span>
                <span class="adl-badge adl-badge-progress">{status_txt}</span>
                {xb}
            </div>
            <div class="adl-desc">{tavsif}</div>
            {kontakt_html}
            {matn_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.stApp { background-color: #EEF1F6; }

/* ---- Streamlit'ning standart yuqori panelini (Deploy tugmasi, ⋮ menyu) yashirish ---- */
header[data-testid="stHeader"] { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
.stDeployButton { display: none !important; }
.block-container { padding-top: 1.5rem !important; }

h1, h2, h3 { font-family: 'Spectral', serif !important; color: #16233B; }

.block-container { padding-top: 1.2rem; }

/* ---- Top navbar (regulation.gov.uz uslubida) ---- */
.adl-navbar {
    display: flex; align-items: center; justify-content: space-between;
    background: #FFFFFF; border: 1px solid #E1E4EC; border-radius: 10px;
    padding: 10px 22px; margin-bottom: 22px;
}
.adl-navbar-left { display: flex; align-items: center; gap: 12px; }
.adl-navbar-logo {
    width: 36px; height: 36px; border-radius: 8px; background: #16233B;
    display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.adl-navbar-title { font-family: 'Spectral', serif; font-weight: 700; color: #16233B; font-size: 16px; line-height: 1.2; }
.adl-navbar-sub { font-size: 11.5px; color: #8A8F9C; }
.adl-navbar-right { display: flex; align-items: center; gap: 22px; font-size: 13.5px; color: #4A5064; }
.adl-navbar-badge {
    background: #E7EBF3; color: #1E3A5F; padding: 4px 12px; border-radius: 999px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; font-weight: 600;
}
.adl-breadcrumb { font-size: 13px; color: #8A8F9C; text-align: center; margin-top: 6px; }
.adl-breadcrumb b { color: #4A5064; }

/* ---- Sidebar ---- */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
div[data-testid="stSidebarContent"],
div[data-testid="stSidebarUserContent"],
div[data-testid="stSidebarNav"],
nav[data-testid="stSidebarNav"],
div[data-testid="stSidebarNavItems"],
div[data-testid="stSidebarNavSeparator"] {
    background-color: #16233B !important;
}
section[data-testid="stSidebar"] { min-height: 100vh; }
section[data-testid="stSidebar"] * { color: #E9EAF0 !important; }
section[data-testid="stSidebar"] .adl-sidebar-logo {
    font-family: 'IBM Plex Mono', monospace; letter-spacing: 2px; font-size: 13px;
    text-transform: uppercase; color: #C89B3C !important; padding: 4px 0 14px;
    border-bottom: 1px solid rgba(255,255,255,0.12); margin-bottom: 10px;
}
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.14); }
section[data-testid="stSidebar"] .stButton>button {
    background-color: transparent; border: 1px solid #C89B3C; color: #C89B3C !important;
}
section[data-testid="stSidebar"] .stButton>button:hover {
    background-color: #C89B3C; color: #16233B !important;
}
/* Streamlit'ning avtomatik sahifa-nav havolalari (Fuqaro / Adliya paneli) */
div[data-testid="stSidebarNav"] a,
div[data-testid="stSidebarNav"] span {
    color: #E9EAF0 !important;
}
div[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: rgba(200,155,60,0.18) !important;
    border-radius: 6px;
}

/* ---- Buttons ---- */
.stButton>button {
    background-color: #16233B; color: #F4E8C6 !important; border: 1px solid #16233B;
    border-radius: 8px; padding: 0.5rem 1rem; font-weight: 600; transition: all .15s ease;
}
.stButton>button:hover { background-color: #C89B3C; border-color: #C89B3C; color: #16233B !important; }

/* ---- Section headers ---- */
.adl-section { margin: 4px 0 20px; }
.adl-eyebrow {
    font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; letter-spacing: 2.5px;
    text-transform: uppercase; color: #C89B3C; margin-bottom: 3px;
}
.adl-section-title { font-size: 27px; font-weight: 700; color: #16233B; }
.adl-section-sub { font-size: 14.5px; color: #6B6656; margin-top: 5px; }

/* ---- Hero (headline, regulation.gov.uz uslubidagi katta ko'k sarlavha) ---- */
.adl-hero { text-align: center; padding: 22px 10px 4px; }
.adl-hero-title {
    font-family: 'Spectral', serif; font-weight: 700; font-size: 30px; line-height: 1.35;
    color: #16233B; max-width: 900px; margin: 0 auto;
}
.adl-hero-tag {
    font-family: 'IBM Plex Mono', monospace; font-size: 12px; letter-spacing: 3px;
    text-transform: uppercase; color: #C89B3C; margin-top: 10px;
}

/* ---- Role cards on landing ---- */
.adl-role-card {
    background: #FFFFFF; border: 1px solid #E4E2DA; border-radius: 12px;
    padding: 26px 22px 20px; text-align: center; height: 100%;
}
.adl-role-icon { font-size: 30px; margin-bottom: 6px; }
.adl-role-title { font-family: 'Spectral', serif; font-weight: 700; font-size: 20px; color: #16233B; }
.adl-role-desc { color: #6B6656; font-size: 14px; margin: 8px 0 4px; line-height: 1.5; }

/* ---- Badges ---- */
.adl-badge {
    display: inline-block; padding: 3px 11px; border-radius: 999px;
    font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600;
    letter-spacing: .3px; margin-right: 6px;
}
.adl-badge-pending  { background: #EFEAD9; color: #8A6D1F; }
.adl-badge-ok       { background: #E1EEE4; color: #2F6B47; }
.adl-badge-bad      { background: #F3E1DB; color: #9A4A34; }
.adl-badge-progress { background: #E7EBF3; color: #1E3A5F; }

/* ---- Case cards (loyiha-kartochka uslubi) ---- */
.adl-card {
    background: #FFFFFF; border: 1px solid #E1E4EC; border-radius: 12px;
    padding: 18px 22px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(22,35,59,0.04);
}
.adl-card.ok      { border-left: 4px solid #2F6B47; }
.adl-card.bad     { border-left: 4px solid #9A4A34; }
.adl-card.pending { border-left: 4px solid #C89B3C; }

.adl-card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.adl-card-agency { display: flex; align-items: center; gap: 10px; }
.adl-avatar {
    width: 34px; height: 34px; border-radius: 50%; background: #EEF1F6;
    display: flex; align-items: center; justify-content: center; font-size: 16px;
    border: 1px solid #E1E4EC;
}
.adl-agency-name { font-size: 13px; font-weight: 600; color: #16233B; }
.adl-case {
    font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; color: #9C9585; letter-spacing: .4px;
}
.adl-like-chip {
    background: #F2F3F5; border: 1px solid #E1E4EC; border-radius: 999px;
    padding: 4px 12px; font-size: 13px; font-weight: 600; color: #16233B;
}

.adl-card-title { font-family: 'Spectral', serif; font-weight: 700; font-size: 18px; color: #16233B; margin: 2px 0 8px; }
.adl-meta-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 12.5px; color: #6B6656; margin-bottom: 10px; }
.adl-meta-sep { color: #D3D6DE; }
.adl-desc { font-size: 14px; color: #3E3B33; line-height: 1.55; }
.adl-meta { font-size: 12.5px; color: #8A8577; margin-top: 8px; }
.adl-note {
    margin-top: 10px; font-size: 13.5px; color: #4A4536; background: #F7F6F1;
    border-radius: 6px; padding: 9px 12px; border-left: 3px solid #C89B3C;
}

/* ---- Misc native widgets ---- */
div[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #E1E4EC; border-radius: 10px; padding: 10px 14px;
}
div[data-testid="stMetricValue"] { color: #16233B; font-family: 'Spectral', serif; font-weight: 700; }
div[data-testid="stMetricLabel"] {
    color: #8A8577; font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    text-transform: uppercase; letter-spacing: .5px;
}
div[data-testid="stExpander"] summary {
    font-family: 'IBM Plex Mono', monospace; font-weight: 600; color: #16233B; font-size: 13.5px;
}
hr { border-top: 1px solid #E0DDD1; }
</style>
"""


def inject_base(page_title, page_icon, sidebar_label):
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="adl-sidebar-logo">⚖️ {sidebar_label}</div>', unsafe_allow_html=True)


def render_navbar(title, subtitle, right_label):
    """regulation.gov.uz'dagi yuqori panelga o'xshash navbar."""
    st.markdown(
        f"""
        <div class="adl-navbar">
            <div class="adl-navbar-left">
                <div class="adl-navbar-logo">⚖️</div>
                <div>
                    <div class="adl-navbar-title">{html.escape(title)}</div>
                    <div class="adl-navbar-sub">{html.escape(subtitle)}</div>
                </div>
            </div>
            <div class="adl-navbar-right">
                <span class="adl-navbar-badge">{html.escape(right_label)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_headline(text, breadcrumb):
    st.markdown(
        f"""
        <div class="adl-hero">
            <div class="adl-hero-title">{html.escape(text)}</div>
        </div>
        <div class="adl-breadcrumb">{breadcrumb}</div>
        """,
        unsafe_allow_html=True,
    )
