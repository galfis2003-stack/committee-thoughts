import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🔍 בדיקת חיבור סופית")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ניסיון קריאה מהלשונית שצילמת
    df = conn.read(worksheet="sheet1", ttl="0s")
    st.success("✅ החיבור הצליח! הנה הנתונים מהגיליון:")
    st.dataframe(df)
except Exception as e:
    st.error("❌ החיבור עדיין נכשל.")
    st.write(f"סוג השגיאה: {type(e).__name__}")
    st.code(str(e))
