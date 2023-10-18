import streamlit as st

from src.detector import PromptInjectionDetector

# download model
model = PromptInjectionDetector(config_path="src/config/config.json")
st.title("Your joke maker")

# Initialize chat history
# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me to crack a joke about..."}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Tell me a joke about..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = model.process_query(request={"query": prompt})
            for key, value in response.items():
                if not isinstance(value, dict):
                    st.write(f"{key} {value}")
                else:
                    for k, v in value.items():
                        st.write(f"{k} {v}")
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
