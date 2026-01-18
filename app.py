import streamlit as st
from openai import OpenAI
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="דיאגנוסטיקה", layout="centered")

# חיבור
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🔍 בדיקת חיבור לענן")

# ניסיון קריאה כללי ללא שם גיליון (קורא את הגיליון הראשון)
try:
    df = conn.read(ttl="0s")
    st.success("✅ הצלחתי להתחבר ולקרוא את הגיליון הראשון!")
    st.write("הנתונים שמצאתי:")
    st.dataframe(df.head())
    
    # הצגת העמודות הקיימות בגיליון
    st.info(f"העמודות בגיליון הן: {list(df.columns)}")
    
except Exception as e:
    st.error("❌ נכשלה הקריאה מהגיליון.")
    st.info("זה קורה בדרך כלל אם ה-Secrets לא הוגדרו נכון או שהקישור ב-Secrets לא מדויק.")
    st.code(str(e))

st.divider()

# טופס בדיקת כתיבה
st.subheader("📝 בדיקת כתיבה (סימולציה)")
test_msg = st.text_input("כתוב משהו לבדיקה:")
if st.button("נסה לכתוב לענן"):
    try:
        # יצירת שורה חדשה לבדיקה
        new_row = pd.DataFrame([{"meeting": "בדיקה", "thought": test_msg}])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # ניסיון עדכון ללא ציון שם גיליון (יכתוב לגיליון הראשון)
        conn.update(data=updated_df)
        st.success("🔥 הצלחתי לכתוב! המערכת מוגדרת מצוין.")
    except Exception as e:
        st.error("שגיאת כתיבה:")
        st.code(str(e))
