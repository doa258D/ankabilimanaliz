import streamlit as st
import pandas as pd
import io
import sys
import altair as alt

# Sayfa ayarları
st.set_page_config(layout="wide", page_title="Okul Sınav Analiz ve Karşılaştırma Sistemi")
st.title("👨‍🏫 Okul Sınav Analiz ve Karşılaştırma Sistemi")
st.markdown("---")

# --- BAŞLIK LİSTELERİ ---

# 2. Sınıf Başlıkları (24 Sütun)
basliklar_2_sinif = [
    "Öğr.No", "Ad, Soyad", "Sınıf",
    "TÜRKÇE DOĞRU", "TÜRKÇE YANLIŞ", "TÜRKÇE NET",
    "MATEMATİK DOĞRU", "MATEMATİK YANLIŞ", "MATEMATİK NET",
    "HAYAT BİLGİSİ DOĞRU", "HAYAT BİLGİSİ YANLIŞ", "HAYAT BİLGİSİ NET",
    "İNGİLİZCE DOĞRU", "İNGİLİZCE YANLIŞ", "İNGİLİZCE NET",
    "TOPLAM DOĞRU", "TOPLAM YANLIŞ", "TOPLAM NET",
    "LGS PUAN", "Sınıf derece", "Kurum", "İlçe", "İl", "Genel"
]

# 3. Sınıf Başlıkları (27 Sütun)
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

# 4. Sınıf Başlıkları (30 Sütun)
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

# --- YARDIMCI FONKSİYONLAR ---

def clean_orbim_file(uploaded_file, kademe):
    """Orbim dosyasını temizler ve DataFrame'e çevirir."""
    if kademe == 2:
        yeni_basliklar = basliklar_2_sinif
    elif kademe == 3:
        yeni_basliklar = basliklar_3_sinif
    elif kademe == 4:
        yeni_basliklar = basliklar_4_sinif
    else:
        st.error("Lütfen geçerli bir kademe seçin.")
        return None

    file_bytes = uploaded_file.getvalue()
    file_io = io.BytesIO(file_bytes)
    
    df = None
    try:
        df = pd.read_excel(file_io, header=2, skiprows=[3, 4])
    except:
        try:
            file_io.seek(0)
            df = pd.read_csv(file_io, header=2, skiprows=[3, 4], encoding='windows-1254')
        except Exception as e:
            st.error(f"Dosya okunamadı: {e}")
            return None

    if len(df.columns) != len(yeni_basliklar):
        st.error(f"Sütun sayısı uyuşmuyor. Dosya: {uploaded_file.name}, Kademe: {kademe}")
        return None
    
    df.columns = yeni_basliklar
    df = df[pd.to_numeric(df['Öğr.No'], errors='coerce').notna()]
    return df

def format_data(df):
    """Veriyi analiz formatına (Uzun Format) çevirir."""
    try:
        id_vars = ['Öğr.No', 'Ad, Soyad', 'Sınıf']
        value_vars = [col for col in df.columns if 'DOĞRU' in col or 'YANLIŞ' in col or 'NET' in col]
        long_df = pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name='DersBilgisi', value_name='Deger')
        
        split_data = long_df['DersBilgisi'].str.rsplit(' ', n=1, expand=True)
        long_df['Ders'] = split_data[0]
        long_df['Tip'] = split_data[1]
        
        long_df['Deger'] = pd.to_numeric(long_df['Deger'], errors='coerce')
        
        final_df = long_df.pivot_table(
            index=['Öğr.No', 'Ad, Soyad', 'Sınıf', 'Ders'],
            columns='Tip',
            values='Deger'
        ).reset_index()
        
        final_df.rename(columns={'DOĞRU': 'DogruSayisi', 'YANLIŞ': 'YanlisSayisi'}, inplace=True)
        final_df.columns.name = None
        
        # Sınıf sütununu parçala
        final_df = final_df[final_df['Sınıf'].str.contains('-', na=False)]
        final_df[['Kademe', 'Sube']] = final_df['Sınıf'].str.split('-', expand=True)
        final_df['Kademe'] = pd.to_numeric(final_df['Kademe'], errors='coerce')
        final_df.dropna(subset=['Kademe', 'Sube', 'DogruSayisi', 'YanlisSayisi', 'Ders'], inplace=True)
        
        return final_df
    except Exception as e:
        st.error(f"Formatlama hatası: {e}")
        return pd.DataFrame()

# --- ANALİZ FONKSİYONLARI ---

def analyze_single_exam(df, sinav_adi):
    """Tek sınav için standart analiz."""
    st.header(f"📊 {sinav_adi} Analiz Sonuçları")
    
    # Filtreler
    dersler = sorted(df['Ders'].unique().tolist())
    secilen_ders = st.selectbox(f"{sinav_adi} İçin Ders Seçin", ["Tüm Dersler"] + dersler, key=f"ders_{sinav_adi}")
    
    if secilen_ders != "Tüm Dersler":
        filtered_df = df[df['Ders'] == secilen_ders]
    else:
        filtered_df = df.copy()
        
    # Özet Kartları
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Öğrenci", len(filtered_df['Öğr.No'].unique()))
    col1.metric("Ortalama Doğru", f"{filtered_df['DogruSayisi'].mean():.2f}")
    
    # En İyiler
    max_dogru = filtered_df['DogruSayisi'].max()
    en_iyiler = filtered_df[filtered_df['DogruSayisi'] == max_dogru]
    
    with st.expander("En Yüksek Doğru Yapan Öğrenciler (Tıklayın)"):
        st.dataframe(en_iyiler[['Ad, Soyad', 'Sınıf', 'Ders', 'DogruSayisi']])
        
    # Grafikler
    st.subheader("Sınıf Ortalamaları")
    sinif_ort = filtered_df.groupby(['Sube', 'Ders'])['DogruSayisi'].mean().reset_index()
    
    chart = alt.Chart(sinif_ort).mark_bar().encode(
        x=alt.X('Sube', title='Şubeler'),
        y=alt.Y('DogruSayisi', title='Ortalama Doğru'),
        color='Sube',
        tooltip=['Sube', 'Ders', 'DogruSayisi']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

def analyze_comparison(df1, df2):
    """İki sınavı karşılaştıran fonksiyon."""
    st.header("⚖️ 1. ve 2. Sınav Karşılaştırma Raporu")
    
    # Ortak Ders Filtresi
    dersler = sorted(df1['Ders'].unique().tolist())
    secilen_ders = st.selectbox("Karşılaştırma İçin Ders Seçin", ["Tüm Dersler"] + dersler, key="comp_ders")
    
    if secilen_ders != "Tüm Dersler":
        df1_filt = df1[df1['Ders'] == secilen_ders].copy()
        df2_filt = df2[df2['Ders'] == secilen_ders].copy()
    else:
        df1_filt = df1.copy()
        df2_filt = df2.copy()
        
    # --- 1. SINIF BAZLI KARŞILAŞTIRMA (GRAFİK) ---
    st.subheader(f"Sınıf Bazlı Gelişim ({secilen_ders})")
    
    # İki sınavın ortalamalarını hazırla
    ort1 = df1_filt.groupby('Sube')['DogruSayisi'].mean().reset_index()
    ort1['Sınav'] = '1. Sınav'
    
    ort2 = df2_filt.groupby('Sube')['DogruSayisi'].mean().reset_index()
    ort2['Sınav'] = '2. Sınav'
    
    # Verileri birleştir
    combined_ort = pd.concat([ort1, ort2])
    
    # Yan Yana Çubuk Grafik
    chart_comp = alt.Chart(combined_ort).mark_bar().encode(
        x=alt.X('Sube', title='Şubeler'),
        y=alt.Y('DogruSayisi', title='Ortalama Doğru Sayısı'),
        color=alt.Color('Sınav', scale=alt.Scale(domain=['1. Sınav', '2. Sınav'], range=['#1f77b4', '#ff7f0e'])),
        xOffset='Sınav:N', # Yan yana barlar için
        tooltip=['Sube', 'Sınav', 'DogruSayisi']
    ).interactive()
    
    st.altair_chart(chart_comp, use_container_width=True)
    
    # --- 2. ÖĞRENCİ BAZLI GELİŞİM ---
    st.subheader("Öğrenci Gelişim Analizi")
    st.info("Not: Bu analiz sadece her iki sınava da giren öğrenciler için yapılır.")
    
    # Öğrenci bazında birleştirme (Öğr.No ile eşleştir)
    # Sadece seçilen ders için
    merge_df = pd.merge(
        df1_filt[['Öğr.No', 'Ad, Soyad', 'Sınıf', 'Ders', 'DogruSayisi']],
        df2_filt[['Öğr.No', 'Ders', 'DogruSayisi']],
        on=['Öğr.No', 'Ders'],
        suffixes=('_Sinav1', '_Sinav2')
    )
    
    # Farkı Hesapla
    merge_df['Gelişim'] = merge_df['DogruSayisi_Sinav2'] - merge_df['DogruSayisi_Sinav1']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("Netini En Çok Yükselten Öğrenciler")
        top_improvers = merge_df.sort_values(by='Gelişim', ascending=False).head(10)
        # Sadece pozitif olanları göster
        top_improvers = top_improvers[top_improvers['Gelişim'] > 0]
        st.dataframe(top_improvers[['Ad, Soyad', 'Sınıf', 'DogruSayisi_Sinav1', 'DogruSayisi_Sinav2', 'Gelişim']])
        
    with col2:
        st.error("Netini En Çok Düşüren Öğrenciler")
        droppers = merge_df.sort_values(by='Gelişim', ascending=True).head(10)
        # Sadece negatif olanları gösterelim
        droppers = droppers[droppers['Gelişim'] < 0]
        st.dataframe(droppers[['Ad, Soyad', 'Sınıf', 'DogruSayisi_Sinav1', 'DogruSayisi_Sinav2', 'Gelişim']])

# --- ANA UYGULAMA AKIŞI ---

# Sidebar
st.sidebar.header("Veri Yükleme Alanı")

kademe = st.sidebar.selectbox("Kademe Seçin:", (None, 2, 3, 4))

st.sidebar.markdown("### 1. Dosyalar")
file1 = st.sidebar.file_uploader("1. Sınav Dosyası (.xlsx/.csv)", type=["xlsx", "csv"], key="f1")
file2 = st.sidebar.file_uploader("2. Sınav Dosyası (.xlsx/.csv)", type=["xlsx", "csv"], key="f2")

if kademe and file1:
    st.sidebar.success("1. Dosya Yüklendi ✅")
    df1_wide = clean_orbim_file(file1, kademe)
    if df1_wide is not None:
        df1_long = format_data(df1_wide)

    # Senaryo 1: İki dosya da var -> KARŞILAŞTIRMA
    if file2:
        st.sidebar.success("2. Dosya Yüklendi ✅")
        df2_wide = clean_orbim_file(file2, kademe)
        if df2_wide is not None:
            df2_long = format_data(df2_wide)
            
            # Veriler hazırsa karşılaştır
            if not df1_long.empty and not df2_long.empty:
                analyze_comparison(df1_long, df2_long)
                
    # Senaryo 2: Sadece 1. dosya var -> TEKİL ANALİZ
    elif not df1_long.empty:
        analyze_single_exam(df1_long, "1. Sınav")

elif not kademe:
    st.info("👈 Lütfen sol menüden Kademe seçin.")
elif not file1:
    st.info("👈 Lütfen en azından 1. Sınav dosyasını yükleyin.")