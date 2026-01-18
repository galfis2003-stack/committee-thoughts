import streamlit as st

st.title("🛠️ בדיקת עומק ל-Secrets")

# 1. בדיקה אם ה-Secrets בכלל קיימים בזיכרון
if "connections" in st.secrets:
    st.success("✅ השרת טען את ה-Secrets בהצלחה.")
    
    # 2. הצגת האימייל של הבוט (לוודא שזה הבוט הנכון)
    bot_email = st.secrets.connections.gsheets.get("service_account", {}).get("client_email")
    st.write(f"הבוט שמנסה להתחבר: `{bot_email}`")
    
    # 3. ניסיון קריאה בסיסי
    from streamlit_gsheets import GSheetsConnection
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl="0s")
        st.success("🔥 הצלחתי! החיבור עובד.")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"נכשל: {e}")
        # כאן נראה אם זו שגיאת 401 או משהו אחר
else:
    st.error("❌ ה-Secrets לא נמצאו בזיכרון של האפליקציה.")
