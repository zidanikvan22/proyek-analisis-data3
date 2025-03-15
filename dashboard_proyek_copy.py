import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard E-Commerce",
    page_icon="🛒",
    layout="wide"
)

# Load data utama
@st.cache_data
def load_data():
    all_df = pd.read_csv("dataset/all_data.csv")
    # Konversi kolom tanggal ke datetime
    all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])
    # Menambahkan kolom tambahan untuk filtering
    all_df['order_date'] = all_df['order_purchase_timestamp'].dt.date
    return all_df

all_df = load_data()

# Menampilkan judul dashboard
st.title("Dashboard E-Commerce")

# Membuat sidebar untuk filter data
st.sidebar.header("Filter Data")

# Filter berdasarkan tanggal
st.sidebar.subheader("Filter berdasarkan Tanggal")
min_date = all_df['order_date'].min()
max_date = all_df['order_date'].max()
date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# memastikan date_range memiliki dua nilai
start_date, end_date = (date_range if len(date_range) == 2 else (date_range[0], date_range[0]))

# Filter data berdasarkan rentang tanggal
filtered_df = all_df[(all_df['order_date'] >= start_date) & (all_df['order_date'] <= end_date)]

# Filter untuk kategori produk
st.sidebar.subheader("Filter berdasarkan Kategori Produk")
all_categories = sorted(filtered_df['product_category_name'].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Pilih Kategori Produk",
    options=all_categories,
    default=all_categories[:5] if len(all_categories) >= 5 else all_categories
)

# Terapkan filter kategori produk jika ada yang dipilih
if selected_categories:
    filtered_df = filtered_df[filtered_df['product_category_name'].isin(selected_categories)]

# Fungsi untuk menghasilkan data agregat dari data yang difilter
@st.cache_data
def generate_aggregations(df):
    # 1. Data penjualan harian
    daily_sales = df.groupby(df['order_purchase_timestamp'].dt.date).agg(
        total_orders=('order_id', 'nunique'),
        total_revenue=('price', 'sum')
    ).reset_index()
    daily_sales.rename(columns={'order_purchase_timestamp': 'date'}, inplace=True)
    
    # 2. kota dengan pelanggan terbanyak
    top_10_cities = df.groupby('customer_city').agg(
        customer_count=('customer_id', 'nunique')
    ).reset_index().sort_values('customer_count', ascending=False).head(10)
    
    # 3. kota dengan pelanggan paling sedikit
    bottom_5_cities = df.groupby('customer_city').agg(
        customer_count=('customer_id', 'nunique')
    ).reset_index().sort_values('customer_count').head(5)
    
    # 4. Top 10 produk terlaris berdasarkan product_id dan menampilkan kategorinya
    product_sales = df.groupby(['product_id', 'product_category_name']).agg(
        sales=('order_item_id', 'count'),
        revenue=('price', 'sum')
    ).reset_index()
    top_10_products = product_sales.sort_values('sales', ascending=False).head(10)
    
    # 5. Bottom 10 produk paling sedikit terjual berdasarkan product_id
    bottom_10_products = product_sales.sort_values('sales').head(5)
    
    # 6. Data agregat untuk kategori produk
    category_sales = df.groupby('product_category_name').agg(
        sales=('order_item_id', 'count'),
        revenue=('price', 'sum'),
        product_count=('product_id', 'nunique')
    ).reset_index().sort_values('sales', ascending=False)
    top_10_categories = category_sales.head(10)
    bottom_10_categories = category_sales.sort_values('sales').head(10)
    
    return daily_sales, top_10_cities, bottom_5_cities, top_10_products, bottom_10_products, top_10_categories, bottom_10_categories

# Periksa apakah data yang difilter tidak kosong
if filtered_df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Silakan ubah filter Anda.")
else:
    # Menghasilkan agregasi data
    daily_sales, top_10_cities, bottom_5_cities, top_10_products, bottom_10_products, top_10_categories, bottom_10_categories = generate_aggregations(filtered_df)
    
    # Visualisasi Tren Penjualan dengan data yang telah difilter
    st.subheader(f"Tren Total Order dan Revenue ({start_date} - {end_date})")
    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    x = range(len(daily_sales))
    ax1.bar(x, daily_sales["total_orders"], color="skyblue", label="Total Orders")
    ax2 = ax1.twinx()
    ax2.plot(x, daily_sales["total_revenue"], marker="o", color="red", linewidth=2, label="Total Revenue")
    ax1.set_xlabel("Tanggal", fontsize=12)
    ax1.set_ylabel("Jumlah Order", fontsize=12, color="blue")
    ax2.set_ylabel("Total Revenue (Rp)", fontsize=12, color="red")
    
    if len(daily_sales) > 20:
        step = len(daily_sales) // 10
        tick_positions = x[::step]
        tick_labels = [str(date) for date in daily_sales["date"].iloc[::step]]
    else:
        tick_positions = x
        tick_labels = [str(date) for date in daily_sales["date"]]
    
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, rotation=45)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    st.pyplot(fig)
    
    # Metrics untuk menampilkan ringkasan data
    st.subheader("Ringkasan Data")
    col1, col2, col3 = st.columns(3)
    total_orders = daily_sales['total_orders'].sum()
    total_revenue = daily_sales['total_revenue'].sum()
    avg_revenue_per_order = total_revenue / total_orders if total_orders > 0 else 0
    
    with col1:
        st.metric(label="Total Order", value=f"{total_orders:,}")
    with col2:
        st.metric(label="Total Revenue", value=f"Rp {total_revenue:,.2f}")
    with col3:
        st.metric(label="Rata-rata Revenue per Order", value=f"Rp {avg_revenue_per_order:,.2f}")
    
    # Visualisasi Kota dengan Pelanggan Terbanyak
    st.subheader("Kota dengan Pelanggan Terbanyak")
    if not top_10_cities.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(y=top_10_cities["customer_city"], x=top_10_cities["customer_count"], palette="Blues_r", ax=ax)
        ax.set_xlabel("Jumlah Pelanggan")
        ax.set_ylabel("Kota")
        ax.set_title("Kota dengan Pelanggan Terbanyak")
        st.pyplot(fig)
    else:
        st.warning("Tidak ada data kota untuk filter yang dipilih.")
    
    # Visualisasi Kota dengan Pelanggan Paling Sedikit
    st.subheader("Kota dengan Pelanggan Paling Sedikit")
    if not bottom_5_cities.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(y=bottom_5_cities["customer_city"], x=bottom_5_cities["customer_count"], palette="Reds_r", ax=ax)
        ax.set_xlabel("Jumlah Pelanggan")
        ax.set_ylabel("Kota")
        ax.set_title("Kota dengan Pelanggan Paling Sedikit")
        st.pyplot(fig)
    else:
        st.warning("Tidak ada data kota untuk filter yang dipilih.")
    
    # Visualisasi Produk Terlaris
    st.subheader(f"Produk Terlaris")
    if not top_10_products.empty:
        top_10_products['short_id'] = top_10_products['product_id'].str[:10] + '...'
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(y='short_id', x='sales', data=top_10_products, palette="Blues_r", ax=ax)
        ax.set_xlabel("Jumlah Terjual")
        ax.set_ylabel("ID Produk")
        ax.set_title("Produk Terlaris")
        for i, (idx, row) in enumerate(top_10_products.iterrows()):
            ax.text(5, i, f" ({row['product_category_name']})", fontsize=8, va='center')
        st.pyplot(fig)
    else:
        st.warning("Tidak ada data produk untuk filter yang dipilih.")
    
    # Visualisasi Produk Paling Sedikit Terjual
    st.subheader(f"Produk Paling Sedikit Terjual")
    if not bottom_10_products.empty:
        bottom_10_products['short_id'] = bottom_10_products['product_id'].str[:10] + '...'
        fig, ax = plt.subplots(figsize=(12, 6))  # Perbesar ukuran plot
        sns.barplot(y='short_id', x='sales', data=bottom_10_products, palette="Reds_r", ax=ax)
        ax.set_xlabel("Jumlah Terjual", fontsize=12)
        ax.set_ylabel("ID Produk", fontsize=12)
        ax.set_title("Produk Paling Sedikit Terjual", fontsize=14)
        ax.set_xlim(0, max(bottom_10_products['sales']) * 1.1)  # Sesuaikan skala sumbu X
        for i, (idx, row) in enumerate(bottom_10_products.iterrows()):
            ax.text(row['sales'] + 0.1, i, f" ({row['product_category_name']})", fontsize=10, va='center')
        st.pyplot(fig)
    else:
        st.warning("Tidak ada data produk untuk filter yang dipilih.")
    
    # Dropdown untuk pilihan tampilan lihat data detail
    view_details = st.selectbox(
        "Lihat Data Detail",
        ["Tren Penjualan", "Data Kota", "Data Produk"]
    )
    
    # Menampilkan data detail sesuai pilihan
    if view_details == "Tren Penjualan":
        st.subheader("Data Penjualan Harian")
        st.dataframe(daily_sales)
    elif view_details == "Data Kota":
        st.subheader("Data Pelanggan per Kota")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Top 10 Kota:")
            st.dataframe(top_10_cities)
        with col2:
            st.write("Bottom 5 Kota:")
            st.dataframe(bottom_5_cities)
    else:  # Data Produk
        st.subheader("Data Penjualan Produk")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Produk Terlaris:")
            st.dataframe(top_10_products)
        with col2:
            st.write("Produk Paling Sedikit Terjual:")
            st.dataframe(bottom_10_products)

st.caption('Copyright (c) 2025. Zidan Muhammad Ikvan | Proyek Akhir Analisis Data')


