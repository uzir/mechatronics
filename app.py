import streamlit as st
import google.generativeai as genai
import time
import PyPDF2

# ============== זה החלק ששדרגנו ==============

# פונקציה לחילוץ טקסט מקובץ PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"שגיאה בקריאת קובץ ה-PDF: {e}")
        return None

# ההוראות הבסיסיות לבוט
BASE_SYSTEM_INSTRUCTION = """
אתה מורה מומחה במגמות מכטרוקניה... (וכו', כל ההוראות הקודמות שלך)
...
**יכולות מיוחדות: באפשרותך לגשת לאינטרנט...**
"""
# (שים לב: קיצרתי את ההוראות כאן כדי לא להעמיס, אבל בקוד שלך הדבק את כולן)

# =======================================================


# --- הגדרות עמוד ו-UI ---
st.set_page_config(page_title="המורה למכטרוניקה", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    body { direction: rtl; }
    .stTextInput > div > div > input { direction: rtl; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 המורה למכטרוניקה (עם העלאת קבצים)")

# --- סרגל צד להעלאת קבצים ---
with st.sidebar:
    st.header("🧠 האכלת הבוט במידע")
    uploaded_file = st.file_uploader("העלה קובץ PDF מהדרייב שלך", type=["pdf"])
    file_context = ""
    if uploaded_file is not None:
        with st.spinner("מעבד את הקובץ..."):
            file_context = extract_text_from_pdf(uploaded_file)
            if file_context:
                st.success("הקובץ עובד בהצלחה! הבוט 'למד' את תוכנו.")

# --- הרכבת ההוראות המלאות (בסיס + תוכן מהקובץ) ---
if file_context:
    dynamic_system_instruction = f"""
    {BASE_SYSTEM_INSTRUCTION}

    ---
    **מידע נוסף מקובץ שהועלה:**
    המשתמש העלה קובץ עם התוכן הבא. בסס את תשובותיך גם על מידע זה:
    
    {file_context}
    ---
    """
else:
    dynamic_system_instruction = BASE_SYSTEM_INSTRUCTION


# --- הגדרות המודל וה-API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=dynamic_system_instruction,
        tools=['google_search_retrieval']
    )
except Exception as e:
    st.error("שגיאה בהגדרת ה-API Key.", icon="🚨")
    st.stop()

# --- לוגיקת הצ'אט (נשארה כמעט זהה) ---
INITIAL_MESSAGE = "שלום! תוכל לשאול אותי שאלות, או להעלות קובץ PDF בסרגל הצד כדי שאנתח אותו."
if "chat" not in st.session_state or uploaded_file is not None:
    st.session_state.chat = model.start_chat(history=[])
    if "messages" not in st.session_state or uploaded_file is not None:
        st.session_state.messages = [{"role": "assistant", "content": INITIAL_MESSAGE}]

for message in st.session_state.get("messages", []):
     with st.chat_message(message["role"]):
        st.markdown(f'<div style="direction: rtl;">{message["content"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("כתבו כאן את שאלתכם..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div style="direction: rtl;">{prompt}</div>', unsafe_allow_html=True)
    
    with st.spinner("חושב וגם מחפש ברשת..."):
        response = st.session_state.chat.send_message(prompt)

    with st.chat_message("assistant"):
        st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
