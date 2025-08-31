import streamlit as st
import google.generativeai as genai
import time

# ============== זה החלק ששדרגנו ==============
# 1. הוספנו הנחיה לתת עדיפות לאתר odedy.co.il
# 2. שינינו את הכותרת והודעת הפתיחה.

SYSTEM_INSTRUCTION = """
אתה מורה מומחה במגמות מכטרוניקה (כיתות י–י"ב) עם שלושה מצבים:
1) Teacher Mode (ברירת מחדל): הסברים בהירים, מערכי שיעור, תוכנית שנתית/חודשית, תרגילים ופתרונות מודרכים.
2) Expert Mode ("במצב מומחה"): ניתוח מעמיק ברמה אקדמית/תעשייתית כולל נוסחאות, סטנדרטים, דיאגרמות וטבלאות השוואה.
3) Student Mode ("במצב תלמיד"): בוחן את התלמיד בשאלות מדורגות, שואל שאלות הבהרה, נותן רמזים לפני פתרון, ומנטר התקדמות.

בכל מצב:
- להתאים לרמה: כיתה י / י"א / י"ב.
- לכסות תחומים: בקרה אוטומטית, לוגיקה ושערים לוגיים, ממסרות (Relays), שרטוט טכני (כולל שרטוטי הרכבה), תכן ממוחשב (CAD), PBL ותכנון פרויקטים (י–י"ב), חשמל ואלקטרוניקה בסיסית, סטטיקה וחוזק חומרים.
- **מקור מידע מרכזי ומועדף עבורך הוא האתר odedy.co.il. חפש בו כאשר אתה נשאל על פרויקטים, דוגמאות והסברים מעשיים.**
- לנסח תשובות ב־RTL, בעברית תקנית, כולל טבלאות/תרשימי זרימה ב-Markdown בעת הצורך.
- לבנות מערכי שיעור: מטרות למידה (SMART), שלבי הוראה, זמן משוער, חומרים/ציוד, דוגמאות, הערכה מסכמת/מעצבת, שיעורי בית.
- עבור PBL/פרויקטים י"ב: חלוקת אבני דרך (Milestones), תרשים גאנט טקסטואלי, קריטריונים לרובריקה, בדיקות בטיחות, בדיקות ביצועים.

בחירת מצב:
- אם הטקסט כולל "במצב מומחה" → הפעל Expert Mode.
- אם הטקסט כולל "במצב תלמיד" → הפעל Student Mode.
- אחרת → Teacher Mode.

**יכולות מיוחדות: באפשרותך לגשת לאינטרנט כדי לחפש מידע עדכני, כגון בחינות בגרות, מאמרים טכניים וחדשות. השתמש ביכולת זו כדי לספק תשובות מדויקות ומבוססות יותר.**
"""

PAGE_TITLE = "🤖 המורה למכטרוניקה (עם גישה לרשת)"
INITIAL_MESSAGE = "שלום, אני המורה הדיגיטלי שלכם למכטרוניקה. אני יכול גם לחפש מידע עדכני ברשת, עם התמחות באתר של עודד - איך אוכל לעזור?"

# =======================================================


# הגדרות עמוד
st.set_page_config(page_title=PAGE_TITLE, page_icon="🤖", layout="wide")

# הוספת CSS לכיוון RTL כללי באפליקציה
st.markdown("""
<style>
    body {
        direction: rtl;
    }
    .stTextInput > div > div > input {
        direction: rtl;
    }
</style>
""", unsafe_allow_html=True)


st.title(PAGE_TITLE)

# הגדרות API Key (באמצעות 'סודות' של Streamlit)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # === הוספנו כאן גישה לכלי חיפוש ===
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=SYSTEM_INSTRUCTION,
        tools=['google_search_retrieval'] # הפעלת כלי חיפוש גוגל
    )
except Exception as e:
    st.error("שגיאה בהגדרת ה-API Key. אנא ודא שהוספת אותו כראוי ב'סודות' של האפליקציה.", icon="🚨")
    st.stop()


# אתחול היסטוריית הצ'אט
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
    # הצגת הודעת פתיחה ראשונית מהבוט
    with st.chat_message("assistant"):
        # === הוספנו כאן תמיכה ב-RTL ===
        st.markdown(f'<div style="direction: rtl;">{INITIAL_MESSAGE}</div>', unsafe_allow_html=True)
    # שמירת הודעת הפתיחה בהיסטוריה
    st.session_state.messages = [{"role": "assistant", "content": INITIAL_MESSAGE}]


# הצגת הודעות קודמות מההיסטוריה
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        # === הוספנו כאן תמיכה ב-RTL ===
        st.markdown(f'<div style="direction: rtl;">{message["content"]}</div>', unsafe_allow_html=True)

# קבלת קלט מהמשתמש
if prompt := st.chat_input("כתבו כאן את שאלתכם..."):
    # הוספת הודעת המשתמש להיסטוריה ולהצגה
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        # === הוספנו כאן תמיכה ב-RTL ===
        st.markdown(f'<div style="direction: rtl;">{prompt}</div>', unsafe_allow_html=True)

    # שליחת ההודעה למודל וקבלת תשובה
    with st.spinner("חושב וגם מחפש ברשת..."):
        response = st.session_state.chat.send_message(prompt)

    # הצגת תשובת הבוט והוספתה להיסטוריה
    with st.chat_message("assistant"):
        # === הוספנו כאן תמיכה ב-RTL ===
        st.markdown(f'<div style="direction: rtl;">{response.text}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
