import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
from PIL import Image
from openai import OpenAI

import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ================================
# 🔑 API KEY (ADD YOUR KEY HERE)
# ================================
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="YOUR_API_KEY_HERE"
)

# ================================
# 🧠 CORE LOGIC
# ================================

def get_trust_score(worker):
    score = 100
    score -= worker["complaints"] * 5
    score -= worker["location_changes"] * 3
    if worker["id_verified"] == 0:
        score -= 30
    return max(0, score)

def fraud_score(worker):
    score = 0
    if worker["id_verified"] == 0:
        score += 50
    if worker["face_match_score"] < 50:
        score += 30
    if worker["complaints"] > 3:
        score += 20
    return score

# ================================
# 📄 DOCUMENT OCR
# ================================
def extract_text(image):
    return pytesseract.image_to_string(image)

def document_verification(image):
    text = extract_text(image)

    return {
        "Extracted Text": text[:200],
        "Aadhaar Check": "Detected" if any(c.isdigit() for c in text) else "Not Found",
        "Document Authenticity": "Suspicious" if "xxxx" in text.lower() else "Likely Genuine"
    }

# ================================
# 🌐 NETWORK ANALYSIS
# ================================
G = nx.Graph()

def add_connection(w1, w2):
    G.add_edge(w1, w2)

def network_check(worker_id):
    return list(G.neighbors(worker_id)) if worker_id in G else []

# ================================
# 🤖 AGENTS
# ================================
def decision_agent(score):
    if score > 70:
        return "Approve"
    elif score > 40:
        return "Review"
    return "Reject"

def alert_agent(worker):
    alerts = []
    if worker["complaints"] > 3:
        alerts.append("High complaints")
    if worker["location_changes"] > 5:
        alerts.append("Suspicious movement")
    return alerts

# ================================
# 🧠 QWEN LLM
# ================================
def qwen_explain(worker, result):
    try:
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-3b-instruct",
            messages=[{
                "role": "user",
                "content": f"Explain worker risk clearly:\nWorker:{worker}\nResult:{result}"
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM Error: {str(e)}"

# ================================
# 🪪 DIGITAL PASSPORT
# ================================
def generate_passport(result, worker_id):
    return f"""
    Worker ID: {worker_id}
    Trust Score: {result['Trust Score']}
    Risk Level: {result['Risk Level']}
    Decision: {result['Decision']}
    """

# ================================
# 🔥 FULL SYSTEM
# ================================
def full_system(worker, image):

    worker_id = "W123"

    score = get_trust_score(worker)

    result = {
        "Trust Score": score,
        "Risk Level": "Low" if score > 70 else "Medium" if score > 40 else "High",
        "Fraud Score": fraud_score(worker),
        "Decision": decision_agent(score),
        "Document Check": document_verification(image),
        "Network": network_check(worker_id),
        "Network Risk": "High" if len(network_check(worker_id)) > 0 else "Low",
        "Alerts": alert_agent(worker),
    }

    # LLM
    result["Explanation"] = qwen_explain(worker, result)

    # Extra features
    result["Digital Passport"] = generate_passport(result, worker_id)
    result["Risk Timeline"] = [score, score-5, score-10]

    return result

# ================================
# 🎨 UI
# ================================

st.set_page_config(page_title="Worker Verification AI", layout="wide")

st.title("🚀 AI-Based Worker Verification System")

# Sidebar Input
st.sidebar.header("Worker Input")

id_verified = st.sidebar.selectbox("ID Verified", [0,1])
face_match = st.sidebar.slider("Face Match Score", 0, 100, 80)
location_changes = st.sidebar.slider("Location Changes", 0, 10, 2)
previous_employers = st.sidebar.slider("Previous Employers", 0, 5, 2)
complaints = st.sidebar.slider("Complaints", 0, 10, 1)
work_gap = st.sidebar.slider("Work Gap Days", 0, 200, 20)
age = st.sidebar.slider("Age", 18, 60, 25)

worker = {
    "id_verified": id_verified,
    "face_match_score": face_match,
    "location_changes": location_changes,
    "previous_employers": previous_employers,
    "complaints": complaints,
    "work_gap_days": work_gap,
    "age": age
}

# Upload
uploaded_file = st.file_uploader("Upload ID Document", type=["png","jpg","jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Document", width=300)

    if st.button("Verify Worker"):

        result = full_system(worker, image)

        # ================================
        # 🎯 OUTPUT UI
        # ================================

        st.subheader("📊 Results")

        # Risk color
        if result["Risk Level"] == "High":
            st.error("🔴 High Risk")
        elif result["Risk Level"] == "Medium":
            st.warning("🟠 Medium Risk")
        else:
            st.success("🟢 Low Risk")

        # Core
        st.write("### Core Metrics")
        st.write("Trust Score:", result["Trust Score"])
        st.write("Fraud Score:", result["Fraud Score"])
        st.write("Decision:", result["Decision"])

        # Document
        st.write("### 📄 Document Check")
        st.json(result["Document Check"])

        # Network
        st.write("### 🌐 Network")
        st.write("Connections:", result["Network"])
        st.write("Network Risk:", result["Network Risk"])

        # Alerts
        st.write("### 🚨 Alerts")
        st.write(result["Alerts"])

        # Timeline
        st.write("### 📉 Risk Timeline")
        st.line_chart(result["Risk Timeline"])

        # Passport
        st.write("### 🪪 Digital Passport")
        st.code(result["Digital Passport"])

        # LLM
        st.write("### 🧠 AI Explanation")
        st.write(result["Explanation"])