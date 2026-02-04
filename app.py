def get_sheet_service():
    # שליפת המידע מה-Secrets
    sa_data = st.secrets.connections.gsheets.service_account
    
    # המרת טקסט ה-JSON לדיקשנרי (Dictionary)
    sa_info = json.loads(sa_data) if isinstance(sa_data, str) else sa_data
    
    # תיקון קריטי לשגיאת "Invalid private key":
    # מחליף את הטקסט "\\n" בתו ירידת שורה אמיתי
    if "private_key" in sa_info:
        sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
    
    try:
        creds = service_account.Credentials.from_service_account_info(
            sa_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=creds).spreadsheets()
    except ValueError as e:
        st.error(f"המפתח הפרטי לא תקין. וודא שהעתקת אותו במלואו כולל ה-BEGIN וה-END. שגיאה: {e}")
        raise e
