import streamlit as st
import google.generativeai as genai
import time
import PyPDF2
from PIL import Image

# --- פונקציה לקריאת מאגר השאלות מהקובץ ---
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
        # This error is now less critical as it only affects the chat tab
        return None
    except Exception as e:
        st.error(f"שגיאה בקריאת קובץ ה-PDF: {e}")
        return None

# --- הגדרות והוראות לבוט ---

# 1. טעינת הידע מהקובץ שהעלינו ל-GitHub (שם הקובץ עודכן)
knowledge_base_text = load_knowledge_base("819387ALL.pdf")

# 2. ההוראות הבסיסיות לבוט (העתק לכאן את כל ההוראות המפורטות שלך)
BASE_SYSTEM_INSTRUCTION = """
אתה מורה מומחה במגמות מכטרוניקה (כיתות י–י"ב) עם שלושה מצבים... (וכו')
"""

# 3. שילוב מאגר הידע בהוראות למערכת
if knowledge_base_text:
    SYSTEM_INSTRUCTION = f"""
    {BASE_SYSTEM_INSTRUCTION}
    ---
    **מאגר ידע קבוע:**
    {knowledge_base_text}
    ---
    """
else:
    SYSTEM_INSTRUCTION = BASE_SYSTEM_INSTRUCTION


PAGE_TITLE = "🤖 המורה למכטרוניקה"

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
    # Model for image/quiz generation that doesn't need the whole system prompt
    basic_model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

except Exception as e:
    st.error("שגיאה בהגדרת ה-API Key.", icon="🚨")
    st.stop()

# --- הגדרת טאבים (לשוניות) ---
tab_chat, tab_image, tab_quiz = st.tabs(["💬 צ'אט עם הבוט", "🖼️ ניתוח תמונות", "🧠 מחולל מבחנים"])

# --- טאב 1: צ'אט רגיל ---
with tab_chat:
    st.header("שיחה עם המורה למכטרוניקה")
    if not knowledge_base_text:
        st.warning("שים לב: מאגר הידע הקבוע (קובץ ה-PDF) לא נטען. הבוט יפעל על בסיס הידע הכללי שלו וחיפוש באינטרנט.")
    
    INITIAL_MESSAGE = "שלום, אני המורה הדיגיטלי למכטרוניקה. מאגר הידע שלי טעון ומוכן. איך אוכל לעזור?"
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

# --- טאב 2: ניתוח תמונות ---
with tab_image:
    st.header("ניתוח שרטוטים ותמונות")
    st.info("העלה תמונה של שרטוט טכני, מעגל חשמלי, או רכיב, ושאל את הבוט שאלה לגביה.")
    
    uploaded_image = st.file_uploader("בחר קובץ תמונה", type=["png", "jpg", "jpeg"])
    image_prompt = st.text_input("מה תרצה לשאול על התמונה?", key="image_q")

    if st.button("נתח את התמונה"):
        if uploaded_image and image_prompt:
            with st.spinner("מעבד את התמונה ומנתח..."):
                try:
                    image_obj = Image.open(uploaded_image)
                    # Send both text and image to the model
                    response = basic_model.generate_content([image_prompt, image_obj])
                    st.subheader("תוצאות הניתוח:")
                    st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"אירעה שגיאה בעיבוד התמונה: {e}")
        else:
            st.warning("אנא העלה תמונה וכתוב שאלה.")

# --- טאב 3: מחולל מבחנים ---
with tab_quiz:
    st.header("מחולל מבחנים וחידונים אינטראקטיבי")
    st.info("הגדר את הפרמטרים הרצויים, והבוט יכין עבורך מבחן מותאם אישית.")

    with st.form("quiz_form"):
        quiz_topic = st.text_input("נושא המבחן (לדוגמה: 'חוק אוהם ומעגלים טוריים')")
        num_questions = st.number_input("מספר שאלות", min_value=1, max_value=20, value=5)
        question_type = st.selectbox("סוג השאלות", ["רב-ברירתיות (אמריקאיות) עם 4 אפשרויות", "שאלות פתוחות", "שאלות נכון / לא נכון"])
        difficulty = st.select_slider("רמת קושי", options=["יסודית", "בינונית", "מתקדמת"])
        
        submitted = st.form_submit_button("🚀 צור את המבחן")

    if submitted:
        if quiz_topic:
            with st.spinner(f"מכין מבחן ברמה {difficulty} על {quiz_topic}..."):
                quiz_prompt = f"""
                צור מבחן עבור תלמידי מגמת מכטרוניקה.
                הנושא: {quiz_topic}
                מספר השאלות: {num_questions}
                סוג השאלות: {question_type}
                רמת קושי: {difficulty}
                
                הצג את המבחן בפורמט Markdown, כולל כותרת ברורה.
                אם השאלות הן רב-ברירתיות, הצג 4 אפשרויות וסמן את התשובה הנכונה בסוף המבחן (בקטע נפרד של "מחוון תשובות").
                """
                response = basic_model.generate_content(quiz_prompt)
                st.subheader(f"מבחן בנושא: {quiz_topic}")
                st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)
        else:
            st.warning("אנא הזн נושא למבחן.")
