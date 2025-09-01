import streamlit as st
import google.generativeai as genai
import PyPDF2
from PIL import Image
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.text import PP_ALIGN
import io

# --- פונקציות עזר ---

@st.cache_data
def load_knowledge_base(file_path):
    """קוראת תוכן מקובץ PDF ומחזירה אותו כטקסט."""
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

# --- פונקציה מתוקנת ליצירת מצגת (עם תמיכה מלאה ב-RTL ובחירת תבנית חכמה) ---
def create_presentation_from_text(text_content):
    prs = Presentation()
    slides_text = text_content.strip().split("\n\n")

    # הגדרת אינדקסים לתבניות נפוצות
    TITLE_AND_CONTENT_LAYOUT = 1
    TITLE_ONLY_LAYOUT = 5

    for slide_text in slides_text:
        lines = slide_text.strip().split('\n')
        if not lines or not lines[0]: continue

        title = lines[0].replace("#", "").strip()
        content_points = [line.replace("-", "").strip() for line in lines[1:] if line.strip().startswith("-")]

        # --- התיקון המרכזי: בחירת תבנית דינמית ---
        if content_points:
            slide_layout = prs.slide_layouts[TITLE_AND_CONTENT_LAYOUT]
            slide = prs.slides.add_slide(slide_layout)
            
            # טיפול בתוכן רק אם הוא קיים
            content_shape = slide.shapes.placeholders[1]
            tf = content_shape.text_frame
            tf.clear()
            
            for point in content_points:
                p = tf.add_paragraph()
                p.text = point
                p.alignment = PP_ALIGN.RIGHT
                p.level = 0
        else:
            # אם אין נקודות תוכן, השתמש בתבנית של כותרת בלבד
            slide_layout = prs.slide_layouts[TITLE_ONLY_LAYOUT]
            slide = prs.slides.add_slide(slide_layout)
        
        # טיפול בכותרת (משותף לשתי התבניות)
        title_shape = slide.shapes.title
        title_shape.text = title
        title_shape.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT
            
    # שמירת המצגת
    bio = io.BytesIO()
    prs.save(bio)
    return bio.getvalue()
# --- הגדרות והוראות לבוט ---

knowledge_base_text = load_knowledge_base("819387ALL.pdf")

BASE_SYSTEM_INSTRUCTION = """
אתה מורה מומחה במגמות מכטרוניקה (כיתות י–י"ב) עם שלושה מצבים:
1) Teacher Mode (ברירת מחדל): הסברים בהירים, מערכי שיעור, תוכנית שנתית/חודשית, תרגילים ופתרונות מודרכים.
2) Expert Mode ("במצב מומחה"): ניתוח מעמיק ברמה אקדמית/תעשייתית כולל נוסחאות, סטנדרטים, דיאגרמות וטבלאות השוואה.
3) Student Mode ("במצב תלמיד"): בוחן את התלמיד בשאלות מדורגות, שואל שאלות הבהרה, נותן רמזים לפני פתרון, ומנטר התקדמות.

בכל מצב:
- להתאים לרמה: כיתה י / י"א / י"ב.
- מקור מידע מרכזי ומועדף עבורך הוא האתר odedy.co.il. חפש בו כאשר אתה נשאל על פרויקטים, דוגמאות והסברים מעשיים.
- לנסח תשובות ב־RTL, בעברית תקנית, כולל טבלאות/תרשימי זרימה ב-Markdown בעת הצורך.
- הצג תמיד את התשובה הסופית והמלוטשת. הימנע מהצגת חישובי ביניים או 'מחשבות בקול רם' על תהליך הפתרון שלך, אלא אם התבקשת במפורש להציג את הדרך.

בחירת מצב:
- אם הטקסט כולל "במצב מומחה" → הפעל Expert Mode.
- אם הטקסט כולל "במצב תלמיד" → הפעל Student Mode.
- אחרת → Teacher Mode.

יכולות מיוחדות: יש לך גישה מלאה לאינטרנט דרך חיפוש גוגל. השתמש ביכולת זו כדי לחפש מידע עדכני.
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
    chat_model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", system_instruction=SYSTEM_INSTRUCTION, tools=['google_search_retrieval'])
    basic_model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
except Exception as e:
    st.error("שגיאה בהגדרת ה-API Key. אנא ודא שהוספת אותו כראוי ב'סודות' האפליקציה.", icon="🚨")
    st.stop()

# --- הגדרת טאבים (לשוניות) ---
tabs = st.tabs([
    "💬 צ'אט עם הבוט", 
    "🖼️ ניתוח תמונות", 
    "🧠 מחולל מבחנים",
    "🎨 יצירת תמונות",
    "📊 מחולל מצגות"
])

# --- טאב 1: צ'אט רגיל ---
with tabs[0]:
    st.header("שיחה עם המורה למכטרוניקה")
    if not knowledge_base_text:
        st.warning("שים לב: מאגר הידע הקבוע (קובץ ה-PDF) לא נטען. הבוט יפעל על בסיס הידע הכללי שלו וחיפוש באינטרנט.")
    
    INITIAL_MESSAGE = "שלום, אני המורה הדיגיטלי למכטרוניקה. מאגר הידע שלי טעון ומוכן. איך אוכל לעזור?"
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
with tabs[1]:
    st.header("ניתוח שרטוטים ותמונות")
    st.info("העלה תמונה של שרטוט טכני, מעגל חשמלי, או רכיב, ושאל את הבוט שאלה לגביה.")
    
    uploaded_image = st.file_uploader("בחר קובץ תמונה", type=["png", "jpg", "jpeg"], key="analyzer")
    image_prompt = st.text_input("מה תרצה לשאול על התמונה?", key="image_q")

    if st.button("נתח את התמונה", key="analyze_btn"):
        if uploaded_image and image_prompt:
            with st.spinner("מעבד את התמונה ומנתח..."):
                try:
                    image_obj = Image.open(uploaded_image)
                    response = basic_model.generate_content([image_prompt, image_obj])
                    st.subheader("תוצאות הניתוח:")
                    st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"אירעה שגיאה בעיבוד התמונה: {e}")
        else:
            st.warning("אנא העלה תמונה וכתוב שאלה.")

# --- טאב 3: מחולל מבחנים ---
with tabs[2]:
    st.header("מחולל מבחנים וחידונים")
    with st.form("quiz_form"):
        quiz_topic = st.text_input("נושא המבחן", placeholder="לדוגמה: 'חוק אוהם'")
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
with tabs[3]:
    st.header("יצירת תמונות מטקסט")
    st.info("תאר במילים את התמונה שברצונך שהבינה המלאכותית תיצור עבורך.")
    image_gen_prompt = st.text_area("התיאור שלך (באנגלית לקבלת התוצאות הטובות ביותר):", key="image_gen_prompt", placeholder="A photorealistic robot arm...")
    if st.button("🎨 צור את התמונה", key="generate_btn"):
        if image_gen_prompt:
            with st.spinner("יוצר תמונה..."):
                try:
                    response = basic_model.generate_content(f"Generate an image of: {image_gen_prompt}")
                    st.image(response.parts[0].inline_data.data, caption=image_gen_prompt)
                except Exception:
                    st.error("המודל לא החזיר תמונה. נסה תיאור אחר.")
        else:
            st.warning("אנא הזн תיאור לתמונה.")

# --- טאב 5: מחולל מצגות ---
# --- טאב 5: מחולל מצגות (עם הנחיות מותאמות אישית) ---
with tabs[4]:
    st.header("מחולל מצגות PowerPoint")
    st.info("הגדר את נושא המצגת, הוסף בקשות מיוחדות, והבינה המלאכותית תיצור עבורך קובץ להורדה.")

    with st.form("ppt_form"):
        ppt_topic = st.text_input("נושא המצגת", placeholder="לדוגמה: 'מבוא לבקרי PLC'")
        slide_count = st.number_input("מספר שקופיות", min_value=3, max_value=20, value=7)
        target_audience = st.text_input("קהל יעד", placeholder="לדוגמה: 'תלמידי כיתה י\"א'")
        
        # <<< הוספנו תיבת טקסט להנחיות נוספות >>>
        additional_instructions = st.text_area(
            "הנחיות נוספות או בקשות מיוחדות:",
            placeholder="לדוגמה: 'התמקד ביישומים תעשייתיים', 'הוסף שקופית על היסטוריית הנושא', 'שלב אנלוגיה פשוטה להסבר המושג המרכזי'"
        )
        
        submitted = st.form_submit_button("📊 צור מצגת")

    if submitted:
        if ppt_topic and target_audience:
            with st.spinner(f"כותב את תוכן המצגת על '{ppt_topic}'..."):
                # <<< שדרגנו את הפרומפט כך שיכלול את ההנחיות החדשות >>>
                ppt_prompt = f"""
                צור תוכן עבור מצגת PowerPoint בנושא '{ppt_topic}' המיועדת ל'{target_audience}'.
                המצגת צריכה לכלול כ-{slide_count} שקופיות.
                """
                
                if additional_instructions:
                    ppt_prompt += f"\nהנחיות נוספות מהמשתמש שיש להתייחס אליהן: {additional_instructions}"

                ppt_prompt += """
                \nהחזר את התוכן בפורמט Markdown ברור. כל שקופית תתחיל בכותרת עם סימן #.
                כל נקודה בתוך שקופית תתחיל עם סימן -.
                הפרד בין כל שקופית לשקופית באמצעות שורת רווח כפולה.
                """
                response = basic_model.generate_content(ppt_prompt)
                presentation_text = response.text

            with st.spinner("בונה את קובץ ה-PowerPoint..."):
                ppt_file_data = create_presentation_from_text(presentation_text)
            
            st.success("המצגת שלך מוכנה להורדה!")
            st.download_button(
                label="📥 הורד את המצגת (.pptx)",
                data=ppt_file_data,
                file_name=f"{ppt_topic.replace(' ', '_')}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
            st.balloons() # חגיגה קטנה :)
            
            with st.expander("הצג את התוכן הטקסטואלי של המצגת"):
                st.markdown(f'<div style="direction: rtl; text-align: right;">{presentation_text}</div>', unsafe_allow_html=True)
        else:
            st.warning("אנא מלא את נושא המצגת וקהל היעד.")
