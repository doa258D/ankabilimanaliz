import streamlit as st
import pandas as pd
import io
import altair as alt

# --- 1. SAYFA AYARLARI ---
st.set_page_config(layout="wide", page_title="Okul Sınav Takip Sistemi")

# --- 2. CSS STİLLERİ (GÜÇLENDİRİLMİŞ YAZDIRMA AYARI) ---
st.markdown("""
<style>
@media print {
    /* 1. Tüm sayfa yapısını serbest bırak */
    html, body, [class*="View"], [class*="App"] {
        height: auto !important;
        width: 100% !important;
        overflow: visible !important;
        position: static !important;
    }

    /* 2. Yan menü, üst bilgi, alt bilgi ve butonları gizle */
    .stSidebar, header, footer, .stButton, .stSelectbox, .stTabs [role="tablist"], .stAlert, [data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 3. İçerik konteynerini genişlet */
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        overflow: visible !important;
        height: auto !important;
        max-width: 100% !important;
    }

    /* 4. Tabloların ve Grafiklerin kesilmesini önle */
    .element-container, .stDataFrame, .stTable {
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        width: 100% !important;
        display: block !important;
    }
    
    /* 5. Her öğrenci bloğundan sonra sayfa kes */
    .student-block { 
        page-break-after: always;
        display: block;
        margin-top: 20px;
        border-bottom: 1px solid #ddd; /* Ayırıcı çizgi */
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

# --- 4. TEMİZLİK VE AKILLI KİMLİK OLUŞTURMA ---
def clean_orbim_file(uploaded_file, kademe):
    if kademe == 2:
        yeni_basliklar = basliklar_2_sinif
    elif kademe == 3:
        yeni_basliklar = basliklar_3_sinif
    elif kademe == 4:
        yeni_basliklar = basliklar_4_sinif
    else:
        return None

    try:
        file_bytes = uploaded_file.getvalue()
        file_io = io.BytesIO(file_bytes)
        
        try:
            df = pd.read_excel(file_io, header=2, skiprows=[3, 4])
        except:
            file_io.seek(0)
            df = pd.read_csv(file_io, header=2, skiprows=[3, 4], encoding='windows-1254')

        if len(df.columns) != len(yeni_basliklar):
            st.error(f"HATA: '{uploaded_file.name}' sütun sayısı hatalı.")
            return None
        
        df.columns = yeni_basliklar
        
        df['Öğr.No'] = pd.to_numeric(df['Öğr.No'], errors='coerce').fillna(0).astype(int)
        df = df.dropna(subset=['Ad, Soyad'])
        
        df['Ad_Standart'] = df['Ad, Soyad'].astype(str).str.strip().str.upper()
        df['Merge_Key'] = df.apply(
            lambda row: str(row['Öğr.No']) if row['Öğr.No'] > 0 else row['Ad_Standart'], 
            axis=1
        )
        
        df.drop_duplicates(subset=['Merge_Key'], keep='first', inplace=True)
        return df
    except Exception as e:
        st.error(f"Dosya temizlenirken hata: {e}")
        return None

# --- 5. FORMATLAMA FONKSİYONU ---
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

        final_df = long_df.pivot_table(
            index=['Merge_Key', 'Öğr.No', 'Ad, Soyad', 'Sınıf', 'Ders'], 
            columns='Tip', 
            values='Deger'
        ).reset_index()
        
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

# --- 6. ANALİZ EKRANI ---
def main_analysis(all_data, sinav_siralamasi_listesi):
    st.success(f"✅ Analiz Aktif! Toplam {len(all_data['SinavAdi'].unique())} sınav yüklü.")

    # --- YAZDIRMA MODU KUTUCUĞU ---
    # Bu kutu seçilince sayfa tamamen sadeleşir
    yazdirma_modu = st.sidebar.checkbox("🖨️ YAZDIRMA MODUNU AÇ (PDF Almak İçin)")
    
    if yazdirma_modu:
        st.warning("⚠️ **Yazdırma Modu Açık:** Sayfa PDF için optimize edildi. Şimdi **CTRL + P** tuşlarına basarak yazdırabilirsiniz.")
        # Bu CSS sadece kutu seçiliyken eklenir ve her şeyi gizler
        st.markdown("""
        <style>
            .stTabs [role="tablist"], .stSelectbox, .stMarkdown h1, .stMarkdown h2, [data-testid="stSidebar"] {display: none !important;}
        </style>
        """, unsafe_allow_html=True)

    # --- DERS SEÇİMİ VE SIRALAMA ---
    ham_dersler = all_data['Ders'].unique().tolist()
    temiz_dersler = [d for d in ham_dersler if pd.notna(d) and str(d).strip() != ""]
    
    normal_dersler = sorted([d for d in temiz_dersler if d.strip().upper() != "TOPLAM"])
    toplam_ders = [d for d in temiz_dersler if d.strip().upper() == "TOPLAM"]
    dersler_sirali = normal_dersler + toplam_ders
    
    if not dersler_sirali:
        st.error("Verilerde hiçbir ders bulunamadı.")
        return

    default_index = 0
    if "TOPLAM" in dersler_sirali:
        default_index = dersler_sirali.index("TOPLAM")

    # --- SEKMELER ---
    tab_genel, tab_toplu = st.tabs(["📊 GENEL ANALİZ", "📑 TÜM ÖĞRENCİ KARNELERİ"])

    # --- SEKME 1: GENEL ANALİZ ---
    with tab_genel:
        secilen_ders = st.selectbox("Analiz İçin Ders Seçin", dersler_sirali, index=default_index)
        
        df_filt = all_data[all_data['Ders'] == secilen_ders].copy()
        
        if df_filt.empty:
            st.warning("Seçilen ders için veri yok.")
        else:
            st.subheader(f"📈 Sınıf Bazlı Gelişim ({secilen_ders})")
            try:
                sinif_trend = df_filt.groupby(['Sube', 'SinavAdi'])['DogruSayisi'].mean().reset_index()
                if not sinif_trend.empty:
                    chart = alt.Chart(sinif_trend).mark_bar().encode(
                        x=alt.X('Sube', title='Şubeler', sort=None),
                        y=alt.Y('DogruSayisi', title='Ort. Doğru'),
                        color=alt.Color('SinavAdi', title='Sınav'),
                        xOffset='SinavAdi',
                        tooltip=['Sube', 'SinavAdi', 'DogruSayisi']
                    ).interactive()
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("Grafik için veri yetersiz.")
            except:
                st.warning("Grafik çizilemedi.")

            st.markdown("---")

            if len(sinav_siralamasi_listesi) >= 2:
                st.subheader(f"🏆 {secilen_ders} Dersinde Gelişim Raporu")
                ilk = sinav_siralamasi_listesi[0]
                son = sinav_siralamasi_listesi[-1]
                st.info(f"Karşılaştırma: **{ilk}** ile **{son}** arası.")
                
                df_ilk = df_filt[df_filt['SinavAdi'] == ilk]
                df_son = df_filt[df_filt['SinavAdi'] == son]
                
                if not df_ilk.empty and not df_son.empty:
                    merged = pd.merge(
                        df_ilk[['Merge_Key', 'Sınıf', 'DogruSayisi']], 
                        df_son[['Merge_Key', 'Ad, Soyad', 'DogruSayisi']], 
                        on='Merge_Key', 
                        suffixes=('_ilk', '_son')
                    )
                    merged['Fark'] = merged['DogruSayisi_son'] - merged['DogruSayisi_ilk']
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.success(f"Neti En Çok Yükselenler ({ilk} -> {son})")
                        st.dataframe(merged[merged['Fark'] > 0].sort_values('Fark', ascending=False).head(10)[['Ad, Soyad','Sınıf','DogruSayisi_ilk','DogruSayisi_son','Fark']], hide_index=True)
                    with c2:
                        st.error(f"Neti En Çok Düşenler ({ilk} -> {son})")
                        st.dataframe(merged[merged['Fark'] < 0].sort_values('Fark', ascending=True).head(10)[['Ad, Soyad','Sınıf','DogruSayisi_ilk','DogruSayisi_son','Fark']], hide_index=True)

            st.markdown("---")
            st.subheader("👤 Bireysel Öğrenci Karnesi (Tekli)")
            
            unique_students = all_data[['Merge_Key', 'Ad, Soyad', 'Öğr.No']].drop_duplicates(subset=['Merge_Key'], keep='last')
            unique_students['Etiket'] = unique_students.apply(lambda x: f"{x['Ad, Soyad']} (No: {int(x['Öğr.No'])})" if x['Öğr.No'] > 0 else f"{x['Ad, Soyad']} (No Yok)", axis=1)
            
            ogrenci_etiketleri = sorted(unique_students['Etiket'].tolist())
            secilen_etiket = st.selectbox("Öğrenci Seçin", ogrenci_etiketleri)
            
            if secilen_etiket:
                secilen_key = unique_students[unique_students['Etiket'] == secilen_etiket]['Merge_Key'].iloc[0]
                ogr_data = all_data[all_data['Merge_Key'] == secilen_key].copy()
                
                if not ogr_data.empty:
                    try:
                        pvt = ogr_data.pivot_table(index='Ders', columns='SinavAdi', values='DogruSayisi')
                        mevcut_ve_sirali = [d for d in dersler_sirali if d in pvt.index]
                        pvt = pvt.reindex(mevcut_ve_sirali)
                        st.write(f"**{secilen_etiket}** Doğru Sayıları:")
                        st.dataframe(pvt) # Bireysel karne dataframe olarak kalsın, sorun yok
                    except:
                        st.error("Tablo hatası.")

                    st.write("Öğrencinin Ders Bazlı Gelişim Grafiği:")
                    try:
                        c_ogr = alt.Chart(ogr_data).mark_bar().encode(
                            x=alt.X('Ders', title='Dersler', sort=dersler_sirali),
                            y=alt.Y('DogruSayisi', title='Doğru Sayısı'),
                            color=alt.Color('SinavAdi', title='Sınav'),
                            xOffset='SinavAdi',
                            tooltip=['Ders', 'SinavAdi', 'DogruSayisi']
                        ).interactive()
                        st.altair_chart(c_ogr, use_container_width=True)
                    except: 
                        st.write("Grafik verisi yok.")

    # --- SEKME 2: TOPLU KARNELER ---
    with tab_toplu:
        st.header("📑 Tüm Öğrenci Karneleri")
        st.info("Sınıf seçin, 'Listeyi Getir'e basın. PDF almak için sol menüden **'Yazdırma Modunu Aç'**ı işaretleyin ve **CTRL+P** yapın.")
        
        subeler = sorted(all_data['Sube'].unique().tolist())
        secenekler_sube = ["TÜM OKUL (Bütün Şubeler)"] + subeler
        secilen_sube_toplu = st.selectbox("Hangi Sınıfı Listelemek İstersiniz?", secenekler_sube)
        
        if secilen_sube_toplu == "TÜM OKUL (Bütün Şubeler)":
            sinif_data = all_data.copy()
        else:
            sinif_data = all_data[all_data['Sube'] == secilen_sube_toplu].copy()
        
        sinif_ogrencileri = sinif_data[['Merge_Key', 'Ad, Soyad', 'Sube', 'Öğr.No']].drop_duplicates(subset=['Merge_Key'], keep='last')
        sinif_ogrencileri = sinif_ogrencileri.sort_values(['Sube', 'Ad, Soyad'])
        
        # Yazdırma modundaysa buton olmadan direkt listele
        if st.button(f"Listeyi Getir ({len(sinif_ogrencileri)} Öğrenci)") or yazdirma_modu:
            
            st.divider()
            for index, row in sinif_ogrencileri.iterrows():
                ogr_key = row['Merge_Key']
                ogr_ad = row['Ad, Soyad']
                ogr_sube = row['Sube']
                ogr_no = int(row['Öğr.No']) if row['Öğr.No'] > 0 else "Yok"
                
                tek_ogr_data = sinif_data[sinif_data['Merge_Key'] == ogr_key]
                
                # SAYFA KESME VE BLOKLAMA
                st.markdown('<div class="student-block">', unsafe_allow_html=True)
                
                st.markdown(f"### 👤 {ogr_ad} ({ogr_sube} - No: {ogr_no})")
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    try:
                        pvt_toplu = tek_ogr_data.pivot_table(index='SinavAdi', columns='Ders', values='DogruSayisi')
                        mevcut_cols = [c for c in dersler_sirali if c in pvt_toplu.columns]
                        pvt_toplu = pvt_toplu[mevcut_cols]
                        
                        # YAZDIRMA İÇİN KRİTİK: st.table kullanıyoruz!
                        # st.dataframe yazdırırken kaydırma çubuğu çıkarır, st.table ise tüm satırları basar.
                        st.table(pvt_toplu)
                    except:
                        st.error("Tablo hatası")
                
                with col2:
                    try:
                        chart_toplu = alt.Chart(tek_ogr_data).mark_bar().encode(
                            x=alt.X('Ders', title=None, sort=dersler_sirali),
                            y=alt.Y('DogruSayisi', title='Doğru'),
                            color=alt.Color('SinavAdi', title='Sınav', legend=alt.Legend(orient='top')), 
                            xOffset='SinavAdi'
                        ).properties(height=200)
                        st.altair_chart(chart_toplu, use_container_width=True)
                    except:
                        pass
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---") 

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
                if not fmt_df.empty:
                    dfs.append(fmt_df)
        
        if dfs:
            st.session_state.master_df = pd.concat(dfs, ignore_index=True)
            st.session_state.sinav_listesi = [x["sinav_adi"] for x in dosya_bilgileri]
            st.success("Veriler işlendi!")
        else:
            st.error("Dosyalar işlenemedi.")

if st.session_state.master_df is not None:
    main_analysis(st.session_state.master_df, st.session_state.sinav_listesi)

elif not kademe:
    st.info("Lütfen soldan Kademe seçin.")