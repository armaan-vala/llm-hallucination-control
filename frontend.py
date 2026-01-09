import streamlit as st
import requests

# Backend API URL
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="GraphRAG Agent", layout="wide")

st.title("🤖 GraphRAG Knowledge Agent")
st.markdown("### Powered by Groq, Neo4j, and ChromaDB")

# --- Sidebar: PDF Upload ---
with st.sidebar:
    st.header("📂 Document Upload")
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Process PDF"):
            with st.spinner("Extracting Text, Building Graph, and Vectorizing..."):
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                try:
                    response = requests.post(f"{API_URL}/upload-pdf", files=files)
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Processing Complete!")
                        st.markdown(f"**Nodes Created:** {data.get('graph_nodes', 0)}")
                        st.markdown(f"**Vector Chunks:** {data.get('vector_chunks', 0)}")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection Failed: {e}")

# --- Main Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask a question about your PDF..."):
    # 1. Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call Backend API
    with st.chat_message("assistant"):
        with st.spinner("Thinking (Querying Graph + Vectors)..."):
            try:
                payload = {"question": prompt}
                response = requests.post(f"{API_URL}/ask-question", json=payload)
                
                if response.status_code == 200:
                    ans_data = response.json()
                    answer_text = ans_data.get("answer", "No answer found.")
                    
                    st.markdown(answer_text)
                    
                    # Optional: Show what context was used (Debug info)
                    with st.expander("🔍 See Context Used"):
                        st.json(ans_data.get("context_used", {}))
                    
                    # Add to history
                    st.session_state.messages.append({"role": "assistant", "content": answer_text})
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")