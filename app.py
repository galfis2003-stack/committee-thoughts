import streamlit as st
from openai import OpenAI

# הגדרות עיצוב RTL לעברית
st.set_page_config(page_title="תיבת מחשבות - ועדה", layout="centered")
st.markdown("""
    <style>
    .stApp { direction: RTL; text-align: right; }
    textarea { direction: RTL; text-align: right; }
    div[role="alert"] { direction: RTL; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

st.title("💡 תיבת המחשבות של הוועדה")
st.write("כאן ניתן לשתף תובנות, רעיונות או הערות מהמפגש האחרון בצורה אנונימית.")

# התחברות ל-OpenAI דרך ה-Secrets של השרת
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ניהול רשימת המחשבות (זמני ל-Session הנוכחי)
if 'thoughts' not in st.session_state:
    st.session_state.thoughts = []

# ממשק כתיבה
with st.container():
    new_thought = st.text_area("מה המחשבה שלך?", placeholder="כתוב כאן את מה שלא הספקת להגיד...", height=150)
    if st.button("שליחה אנונימית"):
        if new_thought.strip():
            st.session_state.thoughts.append(new_thought)
            st.success("המחשבה נשמרה במערכת. תודה!")
        else:
            st.warning("נא להזין טקסט לפני השליחה.")

st.divider()

# הצגת הסיכום לכולם
st.header("🔍 סיכום התובנות המרכזיות (AI)")
if st.button("ייצר סיכום מעודכן"):
    if len(st.session_state.thoughts) > 1:
        with st.spinner("ה-AI מנתח את כלל התגובות..."):
            all_text = " | ".join(st.session_state.thoughts)
            prompt = f"להלן רשימת מחשבות אנונימיות של חברי ועדה מקצועית: {all_text}. סכם את התמות המרכזיות, נקודות הדמיון והמחלוקת בצורה מקצועית ואנונימית."
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            st.info(response.choices[0].message.content)
    else:
        st.info("עדיין אין מספיק תגובות (לפחות 2) כדי לייצר ניתוח משמעותי.")
