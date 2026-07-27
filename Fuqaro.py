# Fuqaro.py — Fuqarolar Tashabbusi Platformasi (asosiy kirish fayli)
import streamlit as st
from shared import (
    t, get_kategoriyalar, get_status_nomlari, get_conn, init_db, hash_parol,
    apply_custom_css, status_badge, generate_murojaat_docx, render_gov_header,
    render_gov_nav, render_gov_footer, init_session_state,
    KATEGORIYALAR, KATEGORIYALAR_RU, KATEGORIYALAR_EN,
    STATUS_NOMLARI, STATUS_TARTIBI,
)

# ============================================================
# STREAMLIT SOZLAMALARI
# ============================================================
st.set_page_config(page_title="O'zbekiston Respublikasi Adliya vazirligi", page_icon="🇺🇿", layout="wide",
                   initial_sidebar_state="collapsed")
init_db()
init_session_state()
apply_custom_css()


# ============================================================
# BOSH SAHIFA
# ============================================================
def sahifa_bosh():
    conn = get_conn()
    jami = conn.execute("SELECT COUNT(*) FROM murojaatlar").fetchone()[0]
    asosli = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='asosli'").fetchone()[0]
    loyiha = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='loyiha_tayyorlandi'").fetchone()[0]
    kiritilgan = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='kiritildi'").fetchone()[0]
    conn.close()

    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="gov-hero">
        <h2>{t('hero_title')}</h2>
        <p>{t('hero_desc')}</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.xodim_id:
        if st.button(t("hero_btn"), type="primary"):
            st.session_state.sahifa = "Taklif yuborish"
            st.rerun()

    st.write("")
    st.markdown(f'<div class="gov-section-title">{t("stats_title")}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    stats_data = [(jami, t("stats_total"), "📝"), (asosli, t("stats_valid"), "✅"),
                  (loyiha, t("stats_draft"), "📄"), (kiritilgan, t("stats_submitted"), "🚀")]
    for col, (son, nom, icon) in zip((c1, c2, c3, c4), stats_data):
        col.markdown(f'<div class="stat-card"><span class="stat-icon">{icon}</span><h3>{son}</h3><p>{nom}</p></div>',
                     unsafe_allow_html=True)

    st.write("")
    st.markdown(f'<div class="gov-section-title">{t("how_title")}</div>', unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    qadamlar = [("1", t("step1_title"), t("step1_desc")), ("2", t("step2_title"), t("step2_desc")),
                ("3", t("step3_title"), t("step3_desc")), ("4", t("step4_title"), t("step4_desc"))]
    for col, (num, h, p) in zip((r1, r2, r3, r4), qadamlar):
        col.markdown(f'<div class="step-card"><div class="step-number">{num}</div><h4>{h}</h4><p>{p}</p></div>',
                     unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    render_gov_footer()


# ============================================================
# TAKLIF YUBORISH
# ============================================================
def sahifa_murojaat_yuborish():
    kateg = get_kategoriyalar()
    status_nomlari = get_status_nomlari()

    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="gov-section-title">{t("submit_title")}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:15px; color:#334155; margin-bottom:24px; line-height:1.6;">{t("submit_desc")}</p>',
        unsafe_allow_html=True)

    with st.form("murojaat_form"):
        with st.container(border=True):
            st.markdown(f'<h3 style="font-size:16px; font-weight:600; color:#1E3A8A; margin:0 0 14px 0;">{t("personal_info")}</h3>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            ism = c1.text_input(t("full_name"), value=st.session_state.form_ism)
            telefon = c2.text_input(t("phone"), value=st.session_state.form_telefon)
            email = st.text_input(t("email_opt"), value=st.session_state.form_email)

        with st.container(border=True):
            st.markdown(f'<h3 style="font-size:16px; font-weight:600; color:#1E3A8A; margin:0 0 14px 0;">{t("problem_title")}</h3>', unsafe_allow_html=True)
            kateg_options = [t("category_placeholder")] + kateg
            current_k = st.session_state.form_kategoriya
            try:
                k_idx = kateg_options.index(current_k) if current_k in kateg_options else 0
            except ValueError:
                # Agar eski kategorya boshqa tilda bo'lsa, default ga o'tkazamiz
                k_idx = 0
            kategoriya = st.selectbox(t("category"), kateg_options, index=k_idx)
            muammo = st.text_area(t("problem"), value=st.session_state.form_muammo)
            qonun_asosi = st.text_input(t("law_basis"), value=st.session_state.form_qonun)
            nima_uchun_xato = st.text_area(t("why_wrong"), value=st.session_state.form_nima)
            taklif = st.text_area(t("suggestion"), value=st.session_state.form_taklif)

        st.caption(t("required_note"))

        col1, col2, col3 = st.columns([1, 1, 6])
        with col1:
            yuborildi = st.form_submit_button(t("submit_btn"), type="primary")
        with col2:
            tozalash = st.form_submit_button(t("clear_btn"), type="secondary")

        if tozalash:
            for k in ["form_ism", "form_telefon", "form_email", "form_kategoriya", "form_muammo", "form_qonun",
                      "form_nima", "form_taklif"]:
                st.session_state[k] = "" if k != "form_kategoriya" else "Tanlang..."
            st.rerun()

        if yuborildi:
            st.session_state.form_ism = ism
            st.session_state.form_telefon = telefon
            st.session_state.form_email = email
            st.session_state.form_kategoriya = kategoriya
            st.session_state.form_muammo = muammo
            st.session_state.form_qonun = qonun_asosi
            st.session_state.form_nima = nima_uchun_xato
            st.session_state.form_taklif = taklif

            xato = False
            xatoliklar = []
            if not ism: xatoliklar.append(t("full_name").replace(" *", "")); xato = True
            if not telefon: xatoliklar.append(t("phone").replace(" *", "")); xato = True
            if kategoriya == t("category_placeholder"): xatoliklar.append(t("category").replace(" *", "")); xato = True
            if not muammo: xatoliklar.append(t("problem").replace(" *", "")); xato = True
            if not nima_uchun_xato: xatoliklar.append(t("why_wrong").replace(" *", "")); xato = True
            if not taklif: xatoliklar.append(t("suggestion").replace(" *", "")); xato = True

            if xato:
                st.error(f"{t('required_error')}: {', '.join(xatoliklar)}")
            else:
                conn = get_conn()
                # Kategoriyani asl (o'zbek) tilida saqlaymiz
                uz_kateg = kategoriya
                if kategoriya in KATEGORIYALAR_RU:
                    uz_kateg = KATEGORIYALAR[KATEGORIYALAR_RU.index(kategoriya)]
                elif kategoriya in KATEGORIYALAR_EN:
                    uz_kateg = KATEGORIYALAR[KATEGORIYALAR_EN.index(kategoriya)]

                cur = conn.execute("""INSERT INTO murojaatlar
                                      (fuqaro_ism, telefon, email, kategoriya, muammo, qonun_asosi, nima_uchun_xato,
                                       taklif)
                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                   (ism, telefon, email, uz_kateg, muammo, qonun_asosi, nima_uchun_xato, taklif))
                conn.commit()
                murojaat_id = cur.lastrowid
                conn.close()

                for k in ["form_ism", "form_telefon", "form_email", "form_kategoriya", "form_muammo", "form_qonun",
                          "form_nima", "form_taklif"]:
                    st.session_state[k] = "" if k != "form_kategoriya" else "Tanlang..."

                st.success(f"{t('success_msg')}")
                st.info(f"{t('your_number')}: **№ {murojaat_id}**")
                st.info(f"📌 {t('save_number')}")

    st.markdown('</div>', unsafe_allow_html=True)
    render_gov_footer()


# ============================================================
# OCHIQ REESTR
# ============================================================
def sahifa_ochiq_reestr():
    kateg = get_kategoriyalar()
    status_nomlari = get_status_nomlari()

    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="gov-section-title">{t("reestr_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:15px; color:#334155; margin-bottom:24px;">{t("reestr_desc")}</p>',
                unsafe_allow_html=True)

    conn = get_conn()
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        qidiruv = c1.text_input(t("search"), placeholder=t("search_placeholder"))
        status_options = [t("all")] + [status_nomlari[s] for s in STATUS_TARTIBI]
        filtr_status = c2.selectbox(t("status_filter"), status_options)
        kateg_options = [t("all")] + kateg
        filtr_kategoriya = c3.selectbox(t("category_filter"), kateg_options)

    query = "SELECT id, kategoriya, muammo, taklif, status, yaratilgan FROM murojaatlar WHERE 1=1"
    params = []
    if qidiruv:
        query += " AND (muammo LIKE ? OR taklif LIKE ? OR kategoriya LIKE ?)"
        params.extend([f"%{qidiruv}%"] * 3)
    if filtr_status != t("all"):
        status_kaliti = [k for k, v in STATUS_NOMLARI.items() if v == filtr_status][0]
        query += " AND status=?";
        params.append(status_kaliti)
    if filtr_kategoriya != t("all"):
        query += " AND kategoriya=?";
        params.append(filtr_kategoriya)
    query += " ORDER BY yaratilgan DESC"
    murojaatlar = conn.execute(query, params).fetchall()
    conn.close()

    st.markdown(
        f"<p style='color:#64748B; font-size:14px; margin-bottom:18px;'><strong>{len(murojaatlar)}</strong> {t('total_found')}</p>",
        unsafe_allow_html=True)

    if not murojaatlar:
        st.info(t("not_found"))
        st.markdown('</div>', unsafe_allow_html=True)
        render_gov_footer()
        return

    for m in murojaatlar:
        st.markdown(f"""
        <div class="reestr-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
                <div style="flex:1;">
                    <strong style="font-size:14px;">№{m['id']}</strong>
                    <span style="color:#64748B; font-size:13px; margin-left:12px;">📅 {m['yaratilgan'][:10]}</span>
                    <span style="color:#64748B; font-size:13px; margin-left:8px;">🏷 {m['kategoriya']}</span>
                    <div style="margin-top:6px; color:#334155; font-size:13px; line-height:1.5;">
                        {m['muammo'][:120]}{'...' if len(m['muammo']) > 120 else ''}
                    </div>
                    <div style="margin-top:6px;">{status_badge(m['status'], status_nomlari)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns([1, 10])
        with cols[0]:
            if st.button(f"{t('detail')}", key=f"reestr_btn_{m['id']}"):
                st.session_state.tanlangan_murojaat = m['id']
                st.session_state.sahifa = "Ochiq reestr: Batafsil"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    render_gov_footer()


def sahifa_ochiq_reestr_detail(murojaat_id):
    status_nomlari = get_status_nomlari()

    conn = get_conn()
    m = conn.execute("SELECT * FROM murojaatlar WHERE id=?", (murojaat_id,)).fetchone()
    conn.close()
    if not m: st.error(t("not_found")); return

    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    if st.button(f"{t('back')}"):
        st.session_state.sahifa = "Ochiq reestr";
        st.rerun()

    st.markdown(
        f'<div class="detail-section"><h2>Murojaat № {m["id"]} &nbsp; {status_badge(m["status"], status_nomlari)}</h2></div>',
        unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f'<h3 style="font-size:16px; font-weight:600; color:#1E3A8A; margin:0 0 14px 0;">{t("content")}</h3>', unsafe_allow_html=True)
        for label, val in [(t("category_label"), m["kategoriya"]), (t("date_sent"), m["yaratilgan"]),
                           (t("problem").replace(" *", ""), m["muammo"]),
                           (t("law_basis_label"), m["qonun_asosi"] or t("not_indicated")),
                           (t("why_wrong_label"), m["nima_uchun_xato"]),
                           (t("suggestion_label"), m["taklif"])]:
            st.markdown(f'<div class="detail-label">{label}</div><div class="detail-value">{val}</div>',
                        unsafe_allow_html=True)

    if m["javob"]:
        with st.container(border=True):
            st.markdown(f'<h3 style="font-size:16px; font-weight:600; color:#1E3A8A; margin:0 0 14px 0;">{t("response")}</h3>', unsafe_allow_html=True)
            st.info(m["javob"])
            if m["ko_rib_chiqilgan"]: st.caption(f"{t('reviewed_at')}: {m['ko_rib_chiqilgan']}")

    st.markdown('</div>', unsafe_allow_html=True)
    render_gov_footer()


# ============================================================
# XODIM KIRISHI
# ============================================================
def sahifa_xodim_login():
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="gov-section-title">{t("login_title")}</div>', unsafe_allow_html=True)
    with st.form("login_form"):
        login = st.text_input(t("login_username"))
        parol = st.text_input(t("login_password"), type="password")
        if st.form_submit_button(t("login_btn"), type="primary"):
            conn = get_conn()
            xodim = conn.execute("SELECT * FROM xodimlar WHERE login=? AND parol_hash=?",
                                 (login, hash_parol(parol))).fetchone()
            conn.close()
            if xodim:
                st.session_state.xodim_id = xodim["id"]
                st.session_state.xodim_ism = xodim["ism"]
                st.session_state.sahifa = "Xodim: Murojaatlar"
                st.switch_page("pages/1_Adliya_paneli.py")
            else:
                st.error(t("login_error"))
        st.caption(t("login_default"))
    st.markdown('</div>', unsafe_allow_html=True)
    render_gov_footer()


# ============================================================
# ROUTING
# ============================================================
render_gov_header()
render_gov_nav()

sahifa = st.session_state.sahifa
if sahifa == "Bosh sahifa":
    sahifa_bosh()
elif sahifa == "Taklif yuborish":
    if st.session_state.xodim_id:
        st.warning(t("warning_xodim"))
        sahifa_bosh()
    else:
        sahifa_murojaat_yuborish()
elif sahifa == "Ochiq reestr":
    sahifa_ochiq_reestr()
elif sahifa == "Ochiq reestr: Batafsil":
    m_id = st.session_state.get("tanlangan_murojaat")
    if m_id:
        sahifa_ochiq_reestr_detail(m_id)
    else:
        sahifa_ochiq_reestr()
elif sahifa == "Xodim kirishi":
    sahifa_xodim_login()
else:
    # Boshqa (xodimga oid) sahifalar 1_Adliya_paneli.py faylida joylashgan
    sahifa_bosh()
