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
        return None
    except Exception as e:
        st.error(f"שגיאה בקריאת קובץ ה-PDF: {e}")
        return None

# --- הגדרות והוראות לבוט ---
knowledge_base_text = load_knowledge_base("819387ALL.pdf")
BASE_SYSTEM_INSTRUCTION = """
אתה מורה מומחה במגמות מכטרוניקה... (העתק לכאן את כל ההוראות המפורטות שלך)
"""
if knowledge_base_text:
    SYSTEM_INSTRUCTION = f"{BASE_SYSTEM_INSTRUCTION}\n\n---מאגר ידע קבוע---\n{knowledge_base_text}\n---"
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
    # Model for chat with system instructions
    chat_model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=SYSTEM_INSTRUCTION,
        tools=['google_search_retrieval']
    )
    # Basic model for other tasks like image/quiz generation
    basic_model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
except Exception as e:
    st.error("שגיאה בהגדרת ה-API Key.", icon="🚨")
    st.stop()

# --- הגדרת טאבים (לשוניות) ---
tab_chat, tab_image_analysis, tab_quiz, tab_image_generation = st.tabs([
    "💬 צ'אט עם הבוט", 
    "🖼️ ניתוח תמונות", 
    "🧠 מחולל מבחנים",
    "🎨 יצירת תמונות"
])

# --- טאב 1: צ'אט רגיל ---
with tab_chat:
    # ... (כל קוד הצ'אט מהגרסה הקודמת נשאר כאן ללא שינוי) ...
    st.header("שיחה עם המורה למכטרוניקה")
    if not knowledge_base_text:
        st.warning("שים לב: מאגר הידע הקבוע (קובץ ה-PDF) לא נטען.")
    
    INITIAL_MESSAGE = "שלום, אני המורה הדיגיטלי למכטרוניקה. איך אוכל לעזור?"
    if "chat" not in st.session_state:
        st.session_state.chat = chat_model.start_chat(history=[])
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
with tab_image_analysis:
    # ... (כל קוד ניתוח התמונות מהגרסה הקודמת נשאר כאן ללא שינוי) ...
    st.header("ניתוח שרטוטים ותמונות")
    st.info("העלה תמונה של שרטוט טכני, מעגל חשמלי, או רכיב, ושאל את הבוט שאלה לגביה.")
    uploaded_image = st.file_uploader("בחר קובץ תמונה", type=["png", "jpg", "jpeg"], key="analyzer")
    image_prompt = st.text_input("מה תרצה לשאול על התמונה?", key="image_q")
    if st.button("נתח את התמונה"):
        if uploaded_image and image_prompt:
            with st.spinner("מעבד את התמונה ומנתח..."):
                image_obj = Image.open(uploaded_image)
                response = basic_model.generate_content([image_prompt, image_obj])
                st.subheader("תוצאות הניתוח:")
                st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)
        else:
            st.warning("אנא העלה תמונה וכתוב שאלה.")

# --- טאב 3: מחולל מבחנים ---
with tab_quiz:
    # ... (כל קוד מחולל המבחנים מהגרסה הקודמת נשאר כאן ללא שינוי) ...
    st.header("מחולל מבחנים וחידונים אינטראקטיבי")
    with st.form("quiz_form"):
        quiz_topic = st.text_input("נושא המבחן")
        num_questions = st.number_input("מספר שאלות", min_value=1, max_value=20, value=5)
        question_type = st.selectbox("סוג השאלות", ["רב-ברירתיות (אמריקאיות)", "פתוחות", "נכון / לא נכון"])
        difficulty = st.select_slider("רמת קושי", options=["קלה", "בינונית", "קשה"])
        submitted = st.form_submit_button("🚀 צור את המבחן")
    if submitted and quiz_topic:
        with st.spinner("מכין מבחן..."):
            quiz_prompt = f"צור מבחן בנושא {quiz_topic}, עם {num_questions} שאלות מסוג {question_type} ברמת קושי {difficulty}."
            response = basic_model.generate_content(quiz_prompt)
            st.subheader(f"מבחן בנושא: {quiz_topic}")
            st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)

# --- טאב 4: יצירת תמונות ---
with tab_image_generation:
    st.header("יצירת תמונות מטקסט (Text-to-Image)")
    st.info("תאר במילים את התמונה שברצונך שהבינה המלאכותית תיצור עבורך - עדיף באנגלית.")
    
    image_gen_prompt = st.text_area("התיאור שלך (באנגלית לקבלת התוצאות הטובות ביותר):", key="image_gen_prompt", placeholder="A photorealistic image of a robot arm assembling a circuit board in a futuristic factory")

    if st.button("🎨 צור את התמונה"):
        if image_gen_prompt:
            with st.spinner("האמן הדיגיטלי עובד על היצירה שלך... (זה עשוי לקחת כדקה)"):
                try:
                    # The prompt to the model needs to be explicit about the task
                    generation_task_prompt = f"Generate an image based on the following description: {image_gen_prompt}"
                    
                    response = basic_model.generate_content(generation_task_prompt)
                    
                    # The model that can generate images will return image data in one of its 'parts'
                    # We need to find and display it
                    image_data_found = False
                    for part in response.parts:
                        if part.inline_data:
                            image_data = part.inline_data.data
                            st.image(image_data, caption=f"יצירה על פי התיאור: {image_gen_prompt}")
                            image_data_found = True
                            break # Stop after finding the first image
                    
                    if not image_data_found:
                        st.error("המודל לא החזיר תמונה. ייתכן שהבקשה הפרה את מדיניות הבטיחות או שלא הובנה. נסה תיאור אחר.")

                except Exception as e:
                    st.error(f"אירעה שגיאה ביצירת התמונה: {e}")
        else:
            st.warning("אנא הזн תיאור לתמונה.")
