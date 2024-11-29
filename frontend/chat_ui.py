import streamlit as st
import requests
import json
import websockets
import asyncio
import json

# Configure the page
st.set_page_config(page_title="Chat Application", layout="wide")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "token" not in st.session_state:
    st.session_state.token = None
if "name" not in st.session_state:
    st.session_state.name = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Backend configuration
BACKEND_URL = "http://localhost:3500"
WS_URL = "ws://localhost:3500"

def get_token(name):
    """Get authentication token from backend"""
    try:
        response = requests.post(f"{BACKEND_URL}/token", params={"name": name})
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        else:
            st.error(f"Error getting token: {response.json()}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

async def connect_websocket(token, message):
    """Connect to WebSocket and send/receive messages"""
    try:
        async with websockets.connect(f"{WS_URL}/chat?token={token}") as websocket:
            # Send message
            await websocket.send(message)
            
            # Wait for response
            response = await websocket.recv()
            return response
    except Exception as e:
        st.error(f"WebSocket error: {str(e)}")
        return None

# Login section (only show if not authenticated)
if not st.session_state.authenticated:
    st.title("Chat Login")
    with st.form("login_form"):
        name = st.text_input("Enter your name")
        submit = st.form_submit_button("Join Chat")
        
        if submit and name:
            token = get_token(name)
            if token:
                st.session_state.token = token
                st.session_state.name = name
                st.session_state.authenticated = True
                st.rerun()

# Chat interface (only show if authenticated)
if st.session_state.authenticated:
    st.title(f"Chat as {st.session_state.name}")
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.token = None
        st.session_state.name = None
        st.session_state.messages = []
        st.rerun()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Send message through WebSocket and get response
        response = asyncio.run(connect_websocket(st.session_state.token, prompt))
        
        if response:
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response)
        
        # Force a rerun to update the chat display
        st.rerun()

# Add some styling
st.markdown("""
    <style>
    .stChat {
        padding: 20px;
    }
    .stChatMessage {
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)