import os
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


def send_message(message: str):
    url = f"{API_URL}/chat"
    payload = {"message": message,
               "session_id": st.session_state["session_id"]}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=60)
    except requests.RequestException as exc:
        st.error(f"⚠️ No se pudo conectar con el servidor: {exc}")
        return

    if response.status_code == 200:
        data = response.json()
        if "reply" in data:
            st.session_state["chat_history"].append(("Usuario", message))
            st.session_state["chat_history"].append(("Chatbot", data["reply"]))
        else:
            st.error("⚠️ Error en servidor")
    else:
        st.error(f"⚠️ Error HTTP {response.status_code}")


# Per-browser session id so each visitor gets an isolated conversation.
if "session_id" not in st.session_state:
    st.session_state["session_id"] = f"ui-{uuid.uuid4().hex[:12]}"
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

st.set_page_config(page_title="Chatbot Pedidos",
                   page_icon="🛒", layout="centered")
st.title("💬 Chatbot de pedidos")
st.subheader("Haga sus pedidos")

user_input = st.chat_input("Escribe tu pedido:")
if user_input:
    send_message(user_input)

for sender, text in st.session_state["chat_history"]:
    if sender == "Usuario":
        with st.chat_message("user", avatar="🧑"):
            st.markdown(text)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(text)
