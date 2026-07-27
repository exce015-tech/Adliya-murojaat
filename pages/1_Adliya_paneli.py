# pages/1_Adliya_paneli.py — Xodim (Adliya) paneli
from datetime import datetime
import streamlit as st
from shared import (
    t, get_status_nomlari, get_conn, init_db, apply_custom_css, status_badge,
    generate_murojaat_docx, render_gov_header, render_gov_nav, render_gov_footer,
    init_session_state, STATUS_NOMLARI, STATUS_TARTIBI,
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
# XODIM: MUROJAATLAR
# ============================================================
def sahifa_xodim_dashboard():
    status_nomlari = get_status_nomlari()

    conn = get_conn()
    jami = conn.execute("SELECT COUNT(*) FROM murojaatlar").fetchone()[0]
    yangi = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='yangi'").fetchone()[0]
    jarayonda = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='ko_rib_chiqilmoqda'").fetchone()[0]
    asosli = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='asosli'").fetchone()[0]

    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="gov-section-title">{t("appeals_title")}</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    stats_data = [(jami, t("stats_total"), "📝"), (yangi, t("new"), "🆕"),
                  (jarayonda, t("in_progress"), "🟡"), (asosli, t("valid"), "✅")]
    for col, (son, nom, icon) in zip((c1, c2, c3, c4), stats_data):
        col.markdown(f'<div class="stat-card"><span class="stat-icon">{icon}</span><h3>{son}</h3><p>{nom}</p></div>',
                     unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        status_options = [t("all")] + [status_nomlari[s] for s in STATUS_TARTIBI]
        filtr_tanlov = st.selectbox(t("filter_status"), status_options)

    if filtr_tanlov == t("all"):
        murojaatlar = conn.execute("SELECT * FROM murojaatlar ORDER BY yaratilgan DESC").fetchall()
    else:
        status_kaliti = [k for k, v in STATUS_NOMLARI.items() if v == filtr_tanlov][0]
        murojaatlar = conn.execute("SELECT * FROM murojaatlar WHERE status=? ORDER BY yaratilgan DESC",
                                   (status_kaliti,)).fetchall()
    conn.close()

    if not murojaatlar:
        st.info(t("not_found"))
        st.markdown('</div>', unsafe_allow_html=True)
        render_gov_footer()
        return

    for m in murojaatlar:
        st.markdown(f"""
        <div class="murojaat-card">
            <div class="title">№{m['id']} — {m['fuqaro_ism']}</div>
            <div class="meta">
                📅 {m['yaratilgan'][:10]} &nbsp;|&nbsp; 🏷 {m['kategoriya']}
            </div>
            <div class="preview">{m['muammo'][:120]}{'...' if len(m['muammo']) > 120 else ''}</div>
            <div style="margin-top:6px;">{status_badge(m['status'], status_nomlari)}</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([1, 1, 1.6, 6.4])
        with col1:
            if st.button(f"{t('view')}", key=f"view_{m['id']}"):
                st.session_state.tanlangan_murojaat = m["id"]
                st.session_state.sahifa = "Xodim: Batafsil"
                st.rerun()
        with col2:
            if st.button(f"{t('delete')}", key=f"del_{m['id']}"):
                conn2 = get_conn()
                conn2.execute("DELETE FROM murojaatlar WHERE id=?", (m["id"],))
                conn2.commit()
                conn2.close()
                st.success(f"✅ {t('deleted_success')} №{m['id']}")
                st.rerun()
        with col3:
            st.download_button(
                "📥 Word",
                data=generate_murojaat_docx(m, status_nomlari),
                file_name=f"murojaat_{m['id']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"docx_{m['id']}",
            )

    st.markdown('</div>', unsafe_allow_html=True)
    render_gov_footer()


# ============================================================
# XODIM: BATAFSIL
# ============================================================
def sahifa_xodim_detail(murojaat_id):
    status_nomlari = get_status_nomlari()

    conn = get_conn()
    m = conn.execute("SELECT * FROM murojaatlar WHERE id=?", (murojaat_id,)).fetchone()
    if not m: st.error(t("not_found")); conn.close(); return

    st.markdown('<div class="page-container">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([1, 1, 1.6, 5.4])
    with c1:
        if st.button(f"{t('back')}"):
            st.session_state.sahifa = "Xodim: Murojaatlar";
            st.rerun()
    with c2:
        if st.button(f"{t('delete')}"):
            conn2 = get_conn()
            conn2.execute("DELETE FROM murojaatlar WHERE id=?", (murojaat_id,))
            conn2.commit()
            conn2.close()
            st.success(f"✅ {t('deleted_success')} №{murojaat_id}")
            st.session_state.sahifa = "Xodim: Murojaatlar"
            st.rerun()
    with c3:
        docx_bytes = generate_murojaat_docx(m, status_nomlari)
        st.download_button(
            "📥 Word (.docx)",
            data=docx_bytes,
            file_name=f"murojaat_{m['id']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    st.markdown(
        f'<div class="detail-section"><h2>Murojaat № {m["id"]} &nbsp; {status_badge(m["status"], status_nomlari)}</h2></div>',
        unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f'<h3 style="font-size:16px; font-weight:600; color:#1E3A8A; margin:0 0 14px 0;">{t("citizen_info")}</h3>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        for col, pairs in [
            (c1, [(t("full_name").replace(" *", ""), m["fuqaro_ism"]), (t("phone").replace(" *", ""), m["telefon"])]),
            (c2, [(t("email_opt").replace(" (ixtiyoriy)", "").replace(" (необязательно)", "").replace(" (optional)", ""),
                   m["email"] or t("not_indicated")), (t("date_sent"), m["yaratilgan"])])]:
            for label, val in pairs:
                col.markdown(f'<div class="detail-label">{label}</div><div class="detail-value">{val}</div>',
                             unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f'<h3 style="font-size:16px; font-weight:600; color:#1E3A8A; margin:0 0 14px 0;">{t("content")}</h3>', unsafe_allow_html=True)
        for label, val in [(t("category_label"), m["kategoriya"]), (t("problem").replace(" *", ""), m["muammo"]),
                           (t("law_basis_label"), m["qonun_asosi"] or t("not_indicated")),
                           (t("why_wrong_label"), m["nima_uchun_xato"]),
                           (t("suggestion_label"), m["taklif"])]:
            st.markdown(f'<div class="detail-label">{label}</div><div class="detail-value">{val}</div>',
                        unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f'<h3 style="font-size:16px; font-weight:600; color:#1E3A8A; margin:0 0 14px 0;">{t("decision_title")}</h3>', unsafe_allow_html=True)
        with st.form("qaror_form"):
            status_variantlari = [status_nomlari[s] for s in STATUS_TARTIBI if s != "yangi"]
            joriy = status_nomlari.get(m["status"])
            default_index = status_variantlari.index(joriy) if joriy in status_variantlari else 0
            yangi_status_nomi = st.selectbox(t("change_status"), status_variantlari, index=default_index)
            izoh = st.text_area(t("internal_note"), value=m["xodim_izohi"] or "")
            javob = st.text_area(t("response_to_citizen"), value=m["javob"] or "")

            if st.form_submit_button(t("save_btn"), type="primary"):
                if not javob.strip():
                    st.error(t("response_required"))
                else:
                    yangi_status_kaliti = [k for k, v in STATUS_NOMLARI.items() if v == yangi_status_nomi][0]
                    conn.execute("""UPDATE murojaatlar
                                    SET status=?,
                                        xodim_id=?,
                                        xodim_izohi=?,
                                        javob=?,
                                        ko_rib_chiqilgan=?
                                    WHERE id = ?""",
                                 (yangi_status_kaliti, st.session_state.xodim_id, izoh, javob,
                                  datetime.now().strftime("%Y-%m-%d %H:%M"), murojaat_id))
                    conn.commit()
                    st.success(t("updated_success"))
                    st.rerun()
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)
    render_gov_footer()


# ============================================================
# XODIM: STATISTIKA
# ============================================================
def sahifa_xodim_statistika():
    status_nomlari = get_status_nomlari()

    conn = get_conn()
    jami = conn.execute("SELECT COUNT(*) FROM murojaatlar").fetchone()[0]
    yangi = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='yangi'").fetchone()[0]
    asosli = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='asosli'").fetchone()[0]
    asossiz = conn.execute("SELECT COUNT(*) FROM murojaatlar WHERE status='asossiz'").fetchone()[0]
    kategoriya_stats = conn.execute(
        "SELECT kategoriya, COUNT(*) as son FROM murojaatlar GROUP BY kategoriya ORDER BY son DESC").fetchall()
    status_stats = conn.execute(
        "SELECT status, COUNT(*) as son FROM murojaatlar GROUP BY status ORDER BY son DESC").fetchall()
    conn.close()

    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="gov-section-title">{t("stats_page_title")}</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    stats_data = [(jami, t("stats_total"), "📝"), (yangi, t("new"), "🆕"),
                  (asosli, t("valid"), "✅"), (asossiz, "❌ " + (
            "Asossiz" if st.session_state.til == "uz" else "Необоснованные" if st.session_state.til == "ru" else "Unsubstantiated"),
                                              "❌")]
    for col, (son, nom, icon) in zip((c1, c2, c3, c4), stats_data):
        col.markdown(f'<div class="stat-card"><span class="stat-icon">{icon}</span><h3>{son}</h3><p>{nom}</p></div>',
                     unsafe_allow_html=True)

    st.write("")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f'<div class="gov-section-title" style="font-size:18px;">{t("stats_by_category")}</div>',
                    unsafe_allow_html=True)
        if kategoriya_stats:
            st.bar_chart({r["kategoriya"]: r["son"] for r in kategoriya_stats})
        else:
            st.info(t("no_data"))
    with col_b:
        st.markdown(f'<div class="gov-section-title" style="font-size:18px;">{t("stats_by_status")}</div>',
                    unsafe_allow_html=True)
        if status_stats:
            st.bar_chart({status_nomlari.get(r["status"], r["status"]): r["son"] for r in status_stats})
        else:
            st.info(t("no_data"))

    st.markdown('</div>', unsafe_allow_html=True)
    render_gov_footer()


# ============================================================
# ROUTING (kirish tekshiruvi + sahifa yo'naltirish)
# ============================================================
if not st.session_state.xodim_id:
    st.session_state.sahifa = "Xodim kirishi"
    st.switch_page("Fuqaro.py")
else:
    render_gov_header()
    render_gov_nav()

    sahifa = st.session_state.sahifa
    if sahifa == "Xodim: Murojaatlar":
        sahifa_xodim_dashboard()
    elif sahifa == "Xodim: Batafsil":
        m_id = st.session_state.get("tanlangan_murojaat")
        if m_id:
            sahifa_xodim_detail(m_id)
        else:
            sahifa_xodim_dashboard()
    elif sahifa == "Xodim: Statistika":
        sahifa_xodim_statistika()
    else:
        sahifa_xodim_dashboard()
