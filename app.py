import streamlit as st
import google.generativeai as genai
import time
import PyPDF2

# --- פונקציה לקריאת מאגר השאלות מהקובץ ---
# @st.cache_data יגרום לפונקציה לרוץ רק פעם אחת ולשמור את התוצאה בזיכרון
@st.cache_data
def load_knowledge_base(file_path):
    try:
        with open(file_path, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except FileNotFoundError:
        st.error(f"שגיאה: הקובץ '{file_path}' לא נמצא במאגר ה-GitHub. אנא ודא שהעלית אותו בשם הנכון.")
        return None
    except Exception as e:
        st.error(f"שגיאה בקריאת קובץ ה-PDF: {e}")
        return None

# --- הגדרות והוראות לבוט ---

# 1. טעינת הידע מהקובץ שהעלינו ל-GitHub
knowledge_base_text = load_knowledge_base("819387ALL_scanned.pdf")

# 2. ההוראות הבסיסיות לבוט (העתק לכאן את כל ההוראות המפורטות שלך)
BASE_SYSTEM_INSTRUCTION = """
אתה מורה מומחה במגמות מכטרוניקה... (וכו')
...
**יכולות מיוחדות: יש לך גישה מלאה לאינטרנט...**
"""

# 3. שילוב מאגר הידע בהוראות למערכת
# רק אם הקובץ נטען בהצלחה, נוסיף את תוכנו להוראות
if knowledge_base_text:
    SYSTEM_INSTRUCTION = f"""
    {BASE_SYSTEM_INSTRUCTION}

    ---
    **מאגר ידע קבוע:**
    להלן מאגר ידע קבוע המכיל שאלות, תרגילים וחומרים נוספים.
    השתמש במאגר זה כמקור מידע מרכזי ובסיסי לפני שאתה פונה לאינטרנט.
    תוכן המאגר:
    {knowledge_base_text}
    ---
    """
else:
    SYSTEM_INSTRUCTION = BASE_SYSTEM_INSTRUCTION


PAGE_TITLE = "🤖 המורה למכטרוניקה (עם מאגר ידע)"
INITIAL_MESSAGE = "שלום, אני המורה הדיגיטלי למכטרוניקה. מאגר הידע שלי טעון ומוכן. איך אוכל לעזור?"

# --- הגדרות עמוד ו-UI (ללא שינוי) ---
st.set_page_config(page_title=PAGE_TITLE, page_icon="🤖", layout="wide")
st.markdown("""<style> body { direction: rtl; } .stTextInput > div > div > input { direction: rtl; } </style>""", unsafe_allow_html=True)
st.title(PAGE_TITLE)

# --- הגדרות המודל וה-API ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=SYSTEM_INSTRUCTION,
        tools=['google_search_retrieval']
    )
except Exception as e:
    st.error("שגיאה בהגדרת ה-API Key.", icon="🚨")
    st.stop()

# --- לוגיקת הצ'אט (ללא שינוי) ---
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    st.session_state.messages = [{"role": "assistant", "content": INITIAL_MESSAGE}]

for message in st.session_state.get("messages", []):
     with st.chat_message(message["role"]):
        st.markdown(f'<div style="direction: rtl;">{message["content"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("כתבו כאן את שאלתכם..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f'<div style="direction: rtl;">{prompt}</div>', unsafe_allow_html=True)
    
    with st.spinner("חושב, מעיין במאגר וגם מחפש ברשת..."):
        response = st.session_state.chat.send_message(prompt)

    with st.chat_message("assistant"):
        st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
