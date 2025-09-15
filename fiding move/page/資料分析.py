import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_manager import DataManager

st.set_page_config(
    page_title="資料分析 - 台北運動場地搜尋引擎",
    page_icon="📊",
    layout="wide"
)

# 確保 session state 已初始化
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

st.title("📊 場地資料分析")
st.markdown("深入了解台北市運動場地的分布、趨勢和統計資訊")

# 側邊欄控制
with st.sidebar:
    st.header("📊 分析設定")
    
    # 分析時間範圍（模擬）
    analysis_period = st.selectbox(
        "分析期間",
        ["最近一週", "最近一個月", "最近三個月", "最近一年", "全部時間"],
        index=2,
        key="analysis_period"
    )
    
    # 分析維度選擇
    analysis_dimensions = st.multiselect(
        "分析維度",
        ["運動類型", "地區分布", "價格分析", "評分分析", "設施分析", "使用趨勢"],
        default=["運動類型", "地區分布", "價格分析"],
        key="analysis_dims"
    )
    
    # 資料視覺化類型
    viz_type = st.selectbox(
        "視覺化類型",
        ["互動式圖表", "靜態圖表", "儀表板模式"],
        key="viz_type"
    )

# 獲取場地資料
all_venues = st.session_state.data_manager.get_all_venues()

if all_venues is not None and not all_venues.empty:
    # 總覽統計
    st.subheader("📈 總覽統計")
    
    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
    
    with overview_col1:
        total_venues = len(all_venues)
        st.metric("總場地數", total_venues)
    
    with overview_col2:
        if 'sport_type' in all_venues.columns:
            unique_sports = all_venues['sport_type'].nunique()
            st.metric("運動類型數", unique_sports)
        else:
            st.metric("運動類型數", "N/A")
    
    with overview_col3:
        if 'district' in all_venues.columns:
            unique_districts = all_venues['district'].nunique()
            st.metric("服務地區數", unique_districts)
        else:
            st.metric("服務地區數", "N/A")
    
    with overview_col4:
        if 'price_per_hour' in all_venues.columns:
            avg_price = all_venues['price_per_hour'].mean()
            st.metric("平均價格", f"NT${avg_price:.0f}/hr" if pd.notna(avg_price) else "N/A")
        else:
            st.metric("平均價格", "N/A")
    
    # 分析標籤頁
    tab1, tab2, tab3, tab4 = st.tabs(["🏃‍♂️ 運動類型分析", "📍 地區分析", "💰 價格分析", "⭐ 評分與品質分析"])
    
    with tab1:
        if "運動類型" in analysis_dimensions and 'sport_type' in all_venues.columns:
            st.subheader("🏃‍♂️ 運動類型分布分析")
            
            # 運動類型分布圓餅圖
            sport_counts = all_venues['sport_type'].value_counts()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_pie = px.pie(
                    values=sport_counts.values,
                    names=sport_counts.index,
                    title="運動類型場地數量分布",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.markdown("**📊 統計資訊:**")
                for sport, count in sport_counts.head(10).items():
                    percentage = (count / total_venues) * 100
                    st.markdown(f"• **{sport}**: {count} 個場地 ({percentage:.1f}%)")
            
            # 運動類型與價格關係
            if 'price_per_hour' in all_venues.columns:
                st.subheader("💰 各運動類型平均價格")
                
                sport_price_avg = all_venues.groupby('sport_type')['price_per_hour'].agg(['mean', 'count']).reset_index()
                sport_price_avg = sport_price_avg[sport_price_avg['count'] >= 3]  # 至少3個場地才顯示
                
                fig_price = px.bar(
                    sport_price_avg,
                    x='sport_type',
                    y='mean',
                    title="各運動類型平均價格比較",
                    labels={'mean': '平均價格 (NT$/hr)', 'sport_type': '運動類型'},
                    color='mean',
                    color_continuous_scale='RdYlBu_r'
                )
                fig_price.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_price, use_container_width=True)
        
        else:
            st.info("運動類型資料不可用或未選擇此分析維度")
    
    with tab2:
        if "地區分布" in analysis_dimensions and 'district' in all_venues.columns:
            st.subheader("📍 地區分布分析")
            
            # 地區場地數量分布
            district_counts = all_venues['district'].value_counts()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig_district = px.bar(
                    x=district_counts.index,
                    y=district_counts.values,
                    title="各地區場地數量分布",
                    labels={'x': '地區', 'y': '場地數量'},
                    color=district_counts.values,
                    color_continuous_scale='Blues'
                )
                fig_district.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_district, use_container_width=True)
            
            with col2:
                st.markdown("**📊 地區排行:**")
                for i, (district, count) in enumerate(district_counts.head(10).items(), 1):
                    st.markdown(f"{i}. **{district}**: {count} 個場地")
            
            # 地區與運動類型交叉分析
            if 'sport_type' in all_venues.columns:
                st.subheader("🎯 地區運動類型分布熱力圖")
                
                # 創建交叉表
                cross_tab = pd.crosstab(all_venues['district'], all_venues['sport_type'])
                
                # 只顯示主要地區和運動類型
                top_districts = district_counts.head(8).index
                top_sports = all_venues['sport_type'].value_counts().head(8).index
                
                filtered_cross_tab = cross_tab.loc[top_districts, top_sports]
                
                fig_heatmap = px.imshow(
                    filtered_cross_tab.values,
                    x=filtered_cross_tab.columns,
                    y=filtered_cross_tab.index,
                    title="地區 × 運動類型分布熱力圖",
                    color_continuous_scale='Blues',
                    aspect='auto'
                )
                fig_heatmap.update_layout(
                    xaxis_title="運動類型",
                    yaxis_title="地區"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
        else:
            st.info("地區資料不可用或未選擇此分析維度")
    
    with tab3:
        if "價格分析" in analysis_dimensions and 'price_per_hour' in all_venues.columns:
            st.subheader("💰 價格分布分析")
            
            # 過濾有效價格資料
            price_data = all_venues[all_venues['price_per_hour'].notna() & (all_venues['price_per_hour'] > 0)]
            
            if not price_data.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 價格分布直方圖
                    fig_hist = px.histogram(
                        price_data,
                        x='price_per_hour',
                        nbins=20,
                        title="場地價格分布",
                        labels={'price_per_hour': '每小時價格 (NT$)', 'count': '場地數量'},
                        color_discrete_sequence=['#1f77b4']
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    # 價格統計
                    price_stats = price_data['price_per_hour'].describe()
                    
                    st.markdown("**📊 價格統計:**")
                    st.markdown(f"• **平均價格**: NT${price_stats['mean']:.0f}/hr")
                    st.markdown(f"• **中位數價格**: NT${price_stats['50%']:.0f}/hr")
                    st.markdown(f"• **最低價格**: NT${price_stats['min']:.0f}/hr")
                    st.markdown(f"• **最高價格**: NT${price_stats['max']:.0f}/hr")
                    st.markdown(f"• **標準差**: NT${price_stats['std']:.0f}")
                
                # 價格區間分析
                st.subheader("📊 價格區間分布")
                
                # 定義價格區間
                price_bins = [0, 200, 400, 600, 800, 1000, float('inf')]
                price_labels = ['<200', '200-400', '400-600', '600-800', '800-1000', '>1000']
                
                price_data['price_range'] = pd.cut(
                    price_data['price_per_hour'],
                    bins=price_bins,
                    labels=price_labels,
                    include_lowest=True
                )
                
                price_range_counts = price_data['price_range'].value_counts().sort_index()
                
                fig_range = px.bar(
                    x=price_range_counts.index,
                    y=price_range_counts.values,
                    title="價格區間場地分布",
                    labels={'x': '價格區間 (NT$/hr)', 'y': '場地數量'},
                    color=price_range_counts.values,
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig_range, use_container_width=True)
                
                # 價格與評分關係
                if 'rating' in price_data.columns:
                    st.subheader("⭐ 價格與評分關係")
                    
                    rating_data = price_data[price_data['rating'].notna()]
                    
                    if not rating_data.empty:
                        fig_scatter = px.scatter(
                            rating_data,
                            x='price_per_hour',
                            y='rating',
                            title="價格 vs 評分散點圖",
                            labels={'price_per_hour': '每小時價格 (NT$)', 'rating': '評分'},
                            color='sport_type' if 'sport_type' in rating_data.columns else None,
                            size='rating',
                            hover_data=['name'] if 'name' in rating_data.columns else None
                        )
                        
                        # 添加趨勢線
                        fig_scatter.add_trace(
                            go.Scatter(
                                x=rating_data['price_per_hour'],
                                y=rating_data['rating'],
                                mode='lines',
                                name='趨勢線',
                                line=dict(dash='dash', color='red')
                            )
                        )
                        
                        st.plotly_chart(fig_scatter, use_container_width=True)
            
            else:
                st.warning("沒有有效的價格資料可供分析")
        
        else:
            st.info("價格資料不可用或未選擇此分析維度")
    
    with tab4:
        if "評分分析" in analysis_dimensions and 'rating' in all_venues.columns:
            st.subheader("⭐ 評分與品質分析")
            
            # 過濾有效評分資料
            rating_data = all_venues[all_venues['rating'].notna() & (all_venues['rating'] > 0)]
            
            if not rating_data.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 評分分布
                    fig_rating_dist = px.histogram(
                        rating_data,
                        x='rating',
                        nbins=20,
                        title="場地評分分布",
                        labels={'rating': '評分', 'count': '場地數量'},
                        color_discrete_sequence=['#ff7f0e']
                    )
                    st.plotly_chart(fig_rating_dist, use_container_width=True)
                
                with col2:
                    # 評分統計
                    rating_stats = rating_data['rating'].describe()
                    
                    st.markdown("**⭐ 評分統計:**")
                    st.markdown(f"• **平均評分**: {rating_stats['mean']:.2f}/5.0")
                    st.markdown(f"• **中位數評分**: {rating_stats['50%']:.2f}/5.0")
                    st.markdown(f"• **最低評分**: {rating_stats['min']:.2f}/5.0")
                    st.markdown(f"• **最高評分**: {rating_stats['max']:.2f}/5.0")
                    
                    # 評分等級分布
                    excellent = len(rating_data[rating_data['rating'] >= 4.5])
                    good = len(rating_data[(rating_data['rating'] >= 4.0) & (rating_data['rating'] < 4.5)])
                    average = len(rating_data[(rating_data['rating'] >= 3.0) & (rating_data['rating'] < 4.0)])
                    poor = len(rating_data[rating_data['rating'] < 3.0])
                    
                    st.markdown(f"• **優秀** (≥4.5): {excellent} 個場地")
                    st.markdown(f"• **良好** (4.0-4.5): {good} 個場地")
                    st.markdown(f"• **普通** (3.0-4.0): {average} 個場地")
                    st.markdown(f"• **需改善** (<3.0): {poor} 個場地")
                
                # 各運動類型平均評分
                if 'sport_type' in rating_data.columns:
                    st.subheader("🏃‍♂️ 各運動類型平均評分")
                    
                    sport_rating_avg = rating_data.groupby('sport_type')['rating'].agg(['mean', 'count']).reset_index()
                    sport_rating_avg = sport_rating_avg[sport_rating_avg['count'] >= 3]  # 至少3個場地
                    sport_rating_avg = sport_rating_avg.sort_values('mean', ascending=False)
                    
                    fig_sport_rating = px.bar(
                        sport_rating_avg,
                        x='sport_type',
                        y='mean',
                        title="各運動類型平均評分排行",
                        labels={'mean': '平均評分', 'sport_type': '運動類型'},
                        color='mean',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_sport_rating.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_sport_rating, use_container_width=True)
                
                # 各地區平均評分
                if 'district' in rating_data.columns:
                    st.subheader("📍 各地區平均評分")
                    
                    district_rating_avg = rating_data.groupby('district')['rating'].agg(['mean', 'count']).reset_index()
                    district_rating_avg = district_rating_avg[district_rating_avg['count'] >= 3]
                    district_rating_avg = district_rating_avg.sort_values('mean', ascending=False)
                    
                    fig_district_rating = px.bar(
                        district_rating_avg,
                        x='district',
                        y='mean',
                        title="各地區平均評分排行",
                        labels={'mean': '平均評分', 'district': '地區'},
                        color='mean',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_district_rating.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_district_rating, use_container_width=True)
            
            else:
                st.warning("沒有有效的評分資料可供分析")
        
        else:
            st.info("評分資料不可用或未選擇此分析維度")
    
    # 高級分析
    st.markdown("---")
    st.subheader("🔬 進階分析")
    
    advanced_col1, advanced_col2 = st.columns(2)
    
    with advanced_col1:
        # 相關性分析
        if 'price_per_hour' in all_venues.columns and 'rating' in all_venues.columns:
            st.markdown("**📊 變數相關性分析**")
            
            numeric_columns = ['price_per_hour', 'rating']
            available_numeric = [col for col in numeric_columns if col in all_venues.columns]
            
            if len(available_numeric) >= 2:
                correlation_data = all_venues[available_numeric].corr()
                
                fig_corr = px.imshow(
                    correlation_data.values,
                    x=correlation_data.columns,
                    y=correlation_data.index,
                    title="變數相關性熱力圖",
                    color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1
                )
                
                # 添加數值標籤
                for i in range(len(correlation_data.columns)):
                    for j in range(len(correlation_data.index)):
                        fig_corr.add_annotation(
                            x=correlation_data.columns[i],
                            y=correlation_data.index[j],
                            text=f"{correlation_data.iloc[j, i]:.2f}",
                            showarrow=False,
                            font_color="white" if abs(correlation_data.iloc[j, i]) > 0.5 else "black"
                        )
                
                st.plotly_chart(fig_corr, use_container_width=True)
    
    with advanced_col2:
        # 資料品質報告
        st.markdown("**📋 資料品質報告**")
        
        total_records = len(all_venues)
        quality_report = {}
        
        for column in all_venues.columns:
            non_null_count = all_venues[column].notna().sum()
            completeness = (non_null_count / total_records) * 100
            quality_report[column] = completeness
        
        # 顯示資料完整性
        quality_df = pd.DataFrame(list(quality_report.items()), columns=['欄位', '完整性(%)'])
        quality_df = quality_df.sort_values('完整性(%)', ascending=False)
        
        st.dataframe(quality_df, use_container_width=True)
        
        # 資料品質摘要
        avg_completeness = quality_df['完整性(%)'].mean()
        
        if avg_completeness >= 90:
            quality_status = "🟢 優秀"
        elif avg_completeness >= 70:
            quality_status = "🟡 良好"
        else:
            quality_status = "🔴 需要改善"
        
        st.metric("整體資料品質", f"{avg_completeness:.1f}%", delta=quality_status)

else:
    st.error("無法載入場地資料進行分析。請檢查資料來源或稍後再試。")
    
    st.markdown("""
    ### 📊 分析功能說明
    
    當資料可用時，此頁面將提供：
    
    - **🏃‍♂️ 運動類型分析**: 各類運動場地的分布和價格比較
    - **📍 地區分析**: 台北各地區場地密度和類型分布
    - **💰 價格分析**: 價格分布、區間分析和價格與品質關係
    - **⭐ 評分分析**: 場地品質評估和各維度表現
    - **🔬 進階分析**: 變數相關性和資料品質報告
    """)
