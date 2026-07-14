# -*- coding: utf-8 -*-
"""
fuqaro_app.py — ADLIYA-ALOQA: FUQARO SAYTI
============================================================================
ISHGA TUSHIRISH:
  streamlit run fuqaro_app.py --server.port 8501
"""

import streamlit as st
from shared import (
    SOHALAR, barcha_murojaatlar, yangi_murojaat_qoshish,
    ovoz_qoshish, ovoz_berganmi, render_card, section_title,
    inject_base, render_navbar, render_headline,
)

inject_base(page_title="Adliya-Aloqa — Fuqaro", page_icon="🧍", sidebar_label="Fuqaro sayti")

st.sidebar.markdown("**Bo'lim**")
bolim = st.sidebar.radio("Bo'lim", ["🧍 Murojaat yuborish", "📊 Ochiq reestr"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption(
    "🔗 Murojaatingiz Adliya xodimiga real vaqtda yetib boradi. "
    "Xodim javob bergach, natijani shu saytda ko'rasiz."
)

render_navbar("ADLIYA-ALOQA", "Fuqarolar uchun murojaat portali", "Fuqaro rejimi")
render_headline(
    "Amaldagi qonunchilikka oid fikr-mulohaza va takliflar",
    "Bosh sahifa / <b>Fuqaro</b>",
)

# --------------------------------------------------------------------------
# 1) MUROJAAT YUBORISH
# --------------------------------------------------------------------------
if bolim == "🧍 Murojaat yuborish":
    section_title(
        "Murojaat", "Muammoni bizga yetkazing",
        "Amaldagi qonun yoki tartib amalda qanday ishlayotgani emas, balki o'zi to'g'ri "
        "yozilganmi deb hisoblaysizmi? Fikringizni asoslab yozing — biz o'rganib chiqamiz.",
    )

    with st.form("murojaat_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            ism = st.text_input("Ismingiz (yoki taxallus)")
            kontakt = st.text_input("Kontakt (telefon yoki email)")
        with col2:
            soha = st.selectbox("Qaysi sohaga tegishli?", SOHALAR)

        sarlavha = st.text_input("Muammoning qisqa nomi", placeholder="Masalan: Ikki marta sertifikat olish talabi")
        tavsif = st.text_area(
            "Amaldagi holatni tasvirlab bering",
            placeholder="Qaysi hujjat/qonun moddasi, qanday tartib amal qilyapti?",
            height=100,
        )
        asos = st.text_area(
            "Nima uchun bu noto'g'ri yoki adolatsiz deb hisoblaysiz?",
            placeholder="Asoslaringizni, real holatni yozing",
            height=120,
        )
        yuborish = st.form_submit_button("📨 Murojaatni yuborish", use_container_width=True)

        if yuborish:
            if not (ism and kontakt and sarlavha and tavsif and asos):
                st.error("Iltimos, barcha maydonlarni to'ldiring.")
            else:
                yangi_murojaat_qoshish(ism, kontakt, soha, sarlavha, tavsif, asos)
                st.success("Rahmat! Murojaatingiz qabul qilindi va Adliya xodimiga yuborildi. "
                           "Natija haqida ko'rsatgan kontaktingiz orqali xabar beriladi.")

    st.divider()
    section_title("Kuzatish", "Mening murojaatlarim holati")
    kontakt_qidiruv = st.text_input("Holatni ko'rish uchun kontaktingizni kiriting")
    if kontakt_qidiruv:
        df = barcha_murojaatlar()
        mening = df[df["kontakt"] == kontakt_qidiruv]
        if mening.empty:
            st.info("Bu kontakt bo'yicha murojaat topilmadi.")
        else:
            for _, r in mening.iterrows():
                render_card(r, show_kontakt=False)

# --------------------------------------------------------------------------
# 2) OCHIQ REESTR — bir kishi bir murojaatga faqat 1 marta ovoz beradi
# --------------------------------------------------------------------------
else:
    section_title(
        "Shaffoflik", "Ochiq reestr",
        "Barcha murojaatlar (shaxsiy ma'lumotlarsiz) va ularning natijasi. "
        "O'xshash muammoni ko'rgan fuqaro ovoz berib qo'llab-quvvatlashi mumkin.",
    )

    st.text_input(
        "Ovoz berish uchun telefon yoki email kiriting (har bir kontakt 1 marta ovoz bera oladi)",
        key="ovoz_kontakt",
        placeholder="masalan: +998901234567",
    )
    voter = st.session_state.get("ovoz_kontakt", "").strip()

    df = barcha_murojaatlar()
    if df.empty:
        st.info("Hozircha murojaatlar yo'q.")
    else:
        soha_filtr = st.selectbox("Soha bo'yicha filtr", ["Barchasi"] + SOHALAR, key="reestr_filtr")
        ko_df = df if soha_filtr == "Barchasi" else df[df["soha"] == soha_filtr]

        for _, r in ko_df.iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                render_card(r, show_kontakt=False)
            with col2:
                st.metric("Ovoz", int(r["ovoz"]))
                if not voter:
                    st.caption("Ovoz berish uchun avval kontakt kiriting")
                elif ovoz_berganmi(r["id"], voter):
                    st.success("Ovoz berilgan ✓", icon="✅")
                else:
                    if st.button("👍 Men ham", key=f"vote_{r['id']}", use_container_width=True):
                        agar_ok = ovoz_qoshish(r["id"], voter)
                        if agar_ok:
                            st.rerun()
                        else:
                            st.warning("Siz bu murojaatga allaqachon ovoz bergansiz.")
