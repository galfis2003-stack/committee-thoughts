import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# הגדרות עמוד
st.set_page_config(page_title="מחשבות הוועדה", layout="centered")

# אתחול חיבורים (מבוסס על ה-Secrets שהגדרת)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

# פונקציה לקריאת נתונים בזמן אמת מהענן
def get_data():
    try:
        # ttl="0s" מבטיח שלא יהיה Cache והמידע יהיה תמיד מעודכן
        return conn.read(ttl="0s")
    except:
        # במקרה שהגיליון ריק לגמרי, ניצור מבנה בסיסי
        return pd.DataFrame(columns=["meeting", "thought"])

st.title("📝 מערכת איסוף מחשבות לוועדה")

# רשימת המפגשים המעודכנת
meetings = [
    "מפגש התנעה", "מפגש שני", "מפגש שלישי", "מפגש רביעי", 
    "מפגש חמישי", "מפגש שישי", "מפגש שביעי", "מפגש שמיני"
]
meeting_id = st.selectbox("בחר את המפגש הרלוונטי:", options=meetings)

if meeting_id:
    df = get_data()
    
    # סינון תגובות ששייכות רק למפגש שנבחר (מבוסס על עמודת meeting בגיליון)
    #
    current_thoughts = df[df['meeting'] == meeting_id]['thought'].tolist() if not df.empty else []

    st.subheader(f"הזנת מחשבה - {meeting_id}")
    with st.form("add_thought", clear_on_submit=True):
        msg = st.text_area("מה המחשבה שלך בנושא הדיון?")
        if st.form_submit_button("שלח מחשבה"):
            if msg:
                # יצירת שורה חדשה ושמירה לענן
                new_row = pd.DataFrame([{"meeting": meeting_id, "thought": msg}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("המחשבה נשמרה בענן בהצלחה!")
                st.rerun()

    st.divider()

    # --- אזור מנהל (מוגן בסיסמה) ---
    with st.sidebar:
        st.header("🔐 אזור מנהל")
        pwd = st.text_input("הזן סיסמת מנהל:", type="password")
    
    if pwd == "1234":
        st.sidebar.success("מצב מנהל פעיל")
        
        # 1. סיכום AI ספציפי למפגש שנבחר
        if st.button(f"🪄 סכם AI עבור {meeting_id}"):
            if current_thoughts:
                with st.spinner(f"ה-AI מנתח את התגובות של {meeting_id}..."):
                    all_text = "\n".join(current_thoughts)
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": f"אתה עוזר מקצועי לוועדה. סכם את המחשבות מ{meeting_id} לנקודות מרכזיות ותובנות."},
                            {"role": "user", "content": f"להלן המחשבות:\n{all_text}"}
                        ]
                    )
                    st.info(f"סיכום עבור {meeting_id}:")
                    st.write(response.choices[0].message.content)
            else:
                st.warning(f"אין עדיין מחשבות לסכם עבור {meeting_id}.")

        # 2. ניהול ומחיקת תגובות מהענן
        st.subheader(f"🗑️ ניהול תגובות - {meeting_id}")
        if current_thoughts:
            for i, t in enumerate(current_thoughts):
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"**{i+1}.** {t}")
                if col2.button("מחק", key=f"del_{meeting_id}_{i}"):
                    # מציאת האינדקס המדויק בגיליון ומחיקתו
                    index_to_drop = df[(df['meeting'] == meeting_id) & (df['thought'] == t)].index[0]
                    df = df.drop(index_to_drop)
                    conn.update(data=df)
                    st.success("התגובה נמחקה מהענן.")
                    st.rerun()
        else:
            st.write("אין תגובות שמורות במפגש זה.")
