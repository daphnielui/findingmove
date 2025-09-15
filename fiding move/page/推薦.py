import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_manager import DataManager
from utils.recommendation_engine import RecommendationEngine

st.set_page_config(
    page_title="個人推薦 - 台北運動場地搜尋引擎",
    page_icon="⭐",
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

if 'recommendation_engine' not in st.session_state:
    st.session_state.recommendation_engine = RecommendationEngine()

if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        'preferred_sports': [],
        'preferred_districts': [],
        'price_range': [0, 10000],
        'search_history': [],
        'visited_venues': [],
        'favorite_venues': []
    }

st.title("⭐ 個人化推薦")
st.markdown("基於您的偏好和行為，為您推薦最適合的運動場地")

# 側邊欄 - 推薦設定
with st.sidebar:
    st.header("🎯 推薦設定")
    
    # 推薦類型選擇
    recommendation_type = st.selectbox(
        "推薦類型",
        ["個人化推薦", "機器學習推薦", "聚類分析推薦", "內容相似推薦", "熱門場地", "新場地", "相似用戶推薦", "基於評分推薦"],
        key="rec_type"
    )
    
    # 推薦數量
    num_recommendations = st.slider(
        "推薦數量",
        5, 20, 10,
        key="num_rec"
    )
    
    # 多樣性設定
    diversity_weight = st.slider(
        "結果多樣性",
        0.0, 1.0, 0.3,
        step=0.1,
        help="數值越高，推薦結果越多樣化",
        key="diversity"
    )
    
    st.subheader("📊 偏好分析")
    
    # 顯示用戶偏好統計
    if st.session_state.user_preferences['search_history']:
        st.metric("搜尋次數", len(st.session_state.user_preferences['search_history']))
    
    if 'favorites' in st.session_state:
        st.metric("收藏場地", len(st.session_state.favorites))
    
    # 更新偏好按鈕
    if st.button("🔄 更新偏好分析", use_container_width=True):
        # 重新分析用戶偏好
        st.session_state.recommendation_engine.update_user_profile(
            st.session_state.user_preferences
        )
        st.success("偏好分析已更新！")

# 主要內容
tab1, tab2, tab3, tab4 = st.tabs(["🎯 推薦結果", "📊 偏好分析", "🔄 推薦解釋", "⚙️ 設定調整"])

with tab1:
    st.subheader(f"🌟 {recommendation_type}")
    
    # 根據選擇的推薦類型獲取推薦結果
    if recommendation_type == "個人化推薦":
        recommendations = st.session_state.recommendation_engine.get_personalized_recommendations(
            st.session_state.user_preferences,
            num_recommendations=num_recommendations,
            diversity_weight=diversity_weight
        )
    elif recommendation_type == "機器學習推薦":
        recommendations = st.session_state.recommendation_engine.get_ml_based_recommendations(
            st.session_state.user_preferences,
            num_recommendations=num_recommendations
        )
    elif recommendation_type == "聚類分析推薦":
        recommendations = st.session_state.recommendation_engine.get_cluster_based_recommendations(
            st.session_state.user_preferences,
            num_recommendations=num_recommendations
        )
    elif recommendation_type == "內容相似推薦":
        recommendations = st.session_state.recommendation_engine.get_content_based_ml_recommendations(
            st.session_state.user_preferences,
            num_recommendations=num_recommendations
        )
    elif recommendation_type == "熱門場地":
        recommendations = st.session_state.recommendation_engine.get_trending_venues(
            num_recommendations=num_recommendations
        )
    elif recommendation_type == "新場地":
        recommendations = st.session_state.recommendation_engine.get_new_venues(
            num_recommendations=num_recommendations
        )
    elif recommendation_type == "相似用戶推薦":
        recommendations = st.session_state.recommendation_engine.get_collaborative_recommendations(
            st.session_state.user_preferences,
            num_recommendations=num_recommendations
        )
    else:  # 基於評分推薦
        recommendations = st.session_state.recommendation_engine.get_rating_based_recommendations(
            st.session_state.user_preferences,
            num_recommendations=num_recommendations
        )
    
    if recommendations is not None and not recommendations.empty:
        # 顯示推薦結果
        for idx, venue in recommendations.iterrows():
            with st.expander(
                f"⭐ {venue.get('name', '未知場地')} - 推薦度: {venue.get('recommendation_score', 0):.1f}",
                expanded=idx < 3  # 前3個自動展開
            ):
                rec_col1, rec_col2, rec_col3 = st.columns([2, 1, 1])
                
                with rec_col1:
                    st.markdown(f"**📍 地址:** {venue.get('address', '地址未提供')}")
                    st.markdown(f"**🏃‍♂️ 運動類型:** {venue.get('sport_type', '未指定')}")
                    st.markdown(f"**🏢 地區:** {venue.get('district', '未知地區')}")
                    
                    if venue.get('facilities'):
                        facilities_list = venue.get('facilities', '').split(',') if isinstance(venue.get('facilities'), str) else venue.get('facilities', [])
                        st.markdown(f"**🏢 設施:** {', '.join(facilities_list)}")
                    
                    if venue.get('description'):
                        st.markdown(f"**📝 描述:** {venue.get('description')}")
                    
                    # 推薦原因
                    if venue.get('recommendation_reason'):
                        st.markdown(f"**💡 推薦原因:** {venue.get('recommendation_reason')}")
                
                with rec_col2:
                    # 評分和價格
                    if venue.get('rating'):
                        st.metric("評分", f"{venue.get('rating'):.1f}/5.0")
                    
                    if venue.get('price_per_hour'):
                        st.metric("價格", f"NT${venue.get('price_per_hour')}/hr")
                    
                    # 推薦度分數
                    if venue.get('recommendation_score'):
                        st.metric("推薦度", f"{venue.get('recommendation_score'):.1f}/10")
                
                with rec_col3:
                    # 操作按鈕
                    if st.button(f"🔍 詳細資訊", key=f"rec_detail_{idx}"):
                        st.session_state.selected_venue = venue.to_dict()
                        st.switch_page("pages/1_🔍_Search_Venues.py")
                    
                    if st.button(f"📍 地圖位置", key=f"rec_map_{idx}"):
                        st.session_state.selected_venue = venue.to_dict()
                        st.switch_page("pages/2_🗺️_Map_View.py")
                    
                    if st.button(f"❤️ 收藏", key=f"rec_fav_{idx}"):
                        if 'favorites' not in st.session_state:
                            st.session_state.favorites = []
                        
                        venue_id = venue.get('id', venue.get('name'))
                        if venue_id not in st.session_state.favorites:
                            st.session_state.favorites.append(venue_id)
                            st.success("已加入收藏！")
                        else:
                            st.info("已在收藏列表中")
                    
                    # 反饋按鈕
                    feedback_col1, feedback_col2 = st.columns(2)
                    with feedback_col1:
                        if st.button("👍", key=f"rec_like_{idx}", help="喜歡這個推薦"):
                            st.session_state.recommendation_engine.record_feedback(
                                venue.get('id'), 'like', st.session_state.user_preferences
                            )
                            st.success("感謝您的反饋！")
                    
                    with feedback_col2:
                        if st.button("👎", key=f"rec_dislike_{idx}", help="不喜歡這個推薦"):
                            st.session_state.recommendation_engine.record_feedback(
                                venue.get('id'), 'dislike', st.session_state.user_preferences
                            )
                            st.info("我們會改善推薦結果")
    
    else:
        st.warning("暫時無法生成推薦結果。請嘗試：")
        st.markdown("""
        - 在主頁面設定您的偏好
        - 搜尋一些場地以建立使用歷史
        - 收藏一些您喜歡的場地
        - 調整推薦設定
        """)

with tab2:
    st.subheader("📊 您的偏好分析")
    
    # 偏好運動類型圖表
    if st.session_state.user_preferences['preferred_sports']:
        sport_counts = {}
        for sport in st.session_state.user_preferences['preferred_sports']:
            sport_counts[sport] = sport_counts.get(sport, 0) + 1
        
        if sport_counts:
            fig_sports = px.pie(
                values=list(sport_counts.values()),
                names=list(sport_counts.keys()),
                title="偏好運動類型分布"
            )
            st.plotly_chart(fig_sports, use_container_width=True)
    else:
        st.info("請在主頁面設定您的運動類型偏好")
    
    # 偏好地區圖表
    if st.session_state.user_preferences['preferred_districts']:
        district_counts = {}
        for district in st.session_state.user_preferences['preferred_districts']:
            district_counts[district] = district_counts.get(district, 0) + 1
        
        if district_counts:
            fig_districts = px.bar(
                x=list(district_counts.keys()),
                y=list(district_counts.values()),
                title="偏好地區分布",
                labels={'x': '地區', 'y': '偏好程度'}
            )
            st.plotly_chart(fig_districts, use_container_width=True)
    
    # 搜尋歷史分析
    if st.session_state.user_preferences['search_history']:
        st.subheader("🔍 搜尋歷史分析")
        
        search_frequency = {}
        for search in st.session_state.user_preferences['search_history']:
            search_frequency[search] = search_frequency.get(search, 0) + 1
        
        # 顯示最常搜尋的關鍵字
        sorted_searches = sorted(search_frequency.items(), key=lambda x: x[1], reverse=True)
        
        st.markdown("**最常搜尋的關鍵字:**")
        for search, count in sorted_searches[:10]:
            st.markdown(f"• {search}: {count} 次")
    
    # 收藏場地分析
    if 'favorites' in st.session_state and st.session_state.favorites:
        st.subheader("❤️ 收藏場地分析")
        
        favorite_venues = st.session_state.data_manager.get_venues_by_ids(st.session_state.favorites)
        
        if favorite_venues is not None and not favorite_venues.empty:
            # 收藏場地的運動類型分布
            if 'sport_type' in favorite_venues.columns:
                fav_sport_counts = favorite_venues['sport_type'].value_counts()
                
                fig_fav_sports = px.bar(
                    x=fav_sport_counts.index,
                    y=fav_sport_counts.values,
                    title="收藏場地運動類型分布",
                    labels={'x': '運動類型', 'y': '場地數量'}
                )
                st.plotly_chart(fig_fav_sports, use_container_width=True)

with tab3:
    st.subheader("🔄 推薦演算法說明")
    
    st.markdown("""
    ### 🤖 我們如何為您推薦場地
    
    我們的推薦系統結合多種演算法來為您找到最適合的運動場地：
    
    #### 1. 🎯 個人化推薦
    - **基於內容的推薦**: 根據您的運動類型和地區偏好
    - **協同過濾**: 分析與您相似用戶的選擇
    - **混合推薦**: 結合多種方法提供最佳結果
    
    #### 2. 📊 考慮因素
    - **偏好匹配度**: 場地是否符合您設定的偏好
    - **評分權重**: 高評分場地會獲得更高推薦分數
    - **距離因素**: 考慮您偏好地區的地理位置
    - **價格適配**: 符合您預算範圍的場地
    - **設施匹配**: 提供您需要設施的場地
    
    #### 3. 🔄 學習機制
    - **搜尋歷史**: 分析您的搜尋模式
    - **點擊行為**: 記錄您感興趣的場地類型
    - **收藏偏好**: 從您的收藏中學習偏好
    - **反饋學習**: 根據您的點讚/點踩調整推薦
    """)
    
    # 顯示當前推薦權重
    if recommendations is not None and not recommendations.empty:
        st.subheader("🔢 當前推薦權重分析")
        
        # 為第一個推薦場地顯示詳細評分分解
        first_venue = recommendations.iloc[0]
        
        st.markdown(f"**以「{first_venue.get('name', '未知場地')}」為例:**")
        
        weight_col1, weight_col2 = st.columns(2)
        
        with weight_col1:
            st.metric("偏好匹配度", f"{first_venue.get('preference_match', 0):.1f}/10")
            st.metric("評分權重", f"{first_venue.get('rating_weight', 0):.1f}/10")
            st.metric("距離評分", f"{first_venue.get('distance_score', 0):.1f}/10")
        
        with weight_col2:
            st.metric("價格適配度", f"{first_venue.get('price_match', 0):.1f}/10")
            st.metric("設施匹配度", f"{first_venue.get('facility_match', 0):.1f}/10")
            st.metric("總推薦分數", f"{first_venue.get('recommendation_score', 0):.1f}/10")

with tab4:
    st.subheader("⚙️ 推薦系統調整")
    
    st.markdown("調整以下設定來個人化您的推薦體驗：")
    
    # 推薦權重調整
    st.markdown("#### 🎚️ 推薦因素權重")
    
    weight_col1, weight_col2 = st.columns(2)
    
    with weight_col1:
        preference_weight = st.slider(
            "偏好匹配重要性",
            0.0, 1.0, 0.3,
            step=0.1,
            key="pref_weight"
        )
        
        rating_weight = st.slider(
            "評分重要性",
            0.0, 1.0, 0.25,
            step=0.1,
            key="rating_weight"
        )
        
        price_weight = st.slider(
            "價格重要性",
            0.0, 1.0, 0.2,
            step=0.1,
            key="price_weight"
        )
    
    with weight_col2:
        distance_weight = st.slider(
            "距離重要性",
            0.0, 1.0, 0.15,
            step=0.1,
            key="distance_weight"
        )
        
        facility_weight = st.slider(
            "設施重要性",
            0.0, 1.0, 0.1,
            step=0.1,
            key="facility_weight"
        )
    
    # 推薦偏好設定
    st.markdown("#### 🎯 推薦偏好")
    
    pref_col1, pref_col2 = st.columns(2)
    
    with pref_col1:
        explore_vs_exploit = st.slider(
            "探索 vs 利用",
            0.0, 1.0, 0.3,
            step=0.1,
            help="數值越高越會推薦新類型場地，越低越會推薦熟悉類型",
            key="explore_exploit"
        )
        
        popularity_bias = st.slider(
            "熱門程度偏好",
            0.0, 1.0, 0.4,
            step=0.1,
            help="數值越高越偏好熱門場地",
            key="popularity_bias"
        )
    
    with pref_col2:
        novelty_preference = st.slider(
            "新場地偏好",
            0.0, 1.0, 0.2,
            step=0.1,
            help="數值越高越會推薦新開放的場地",
            key="novelty_pref"
        )
        
        serendipity_factor = st.slider(
            "意外發現因子",
            0.0, 1.0, 0.15,
            step=0.1,
            help="數值越高越會推薦意想不到但可能喜歡的場地",
            key="serendipity"
        )
    
    # 應用設定
    if st.button("💾 應用設定", type="primary", use_container_width=True):
        # 更新推薦引擎的權重設定
        weights = {
            'preference_weight': preference_weight,
            'rating_weight': rating_weight,
            'price_weight': price_weight,
            'distance_weight': distance_weight,
            'facility_weight': facility_weight,
            'explore_vs_exploit': explore_vs_exploit,
            'popularity_bias': popularity_bias,
            'novelty_preference': novelty_preference,
            'serendipity_factor': serendipity_factor
        }
        
        st.session_state.recommendation_engine.update_weights(weights)
        st.success("推薦設定已更新！重新載入頁面以查看新的推薦結果。")
        
        # 自動重新生成推薦
        st.rerun()
    
    # 重置為預設值
    if st.button("🔄 重置為預設值", use_container_width=True):
        st.session_state.recommendation_engine.reset_weights()
        st.success("已重置為預設推薦設定！")
        st.rerun()
