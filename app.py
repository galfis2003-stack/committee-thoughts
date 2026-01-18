import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json

st.title("🛠️ בדיקת חיבור סופית")

# 1. בדיקה אם המבנה קיים
if "connections" in st.secrets and "gsheets" in st.secrets.connections:
    st.success("✅ המבנה [connections.gsheets] נמצא ב-Secrets.")
    
    # ניסיון חילוץ האימייל של הבוט לבדיקה
    try:
        # Streamlit הופך JSON בתוך גרשיים משולשים למחרוזת (String)
        sa_str = st.secrets.connections.gsheets.service_account
        sa_dict = json.loads(sa_str)
        st.write(f"הבוט שמנסה להתחבר: `{sa_dict['client_email']}`")
    except Exception as e:
        st.warning(f"לא הצלחתי לקרוא את אימייל הבוט מה-JSON: {e}")

    # 2. ניסיון התחברות
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # קריאה מהלשונית שאישרת
        df = conn.read(worksheet="sheet1", ttl="0s")
        st.success("🔥 הצלחתי להתחבר ולקרוא נתונים!")
        st.dataframe(df)
    except Exception as e:
        st.error(f"שגיאה בחיבור לגוגל: {e}")
        # כאן נראה אם זה עדיין 401
else:
    st.error("❌ השרת לא מוצא את [connections.gsheets] ב-Secrets.")
    st.write("ה-Keys שנמצאו ב-Secrets הם:", list(st.secrets.keys()))
