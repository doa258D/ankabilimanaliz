import streamlit as st
import pandas as pd
import io
import altair as alt

# --- 1. SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Okul Sınav Takip Sistemi")

# --- 2. CSS STİLLERİ ---
st.markdown("""
<style>
@media print {
    .stSidebar, header, footer, .stButton, .stSelectbox, .stTabs [role="tablist"], .stAlert, [data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    html, body, [class*="View"] {
        height: auto !important;
        overflow: visible !important;
    }
    .element-container, .stDataFrame, .stTable {
        break-inside: avoid !important;
    }
    .student-block { 
        page-break-after: always;
        display: block;
        margin-top: 20px;
        border-bottom: 2px solid #ddd;
        padding-bottom: 20px;
    }
}
</style>
""", unsafe_allow_html=True)

st.title("📈 Okul Sınav Takip ve Gelişim Sistemi")
st.markdown("---")

# --- 3. BAŞLIK LİSTELERİ ---
basliklar_2_sinif = [
    "Öğr.No", "Ad, Soyad", "Sınıf",
    "TÜRKÇE DOĞRU", "TÜRKÇE YANLIŞ", "TÜRKÇE NET",
    "MATEMATİK DOĞRU", "MATEMATİK YANLIŞ", "MATEMATİK NET",
    "HAYAT BİLGİSİ DOĞRU", "HAYAT BİLGİSİ YANLIŞ", "HAYAT BİLGİSİ NET",
    "İNGİLİZCE DOĞRU", "İNGİLİZCE YANLIŞ", "İNGİLİZCE NET",
    "TOPLAM DOĞRU", "TOPLAM YANLIŞ", "TOPLAM NET",
    "LGS PUAN", "Sınıf derece", "Kurum", "İlçe", "İl", "Genel"
]

basliklar_3_sinif = [
    "Öğr.No", "Ad, Soyad", "Sınıf",
    "TÜRKÇE DOĞRU", "TÜRKÇE YANLIŞ", "TÜRKÇE NET",
    "MATEMATİK DOĞRU", "MATEMATİK YANLIŞ", "MATEMATİK NET",
    "HAYAT BİLGİSİ DOĞRU", "HAYAT BİLGİSİ YANLIŞ", "HAYAT BİLGİSİ NET",
    "FEN DOĞRU", "FEN YANLIŞ", "FEN NET",
    "İNGİLİZCE DOĞRU", "İNGİLİZCE YANLIŞ", "İNGİLİZCE NET", 
    "TOPLAM DOĞRU", "TOPLAM YANLIŞ", "TOPLAM NET",
    "LGS PUAN", "Sınıf derece", "Kurum", "İlçe", "İl", "Genel"
]

basliklar_4_sinif = [
    "Öğr.No", "Ad, Soyad", "Sınıf",
    "TÜRKÇE DOĞRU", "TÜRKÇE YANLIŞ", "TÜRKÇE NET",
    "MATEMATİK DOĞRU", "MATEMATİK YANLIŞ", "MATEMATİK NET",
    "FEN DOĞRU", "FEN YANLIŞ", "FEN NET",
    "SOSYAL BİLGİLER DOĞRU", "SOSYAL BİLGİLER YANLIŞ", "SOSYAL BİLGİLER NET",
    "Din K.ve A.B. DOĞRU", "Din K.ve A.B. YANLIŞ", "Din K.ve A.B. NET", 
    "İNGİLİZCE DOĞRU", "İNGİLİZCE YANLIŞ", "İNGİLİZCE NET",
    "TOPLAM DOĞRU", "TOPLAM YANLIŞ", "TOPLAM NET",
    "LGS PUAN", "Sınıf derece", "Kurum", "İlçe", "İl", "Genel"
]

# --- 4. TEMİZLİK VE AKILLI KİMLİK ---
def clean_orbim_file(uploaded_file, kademe):
    if kademe == 2: basliklar = basliklar_2_sinif
    elif kademe == 3: basliklar = basliklar_3_sinif
    elif kademe == 4: basliklar = basliklar_4_sinif
    else: return None

    try:
        file_bytes = uploaded_file.getvalue()
        file_io = io.BytesIO(file_bytes)
        try: df = pd.read_excel(file_io, header=2, skiprows=[3, 4])
        except: 
            file_io.seek(0)
            df = pd.read_csv(file_io, header=2, skiprows=[3, 4], encoding='windows-1254')

        if len(df.columns) != len(basliklar):
            st.error(f"HATA: '{uploaded_file.name}' sütun sayısı hatalı.")
            return None
        
        df.columns = basliklar
        df['Öğr.No'] = pd.to_numeric(df['Öğr.No'], errors='coerce').fillna(0).astype(int)
        df = df.dropna(subset=['Ad, Soyad'])
        
        df['Ad_Standart'] = df['Ad, Soyad'].astype(str).str.strip().str.upper()
        df['Merge_Key'] = df.apply(lambda row: str(row['Öğr.No']) if row['Öğr.No'] > 0 else row['Ad_Standart'], axis=1)
        
        df.drop_duplicates(subset=['Merge_Key'], keep='first', inplace=True)
        return df
    except Exception as e:
        st.error(f"Dosya temizlenirken hata: {e}")
        return None

# --- 5. FORMATLAMA ---
def format_data(df, sinav_adi):
    try:
        id_vars = ['Merge_Key', 'Öğr.No', 'Ad, Soyad', 'Sınıf']
        df.columns = df.columns.str.strip()
        value_vars = [col for col in df.columns if 'DOĞRU' in col or 'YANLIŞ' in col or 'NET' in col]
        if not value_vars: return pd.DataFrame()

        long_df = pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name='DersBilgisi', value_name='Deger')
        split_data = long_df['DersBilgisi'].str.rsplit(' ', n=1, expand=True)
        long_df['Ders'] = split_data[0].str.strip() 
        long_df['Tip'] = split_data[1].str.strip()
        long_df['Deger'] = pd.to_numeric(long_df['Deger'], errors='coerce')
        long_df.dropna(subset=['Ders', 'Tip', 'Deger'], inplace=True)

        final_df = long_df.pivot_table(index=['Merge_Key', 'Öğr.No', 'Ad, Soyad', 'Sınıf', 'Ders'], columns='Tip', values='Deger').reset_index()
        
        if 'DOĞRU' in final_df.columns: final_df.rename(columns={'DOĞRU': 'DogruSayisi'}, inplace=True)
        if 'YANLIŞ' in final_df.columns: final_df.rename(columns={'YANLIŞ': 'YanlisSayisi'}, inplace=True)
            
        final_df.columns.name = None
        final_df = final_df[final_df['Sınıf'].str.contains('-', na=False)]
        final_df[['Kademe', 'Sube']] = final_df['Sınıf'].str.split('-', expand=True)
        final_df['SinavAdi'] = sinav_adi
        return final_df
    except Exception as e:
        st.error(f"Veri formatlanırken hata: {e}")
        return pd.DataFrame()

# --- YARDIMCI: TEMİZ TABLO GÖSTERİMİ ---
def show_clean_table(df):
    for col in df.select_dtypes(include=['float', 'float64']).columns:
        df[col] = df[col].fillna(0).astype(int)
    st.dataframe(df, hide_index=True, use_container_width=True)

# --- YARDIMCI: RENKLİ TABLO GÖSTERİMİ ---
def show_styled_table(df, ilk_sinav=None, son_sinav=None):
    for col in df.select_dtypes(include=['float', 'float64']).columns:
        df[col] = df[col].fillna(0).astype(int)
    
    def highlight_cols(s):
        col_name = s.name
        if ilk_sinav and str(ilk_sinav) in str(col_name):
            return ['color: #D32F2F; font-weight: bold'] * len(s) # Kırmızı
        elif son_sinav and str(son_sinav) in str(col_name):
            return ['color: #1976D2; font-weight: bold'] * len(s) # Mavi
        return [''] * len(s)

    st.dataframe(df.style.apply(highlight_cols, axis=0), hide_index=True, use_container_width=True)

# --- SABİT GRAFİK EKSEN DEĞERLERİ (0, 5, 10, 15...) ---
y_axis_config = alt.Axis(values=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50])

# ==========================================
# MOD 1: TEK SINAV ANALİZİ
# ==========================================
def analyze_single_exam(all_data, sinav_adi):
    st.success(f"✅ **{sinav_adi}** Analiz Raporu")
    
    ham_dersler = all_data['Ders'].unique().tolist()
    temiz_dersler = [d for d in ham_dersler if pd.notna(d) and str(d).strip() != ""]
    normal_dersler = sorted([d for d in temiz_dersler if d.strip().upper() != "TOPLAM"])
    toplam_ders = [d for d in temiz_dersler if d.strip().upper() == "TOPLAM"]
    dersler_sirali = normal_dersler + toplam_ders
    
    default_idx = dersler_sirali.index("TOPLAM") if "TOPLAM" in dersler_sirali else 0
    secilen_ders = st.selectbox("Ders Seçin", dersler_sirali, index=default_idx)
    
    df_filt = all_data[all_data['Ders'] == secilen_ders].copy()
    
    if df_filt.empty:
        st.warning("Veri yok.")
        return

    st.markdown("### 🏆 Öğrenci Performansları")
    try:
        max_dogru = df_filt['DogruSayisi'].max()
        max_yanlis = df_filt['YanlisSayisi'].max()
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ En Çok Doğru Yapanlar ({int(max_dogru)} Doğru)")
            en_iyiler = df_filt[df_filt['DogruSayisi'] == max_dogru][['Ad, Soyad', 'Sınıf', 'DogruSayisi', 'YanlisSayisi']]
            en_iyiler.columns = ['Ad, Soyad', 'Sınıf', 'Doğru', 'Yanlış']
            show_styled_table(en_iyiler)
            
        with col2:
            st.error(f"❌ En Çok Yanlış Yapanlar ({int(max_yanlis)} Yanlış)")
            en_kotuler = df_filt[df_filt['YanlisSayisi'] == max_yanlis][['Ad, Soyad', 'Sınıf', 'DogruSayisi', 'YanlisSayisi']]
            en_kotuler.columns = ['Ad, Soyad', 'Sınıf', 'Doğru', 'Yanlış']
            show_styled_table(en_kotuler)
    except: pass

    st.markdown("---")
    st.markdown("### 🏫 Sınıf Performansları")
    try:
        sinif_ort = df_filt.groupby('Sube')[['DogruSayisi', 'YanlisSayisi']].mean().reset_index()
        best_sinif = sinif_ort.loc[sinif_ort['DogruSayisi'].idxmax()]
        worst_sinif = sinif_ort.loc[sinif_ort['DogruSayisi'].idxmin()]
        
        c1, c2 = st.columns(2)
        c1.info(f"🌟 **Doğru Sayısı En Yüksek Sınıf:** {best_sinif['Sube']} ({best_sinif['DogruSayisi']:.1f} Ort.)")
        c2.warning(f"⚠️ **Doğru Sayısı En Düşük Sınıf:** {worst_sinif['Sube']} ({worst_sinif['DogruSayisi']:.1f} Ort.)")
        
        st.write("Sınıf Ortalamaları Grafiği:")
        chart = alt.Chart(sinif_ort).mark_bar().encode(
            x=alt.X('Sube', title='Şubeler'),
            y=alt.Y('DogruSayisi', title='Ortalama Doğru', axis=y_axis_config),
            color=alt.Color('Sube', legend=None),
            tooltip=['Sube', alt.Tooltip('DogruSayisi', format='.1f'), alt.Tooltip('YanlisSayisi', format='.1f')]
        ).properties(height=300).interactive()
        st.altair_chart(chart, use_container_width=True)
    except: pass

# ==========================================
# MOD 2: ÇOKLU SINAV ANALİZİ
# ==========================================
def analyze_multiple_exams(all_data, sinav_siralamasi_listesi):
    st.success(f"✅ Karşılaştırma Modu: **{len(sinav_siralamasi_listesi)}** sınav inceleniyor.")

    ham_dersler = all_data['Ders'].unique().tolist()
    temiz_dersler = [d for d in ham_dersler if pd.notna(d) and str(d).strip() != ""]
    normal_dersler = sorted([d for d in temiz_dersler if d.strip().upper() != "TOPLAM"])
    toplam_ders = [d for d in temiz_dersler if d.strip().upper() == "TOPLAM"]
    dersler_sirali = normal_dersler + toplam_ders
    default_idx = dersler_sirali.index("TOPLAM") if "TOPLAM" in dersler_sirali else 0

    tab_genel, tab_toplu = st.tabs(["📊 GENEL ANALİZ", "📑 TÜM ÖĞRENCİ KARNELERİ"])

    with tab_genel:
        secilen_ders = st.selectbox("Ders Seçin", dersler_sirali, index=default_idx)
        df_filt = all_data[all_data['Ders'] == secilen_ders].copy()
        
        if not df_filt.empty:
            st.subheader(f"📈 Sınıf Bazlı Gelişim ({secilen_ders})")
            try:
                sinif_trend = df_filt.groupby(['Sube', 'SinavAdi'])['DogruSayisi'].mean().reset_index()
                chart = alt.Chart(sinif_trend).mark_bar().encode(
                    x=alt.X('Sube', title='Şubeler', sort=None),
                    y=alt.Y('DogruSayisi', title='Ort. Doğru', axis=y_axis_config),
                    color=alt.Color('SinavAdi', title='Sınav'),
                    xOffset='SinavAdi',
                    tooltip=['Sube', 'SinavAdi', alt.Tooltip('DogruSayisi', format='.1f')]
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
            except: pass

            st.markdown("---")

            if len(sinav_siralamasi_listesi) >= 2:
                ilk, son = sinav_siralamasi_listesi[0], sinav_siralamasi_listesi[-1]
                st.info(f"Gelişim Analizi: **{ilk}** (Kırmızı) -> **{son}** (Mavi)")
                
                df_ilk = df_filt[df_filt['SinavAdi'] == ilk]
                df_son = df_filt[df_filt['SinavAdi'] == son]
                
                if not df_ilk.empty and not df_son.empty:
                    merged = pd.merge(df_ilk[['Merge_Key','Sınıf','DogruSayisi']], df_son[['Merge_Key','Ad, Soyad','DogruSayisi','YanlisSayisi']], on='Merge_Key', suffixes=('_ilk','_son'))
                    merged['Fark'] = merged['DogruSayisi_son'] - merged['DogruSayisi_ilk']
                    
                    cols_to_show = ['Ad, Soyad', 'Sınıf', 'DogruSayisi_ilk', 'DogruSayisi_son', 'Fark']
                    renamed_cols = ['Ad, Soyad', 'Sınıf', f'{ilk} (D)', f'{son} (D)', 'Net Değişimi']
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.success("🚀 Netini En Çok Yükseltenler")
                        t1 = merged[merged['Fark'] > 0].sort_values('Fark', ascending=False).head(10)[cols_to_show]
                        t1.columns = renamed_cols
                        show_styled_table(t1, ilk, son)
                    with c2:
                        st.error("📉 Netini En Çok Düşürenler")
                        t2 = merged[merged['Fark'] < 0].sort_values('Fark', ascending=True).head(10)[cols_to_show]
                        t2.columns = renamed_cols
                        show_styled_table(t2, ilk, son)
                    
                    # --- Buradaki "En Çok Yanlış Yapanlar (son)" tablosu kaldırıldı ---
                    # (İstediğin üzere ilgili bölüm tamamen çıkarıldı.)
                    
                    st.markdown("---")

            st.markdown("---")
            st.subheader("👤 Bireysel Karne (Tekli)")
            unique_students = all_data[['Merge_Key', 'Ad, Soyad', 'Öğr.No']].drop_duplicates(subset=['Merge_Key'], keep='last')
            unique_students['Etiket'] = unique_students.apply(lambda x: f"{x['Ad, Soyad']} (No: {int(x['Öğr.No'])})" if x['Öğr.No'] > 0 else f"{x['Ad, Soyad']} (No Yok)", axis=1)
            
            secilen_etiket = st.selectbox("Öğrenci Seçin", sorted(unique_students['Etiket'].tolist()))
            
            if secilen_etiket:
                secilen_key = unique_students[unique_students['Etiket'] == secilen_etiket]['Merge_Key'].iloc[0]
                ogr_data = all_data[all_data['Merge_Key'] == secilen_key].copy()
                
                if not ogr_data.empty:
                    rows = []
                    for ders in dersler_sirali:
                        if ders not in ogr_data['Ders'].values and ders != "TOPLAM": continue
                        r = {'Ders': ders}
                        for s in sinav_siralamasi_listesi:
                            k = ogr_data[(ogr_data['SinavAdi'] == s) & (ogr_data['Ders'] == ders)]
                            if not k.empty:
                                r[f"{s} (D)"] = int(k['DogruSayisi'].iloc[0])
                                r[f"{s} (Y)"] = int(k['YanlisSayisi'].iloc[0])
                            else:
                                r[f"{s} (D)"] = 0
                                r[f"{s} (Y)"] = 0
                        rows.append(r)
                    
                    df_karne = pd.DataFrame(rows)
                    st.write(f"**{secilen_etiket}** Karne Sonuçları:")
                    # Renklendirme uygula
                    ilk_ad = sinav_siralamasi_listesi[0] if len(sinav_siralamasi_listesi)>0 else None
                    son_ad = sinav_siralamasi_listesi[1] if len(sinav_siralamasi_listesi)>1 else None
                    show_styled_table(df_karne, ilk_ad, son_ad)

                    try:
                        c_ogr = alt.Chart(ogr_data).mark_bar().encode(
                            x=alt.X('Ders', title='Dersler', sort=dersler_sirali),
                            y=alt.Y('DogruSayisi', title='Doğru Sayısı', axis=y_axis_config),
                            color=alt.Color('SinavAdi', title='Sınav'),
                            xOffset='SinavAdi',
                            tooltip=['Ders', 'SinavAdi', 'DogruSayisi', 'YanlisSayisi']
                        ).interactive()
                        st.altair_chart(c_ogr, use_container_width=True)
                    except: pass

    with tab_toplu:
        st.header("📑 Tüm Öğrenci Karneleri")
        st.info("Sınıf seçin, 'Listeyi Getir'e basın. PDF için **CTRL + P** yapın.")
        subeler = sorted(all_data['Sube'].unique().tolist())
        secenekler_sube = ["TÜM OKUL (Bütün Şubeler)"] + subeler
        secilen_sube = st.selectbox("Sınıf Seçiniz:", secenekler_sube)
        
        if secilen_sube == "TÜM OKUL (Bütün Şubeler)": target = all_data.copy()
        else: target = all_data[all_data['Sube'] == secilen_sube].copy()
        
        ogrenciler = target[['Merge_Key', 'Ad, Soyad', 'Sube', 'Öğr.No']].drop_duplicates(subset=['Merge_Key'], keep='last').sort_values(['Sube', 'Ad, Soyad'])
        
        if st.button(f"Listeyi Getir ({len(ogrenciler)} Öğrenci)"):
            st.divider()
            ilk_ad = sinav_siralamasi_listesi[0] if len(sinav_siralamasi_listesi)>0 else None
            son_ad = sinav_siralamasi_listesi[1] if len(sinav_siralamasi_listesi)>1 else None

            for index, row in ogrenciler.iterrows():
                ogr_key, ogr_ad, ogr_sube, ogr_no = row['Merge_Key'], row['Ad, Soyad'], row['Sube'], int(row['Öğr.No']) if row['Öğr.No']>0 else "Yok"
                tek_data = target[target['Merge_Key'] == ogr_key]
                
                st.markdown('<div class="student-block">', unsafe_allow_html=True)
                st.markdown(f"### 👤 {ogr_ad} ({ogr_sube} - No: {ogr_no})")
                
                c1, c2 = st.columns([1.5, 2])
                with c1:
                    rows_toplu = []
                    for ders in dersler_sirali:
                        if ders not in tek_data['Ders'].values and ders != "TOPLAM": continue
                        r = {'Ders': ders}
                        for s in sinav_siralamasi_listesi:
                            k = tek_data[(tek_data['SinavAdi'] == s) & (tek_data['Ders'] == ders)]
                            if not k.empty:
                                r[f"{s} (D)"] = int(k['DogruSayisi'].iloc[0])
                                r[f"{s} (Y)"] = int(k['YanlisSayisi'].iloc[0])
                            else:
                                r[f"{s} (D)"] = "-"
                                r[f"{s} (Y)"] = "-"
                        rows_toplu.append(r)
                    
                    show_styled_table(pd.DataFrame(rows_toplu), ilk_ad, son_ad)

                with c2:
                    try:
                        chart = alt.Chart(tek_data).mark_bar().encode(
                            x=alt.X('Ders', sort=dersler_sirali, title=None), y=alt.Y('DogruSayisi', axis=y_axis_config), 
                            color='SinavAdi', xOffset='SinavAdi'
                        ).properties(height=200)
                        st.altair_chart(chart, use_container_width=True)
                    except: pass
                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()

# --- 7. ANA UYGULAMA AKIŞI ---

if 'master_df' not in st.session_state:
    st.session_state.master_df = None
if 'sinav_listesi' not in st.session_state:
    st.session_state.sinav_listesi = []

st.sidebar.header("Veri Yükleme")
kademe = st.sidebar.selectbox("Kademe", [None, 2, 3, 4])
files = st.sidebar.file_uploader("Dosyaları Yükleyin", accept_multiple_files=True)

if kademe and files:
    st.sidebar.markdown("---")
    st.sidebar.write("Sınav Sıralaması:")
    dosya_bilgileri = []
    secenekler = [f"{i}. Sınav" for i in range(1, len(files)+1)]
    for i, f in enumerate(files):
        idx = i if i < len(secenekler) else 0
        sira = st.sidebar.selectbox(f"{f.name}", secenekler, key=f.name, index=idx)
        dosya_bilgileri.append({"file": f, "sinav_adi": sira})
        
    if st.sidebar.button("ANALİZİ BAŞLAT 🚀", type="primary"):
        dosya_bilgileri.sort(key=lambda x: x["sinav_adi"])
        dfs = []
        for item in dosya_bilgileri:
            clean_df = clean_orbim_file(item["file"], kademe)
            if clean_df is not None:
                fmt_df = format_data(clean_df, item["sinav_adi"])
                if not fmt_df.empty: dfs.append(fmt_df)
        
        if dfs:
            st.session_state.master_df = pd.concat(dfs, ignore_index=True)
            st.session_state.sinav_listesi = [x["sinav_adi"] for x in dosya_bilgileri]
            st.success("Veriler işlendi!")
        else: st.error("Dosyalar işlenemedi.")

if st.session_state.master_df is not None:
    sinav_sayisi = len(st.session_state.sinav_listesi)
    if sinav_sayisi == 1:
        analyze_single_exam(st.session_state.master_df, st.session_state.sinav_listesi[0])
    else:
        analyze_multiple_exams(st.session_state.master_df, st.session_state.sinav_listesi)

elif not kademe:
    st.info("Lütfen soldan Kademe seçin.")
