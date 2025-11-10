import streamlit as st
import pandas as pd
import io
import sys
import altair as alt 

# Sayfa ayarları
st.set_page_config(layout="wide", page_title="Okul Sınav Analiz Raporu")
st.title("👨‍🏫 Okul Sınav Analiz Sistemi")
st.write("Lütfen Orbim'den aldığınız .xlsx veya .csv dosyasını yükleyin.")

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

# --- FONKSİYONLAR ---

def clean_orbim_file(uploaded_file, kademe):
    """
    Yüklenen Orbim dosyasını (XLSX veya CSV) alır, temizler ve 
    'TEMIZLENMIS_SONUCLAR.xlsx' formatına (Geniş Format) dönüştürür.
    
    seek() HATASI İÇİN GÜNCELLENDİ.
    """
    
    # 1. Kademeye göre doğru başlık listesini seç
    if kademe == 2:
        yeni_basliklar = basliklar_2_sinif
    elif kademe == 3:
        yeni_basliklar = basliklar_3_sinif
    elif kademe == 4:
        yeni_basliklar = basliklar_4_sinif
    else:
        st.error("Lütfen geçerli bir kademe seçin (2, 3, 4).")
        return None

    # 2. Yüklenen dosyayı oku (XLSX veya CSV olarak deneme)
    # GÜNCELLEME: Dosyayı önce byte olarak hafızaya al,
    # sonra hafızadaki bu dosyayı (BytesIO) okumayı dene.
    
    # Dosyayı bir kez oku
    file_bytes = uploaded_file.getvalue()
    # Hafızada (in-memory) dosya oluştur
    file_io = io.BytesIO(file_bytes)
    
    df = None
    try:
        # Önce .xlsx olarak okumayı dene
        df = pd.read_excel(
            file_io, # Hafızadaki dosyayı oku
            header=2,       
            skiprows=[3, 4] # 4. ve 5. satırları atla
        )
        st.info("Excel (.xlsx) dosyası olarak okundu.")
    except Exception as e_excel:
        st.warning(f"Excel olarak okunamadı. CSV olarak deneniyor...")
        try:
            # Hafızadaki dosyayı başa sar (seek(0))
            file_io.seek(0) 
            
            df = pd.read_csv(
                file_io, # Hafızadaki dosyayı tekrar oku
                header=2,
                skiprows=[3, 4],
                encoding='windows-1254' # Türkçe karakterler için
            )
            st.info("CSV dosyası olarak okundu.")
        except Exception as e_csv:
            st.error(f"Dosya ne Excel ne de CSV olarak okunamadı: {e_csv}")
            st.error("Lütfen Orbim'den aldığınız dosyayı değiştirmeden yüklediğinizden emin olun.")
            return None

    # 3. Sütun sayısını kontrol et ve başlıkları uygula
    if len(df.columns) != len(yeni_basliklar):
        st.error(f"Dosyadaki sütun sayısı ({len(df.columns)}) ile")
        st.error(f"seçtiğiniz {kademe}. sınıf başlık sayısı ({len(yeni_basliklar)}) eşleşmiyor!")
        st.error("Yüklediğiniz dosyanın kademesini sol menüden doğru seçtiğinizden emin olun.")
        return None
    
    df.columns = yeni_basliklar
    
    # 4. Dosyanın sonundaki gereksiz satırları (Genel Ortalama vb.) temizle
    df = df[pd.to_numeric(df['Öğr.No'], errors='coerce').notna()]
    
    st.success("Orbim dosyası başarıyla temizlendi.")
    return df # Temizlenmiş (Geniş Format) DataFrame'i döndür


def format_data(df):
    """
    Temizlenmiş (Geniş Format) DataFrame'i alır ve 
    analiz için 'Uzun Format'a (Ders, Dogru, Yanlis) dönüştürür.
    """
    try:
        id_vars = ['Öğr.No', 'Ad, Soyad', 'Sınıf']
        value_vars = [col for col in df.columns if 'DOĞRU' in col or 'YANLIŞ' in col or 'NET' in col]
        
        long_df = pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name='DersBilgisi', value_name='Deger')
        
        split_data = long_df['DersBilgisi'].str.rsplit(' ', n=1, expand=True)
        long_df['Ders'] = split_data[0]
        long_df['Tip'] = split_data[1]
        
        long_df = long_df[long_df['Tip'].isin(['DOĞRU', 'YANLIŞ'])]
        long_df['Deger'] = pd.to_numeric(long_df['Deger'], errors='coerce')
        
        final_df = long_df.pivot_table(
            index=['Öğr.No', 'Ad, Soyad', 'Sınıf', 'Ders'],
            columns='Tip',
            values='Deger'
        ).reset_index()
        
        final_df.rename(columns={'DOĞRU': 'DogruSayisi', 'YANLIŞ': 'YanlisSayisi'}, inplace=True)
        final_df.columns.name = None
        
        return final_df
    except Exception as e:
        st.error(f"Veri formatlanırken (genişten uzuna) bir hata oluştu: {e}")
        return pd.DataFrame()


def analyze_data(df):
    """
    Analize hazır (Uzun Format) DataFrame'i alır ve raporu gösterir.
    """
    
    # 1. Veri Ön İşleme (Sınıfı Kademe ve Şube'ye ayırma)
    try:
        # Sınıf sütununda '2-A' gibi olmayan (örn: '2-XX') verileri temizle
        df = df[df['Sınıf'].str.contains('-', na=False)]
        
        df[['Kademe', 'Sube']] = df['Sınıf'].str.split('-', expand=True)
        df['Kademe'] = pd.to_numeric(df['Kademe'], errors='coerce')
        
        # 'DogruSayisi' veya 'YanlisSayisi' olmayan satırları atla (NaN)
        df.dropna(subset=['DogruSayisi', 'YanlisSayisi'], inplace=True)
        
        df.dropna(subset=['Kademe', 'Sube', 'Ders'], inplace=True)
        df = df[df['Kademe'].isin([2, 3, 4])]
        
        if df.empty:
            st.error("Veri formatlama sonrası analiz edilecek geçerli veri bulunamadı.")
            return

    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
        st.error("Sınıf sütunu '2-A', '3-B' gibi bir formatta olmalı.")
        return

    # --- Arayüz: Filtreleme Seçenekleri ---
    st.sidebar.header("2. Adım: Raporu Filtrele")
    
    kademeler = sorted(df['Kademe'].unique().tolist())
    secilen_kademe_analiz = st.sidebar.selectbox("Analiz Kademesi Seçin", ["Tüm Kademeler"] + kademeler)

    if secilen_kademe_analiz != "Tüm Kademeler":
        filtered_df = df[df['Kademe'] == secilen_kademe_analiz].copy()
    else:
        filtered_df = df.copy()

    dersler = sorted(filtered_df['Ders'].unique().tolist())
    if not dersler:
        st.warning("Seçilen kademe için ders bulunamadı.")
        return
        
    secilen_ders = st.sidebar.selectbox("Ders Seçin", ["Tüm Dersler"] + dersler)

    if secilen_ders != "Tüm Dersler":
        filtered_df = filtered_df[filtered_df['Ders'] == secilen_ders]

    st.header(f"Analiz Sonuçları ({secilen_kademe_analiz} / {secilen_ders})")
    
    if filtered_df.empty:
        st.warning("Bu filtreler için gösterilecek veri bulunamadı.")
        return

    # --- Analiz Bölümü ---
    
    # 2. Öğrenci Bazlı Analiz (İSTEĞİNİZE GÖRE DÜZELTİLDİ)
    st.subheader("Öğrenci Performansları")
    
    max_dogru = filtered_df['DogruSayisi'].max()
    top_students_df = filtered_df[filtered_df['DogruSayisi'] == max_dogru]
    
    max_yanlis = filtered_df['YanlisSayisi'].max()
    bottom_students_df = filtered_df[filtered_df['YanlisSayisi'] == max_yanlis]
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"En Yüksek Doğru Sayısı ({max_dogru} Doğru)")
        st.write("Bu başarıyı gösteren öğrenciler:")
        st.dataframe(top_students_df[['Ad, Soyad', 'Sınıf', 'Ders', 'DogruSayisi', 'YanlisSayisi']])
                  
    with col2:
        st.error(f"En Yüksek Yanlış Sayısı ({max_yanlis} Yanlış)")
        st.write("Bu sonucu alan öğrenciler:")
        st.dataframe(bottom_students_df[['Ad, Soyad', 'Sınıf', 'Ders', 'DogruSayisi', 'YanlisSayisi']])

    st.markdown("---")

    # 3. Sınıf (Şube) Bazlı Analiz
    st.subheader("Sınıf (Şube) Performansları")
    
    try:
        sinif_performans = filtered_df.groupby(['Kademe', 'Sube', 'Ders'])[['DogruSayisi', 'YanlisSayisi']].mean().reset_index()
        sinif_performans = sinif_performans.sort_values(by='DogruSayisi', ascending=False)
    except Exception as e:
        st.error(f"Sınıf performansı hesaplanamadı: {e}")
        return

    if sinif_performans.empty:
        st.warning("Sınıf performansı için yeterli veri yok.")
        return

    en_basarili_sinif = sinif_performans.loc[sinif_performans['DogruSayisi'].idxmax()]
    en_yuksek_yanlis_sinif = sinif_performans.loc[sinif_performans['YanlisSayisi'].idxmax()]
    
    col3, col4 = st.columns(2)
    with col3:
        st.success("En Yüksek Doğru Ortalamalı Sınıf")
        st.metric(label=f"Sınıf: {en_basarili_sinif['Kademe']}-{en_basarili_sinif['Sube']}",
                  value=f"{en_basarili_sinif['DogruSayisi']:.2f} Doğru Ort.",
                  delta=f"Ders: {en_basarili_sinif['Ders']}")

    with col4:
        st.error("En Yüksek Yanlış Ortalamalı Sınıf")
        st.metric(label=f"Sınıf: {en_yuksek_yanlis_sinif['Kademe']}-{en_yuksek_yanlis_sinif['Sube']}",
                  value=f"{en_yuksek_yanlis_sinif['YanlisSayisi']:.2f} Yanlış Ort.",
                  delta=f"Ders: {en_yuksek_yanlis_sinif['Ders']}")
    
    st.subheader("Tüm Sınıfların Ortalama Raporu (Filtrelenmiş)")
    st.dataframe(sinif_performans)
    
    
    # 4. YENİ BÖLÜM: GRAFİKLER
    st.subheader("Görsel Raporlar (Grafikler)")
    
    if not sinif_performans.empty:
        
        if secilen_ders == "Tüm Dersler":
            st.write("Derslere Göre Ortalama Doğru Sayıları")
            
            ders_ortalamalari = filtered_df.groupby('Ders')[['DogruSayisi', 'YanlisSayisi']].mean().reset_index()
            
            chart_dersler = alt.Chart(ders_ortalamalari).mark_bar().encode(
                x=alt.X('Ders', sort=None, title='Dersler'),
                y=alt.Y('DogruSayisi', title='Doğru Sayısı Ortalaması'),
                tooltip=['Ders', 'DogruSayisi']
            ).interactive()
            st.altair_chart(chart_dersler, use_container_width=True)
            
        else:
            st.write(f"'{secilen_ders}' Dersi İçin Şubelerin Ortalama Doğru Sayıları")
            
            chart_subeler_dogru = alt.Chart(sinif_performans).mark_bar().encode(
                x=alt.X('Sube', sort=None, title='Sınıflar (Şubeler)'),
                y=alt.Y('DogruSayisi', title='Doğru Sayısı Ortalaması'),
                color='Sube',
                tooltip=['Sube', 'DogruSayisi']
            ).interactive()
            
            st.altair_chart(chart_subeler_dogru, use_container_width=True)
            
            st.write(f"'{secilen_ders}' Dersi İçin Şubelerin Ortalama Yanlış Sayıları")
            chart_subeler_yanlis = alt.Chart(sinif_performans).mark_bar().encode(
                x=alt.X('Sube', sort=None, title='Sınıflar (Şubeler)'),
                y=alt.Y('YanlisSayisi', title='Yanlış Sayısı Ortalaması'),
                color=alt.Color('Sube', legend=None), 
                tooltip=['Sube', 'YanlisSayisi']
            ).interactive()
            
            st.altair_chart(chart_subeler_yanlis, use_container_width=True)

# --- ANA UYGULAMA AKIŞI ---

st.sidebar.header("1. Adım: Veri Yükleme")

secilen_kademe_temizleme = st.sidebar.selectbox(
    "Yüklenecek dosyanın kademesini seçin:",
    (None, 2, 3, 4),
    index=0,
    placeholder="Kademe seçin..."
)

uploaded_file = st.sidebar.file_uploader(
    "Orbim (.xlsx veya .csv) dosyasını buraya sürükleyin:",
    type=["xlsx", "csv"]
)

if uploaded_file is not None and secilen_kademe_temizleme is not None:
    st.sidebar.success(f"Dosya '{uploaded_file.name}' yüklendi!")
    
    # 1. Dosyayı Temizle (Geniş Format)
    df_wide = clean_orbim_file(uploaded_file, secilen_kademe_temizleme)
    
    if df_wide is not None:
        # 2. Veriyi Analiz Formatına (Uzun) Dönüştür
        df_long = format_data(df_wide)
        
        if df_long is not None and not df_long.empty:
            st.success("Veri başarıyla formatlandı. Rapor Hazır:")
            # 3. Analizi Başlat ve Raporu Göster
            analyze_data(df_long)
        else:
            st.error("Veri formatlanırken bir sorun oluştu.")

elif uploaded_file is None:
    st.info("Lütfen sol menüden kademe seçip bir Orbim dosyası yükleyin.")
elif secilen_kademe_temizleme is None:
    st.info("Lütfen sol menüden yüklenecek dosyanın kademesini (2, 3, 4) seçin.")