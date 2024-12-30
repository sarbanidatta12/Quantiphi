import streamlit as st

from utils import get_user
from bot import get_response


# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_folders"] = []
    st.session_state["page"] = "login"

# Login Page
def login_page():
    """
    Displays the login page where users can enter their username and email to log in.
    """
    st.title("Login")
    username = st.text_input("Enter your username (first name):")
    email = st.text_input("Enter your email:")
    
    if st.button("Login"):
        user_folders = get_user(username, email)
        if isinstance(user_folders, list):
            st.session_state["logged_in"] = True
            st.session_state["user_folders"] = user_folders
            st.session_state["page"] = "chatbot"
            st.success("Logged in successfully!")
            st.rerun()  
        else:
            st.error(user_folders)

# Chatbot Page
def chatbot_page():
    """
    Displays the chatbot page where users can enter their queries and receive responses.
    """
    st.title("Document Search")
    st.write(f"Accessible documents from : {', '.join(st.session_state['user_folders'])}")
    query = st.text_input("Enter your query:")
    if st.button("Submit Query"):
        response = get_response(query, st.session_state['user_folders'])
        st.write(response)

# Navigation logic
if st.session_state["page"] == "login":
    login_page()
elif st.session_state["page"] == "chatbot":
    chatbot_page()
