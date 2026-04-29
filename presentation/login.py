"""
Login Page - Authentication UI for user login and registration.
Updated for new schema.
"""

from typing import Any, Callable, Optional

import streamlit as st

from domain.entities import User
from use_cases.auth_service import AuthResult, AuthService


def render_login_page(
    auth_service: AuthService, on_login_success: Callable[[User, Any], None]
) -> None:
    """
    Render the login/registration page.

    Args:
        auth_service: Authentication service instance
        on_login_success: Callback function when login succeeds
    """
    # Custom CSS for login page
    st.markdown(
        """
        <style>
            .login-container {
                max-width: 400px;
                margin: 50px auto;
                padding: 40px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            .login-header {
                text-align: center;
                margin-bottom: 30px;
            }
            .login-header h1 {
                color: #10B981;
                font-size: 28px;
                margin-bottom: 8px;
            }
            .login-header p {
                color: #64748B;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Login header
        st.markdown(
            """
            <div class="login-header">
                <h1>📊 SmartXL</h1>
                <p>Crie dashboards profissionais a partir dos seus dados</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tab selection for login/register
        tab1, tab2 = st.tabs(["🔑 Entrar", "📝 Registrar"])

        with tab1:
            render_login_form(auth_service, on_login_success)

        with tab2:
            render_register_form(auth_service, on_login_success)


def render_login_form(
    auth_service: AuthService, on_login_success: Callable[[User, Any], None]
) -> None:
    """Render the login form."""
    st.markdown("### Entrar na sua conta")

    username = st.text_input(
        "Usuário ou Email",
        placeholder="Digite seu usuário ou email",
        key="login_username",
    )

    password = st.text_input(
        "Senha", type="password", placeholder="Digite sua senha", key="login_password"
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    if st.button(
        "Entrar", type="primary", key="login_submit", use_container_width=True
    ):
        if not username or not password:
            st.error("Por favor, preencha todos os campos")
            return

        result = auth_service.login(username, password)

        if result.success and result.user:
            st.success(f"Bem-vindo, {result.user.username}!")
            on_login_success(result.user, result.session)
            st.rerun()
        else:
            st.error(result.error_message or "Falha no login")


def render_register_form(
    auth_service: AuthService, on_login_success: Callable[[User, Any], None]
) -> None:
    """Render the registration form."""
    st.markdown("### Criar nova conta")

    username = st.text_input(
        "Usuário",
        placeholder="Escolha um nome de usuário",
        key="register_username",
        max_chars=50,
    )

    email = st.text_input("Email", placeholder="seu@email.com", key="register_email")

    password = st.text_input(
        "Senha",
        type="password",
        placeholder="Mínimo 6 caracteres",
        key="register_password",
    )

    confirm_password = st.text_input(
        "Confirmar Senha",
        type="password",
        placeholder="Digite a senha novamente",
        key="register_confirm_password",
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    if st.button(
        "Criar Conta", type="primary", key="register_submit", use_container_width=True
    ):
        if not all([username, email, password, confirm_password]):
            st.error("Por favor, preencha todos os campos obrigatórios")
            return

        if password != confirm_password:
            st.error("As senhas não coincidem")
            return

        if len(password) < 6:
            st.error("A senha deve ter pelo menos 6 caracteres")
            return

        result = auth_service.register(
            username=username, email=email, password=password
        )

        if result.success and result.user:
            st.success("Conta criada com sucesso!")
            on_login_success(result.user, result.session)
            st.rerun()
        else:
            st.error(result.error_message or "Falha ao criar conta")


def render_user_menu(
    user: User, on_logout: Callable[[], None], on_settings: Callable[[], None]
) -> None:
    """
    Render the user menu in the sidebar.

    Args:
        user: Current user entity
        on_logout: Callback for logout action
        on_settings: Callback for settings action
    """
    st.markdown(
        f"""
        <div style='
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            border-radius: 12px;
            padding: 16px;
            color: white;
            margin-bottom: 16px;
        '>
            <div style='font-weight: 600; font-size: 16px;'>{user.username}</div>
            <div style='font-size: 12px; opacity: 0.9;'>{user.email}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⚙️ Config", key="user_settings_btn", use_container_width=True):
            on_settings()

    with col2:
        if st.button("🚪 Sair", key="user_logout_btn", use_container_width=True):
            on_logout()
            st.rerun()
