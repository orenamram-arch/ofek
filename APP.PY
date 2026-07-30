import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. הגדרות תצורה ועיצוב העמוד (RTL)
# ==========================================
st.set_page_config(page_title="WEBI - ניהול חוסרים מתקדם", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .block-container { direction: rtl; text-align: right; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;
        border-right: 5px solid #1f77b4;
    }
    div[data-testid="metric-container"] label { font-size: 18px !important; color: #555 !important; font-weight: bold; }
    div[data-testid="metric-container"] .css-1wivap2 { font-size: 28px !important; color: #111 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. טעינת נתונים (Cache)
# ==========================================
@st.cache_data
def load_data(file_name):
    df_shortages = pd.read_excel(file_name, sheet_name='חוסרים')
    df_balance = pd.read_excel(file_name, sheet_name='מאזן')
    
    # טיפול בערכים מספריים 
    df_shortages['כמות חוסר'] = pd.to_numeric(df_shortages['כמות חוסר'], errors='coerce').fillna(0)
    df_shortages['מחיר'] = pd.to_numeric(df_shortages['מחיר'], errors='coerce').fillna(0)
    
    # חישוב מחדש של שווי החוסר ליתר ביטחון (כמות * מחיר)
    df_shortages['שווי חוסר'] = df_shortages['כמות חוסר'] * df_shortages['מחיר']
    
    df_shortages['ספק'] = df_shortages['ספק'].fillna('לא מוגדר')
    
    return df_shortages, df_balance

file_path = 'shortages-dashboard.xlsx'

try:
    df_shortages, df_balance = load_data(file_path)
    
    # ==========================================
    # 3. סרגל צד - מסננים חכמים
    # ==========================================
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/8654/8654150.png", width=120)
        st.title("מערכת WEBI")
        st.markdown("---")
        st.header("🔍 סינון נתונים")
        
        if st.button("🔄 רענון נתונים מהאקסל", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        months = ["הכל"] + list(df_shortages['חודש'].dropna().unique())
        categories = ["הכל"] + list(df_shortages['סיווג'].dropna().unique())
        assemblies = ["הכל"] + list(df_shortages['הרכבה'].dropna().unique())
        
        selected_month = st.selectbox("📅 בחר חודש יעד:", options=months, index=1 if len(months)>1 else 0)
        selected_category = st.selectbox("🏷️ סיווג פריט:", options=categories)
        selected_assembly = st.selectbox("🧱 הרכבה:", options=assemblies)

    # ==========================================
    # 4. החלת הסינונים על מסד הנתונים
    # ==========================================
    filtered_df = df_shortages.copy()
    
    # תיקון הבאג: סינון החוצה של שורות שכמות החוסר שלהן היא 0 או פחות
    filtered_df = filtered_df[filtered_df['כמות חוסר'] > 0]
    
    if selected_month != "הכל":
        filtered_df = filtered_df[filtered_df['חודש'] == selected_month]
    if selected_category != "הכל":
        filtered_df = filtered_df[filtered_df['סיווג'] == selected_category]
    if selected_assembly != "הכל":
        filtered_df = filtered_df[filtered_df['הרכבה'] == selected_assembly]

    # ==========================================
    # 5. ממשק המשתמש (Tabs)
    # ==========================================
    st.title(f"📊 דשבורד חוסרים | {selected_month if selected_month != 'הכל' else 'כל החודשים'}")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 דשבורד מנהלים", 
        "📋 טבלת פירוט חוסרים", 
        "🔎 ניתוח פריט בודד (מאזן)", 
        "✏️ עריכה ושמירה לאקסל"
    ])

    # ------------------------------------------
    # Tab 1: דשבורד מנהלים 
    # ------------------------------------------
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        total_value = filtered_df['שווי חוסר'].sum()
        total_items = filtered_df['מק״ט'].nunique()
        total_assemblies = filtered_df['הרכבה'].nunique()
        total_short_qty = filtered_df['כמות חוסר'].sum()
        
        col1.metric("💰 סך שווי חוסר פיננסי", f"${total_value:,.0f}")
        col2.metric("📦 כמות פריטים ייחודיים", f"{total_items:,}")
        col3.metric("🧱 מספר הרכבות מעוכבות", f"{total_assemblies:,}")
        col4.metric("📉 סך יחידות חסרות", f"{total_short_qty:,.0f}")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("שווי חוסר לפי הרכבה")
            df_assy = filtered_df.groupby('הרכבה')['שווי חוסר'].sum().reset_index().sort_values(by='שווי חוסר', ascending=False).head(10)
            if not df_assy.empty and df_assy['שווי חוסר'].sum() > 0:
                fig1 = px.bar(df_assy, x='שווי חוסר', y='הרכבה', orientation='h', text_auto='.2s', color='שווי חוסר', color_continuous_scale='Reds')
                fig1.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("אין נתוני שווי להצגה עבור הרכבות אלו.")

        with col_chart2:
            st.subheader("מקור החוסר: חלוקה לפי ספק (Top 10)")
            df_supplier = filtered_df.groupby('ספק')['שווי חוסר'].sum().reset_index().sort_values(by='שווי חוסר', ascending=False).head(10)
            df_supplier = df_supplier[df_supplier['שווי חוסר'] > 0]
            if not df_supplier.empty:
                fig2 = px.pie(df_supplier, values='שווי חוסר', names='ספק', hole=0.4)
                fig2.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("אין נתוני שווי ספקים בסינון זה.")

    # ------------------------------------------
    # Tab 2: טבלת פירוט 
    # ------------------------------------------
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 פירוט הפריטים החסרים")
        st.markdown("פריטים שכמות החוסר שלהם עודכנה ל-0 אינם מופיעים כאן. ניתן ללחוץ על כותרות העמודות למיון.")
        
        display_cols = ['חודש', 'מק״ט', 'תיאור', 'סיווג', 'הרכבה', 'כמות חוסר', 'דרישה בחודש', 'מלאי', 'ספק', 'LT', 'שווי חוסר', 'מצב אספקה']
        display_cols = [c for c in display_cols if c in filtered_df.columns]
        
        st.dataframe(filtered_df[display_cols].sort_values(by='כמות חוסר', ascending=False), use_container_width=True, hide_index=True, height=500)
        
        csv_data = filtered_df[display_cols].to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 ייצוא התוצאות המסוננות לקובץ CSV", data=csv_data, file_name="shortages_export.csv", mime="text/csv")

    # ------------------------------------------
    # Tab 3: ניתוח פריט 
    # ------------------------------------------
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🔎 ניתוח מגמות פריט - מאזן חומרים לאורך זמן")
        
        all_items = df_balance['מק״ט'].dropna().unique()
        selected_item = st.selectbox("בחר מק״ט לניתוח מעמיק:", options=all_items)
        
        if selected_item:
            item_data = df_balance[df_balance['מק״ט'] == selected_item].iloc[0]
            st.markdown(f"**תיאור פריט:** {item_data.get('תיאור', 'לא מוגדר')} | **ספק:** {item_data.get('ספק', 'לא מוגדר')} | **מלאי נוכחי:** {item_data.get('מלאי', 0)}")
            
            balance_cols = [c for c in df_balance.columns if str(c).startswith('מאזן ')]
            demand_cols = [c for c in df_balance.columns if str(c).startswith('דרישה ')]
            supply_cols = [c for c in df_balance.columns if str(c).startswith('אספקה ')]
            
            months_timeline = [c.replace('מאזן ', '') for c in balance_cols]
            
            df_trend = pd.DataFrame({
                'חודש': months_timeline,
                'מאזן צפוי': [item_data.get(c, 0) for c in balance_cols],
                'דרישה': [item_data.get(d, 0) for d in demand_cols] if len(demand_cols) == len(balance_cols) else 0,
                'אספקה מתוכננת': [item_data.get(s, 0) for s in supply_cols] if len(supply_cols) == len(balance_cols) else 0
            })
            
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df_trend['חודש'], y=df_trend['מאזן צפוי'], mode='lines+markers', name='מאזן (צפי מלאי)', line=dict(color='blue', width=3)))
            fig3.add_trace(go.Bar(x=df_trend['חודש'], y=df_trend['דרישה'], name='דרישה מתוכננת', marker_color='red', opacity=0.6))
            fig3.add_trace(go.Bar(x=df_trend['חודש'], y=df_trend['אספקה מתוכננת'], name='אספקות בדרך', marker_color='green', opacity=0.6))
            
            fig3.update_layout(title=f'תחזית שרשרת אספקה עבור מק״ט {selected_item}', xaxis_title='חודש', yaxis_title='כמות יחידות', hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)

    # ------------------------------------------
    # Tab 4: עריכה ושמירה 
    # ------------------------------------------
    with tab4:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("✏️ עריכת נתונים ידנית ושמירה למחשב")
        st.warning("⚠️ שים לב: כשאתה מעדכן שקיבלת מלאי, **הקפד לשנות את עמודת 'כמות חוסר' ל-0**. פריטים עם חוסר 0 ייעלמו אוטומטית מהדשבורד לאחר השמירה.")
        
        # בלשונית העריכה נציג את כל הנתונים, כולל אלו עם חוסר 0, כדי שתוכל לערוך הכל
        edited_full_df = st.data_editor(
            df_shortages, 
            use_container_width=True, 
            hide_index=True, 
            height=500
        )
        
        if st.button("💾 שמור שינויים לאקסל המקורי", type="primary"):
            try:
                # חישוב אוטומטי וסופי של השווי הכספי לפני כתיבה לאקסל
                edited_full_df['כמות חוסר'] = pd.to_numeric(edited_full_df['כמות חוסר'], errors='coerce').fillna(0)
                edited_full_df['מחיר'] = pd.to_numeric(edited_full_df['מחיר'], errors='coerce').fillna(0)
                edited_full_df['שווי חוסר'] = edited_full_df['כמות חוסר'] * edited_full_df['מחיר']

                # שמירה לאקסל
                with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    edited_full_df.to_excel(writer, sheet_name='חוסרים', index=False)
                
                st.success("✅ הנתונים נשמרו בהצלחה בקובץ האקסל המקורי! האפליקציה מתרעננת...")
                
                st.cache_data.clear()
                st.rerun()
                
            except PermissionError:
                st.error("❌ שגיאה: השמירה נכשלה מכיוון שקובץ האקסל פתוח אצלך במחשב. אנא סגור אותו ונסה שוב.")
            except Exception as e:
                st.error(f"❌ שגיאה לא צפויה בעת השמירה: {e}")

except Exception as e:
    st.error(f"שגיאה בהפעלת המערכת. ודא שהקובץ 'shortages-dashboard.xlsx' נמצא באותה תיקייה ולא פגום. פרטי השגיאה: {e}")
