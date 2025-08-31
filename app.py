import streamlit as st
import google.generativeai as genai
import time
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi
import re

# --- פונקציה לקריאת מאגר השאלות מהקובץ (מהגרסה הקודמת) ---
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
        st.error(f"שגיאה: הקובץ '{file_path}' לא נמצא במאגר ה-GitHub.")
        return None
    except Exception as e:
        st.error(f"שגיאה בקריאת קובץ ה-PDF: {e}")
        return None

# --- פונקציות חדשות לניתוח יוטיוב ---
def get_video_id_from_url(url):
    """Extracts the YouTube video ID from a URL."""
    # Matches formats: youtube.com/watch?v=... , youtu.be/... , youtube.com/embed/...
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

@st.cache_data
def get_transcript(video_url):
    video_id = get_video_id_from_url(video_url)
    if not video_id:
        return None, "כתובת ה-URL של הסרטון אינה תקינה."
    try:
        # Fetch transcript, prioritizing Hebrew, falling back to English
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['iw', 'en'])
        transcript_text = " ".join([item['text'] for item in transcript_list])
        return transcript_text, None
    except Exception as e:
        return None, f"לא נמצא תמלול עבור סרטון זה, או שבעל הסרטון חסם את הגישה. (שגיאה: {e})"

# --- הגדרות והוראות לבוט ---
knowledge_base_text = load_knowledge_base("maagar_sheelot.pdf")
BASE_SYSTEM_INSTRUCTION = """
אתה מורה מומחה למכטרוניקה... (העתק לכאן את כל ההוראות המפורטות שלך)
"""
if knowledge_base_text:
    SYSTEM_INSTRUCTION = f"{BASE_SYSTEM_INSTRUCTION}\n\n---מאגר ידע קבוע---\n{knowledge_base_text}\n---"
else:
    SYSTEM_INSTRUCTION = BASE_SYSTEM_INSTRUCTION

PAGE_TITLE = "🤖 המורה למכטרוניקה"
INITIAL_MESSAGE = "שלום, אני המורה הדיגיטלי למכטרוניקה. מאגר הידע שלי טעון ומוכן. איך אוכל לעזור?"

# --- הגדרות עמוד ו-UI ---
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

# --- הגדרת טאבים (לשוניות) ---
tab_chat, tab_youtube = st.tabs(["💬 צ'אט עם הבוט", "🎬 ניתוח סרטוני YouTube"])

# --- טאב 1: צ'אט רגיל ---
with tab_chat:
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
        
        with st.chat_message("assistant"):
            with st.spinner("חושב, מעיין במאגר וגם מחפש ברשת..."):
                response_stream = st.session_state.chat.send_message(prompt, stream=True)
                full_response = st.write_stream(response_stream)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- טאב 2: ניתוח יוטיוב ---
with tab_youtube:
    st.header("ניתוח סרטוני לימוד מ-YouTube")
    st.write("הדבק קישור לסרטון, בחר מה תרצה לעשות, והבוט ינתח את התמלול עבורך.")
    
    youtube_url = st.text_input("הדבק כאן קישור לסרטון YouTube:")
    action_type = st.selectbox(
        "בחר את הפעולה הרצויה:",
        ["סיכום הסרטון בנקודות", "יצירת 5 שאלות מבחן על הסרטון", "זיהוי 3 מושגי מפתח והסברם"]
    )

    if st.button("🚀 נתח את הסרטון"):
        if youtube_url:
            with st.spinner("מוריד ומעבד את תמלול הסרטון..."):
                transcript, error_message = get_transcript(youtube_url)
            
            if error_message:
                st.error(error_message)
            else:
                st.success("התמלול הורד בהצלחה!")
                
                prompt_for_analysis = f"בהתבסס על תמלול הסרטון הבא, בצע את המשימה: '{action_type}'.\n\nהתמלול:\n{transcript}"
                
                with st.spinner("הבינה המלאכותית מנתחת את התוכן..."):
                    # For one-off tasks like this, using generate_content is often simpler
                    analysis_model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
                    response = analysis_model.generate_content(prompt_for_analysis)
                
                st.subheader("תוצאות הניתוח:")
                st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)
        else:
            st.warning("אנא הדבק קישור לסרטון.")
