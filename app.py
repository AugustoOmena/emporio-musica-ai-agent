import os
import streamlit as st
from dotenv import load_dotenv
from src.agent import StoreAgent

load_dotenv()

DEFAULT_CONFIGURED_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-3.5-flash-lite")

AVAILABLE_MODELS = [ DEFAULT_CONFIGURED_MODEL,"gemini/gemini-3.5-flash-lite" ]

AVAILABLE_MODELS = list(dict.fromkeys(AVAILABLE_MODELS))

st.set_page_config(
    page_title="Empório da Música - Atendimento Virtual",
    page_icon="🎸",
    layout="centered"
)

st.title("🎸 Empório da Música")
st.caption("Atendimento Inteligente - Campo Grande/MS")

with st.sidebar:
    st.header("Configurações do Agente")
    selected_model = st.selectbox(
        "Modelo de Linguagem (LiteLLM)",
        options=AVAILABLE_MODELS,
        index=0
    )
    if st.button("Limpar Histórico de Conversa"):
        st.session_state.chat_history = []
        st.rerun()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent" not in st.session_state or st.session_state.get("current_model") != selected_model:
    st.session_state.agent = StoreAgent(model_name=selected_model)
    st.session_state.current_model = selected_model

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