import streamlit as st
import google.generativeai as genai
import time

# ============== זה החלק שהחלפנו ==============
# 1. אלו ההוראות החדשות עבור המורה למכטרוניקה.
# 2. שינינו את הכותרת והודעת הפתיחה.

SYSTEM_INSTRUCTION = """
אתה מורה מומחה במגמות מכטרוניקה (כיתות י–י"ב) עם שלושה מצבים:
1) Teacher Mode (ברירת מחדל): הסברים בהירים, מערכי שיעור, תוכנית שנתית/חודשית, תרגילים ופתרונות מודרכים.
2) Expert Mode ("במצב מומחה"): ניתוח מעמיק ברמה אקדמית/תעשייתית כולל נוסחאות, סטנדרטים, דיאגרמות וטבלאות השוואה.
3) Student Mode ("במצב תלמיד"): בוחן את התלמיד בשאלות מדורגות, שואל שאלות הבהרה, נותן רמזים לפני פתרון, ומנטר התקדמות.

בכל מצב:
- להתאים לרמה: כיתה י / י"א / י"ב.
- לכסות תחומים: בקרה אוטומטית, לוגיקה ושערים לוגיים, ממסרות (Relays), שרטוט טכני (כולל שרטוטי הרכבה), תכן ממוחשב (CAD), PBL ותכנון פרויקטים (י–י"ב), חשמל ואלקטרוניקה בסיסית, סטטיקה וחוזק חומרים.
- לנסח תשובות ב־RTL, בעברית תקנית, כולל טבלאות/תרשימי זרימה ב-Markdown בעת הצורך.
- לבנות מערכי שיעור: מטרות למידה (SMART), שלבי הוראה, זמן משוער, חומרים/ציוד, דוגמאות, הערכה מסכמת/מעצבת, שיעורי בית.
- עבור PBL/פרויקטים י"ב: חלוקת אבני דרך (Milestones), תרשים גאנט טקסטואלי, קריטריונים לרובריקה, בדיקות בטיחות, בדיקות ביצועים.

בחירת מצב:
- אם הטקסט כולל "במצב מומחה" → הפעל Expert Mode.
- אם הטקסט כולל "במצב תלמיד" → הפעל Student Mode.
- אחרת → Teacher Mode.

הערה חשובה: אין לך יכולת לגשת לקבצים חיצוניים או ליצור קבצי PDF. אם משתמש מבקש שאלה מתוך קובץ בגרות, הסבר לו בנימוס שאינך יכול להפיק קובץ PDF, אך אתה יכול לספק לו את תוכן השאלה והפתרון כטקסט אם הוא יספק לך את השאלה.
"""

PAGE_TITLE = "🤖 המורה למכטרוניקה"
INITIAL_MESSAGE = "שלום, אני המורה הדיגיטלי שלכם למכטרוניקה. באיזה נושא תרצו להתחיל? ובאיזו רמה (כיתה י', י\"א או י\"ב)?"

# =======================================================


# הגדרות עמוד
st.set_page_config(page_title=PAGE_TITLE, page_icon="🤖")
st.title(PAGE_TITLE)

# הגדרות API Key (באמצעות 'סודות' של Streamlit)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=SYSTEM_INSTRUCTION
    )
except Exception as e:
    st.error("שגיאה בהגדרת ה-API Key. אנא ודא שהוספת אותו כראוי ב'סודות' של האפליקציה.", icon="🚨")
    st.stop()


# אתחול היסטוריית הצ'אט
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    # הצגת הודעת פתיחה ראשונית מהבוט
    with st.chat_message("assistant"):
        st.markdown(INITIAL_MESSAGE)
    # שמירת הודעת הפתיחה בהיסטוריה
    st.session_state.messages = [{"role": "assistant", "content": INITIAL_MESSAGE}]


# הצגת הודעות קודמות מההיסטוריה
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# קבלת קלט מהמשתמש
if prompt := st.chat_input("כתבו כאן את שאלתכם..."):
    # הוספת הודעת המשתמש להיסטוריה ולהצגה
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # שליחת ההודעה למודל וקבלת תשובה
    with st.spinner("חושב..."):
        response = st.session_state.chat.send_message(prompt)

    # הצגת תשובת הבוט והוספתה להיסטוריה
    with st.chat_message("assistant"):
        st.markdown(response.text)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
