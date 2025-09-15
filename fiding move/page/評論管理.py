import streamlit as st
import pandas as pd
from utils.data_manager import DataManager

st.set_page_config(
    page_title="評論管理 - 台北運動場地搜尋引擎",
    page_icon="👨‍💼",
    layout="wide"
)

# 確保 session state 已初始化
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

st.title("👨‍💼 評論管理系統")
st.markdown("管理和審核用戶提交的場地評論")

# 管理員密碼保護
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.subheader("🔐 管理員登入")
    
    with st.form("admin_login"):
        admin_password = st.text_input("管理員密碼", type="password", placeholder="請輸入管理員密碼")
        
        if st.form_submit_button("登入"):
            # 使用環境變數設定管理員密碼
            import os
            admin_secret = os.getenv("ADMIN_PASSWORD", "replit_admin_2024")
            
            if admin_password == admin_secret:
                st.session_state.admin_authenticated = True
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("密碼錯誤，請重新輸入。")
    
    st.info("💡 請聯繫管理員取得登入密碼")
    st.stop()

# 管理員介面
tab1, tab2, tab3 = st.tabs(["⏳ 待審核評論", "✅ 已審核評論", "📊 評論統計"])

with tab1:
    st.subheader("待審核評論")
    
    try:
        # 獲取所有待審核的評論
        if hasattr(st.session_state.data_manager, 'engine') and st.session_state.data_manager.engine:
            query = """
            SELECT r.id, r.venue_id, v.name as venue_name, r.user_name, 
                   r.rating, r.comment, r.created_at
            FROM reviews r
            JOIN venues v ON r.venue_id = v.id
            WHERE r.status = 'pending'
            ORDER BY r.created_at DESC
            """
            
            pending_reviews = pd.read_sql(query, st.session_state.data_manager.engine)
            
            if not pending_reviews.empty:
                st.info(f"共有 {len(pending_reviews)} 則待審核評論")
                
                for idx, review in pending_reviews.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**場地:** {review['venue_name']}")
                            st.markdown(f"**用戶:** {review['user_name']}")
                            st.markdown(f"**評分:** {'⭐' * review['rating']} ({review['rating']}/5)")
                            st.markdown(f"**評論:** {review['comment']}")
                            st.caption(f"提交時間: {review['created_at']}")
                        
                        with col2:
                            if st.button(f"✅ 批准", key=f"approve_{review['id']}"):
                                # 批准評論
                                try:
                                    with st.session_state.data_manager.engine.connect() as conn:
                                        from sqlalchemy import text
                                        update_query = text("""
                                        UPDATE reviews 
                                        SET status = 'approved', updated_at = NOW()
                                        WHERE id = :review_id
                                        """)
                                        conn.execute(update_query, {'review_id': review['id']})
                                        conn.commit()
                                    
                                    st.success(f"評論 #{review['id']} 已批准！")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"批准評論失敗: {e}")
                        
                        with col3:
                            if st.button(f"❌ 拒絕", key=f"reject_{review['id']}"):
                                # 拒絕評論
                                try:
                                    with st.session_state.data_manager.engine.connect() as conn:
                                        from sqlalchemy import text
                                        update_query = text("""
                                        UPDATE reviews 
                                        SET status = 'rejected', updated_at = NOW()
                                        WHERE id = :review_id
                                        """)
                                        conn.execute(update_query, {'review_id': review['id']})
                                        conn.commit()
                                    
                                    st.warning(f"評論 #{review['id']} 已拒絕！")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"拒絕評論失敗: {e}")
                        
                        st.divider()
            else:
                st.success("目前沒有待審核的評論！")
        else:
            st.error("無法連接到資料庫")
            
    except Exception as e:
        st.error(f"載入待審核評論時發生錯誤: {e}")

with tab2:
    st.subheader("已審核評論")
    
    try:
        if hasattr(st.session_state.data_manager, 'engine') and st.session_state.data_manager.engine:
            # 狀態篩選
            status_filter = st.selectbox(
                "篩選狀態",
                ["approved", "rejected"],
                format_func=lambda x: "已批准" if x == "approved" else "已拒絕"
            )
            
            query = """
            SELECT r.id, r.venue_id, v.name as venue_name, r.user_name, 
                   r.rating, r.comment, r.status, r.created_at, r.updated_at
            FROM reviews r
            JOIN venues v ON r.venue_id = v.id
            WHERE r.status = %s
            ORDER BY r.updated_at DESC
            LIMIT 50
            """
            
            reviewed_comments = pd.read_sql(query, st.session_state.data_manager.engine, params=[status_filter])
            
            if not reviewed_comments.empty:
                st.info(f"顯示最近 {len(reviewed_comments)} 則{('已批准' if status_filter == 'approved' else '已拒絕')}評論")
                
                for idx, review in reviewed_comments.iterrows():
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.markdown(f"**場地:** {review['venue_name']}")
                            st.markdown(f"**用戶:** {review['user_name']}")
                            st.markdown(f"**評分:** {'⭐' * review['rating']} ({review['rating']}/5)")
                            st.markdown(f"**評論:** {review['comment']}")
                            st.caption(f"提交: {review['created_at']} | 審核: {review['updated_at']}")
                        
                        with col2:
                            status_color = "🟢" if review['status'] == 'approved' else "🔴"
                            status_text = "已批准" if review['status'] == 'approved' else "已拒絕"
                            st.markdown(f"{status_color} **{status_text}**")
                            st.caption(f"ID: {review['id']}")
                        
                        st.divider()
            else:
                st.info(f"沒有{('已批准' if status_filter == 'approved' else '已拒絕')}的評論")
        else:
            st.error("無法連接到資料庫")
            
    except Exception as e:
        st.error(f"載入已審核評論時發生錯誤: {e}")

with tab3:
    st.subheader("評論統計")
    
    try:
        if hasattr(st.session_state.data_manager, 'engine') and st.session_state.data_manager.engine:
            # 基本統計
            stats_query = """
            SELECT 
                COUNT(*) as total_reviews,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
                ROUND(AVG(rating), 2) as avg_rating
            FROM reviews
            """
            
            stats = pd.read_sql(stats_query, st.session_state.data_manager.engine)
            
            if not stats.empty:
                stat_row = stats.iloc[0]
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("總評論數", int(stat_row['total_reviews']))
                
                with col2:
                    st.metric("待審核", int(stat_row['pending_count']))
                
                with col3:
                    st.metric("已批准", int(stat_row['approved_count']))
                
                with col4:
                    st.metric("已拒絕", int(stat_row['rejected_count']))
                
                with col5:
                    avg_rating = stat_row['avg_rating']
                    st.metric("平均評分", f"{avg_rating}/5.0" if avg_rating else "N/A")
            
            # 場地評論統計
            st.subheader("各場地評論統計")
            
            venue_stats_query = """
            SELECT v.name, v.district,
                   COUNT(r.id) as review_count,
                   COUNT(CASE WHEN r.status = 'approved' THEN 1 END) as approved_reviews,
                   ROUND(AVG(CASE WHEN r.status = 'approved' THEN r.rating END), 2) as avg_approved_rating
            FROM venues v
            LEFT JOIN reviews r ON v.id = r.venue_id
            GROUP BY v.id, v.name, v.district
            ORDER BY review_count DESC
            """
            
            venue_stats = pd.read_sql(venue_stats_query, st.session_state.data_manager.engine)
            
            if not venue_stats.empty:
                st.dataframe(
                    venue_stats.rename(columns={
                        'name': '場地名稱',
                        'district': '地區',
                        'review_count': '總評論數',
                        'approved_reviews': '已批准評論',
                        'avg_approved_rating': '平均評分'
                    }),
                    use_container_width=True
                )
            else:
                st.info("暫無場地評論統計資料")
        else:
            st.error("無法連接到資料庫")
            
    except Exception as e:
        st.error(f"載入評論統計時發生錯誤: {e}")

# 快速操作
st.markdown("---")
st.subheader("🚀 快速操作")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 重新載入數據", use_container_width=True):
        st.rerun()

with col2:
    if st.button("🚪 登出", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()
        