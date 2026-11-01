import requests
import streamlit as st

API_URL="http://localhost:8000"

st.title("TFSA Assistant")

question=st.text_input("Ask a question")

if st.button("Ask"):
    with st.spinner("Thinking...."):
        if not question:
            st.warning("Type a question first")
            st.stop()
        else:
            try:
             response = requests.post(f"{API_URL}/ask", json={"question": question}, timeout=120)
            except requests.exceptions.RequestException:
                st.error("Can't reach the assistant right now. Please try again shortly.")
                st.stop()

    if response.status_code!=200:
        st.error(f"Something went wrong (status{response.status_code})")
        st.stop()

    data=response.json()
    category=data["result"]["category"]

    if category == "safe":
        st.success(f"Category: {category}")
    elif category == "violation":
        st.error(f"Category: {category}")
    else:
        st.info(f"Category: {category}")
    
    st.write(data["result"]["answer"])

    if len(data["result"]["citations"])>0:
        st.subheader("Sources")
        for c in data["result"]["citations"]:
            st.write(f"Page {c['page']}: *{c['quote']}*")
    if data["result"]["needs_review"]:
        st.warning("Flagged for human review")