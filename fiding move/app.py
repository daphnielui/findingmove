import streamlit as st
import pandas as pd
import time
import random
from utils.data_manager import DataManager
from utils.recommendation_engine import RecommendationEngine
from utils.weather_manager import WeatherManager
import os

# 設定頁面配置
st.set_page_config(
    page_title="台北運動場地搜尋引擎",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定義灰藍色主題CSS
st.markdown("""
<style>
    /* 主背景顏色 */
    .stApp {
        background-color: #f8fafb;
    }
    
    /* 區塊背景 */
    .block-container {
        background-color: #ecf0f3;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 主標題區域 */
    .main-header {
        background: linear-gradient(135deg, #a6bee2 0%, #8fadd9 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .location-selector-inline {
        background: rgba(255,255,255,0.2);
        border-radius: 10px;
        padding: 10px 15px;
        min-width: 200px;
    }
    
    .location-selector-inline .stSelectbox > div > div {
        background-color: rgba(255,255,255,0.9);
        border-radius: 8px;
    }
    
    /* 天氣區塊特殊樣式 */
    .weather-block {
        background: linear-gradient(135deg, #a6bee2 0%, #8fadd9 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* 搜尋區塊 */
    .search-block {
        background-color: #ecf0f3;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    
    /* 推薦區塊 */
    .recommend-block {
        background-color: #ecf0f3;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    
    /* 運動icon旋轉動畫 */
    @keyframes rotation {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* 動態運動icon */
    .rotating-icon {
        animation: rotation 3s infinite linear;
        display: inline-block;
        font-size: 24px;
    }
    
    @keyframes rotation {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* 應用啟動動畫覆蓋層 */
    .app-startup-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: #a6bee2;
        z-index: 99999;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        color: white;
        font-family: 'Arial', sans-serif;
    }
    
    .startup-logo-container {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .app-startup-overlay.hidden {
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.8s ease-out, visibility 0.8s ease-out;
    }
    
    /* 啟動logo動畫 */
    .startup-logo {
        max-width: 90vw;
        max-height: 90vh;
        width: auto;
        height: auto;
        animation: logoFadeIn 1.5s ease-out;
        position: relative;
    }
    
    @keyframes logoFadeIn {
        0% {
            opacity: 0;
            transform: scale(0.8) translateY(20px);
        }
        100% {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }
    
    /* 啟動標題 - 放置在頁面 2/3 位置 */
    .startup-title-compact {
        position: fixed;
        top: calc(66.67vh - 1.5cm);
        left: 50%;
        transform: translateX(-50%);
        font-size: 1em;
        font-weight: normal;
        text-align: center;
        opacity: 0.9;
        white-space: nowrap;
        font-family: 'uoqmunthenkhung', 'Noto Sans TC', 'Microsoft JhengHei', 'PingFang TC', 'Heiti TC', sans-serif;
        letter-spacing: 2px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* 字符弹跳动画 - 单个字符依次跳动 */
    .bounce-char {
        display: inline-block;
        animation: charBounceOnce 0.6s ease-in-out;
        animation-fill-mode: both;
    }
    
    @keyframes charBounceOnce {
        0% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-0.2cm);
        }
        100% {
            transform: translateY(0);
        }
    }
    
    /* 为每个字符设置不同的动画延迟 - 依次跳动 */
    .bounce-char:nth-child(1) { animation-delay: 0s; }
    .bounce-char:nth-child(2) { animation-delay: 0.6s; }
    .bounce-char:nth-child(3) { animation-delay: 1.2s; }
    .bounce-char:nth-child(4) { animation-delay: 1.8s; }
    .bounce-char:nth-child(5) { animation-delay: 2.4s; }
    .bounce-char:nth-child(6) { animation-delay: 3.0s; }
    .bounce-char:nth-child(7) { animation-delay: 3.6s; }
    .bounce-char:nth-child(8) { animation-delay: 4.2s; }
    .bounce-char:nth-child(9) { animation-delay: 4.8s; }
    .bounce-char:nth-child(10) { animation-delay: 5.4s; }
    .bounce-char:nth-child(11) { animation-delay: 6.0s; }
    .bounce-char:nth-child(12) { animation-delay: 6.6s; }
    .bounce-char:nth-child(13) { animation-delay: 7.2s; }
    .bounce-char:nth-child(14) { animation-delay: 7.8s; }
    .bounce-char:nth-child(15) { animation-delay: 8.4s; }
    .bounce-char:nth-child(16) { animation-delay: 9.0s; }
    .bounce-char:nth-child(17) { animation-delay: 9.6s; }
    .bounce-char:nth-child(18) { animation-delay: 10.2s; }
    .bounce-char:nth-child(19) { animation-delay: 10.8s; }
    .bounce-char:nth-child(20) { animation-delay: 11.4s; }
    .bounce-char:nth-child(21) { animation-delay: 12.0s; }
    .bounce-char:nth-child(22) { animation-delay: 12.6s; }
    .bounce-char:nth-child(23) { animation-delay: 13.2s; }
    .bounce-char:nth-child(24) { animation-delay: 13.8s; }
    
    @keyframes titleSlideUp {
        0% {
            opacity: 0;
            transform: translateY(30px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* 載入進度動畫 */
    .startup-loading {
        display: flex;
        align-items: center;
        gap: 15px;
        animation: loadingFadeIn 2.2s ease-out 0.9s both;
    }
    
    .loading-text {
        font-size: 1.1em;
        margin-right: 10px;
    }
    
    .loading-dots {
        display: flex;
        gap: 5px;
    }
    
    .loading-dot {
        width: 8px;
        height: 8px;
        background-color: white;
        border-radius: 50%;
        animation: dotPulse 1.4s ease-in-out infinite;
    }
    
    .loading-dot:nth-child(1) { animation-delay: 0s; }
    .loading-dot:nth-child(2) { animation-delay: 0.2s; }
    .loading-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes dotPulse {
        0%, 60%, 100% {
            opacity: 0.3;
            transform: scale(0.8);
        }
        30% {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes loadingFadeIn {
        0% {
            opacity: 0;
            transform: translateY(20px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* 轉場動畫覆蓋層 */
    .page-transition-overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(245, 245, 245, 0.95);
        z-index: 9999;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    
    .page-transition-overlay.show {
        display: flex;
    }
    
    /* 載入動畫 */
    .loading-spinner {
        width: 80px;
        height: 80px;
        border: 8px solid #e8e8e8;
        border-top: 8px solid #9e9e9e;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* 輸入欄樣式 */
    .stTextInput > div > div > input {
        background-color: #f0f0f0;
        border: 2px solid #9e9e9e;
        border-radius: 25px;
        padding: 10px 20px;
        font-size: 16px;
    }
    
    /* 場館卡片樣式 */
    .venue-card {
        background-color: #f8f8f8;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #9e9e9e;
    }
    
    /* 標題樣式 */
    h1, h2, h3 {
        color: #424242;
    }
    
    /* 按鈕點擊效果 */
    .stButton > button {
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ===== 启动页面逻辑 =====

# 初始化认证状态
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

if 'data_ready' not in st.session_state:
    st.session_state.data_ready = False

# 如果尚未认证，显示启动页面和数据载入
if not st.session_state.is_authenticated:
    # 显示启动动画
    st.markdown('<div id="appStartup" class="app-startup-overlay" style="display: flex !important;">', unsafe_allow_html=True)
    
    # 显示启动logo
    with open('attached_assets/FM logo_1757941352267.jpg', 'rb') as f:
        logo_data = f.read()
    
    # 编码为base64
    import base64
    logo_base64 = base64.b64encode(logo_data).decode()
    
    st.markdown(f'''
    <img src="data:image/jpeg;base64,{logo_base64}" class="startup-logo" alt="Finding Move Logo" style="max-width: 90vw; max-height: 50vh; width: auto; height: auto;">
    <div class="startup-title-compact">
        <span class="bounce-char">尋</span><span class="bounce-char">地</span><span class="bounce-char">寳</span><span class="bounce-char"> </span><span class="bounce-char">-</span><span class="bounce-char"> </span><span class="bounce-char">根</span><span class="bounce-char">據</span><span class="bounce-char">您</span><span class="bounce-char">的</span><span class="bounce-char">節</span><span class="bounce-char">奏</span><span class="bounce-char">，</span><span class="bounce-char">找</span><span class="bounce-char">到</span><span class="bounce-char">最</span><span class="bounce-char">適</span><span class="bounce-char">合</span><span class="bounce-char">您</span><span class="bounce-char">的</span><span class="bounce-char">運</span><span class="bounce-char">動</span><span class="bounce-char">場</span><span class="bounce-char">所</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # 显示进度条和数据载入
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 模拟数据载入过程
    status_text.text("正在初始化系统...")
    progress_bar.progress(20)
    time.sleep(0.5)
    
    status_text.text("載入場地資料...")
    progress_bar.progress(40)
    # 初始化数据管理器
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    time.sleep(0.5)
    
    status_text.text("載入天氣資料...")
    progress_bar.progress(60)
    # 初始化天气管理器
    if 'weather_manager' not in st.session_state:
        st.session_state.weather_manager = WeatherManager()
    time.sleep(0.5)
    
    status_text.text("建立推薦引擎...")
    progress_bar.progress(80)
    # 初始化推荐引擎
    if 'recommendation_engine' not in st.session_state:
        st.session_state.recommendation_engine = RecommendationEngine()
    time.sleep(0.5)
    
    status_text.text("系統準備完成！")
    progress_bar.progress(100)
    time.sleep(0.5)
    
    # 初始化其他session state
    if 'current_sport_icon' not in st.session_state:
        st.session_state.current_sport_icon = 0
    if 'selected_district' not in st.session_state:
        st.session_state.selected_district = '中正區'
    if 'user_location' not in st.session_state:
        st.session_state.user_location = None
    
    # 设置认证标志
    st.session_state.is_authenticated = True
    st.session_state.data_ready = True
    
    # 自动跳转到主页面
    st.markdown('</div>', unsafe_allow_html=True)
    time.sleep(0.5)
    st.switch_page("pages/1_🔍_場地搜尋.py")

else:
    # 如果已认证，直接跳转到主页面
    st.switch_page("pages/1_🔍_場地搜尋.py")