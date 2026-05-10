"""
Sidebar Component - Main navigation and controls.
"""

from typing import Optional, Callable
from datetime import datetime
import streamlit as st
from utils.session_state import get_state, set_state


def render_sidebar(
    analysis_service,
    on_new_analysis: Callable,
    on_select_analysis: Callable,
    on_settings_click: Callable,
    on_upload: Callable,
) -> None:
    """Sidebar dark com logo, upload, histórico e configurações."""
    with st.sidebar:
        # ── Logo / Brand ──────────────────────────────────────────────────────
        st.markdown(
            """
            <div style='padding: 8px 0 20px; border-bottom: 1px solid rgba(255,255,255,.08); margin-bottom: 20px;'>
                <div style='font-size: 1.4rem; font-weight: 700; color: #F8FAFC; letter-spacing: -0.3px;'>
                    📊 Smart BI
                </div>
                <div style='font-size: 0.72rem; color: #64748B; margin-top: 2px;'>
                    Dashboard Builder
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Ações principais ──────────────────────────────────────────────────
        if st.button("＋  Nova análise", width='stretch', type="primary"):
            on_new_analysis()

        st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)

        # Upload inline (toggle)
        if st.button("📂  Carregar dados", width='stretch'):
            set_state("show_uploader", not get_state("show_uploader"))

        if get_state("show_uploader"):
            with st.container():
                st.markdown(
                    "<div style='background:rgba(255,255,255,.05);border-radius:8px;"
                    "padding:12px;margin-top:8px;border:1px solid rgba(255,255,255,.1)'>",
                    unsafe_allow_html=True,
                )
                uploaded_file = st.file_uploader(
                    "Excel", type=["xlsx", "xls", "csv"], label_visibility="collapsed"
                )
                default_name = (
                    uploaded_file.name.rsplit(".", 1)[0] if uploaded_file else "Nova Análise"
                )
                analysis_name = st.text_input(
                    "Nome", value=default_name, label_visibility="collapsed",
                    placeholder="Nome da análise…",
                    key=f"upload_name_{uploaded_file.name if uploaded_file else 'empty'}",
                )
                if uploaded_file:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✓ Carregar", type="primary", width='stretch'):
                            set_state("show_uploader", False)
                            on_upload(uploaded_file, analysis_name)
                    with c2:
                        if st.button("✗", width='stretch'):
                            set_state("show_uploader", False)
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<div style='border-top:1px solid rgba(255,255,255,.08);margin:20px 0 16px;'></div>",
            unsafe_allow_html=True,
        )

        # ── Histórico ─────────────────────────────────────────────────────────
        st.markdown(
            "<div style='font-size:.7rem;font-weight:600;letter-spacing:.08em;"
            "color:#475569;text-transform:uppercase;margin-bottom:10px;'>Recentes</div>",
            unsafe_allow_html=True,
        )

        history = analysis_service.get_analysis_history()
        if history:
            history.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            current_id = st.session_state.get("current_analysis_id")

            for item in history[:8]:
                aid = item.get("id")
                name = item.get("name", "Sem nome")
                updated = item.get("updated_at", "")
                is_active = current_id == aid

                try:
                    dt = datetime.fromisoformat(updated)
                    date_str = dt.strftime("%d/%m %H:%M")
                except Exception:
                    date_str = ""

                active_style = (
                    "background:rgba(59,130,246,.25);border-color:rgba(59,130,246,.5);"
                    if is_active else ""
                )
                st.markdown(
                    f"""
                    <div style='padding:8px 10px;border-radius:6px;margin-bottom:4px;
                                border:1px solid rgba(255,255,255,.07);cursor:pointer;
                                transition:background .15s;{active_style}'
                         onclick='void(0)'>
                        <div style='font-size:.83rem;font-weight:{"600" if is_active else "400"};
                                    color:{"#93C5FD" if is_active else "#CBD5E1"};
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>
                            {"▶ " if is_active else ""}{name}
                        </div>
                        <div style='font-size:.7rem;color:#475569;margin-top:2px;'>{date_str}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Botão invisível que cobre o card (Streamlit não suporte onclick em divs)
                if st.button(
                    name[:28],
                    key=f"history_{aid}",
                    width='stretch',
                    type="primary" if is_active else "secondary",
                ):
                    on_select_analysis(aid)
        else:
            st.markdown(
                "<div style='font-size:.8rem;color:#475569;padding:8px 0;'>"
                "Nenhuma análise ainda.</div>",
                unsafe_allow_html=True,
            )

        # ── Rodapé ────────────────────────────────────────────────────────────
        st.markdown(
            "<div style='border-top:1px solid rgba(255,255,255,.08);margin:20px 0 12px;'></div>",
            unsafe_allow_html=True,
        )

        settings = analysis_service.get_settings()
        auto_save = st.toggle(
            "Auto-save", value=settings.get("auto_save", True),
            help="Salva automaticamente após cada alteração",
        )
        if auto_save != settings.get("auto_save"):
            analysis_service.update_settings({"auto_save": auto_save})

        if st.button("⚙️  Definições", width='stretch'):
            on_settings_click()

        st.markdown(
            "<div style='font-size:.68rem;color:#334155;text-align:center;margin-top:12px;'>"
            "Smart BI v1.0.0</div>",
            unsafe_allow_html=True,
        )


def render_secondary_sidebar(data_schema, on_add_visualization, visible=True):
    """Legacy — mantido por compatibilidade, não usado no layout atual."""
    pass
