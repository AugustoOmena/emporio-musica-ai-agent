import os
import base64
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from src.agent import StoreAgent

load_dotenv()

CURRENT_MODEL = os.getenv("DEFAULT_MODEL")

if not CURRENT_MODEL:
    st.error("A variável de ambiente 'DEFAULT_MODEL' não foi configurada no arquivo .env.")
    st.stop()


def get_image_base64(path: Path) -> str:
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


logo_path = next((Path(f"docs/assets/logo.{ext}") for ext in ["png", "jpeg", "jpg"] if Path(f"docs/assets/logo.{ext}").exists()), None)

st.set_page_config(
    page_title="Empório da Música",
    page_icon=str(logo_path) if logo_path else "🎸",
    layout="centered"
)

st.markdown(
    """
    <style>
    .header-box {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }
    .header-logo-img {
        width: 64px;
        height: 64px;
        border-radius: 12px;
        object-fit: cover;
    }
    .header-title-box h1 {
        margin: 0;
        font-size: 2rem;
        line-height: 1.1;
    }
    .header-title-box p {
        margin: 4px 0 0 0;
        color: #71717a;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if logo_path:
    b64 = get_image_base64(logo_path)
    mime = "image/png" if logo_path.suffix == ".png" else "image/jpeg"
    st.markdown(
        f"""
        <div class="header-box">
            <img class="header-logo-img" src="data:{mime};base64,{b64}">
            <div class="header-title-box">
                <h1>Empório da Música</h1>
                <p>Central de Atendimento Digital — Campo Grande/MS</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("Empório da Música")
    st.caption("Central de Atendimento Digital — Campo Grande/MS")

with st.sidebar:
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent" not in st.session_state or st.session_state.get("current_model") != CURRENT_MODEL:
    st.session_state.agent = StoreAgent(model_name=CURRENT_MODEL)
    st.session_state.current_model = CURRENT_MODEL

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Digite sua dúvida sobre instrumentos, pedidos ou políticas...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Consultando informações da loja..."):
            agent_response, updated_history = st.session_state.agent.run_conversation_turn(
                st.session_state.chat_history
            )
            st.markdown(agent_response)

    st.session_state.chat_history = updated_history