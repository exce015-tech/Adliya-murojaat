# -*- coding: utf-8 -*-
"""
adliya_app.py — ADLIYA-ALOQA: ADLIYA XODIMI SAYTI
============================================================================
ISHGA TUSHIRISH:
  streamlit run adliya_app.py --server.port 8502
"""

import streamlit as st
from shared import (
    SOHALAR, STATUSLAR, XULOSA_TURLARI, ADMIN_PAROL, TOZALASH_KALITI,
    barcha_murojaatlar, murojaatni_yangilash, murojaatni_ochirish,
    hammasini_tozalash, ovoz_qoshish, ovoz_berganmi,
    render_card, section_title, case_id, status_label,
    inject_base, render_navbar, render_headline,
)

inject_base(page_title="Adliya-Aloqa — Xodim paneli", page_icon="🏛️", sidebar_label="Adliya paneli")

st.sidebar.markdown("**Bo'lim**")
bolim = st.sidebar.radio("Bo'lim", ["🏛️ Boshqaruv paneli", "📊 Ochiq reestr"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption(
    "🔗 Bu yerda ko'rgan murojaatlar fuqaro saytidan real vaqtda keladi. "
    "Siz bergan xulosa fuqaro saytida darhol ko'rinadi."
)

render_navbar("ADLIYA-ALOQA", "Xodimlar uchun boshqaruv paneli", "Xodim rejimi")
render_headline(
    "Murojaatlarni ko'rib chiqish va qonunchilikka oid xulosa berish",
    "Bosh sahifa / <b>Adliya xodimi</b>",
)

# --------------------------------------------------------------------------
# 1) BOSHQARUV PANELI (parol bilan)
# --------------------------------------------------------------------------
if bolim == "🏛️ Boshqaruv paneli":
    section_title("Kirish", "Xodim autentifikatsiyasi")
    parol = st.text_input("Kirish paroli", type="password")

    if parol != ADMIN_PAROL:
        st.warning("Panelga kirish uchun to'g'ri parolni kiriting. (demo paroli: adliya2026)")
        st.stop()

    df = barcha_murojaatlar()

    # --- Test ma'lumotlarni tozalash (butun ro'yxat) ---
    with st.expander("🧹 Test murojaatlarni tozalash (xavfli amal)"):
        st.caption(
            f"Barcha murojaatlarni butunlay o'chirish uchun quyidagi maydonga "
            f"**{TOZALASH_KALITI}** so'zini yozing va tugmani bosing. Bu amalni orqaga qaytarib bo'lmaydi."
        )
        tasdiq = st.text_input("Tasdiqlash so'zi", key="tozalash_tasdiq")
        if st.button("🗑️ Barcha murojaatlarni butunlay o'chirish", type="primary"):
            if tasdiq.strip() == TOZALASH_KALITI:
                hammasini_tozalash()
                st.success("Barcha murojaatlar o'chirildi.")
                st.rerun()
            else:
                st.error(f"Tasdiqlash uchun aynan \"{TOZALASH_KALITI}\" so'zini yozing.")

    if df.empty:
        st.info("Hozircha murojaatlar yo'q.")
        st.stop()

    # --- statistik dashboard ---
    section_title("Statistika", "Umumiy ko'rsatkichlar")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jami murojaatlar", len(df))
    c2.metric("Ko'rib chiqilmoqda", (df["status"] != STATUSLAR[3]).sum())
    c3.metric("Asosli topilgan", (df["xulosa_turi"] == XULOSA_TURLARI[2]).sum())
    c4.metric("Asossiz deb topilgan", (df["xulosa_turi"] == XULOSA_TURLARI[1]).sum())

    st.write("")
    st.markdown('<div class="adl-eyebrow">Soha bo\'yicha taqsimot (eng dolzarb muammolar)</div>', unsafe_allow_html=True)
    soha_stat = df.groupby("soha").size().sort_values(ascending=False)
    st.bar_chart(soha_stat, color="#16233B")

    st.divider()
    section_title("Ko'rib chiqish", "Tushgan murojaatlar")

    soha_filtr = st.selectbox("Soha bo'yicha filtr", ["Barchasi"] + SOHALAR)
    ko_df = df if soha_filtr == "Barchasi" else df[df["soha"] == soha_filtr]

    for _, r in ko_df.iterrows():
        with st.expander(f"{case_id(r)}  —  {r['sarlavha']}  ·  {status_label(r['status'])}"):
            render_card(r, show_kontakt=True)

            yangi_status = st.selectbox(
                "Statusni yangilash", STATUSLAR,
                index=STATUSLAR.index(r["status"]), key=f"status_{r['id']}"
            )
            yangi_xulosa = st.radio(
                "Xulosa", XULOSA_TURLARI,
                index=XULOSA_TURLARI.index(r["xulosa_turi"]),
                key=f"xulosa_{r['id']}", horizontal=True,
            )
            xulosa_matni = st.text_area(
                "Xulosa matni / asoslash (fuqaroga yuboriladi)",
                value=r["xulosa_matni"], key=f"matn_{r['id']}", height=100,
                placeholder=("Agar ASOSSIZ: nega amaldagi tartib to'g'ri ekanini tushuntiring.\n"
                             "Agar ASOSLI: qanday o'zgartirish loyihasi tayyorlanganini yozing."),
            )

            col_save, col_del = st.columns([3, 1])
            with col_save:
                if st.button("💾 Saqlash", key=f"save_{r['id']}", use_container_width=True):
                    murojaatni_yangilash(r["id"], yangi_status, yangi_xulosa, xulosa_matni)
                    st.success("Yangilandi. Fuqaro saytida ham darhol yangi holat ko'rinadi.")
                    st.rerun()
            with col_del:
                del_key = f"confirm_del_{r['id']}"
                if st.session_state.get(del_key):
                    if st.button("⚠️ Tasdiqlash", key=f"confirm_btn_{r['id']}", use_container_width=True):
                        murojaatni_ochirish(r["id"])
                        st.success("Murojaat o'chirildi.")
                        st.session_state.pop(del_key, None)
                        st.rerun()
                else:
                    if st.button("🗑️ O'chirish", key=f"del_{r['id']}", use_container_width=True):
                        st.session_state[del_key] = True
                        st.rerun()

# --------------------------------------------------------------------------
# 2) OCHIQ REESTR (xodim ham umumiy manzarani ko'rishi uchun)
# --------------------------------------------------------------------------
else:
    section_title(
        "Shaffoflik", "Ochiq reestr",
        "Barcha murojaatlar (shaxsiy ma'lumotlarsiz) va ularning natijasi — fuqarolar "
        "ko'rayotgan xuddi shu ko'rinish.",
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