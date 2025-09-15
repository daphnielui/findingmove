import streamlit as st
import pandas as pd
from utils.data_manager import DataManager
from datetime import datetime, timedelta, date, time

st.set_page_config(
    page_title="場地詳情 - 台北運動場地搜尋引擎",
    page_icon="🏢",
    layout="wide"
)

# 確保 session state 已初始化
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

st.title("🏢 場地詳細資訊")

# 從 URL 參數或選擇器獲取場地 ID
venue_id = st.query_params.get("id", None)

if venue_id is None:
    # 如果沒有指定場地ID，顯示選擇器
    all_venues = st.session_state.data_manager.get_all_venues()
    
    if all_venues is not None and not all_venues.empty:
        st.subheader("請選擇要查看的場地")
        
        venue_options = {}
        for _, venue in all_venues.iterrows():
            label = f"{venue['name']} - {venue['district']}"
            venue_options[label] = venue['id']
        
        selected_venue = st.selectbox("選擇場地", list(venue_options.keys()))
        
        if selected_venue:
            venue_id = venue_options[selected_venue]
    else:
        st.error("沒有可用的場地資料")
        st.stop()

if venue_id:
    try:
        venue_id = int(venue_id)
        
        # 獲取場地詳細資訊
        venue_info = st.session_state.data_manager.get_venue_by_id(venue_id)
        
        if venue_info is None:
            st.error("找不到指定的場地")
            st.stop()
        
        # 場地基本資訊
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header(venue_info['name'])
            st.markdown(f"**地址:** {venue_info['address']}")
            st.markdown(f"**地區:** {venue_info['district']}")
            st.markdown(f"**運動類型:** {venue_info['sport_type']}")
            
            if venue_info['description']:
                st.markdown("**場地介紹:**")
                st.write(venue_info['description'])
        
        with col2:
            # 價格和評分資訊
            st.metric("時租價格", f"NT${venue_info['price_per_hour']:.0f}/小時")
            
            # 使用計算後的平均評分
            avg_rating = venue_info.get('avg_rating', venue_info.get('rating', 0))
            if avg_rating and avg_rating > 0:
                st.metric("平均評分", f"{float(avg_rating):.1f}/5.0")
            
            review_count = venue_info.get('review_count', 0)
            st.metric("評論數量", f"{review_count} 則")
        
        # 設施資訊
        if venue_info['facilities']:
            st.subheader("🏃‍♂️ 設施資訊")
            # 處理 PostgreSQL 數組格式
            facilities = venue_info['facilities']
            if isinstance(facilities, str):
                # 如果是字符串，嘗試解析為列表
                facilities = facilities.strip('{}').split(',')
                facilities = [f.strip().strip('"') for f in facilities]
            
            facility_cols = st.columns(min(len(facilities), 4))
            for i, facility in enumerate(facilities):
                with facility_cols[i % 4]:
                    st.info(f"✓ {facility}")
        
        # 聯絡資訊
        st.subheader("📞 聯絡資訊")
        contact_col1, contact_col2 = st.columns(2)
        
        with contact_col1:
            if venue_info['contact_phone']:
                st.markdown(f"**電話:** {venue_info['contact_phone']}")
            if venue_info['opening_hours']:
                st.markdown(f"**營業時間:** {venue_info['opening_hours']}")
        
        with contact_col2:
            if venue_info['website']:
                st.markdown(f"**網站:** [官方網站]({venue_info['website']})")
            if venue_info['latitude'] and venue_info['longitude']:
                st.markdown(f"**座標:** {venue_info['latitude']:.4f}, {venue_info['longitude']:.4f}")
        
        # 分頁標籤
        tab1, tab2, tab3 = st.tabs(["💬 用戶評論", "📅 立即預訂", "📍 地圖位置"])
        
        with tab1:
            # 用戶評論區域
            st.subheader("用戶評論")
            
            # 獲取已審核的評論
            reviews = st.session_state.data_manager.get_venue_reviews(venue_id)
            
            if reviews:
                for review in reviews:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{review['user_name']}**")
                            st.write(review['comment'])
                        with col2:
                            st.metric("評分", f"{review['rating']}/5")
                            st.caption(f"{review['created_at']}")
                        st.divider()
            else:
                st.info("暫無評論，成為第一個評論的用戶吧！")
            
            # 添加新評論
            st.subheader("發表評論")
            with st.form("review_form"):
                user_name = st.text_input("您的姓名", placeholder="請輸入您的姓名")
                rating = st.slider("評分", 1, 5, 5)
                comment = st.text_area("評論內容", placeholder="分享您對這個場地的體驗...")
                
                if st.form_submit_button("提交評論"):
                    if user_name and comment:
                        success = st.session_state.data_manager.add_review(
                            venue_id, user_name, rating, comment
                        )
                        if success:
                            st.success("評論已提交！審核通過後將顯示在評論區域。")
                            st.rerun()
                        else:
                            st.error("提交評論失敗，請稍後再試。")
                    else:
                        st.error("請填寫所有必填欄位。")
        
        with tab2:
            # 預訂功能
            st.subheader("場地預訂")
            
            with st.form("booking_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    user_name = st.text_input("預訂人姓名", placeholder="請輸入您的姓名")
                    user_email = st.text_input("電子郵件", placeholder="用於確認預訂")
                    user_phone = st.text_input("聯絡電話", placeholder="緊急聯絡用")
                
                with col2:
                    booking_date = st.date_input("預訂日期", min_value=date.today())
                    
                    # 時間選擇
                    time_col1, time_col2 = st.columns(2)
                    with time_col1:
                        start_time = st.time_input("開始時間", value=time(9, 0))
                    with time_col2:
                        end_time = st.time_input("結束時間", value=time(10, 0))
                
                special_requests = st.text_area("特殊需求", placeholder="其他需要說明的事項...")
                
                if st.form_submit_button("檢查可用性並預訂"):
                    if user_name and user_email and user_phone:
                        # 檢查時間邏輯
                        if start_time >= end_time:
                            st.error("結束時間必須晚於開始時間！")
                        else:
                            # 檢查可用性
                            is_available = st.session_state.data_manager.check_availability(
                                venue_id, str(booking_date), str(start_time), str(end_time)
                            )
                            
                            if is_available:
                                # 創建預訂
                                booking_id = st.session_state.data_manager.create_booking(
                                    venue_id, user_name, user_email, user_phone,
                                    str(booking_date), str(start_time), str(end_time),
                                    special_requests
                                )
                                
                                if booking_id:
                                    st.success(f"預訂成功！預訂編號：{booking_id}")
                                    st.info("我們將透過電子郵件確認您的預訂詳情。")
                                else:
                                    st.error("預訂失敗，請稍後再試。")
                            else:
                                st.warning("該時段已被預訂，請選擇其他時間。")
                    else:
                        st.error("請填寫所有必填欄位。")
        
        with tab3:
            # 地圖顯示
            st.subheader("地圖位置")
            
            if venue_info['latitude'] and venue_info['longitude']:
                # 創建地圖數據
                map_data = pd.DataFrame({
                    'lat': [float(venue_info['latitude'])],
                    'lon': [float(venue_info['longitude'])],
                    'size': [20],
                    'name': [venue_info['name']]
                })
                
                st.map(map_data, zoom=14)
                
                # 提供 Google Maps 連結
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={venue_info['latitude']},{venue_info['longitude']}"
                st.markdown(f"[在 Google Maps 中查看]({google_maps_url})")
            else:
                st.warning("該場地暫無地理位置資訊")
        
    except ValueError:
        st.error("無效的場地ID")
    except Exception as e:
        st.error(f"載入場地資訊時發生錯誤: {str(e)}")
else:
    st.warning("請選擇要查看的場地")