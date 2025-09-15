import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_manager import DataManager

st.set_page_config(
    page_title="場地比較 - 台北運動場地搜尋引擎",
    page_icon="⚖️",
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

if 'comparison_venues' not in st.session_state:
    st.session_state.comparison_venues = []

st.title("⚖️ 場地比較分析")
st.markdown("選擇多個場地進行詳細比較，幫助您做出最佳選擇")

# 側邊欄 - 場地選擇
with st.sidebar:
    st.header("🏟️ 選擇比較場地")
    
    # 載入所有場地
    venues_data = st.session_state.data_manager.get_all_venues()
    
    if venues_data is not None and not venues_data.empty:
        venue_options = {}
        for _, venue in venues_data.iterrows():
            venue_name = venue.get('name', '未知場地')
            sport_type = venue.get('sport_type', '未知運動')
            district = venue.get('district', '未知地區')
            venue_options[f"{venue_name} ({sport_type} - {district})"] = venue.get('id')
        
        # 多選場地
        selected_venues = st.multiselect(
            "選擇要比較的場地（最多5個）",
            options=list(venue_options.keys()),
            default=[],
            max_selections=5,
            key="venue_multiselect"
        )
        
        if selected_venues:
            # 更新比較列表
            selected_ids = [venue_options[venue] for venue in selected_venues]
            st.session_state.comparison_venues = selected_ids
            
            st.success(f"已選擇 {len(selected_venues)} 個場地進行比較")
            
            # 快速操作按鈕
            if st.button("🔄 清空選擇", use_container_width=True):
                st.session_state.comparison_venues = []
                st.rerun()
        else:
            st.info("請至少選擇2個場地進行比較")
    else:
        st.error("無法載入場地資料")

# 主要內容
if len(st.session_state.comparison_venues) >= 2:
    # 獲取比較場地的詳細資料
    comparison_data = []
    
    for venue_id in st.session_state.comparison_venues:
        venue_info = st.session_state.data_manager.get_venue_by_id(venue_id)
        if venue_info is not None:
            comparison_data.append(venue_info)
    
    if comparison_data:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 基本比較", "💰 價格分析", "⭐ 評分對比", "📍 地理分布"])
        
        with tab1:
            st.subheader("📊 基本資訊比較")
            
            # 創建比較表格
            comparison_df = pd.DataFrame(comparison_data)
            
            # 基本資訊表格
            basic_info_columns = ['name', 'sport_type', 'district', 'address', 'contact_phone', 'price_per_hour', 'rating']
            available_columns = [col for col in basic_info_columns if col in comparison_df.columns]
            
            if available_columns:
                display_df = comparison_df[available_columns].copy()
                
                # 重新命名列
                column_mapping = {
                    'name': '場地名稱',
                    'sport_type': '運動類型',
                    'district': '地區',
                    'address': '地址',
                    'contact_phone': '電話',
                    'price_per_hour': '每小時費用(NT$)',
                    'rating': '評分'
                }
                
                display_df = display_df.rename(columns=column_mapping)
                
                # 轉置表格以便比較
                display_df_transposed = display_df.T
                display_df_transposed.columns = [f"場地 {i+1}" for i in range(len(comparison_data))]
                
                st.dataframe(display_df_transposed, use_container_width=True)
            
            # 設施比較
            st.subheader("🏢 設施比較")
            
            facilities_comparison = {}
            for i, venue in enumerate(comparison_data):
                venue_name = venue.get('name', f'場地 {i+1}')
                facilities = venue.get('facilities', '')
                
                if isinstance(facilities, str) and facilities:
                    facility_list = [f.strip() for f in facilities.split(',')]
                elif isinstance(facilities, list):
                    facility_list = facilities
                else:
                    facility_list = []
                
                facilities_comparison[venue_name] = facility_list
            
            if facilities_comparison:
                # 創建設施對比表
                all_facilities = set()
                for facilities in facilities_comparison.values():
                    all_facilities.update(facilities)
                
                if all_facilities:
                    facility_matrix = []
                    for facility in sorted(all_facilities):
                        row = {'設施': facility}
                        for venue_name, facilities in facilities_comparison.items():
                            row[venue_name] = '✅' if facility in facilities else '❌'
                        facility_matrix.append(row)
                    
                    facility_df = pd.DataFrame(facility_matrix)
                    st.dataframe(facility_df, use_container_width=True)
                else:
                    st.info("暫無設施資訊可比較")
            
        with tab2:
            st.subheader("💰 價格分析")
            
            # 價格比較圖表
            price_data = []
            for venue in comparison_data:
                price_data.append({
                    '場地': venue.get('name', '未知場地'),
                    '每小時費用': venue.get('price_per_hour', 0)
                })
            
            price_df = pd.DataFrame(price_data)
            
            if not price_df['每小時費用'].isna().all():
                col1, col2 = st.columns(2)
                
                with col1:
                    # 柱狀圖
                    fig_bar = px.bar(
                        price_df, 
                        x='場地', 
                        y='每小時費用',
                        title="各場地價格比較",
                        color='每小時費用',
                        color_continuous_scale='viridis'
                    )
                    fig_bar.update_layout(height=400)
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    # 圓餅圖
                    fig_pie = px.pie(
                        price_df, 
                        values='每小時費用', 
                        names='場地',
                        title="價格分布比例"
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # 價格統計
                st.subheader("💵 價格統計")
                col1, col2, col3, col4 = st.columns(4)
                
                prices = price_df['每小時費用'].dropna()
                if not prices.empty:
                    with col1:
                        st.metric("最高價格", f"NT${prices.max():,.0f}")
                    with col2:
                        st.metric("最低價格", f"NT${prices.min():,.0f}")
                    with col3:
                        st.metric("平均價格", f"NT${prices.mean():,.0f}")
                    with col4:
                        st.metric("價格差距", f"NT${prices.max() - prices.min():,.0f}")
            else:
                st.info("暫無價格資訊可比較")
        
        with tab3:
            st.subheader("⭐ 評分對比")
            
            # 評分比較
            rating_data = []
            for venue in comparison_data:
                rating = venue.get('rating', 0)
                if rating and rating > 0:
                    rating_data.append({
                        '場地': venue.get('name', '未知場地'),
                        '評分': rating
                    })
            
            if rating_data:
                rating_df = pd.DataFrame(rating_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 雷達圖
                    fig_radar = go.Figure()
                    
                    for _, row in rating_df.iterrows():
                        fig_radar.add_trace(go.Scatterpolar(
                            r=[row['評分'], row['評分'], row['評分'], row['評分'], row['評分']],
                            theta=['整體滿意度', '設施品質', '服務態度', '環境整潔', '價格合理'],
                            fill='toself',
                            name=row['場地']
                        ))
                    
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 5]
                            )),
                        showlegend=True,
                        title="評分雷達圖比較",
                        height=500
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                
                with col2:
                    # 評分柱狀圖
                    fig_rating = px.bar(
                        rating_df, 
                        x='場地', 
                        y='評分',
                        title="場地評分比較",
                        color='評分',
                        color_continuous_scale='RdYlGn',
                        range_color=[0, 5]
                    )
                    fig_rating.update_layout(height=500)
                    fig_rating.add_hline(y=rating_df['評分'].mean(), 
                                        line_dash="dash", 
                                        annotation_text="平均評分")
                    st.plotly_chart(fig_rating, use_container_width=True)
                
                # 評分統計
                st.subheader("📊 評分統計")
                col1, col2, col3, col4 = st.columns(4)
                
                ratings = rating_df['評分']
                with col1:
                    st.metric("最高評分", f"{ratings.max():.1f}/5.0")
                with col2:
                    st.metric("最低評分", f"{ratings.min():.1f}/5.0")
                with col3:
                    st.metric("平均評分", f"{ratings.mean():.1f}/5.0")
                with col4:
                    best_venue = rating_df.loc[rating_df['評分'].idxmax(), '場地']
                    st.metric("最佳場地", best_venue)
            else:
                st.info("暫無評分資訊可比較")
        
        with tab4:
            st.subheader("📍 地理分布")
            
            # 地區分布
            district_data = [venue.get('district', '未知地區') for venue in comparison_data]
            district_counts = pd.Series(district_data).value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 地區分布圓餅圖
                fig_district = px.pie(
                    values=district_counts.values, 
                    names=district_counts.index,
                    title="場地地區分布"
                )
                st.plotly_chart(fig_district, use_container_width=True)
            
            with col2:
                # 地區列表
                st.subheader("🏪 各地區場地")
                for district, count in district_counts.items():
                    st.write(f"**{district}**: {count} 個場地")
                    venues_in_district = [venue.get('name', '未知場地') 
                                        for venue in comparison_data 
                                        if venue.get('district') == district]
                    for venue_name in venues_in_district:
                        st.write(f"  • {venue_name}")
        
        # 綜合推薦
        st.markdown("---")
        st.subheader("🏆 綜合分析推薦")
        
        # 計算綜合分數
        recommendation_scores = []
        for venue in comparison_data:
            score = 0
            factors = []
            
            # 評分因子 (40%)
            rating = venue.get('rating', 3.0)
            if rating:
                rating_score = rating / 5.0 * 0.4
                score += rating_score
                factors.append(f"評分: {rating:.1f}/5.0")
            
            # 價格因子 (30%) - 價格越低分數越高
            price = venue.get('price_per_hour', 500)
            if price:
                # 假設最高合理價格為1000，價格越低分數越高
                price_score = max(0, (1000 - price) / 1000) * 0.3
                score += price_score
                factors.append(f"每小時 NT${price:,.0f}")
            
            # 設施因子 (20%)
            facilities = venue.get('facilities', '')
            if facilities:
                facility_count = len(facilities.split(',')) if isinstance(facilities, str) else len(facilities)
                facility_score = min(facility_count / 10, 1.0) * 0.2  # 假設10個設施為滿分
                score += facility_score
                factors.append(f"{facility_count} 項設施")
            
            # 地理位置因子 (10%)
            district = venue.get('district', '')
            popular_districts = ['大安區', '信義區', '中正區']  # 熱門地區
            if district in popular_districts:
                score += 0.1
                factors.append(f"位於熱門地區 ({district})")
            else:
                factors.append(f"位於 {district}")
            
            recommendation_scores.append({
                '場地': venue.get('name', '未知場地'),
                '綜合分數': score * 100,  # 轉換為百分制
                '推薦因子': ' • '.join(factors)
            })
        
        # 排序並顯示推薦
        recommendation_df = pd.DataFrame(recommendation_scores)
        recommendation_df = recommendation_df.sort_values('綜合分數', ascending=False)
        
        for i, (_, venue) in enumerate(recommendation_df.iterrows()):
            if i == 0:
                st.success(f"🥇 **最推薦**: {venue['場地']} (綜合分數: {venue['綜合分數']:.1f})")
            elif i == 1:
                st.info(f"🥈 **次推薦**: {venue['場地']} (綜合分數: {venue['綜合分數']:.1f})")
            elif i == 2:
                st.warning(f"🥉 **第三推薦**: {venue['場地']} (綜合分數: {venue['綜合分數']:.1f})")
            else:
                st.write(f"**{i+1}.** {venue['場地']} (綜合分數: {venue['綜合分數']:.1f})")
            
            st.write(f"   {venue['推薦因子']}")
            st.write("")

else:
    # 提示用戶選擇場地
    st.info("請在側邊欄選擇至少2個場地進行比較")
    
    # 顯示快速選擇選項
    if venues_data is not None and not venues_data.empty:
        st.subheader("🚀 快速選擇")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏀 比較籃球場地", use_container_width=True):
                basketball_venues = venues_data[venues_data['sport_type'] == '籃球'].head(3)
                if not basketball_venues.empty:
                    st.session_state.comparison_venues = basketball_venues['id'].tolist()
                    st.rerun()
        
        with col2:
            if st.button("🏊‍♀️ 比較游泳場地", use_container_width=True):
                swimming_venues = venues_data[venues_data['sport_type'] == '游泳'].head(3)
                if not swimming_venues.empty:
                    st.session_state.comparison_venues = swimming_venues['id'].tolist()
                    st.rerun()
        
        with col3:
            if st.button("🏃‍♂️ 比較綜合場地", use_container_width=True):
                mixed_venues = venues_data[venues_data['sport_type'].isin(['綜合運動', '健身', '多功能'])].head(3)
                if not mixed_venues.empty:
                    st.session_state.comparison_venues = mixed_venues['id'].tolist()
                    st.rerun()
        
        # 顯示場地預覽
        st.subheader("🏟️ 可比較場地預覽")
        
        preview_venues = venues_data.head(6)  # 顯示前6個場地作為預覽
        
        for i in range(0, len(preview_venues), 3):
            cols = st.columns(3)
            for j, (_, venue) in enumerate(preview_venues.iloc[i:i+3].iterrows()):
                with cols[j]:
                    st.markdown(f"**{venue.get('name', '未知場地')}**")
                    st.markdown(f"🏃‍♂️ {venue.get('sport_type', '未知運動')}")
                    st.markdown(f"📍 {venue.get('district', '未知地區')}")
                    if venue.get('rating'):
                        st.markdown(f"⭐ {venue.get('rating'):.1f}/5.0")
                    if venue.get('price_per_hour'):
                        st.markdown(f"💰 NT${venue.get('price_per_hour'):,.0f}/小時")

# 導出功能
if len(st.session_state.comparison_venues) >= 2 and comparison_data:
    st.markdown("---")
    st.subheader("📤 導出比較結果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 生成比較報告", use_container_width=True):
            # 生成比較報告的CSV
            comparison_df = pd.DataFrame(comparison_data)
            csv_data = comparison_df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="下載比較報告 (CSV)",
                data=csv_data,
                file_name=f"venue_comparison_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🔗 分享比較連結", use_container_width=True):
            # 生成分享連結（這裡只是示例，實際需要實現URL參數功能）
            venue_ids = ','.join(map(str, st.session_state.comparison_venues))
            share_url = f"?compare={venue_ids}"
            st.code(f"分享連結: {share_url}", language="text")
            st.info("複製此連結可直接分享您的比較結果")