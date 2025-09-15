import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from utils.data_manager import DataManager
from utils.map_utils import MapUtils

st.set_page_config(
    page_title="地圖檢視 - 台北運動場地搜尋引擎",
    page_icon="🗺️",
    layout="wide"
)

# ===== 认证守卫 =====
if not st.session_state.get("is_authenticated"):
    st.warning("请先通过启动页面初始化系统")
    if st.button("返回启动页面"):
        st.switch_page("app.py")
    st.stop()

# 確保 session state 已初始化
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

if 'map_utils' not in st.session_state:
    st.session_state.map_utils = MapUtils()

st.title("🗺️ 場地地圖檢視")
st.markdown("在地圖上探索台北市的運動場地")

# 側邊欄控制
with st.sidebar:
    st.header("🗺️ 地圖控制")
    
    # 地圖中心點選擇
    map_center_option = st.selectbox(
        "地圖中心",
        ["台北市中心", "信義區", "大安區", "中山區", "松山區", "萬華區", "中正區", "大同區", "士林區", "北投區", "內湖區", "南港區"],
        key="map_center"
    )
    
    # 顯示篩選
    st.subheader("📍 顯示篩選")
    
    # 運動類型篩選
    available_sports = st.session_state.data_manager.get_sport_types()
    if available_sports:
        show_sports = st.multiselect(
            "顯示運動類型",
            available_sports,
            default=available_sports[:5] if len(available_sports) > 5 else available_sports,
            key="map_sports_filter"
        )
    else:
        show_sports = []
        st.info("載入運動類型中...")
    
    # 地區篩選
    available_districts = st.session_state.data_manager.get_districts()
    if available_districts:
        show_districts = st.multiselect(
            "顯示地區",
            available_districts,
            default=available_districts[:5] if len(available_districts) > 5 else available_districts,
            key="map_districts_filter"
        )
    else:
        show_districts = []
        st.info("載入地區資料中...")
    
    # 價格範圍篩選
    price_range = st.slider(
        "價格範圍 (每小時)",
        0, 10000,
        value=[0, 5000],
        step=100,
        format="NT$%d",
        key="map_price_filter"
    )
    
    # 評分篩選
    min_rating = st.slider(
        "最低評分",
        0.0, 5.0,
        value=0.0,
        step=0.1,
        format="%.1f",
        key="map_rating_filter"
    )
    
    # 地圖樣式
    st.subheader("🎨 地圖樣式")
    map_style = st.selectbox(
        "地圖樣式",
        ["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter", "Stamen Terrain"],
        key="map_style"
    )
    
    # 顯示選項
    show_heatmap = st.checkbox("顯示熱力圖", value=False, key="show_heatmap")
    show_clusters = st.checkbox("群集顯示", value=True, key="show_clusters")

# 主要內容
col1, col2 = st.columns([3, 1])

with col1:
    # 獲取地圖中心座標
    map_center = st.session_state.map_utils.get_district_center(map_center_option)
    
    # 創建地圖
    m = folium.Map(
        location=map_center,
        zoom_start=12,
        tiles=None
    )
    
    # 添加地圖圖層
    tile_mapping = {
        "OpenStreetMap": folium.TileLayer('openstreetmap', attr='OpenStreetMap contributors'),
        "CartoDB positron": folium.TileLayer('cartodbpositron', attr='CartoDB contributors'),
        "CartoDB dark_matter": folium.TileLayer('cartodbdark_matter', attr='CartoDB contributors'),
        "Stamen Terrain": folium.TileLayer('stamenterrain', attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.')
    }
    
    if map_style in tile_mapping:
        tile_mapping[map_style].add_to(m)
    else:
        folium.TileLayer('openstreetmap').add_to(m)
    
    # 獲取篩選後的場地資料
    filtered_venues = st.session_state.data_manager.get_filtered_venues(
        sport_types=show_sports,
        districts=show_districts,
        price_range=price_range,
        min_rating=min_rating
    )
    
    if filtered_venues is not None and not filtered_venues.empty:
        # 添加場地標記
        if show_clusters:
            from folium.plugins import MarkerCluster
            marker_cluster = MarkerCluster().add_to(m)
            container = marker_cluster
        else:
            container = m
        
        # 為不同運動類型設定不同顏色
        sport_colors = st.session_state.map_utils.get_sport_colors()
        
        for idx, venue in filtered_venues.iterrows():
            if pd.notna(venue.get('latitude')) and pd.notna(venue.get('longitude')):
                sport_type = venue.get('sport_type', '其他')
                color = sport_colors.get(sport_type, 'gray')
                
                # 建立彈出視窗內容
                popup_html = f"""
                <div style="width: 250px;">
                    <h4>{venue.get('name', '未知場地')}</h4>
                    <p><b>🏃‍♂️ 運動類型:</b> {venue.get('sport_type', '未指定')}</p>
                    <p><b>📍 地址:</b> {venue.get('address', '地址未提供')}</p>
                    <p><b>🏢 地區:</b> {venue.get('district', '未知地區')}</p>
                    {f'<p><b>💰 價格:</b> NT${venue.get("price_per_hour")}/hr</p>' if venue.get('price_per_hour') else ''}
                    {f'<p><b>⭐ 評分:</b> {venue.get("rating"):.1f}/5.0</p>' if venue.get('rating') else ''}
                    {f'<p><b>🏢 設施:</b> {venue.get("facilities")}</p>' if venue.get('facilities') else ''}
                </div>
                """
                
                folium.Marker(
                    location=[venue.get('latitude'), venue.get('longitude')],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{venue.get('name', '未知場地')} - {sport_type}",
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(container)
        
        # 添加熱力圖（如果勾選）
        if show_heatmap and not filtered_venues.empty:
            from folium.plugins import HeatMap
            
            heat_data = []
            for idx, venue in filtered_venues.iterrows():
                if pd.notna(venue.get('latitude')) and pd.notna(venue.get('longitude')):
                    # 使用評分作為熱力權重
                    weight = venue.get('rating', 3.0)
                    heat_data.append([venue.get('latitude'), venue.get('longitude'), weight])
            
            if heat_data:
                HeatMap(heat_data, radius=15, max_zoom=18).add_to(m)
        
        # 顯示地圖
        map_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])
        
        # 處理地圖點擊事件
        if map_data['last_clicked']:
            clicked_lat = map_data['last_clicked']['lat']
            clicked_lng = map_data['last_clicked']['lng']
            
            # 尋找最近的場地
            nearest_venue = st.session_state.map_utils.find_nearest_venue(
                filtered_venues, clicked_lat, clicked_lng
            )
            
            if nearest_venue is not None:
                st.session_state.selected_venue = nearest_venue
                
        # 顯示圖例
        st.markdown("### 🎨 圖例")
        legend_cols = st.columns(len(sport_colors))
        
        for i, (sport, color) in enumerate(sport_colors.items()):
            if i < len(legend_cols):
                with legend_cols[i]:
                    st.markdown(f"🔵 **{sport}**" if color == 'blue' else 
                              f"🔴 **{sport}**" if color == 'red' else 
                              f"🟢 **{sport}**" if color == 'green' else 
                              f"🟠 **{sport}**" if color == 'orange' else 
                              f"🟣 **{sport}**" if color == 'purple' else 
                              f"⚫ **{sport}**")
    
    else:
        st.warning("沒有符合篩選條件的場地資料可顯示在地圖上")
        # 顯示空白地圖
        st_folium(m, width=700, height=500)

with col2:
    st.subheader("📊 地圖統計")
    
    if filtered_venues is not None and not filtered_venues.empty:
        # 顯示統計資訊
        total_venues = len(filtered_venues)
        avg_rating = filtered_venues['rating'].mean() if 'rating' in filtered_venues.columns else 0
        avg_price = filtered_venues['price_per_hour'].mean() if 'price_per_hour' in filtered_venues.columns else 0
        
        st.metric("顯示場地數", total_venues)
        if avg_rating > 0:
            st.metric("平均評分", f"{avg_rating:.1f}/5.0")
        if avg_price > 0:
            st.metric("平均價格", f"NT${avg_price:.0f}/hr")
        
        # 按區域統計
        if 'district' in filtered_venues.columns:
            district_counts = filtered_venues['district'].value_counts()
            
            st.markdown("**📍 各區域場地數量:**")
            for district, count in district_counts.head(10).items():
                st.markdown(f"• {district}: {count} 個場地")
        
        # 按運動類型統計
        if 'sport_type' in filtered_venues.columns:
            sport_counts = filtered_venues['sport_type'].value_counts()
            
            st.markdown("**🏃‍♂️ 運動類型分布:**")
            for sport, count in sport_counts.head(10).items():
                st.markdown(f"• {sport}: {count} 個場地")
    
    else:
        st.info("選擇篩選條件以顯示統計資訊")
    
    # 快速導航
    st.subheader("🧭 快速導航")
    
    major_districts = ["信義區", "大安區", "中山區", "松山區"]
    for district in major_districts:
        if st.button(f"📍 {district}", key=f"nav_{district}", use_container_width=True):
            # 更新地圖中心到該區域
            st.session_state.map_center = district
            st.rerun()
    
    # 場地類型快速篩選
    st.subheader("🏃‍♂️ 快速篩選")
    
    if available_sports:
        popular_sports = available_sports[:6]  # 顯示前6個運動類型
        for sport in popular_sports:
            if st.button(f"🏃‍♂️ {sport}", key=f"sport_filter_{sport}", use_container_width=True):
                st.session_state.map_sports_filter = [sport]
                st.rerun()

# 顯示選中場地的詳細資訊
if st.session_state.get('selected_venue'):
    st.markdown("---")
    st.subheader(f"📍 {st.session_state.selected_venue.get('name', '選中場地')}")
    
    venue = st.session_state.selected_venue
    
    info_col1, info_col2, info_col3 = st.columns([2, 1, 1])
    
    with info_col1:
        st.markdown(f"**📍 地址:** {venue.get('address', '地址未提供')}")
        st.markdown(f"**🏃‍♂️ 運動類型:** {venue.get('sport_type', '未指定')}")
        st.markdown(f"**🏢 地區:** {venue.get('district', '未知地區')}")
        
        if venue.get('contact_phone'):
            st.markdown(f"**📞 電話:** {venue.get('contact_phone')}")
    
    with info_col2:
        if venue.get('rating'):
            st.metric("評分", f"{venue.get('rating'):.1f}/5.0")
        if venue.get('price_per_hour'):
            st.metric("價格", f"NT${venue.get('price_per_hour')}/hr")
    
    with info_col3:
        if st.button("🔍 詳細資訊", use_container_width=True):
            st.switch_page("pages/1_🔍_Search_Venues.py")
        
        if st.button("❤️ 加入收藏", key="map_favorite", use_container_width=True):
            if 'favorites' not in st.session_state:
                st.session_state.favorites = []
            
            venue_id = venue.get('id', venue.get('name'))
            if venue_id not in st.session_state.favorites:
                st.session_state.favorites.append(venue_id)
                st.success("已加入收藏！")
            else:
                st.info("已在收藏列表中")
