import pandas as pd
import numpy as np
import os
from typing import List, Optional, Dict, Any
import random
import streamlit as st

@st.cache_data
def load_venues_data():
    """
    使用缓存载入场地数据，避免重复读取
    """
    try:
        # 讀取CSV檔案
        csv_path = "attached_assets/finding move - main (1)_1757915289189.csv"
        
        if not os.path.exists(csv_path):
            print(f"CSV檔案不存在: {csv_path}")
            return pd.DataFrame()
        
        # 讀取CSV，跳過前面的標題行
        raw_data = pd.read_csv(csv_path, encoding='utf-8', skiprows=5)
        
        # 清理欄位名稱
        raw_data.columns = [
            'name', 'district', 'price_range', 'sport_type', 'opening_hours',
            'facilities', 'venue_scale', 'courses', 'other', 'website',
            'address', 'contact_phone', 'photos'
        ]
        
        # 過濾掉空的場地名稱
        raw_data = raw_data.dropna(subset=['name'])
        raw_data = raw_data[raw_data['name'].str.strip() != '']
        
        # 建立標準化的資料結構
        venues_list = []
        
        for idx, row in raw_data.iterrows():
            venue = {
                'id': idx + 1,
                'name': str(row['name']).strip() if pd.notna(row['name']) else '',
                'district': str(row['district']).strip() if pd.notna(row['district']) else '',
                'address': str(row['address']).strip() if pd.notna(row['address']) else '',
                'sport_type': DataManager._normalize_sport_type_static(row['sport_type']),
                'price_per_hour': DataManager._extract_price_static(row['price_range']),
                'rating': round(random.uniform(3.5, 5.0), 1),  # 模擬評分
                'facilities': DataManager._normalize_facilities_static(row['facilities']),
                'description': str(row['other']).strip() if pd.notna(row['other']) else '',
                'contact_phone': str(row['contact_phone']).strip() if pd.notna(row['contact_phone']) else '',
                'opening_hours': str(row['opening_hours']).strip() if pd.notna(row['opening_hours']) else '',
                'website': str(row['website']).strip() if pd.notna(row['website']) else '',
                'venue_scale': str(row['venue_scale']).strip() if pd.notna(row['venue_scale']) else '',
                'courses': str(row['courses']).strip() if pd.notna(row['courses']) else '',
                'photos': str(row['photos']).strip() if pd.notna(row['photos']) else '',
                'latitude': DataManager._get_district_coordinates_static(row['district'])[0],
                'longitude': DataManager._get_district_coordinates_static(row['district'])[1]
            }
            venues_list.append(venue)
        
        # 轉換為DataFrame
        venues_data = pd.DataFrame(venues_list)
        print(f"✅ 成功載入 {len(venues_data)} 筆場地資料")
        return venues_data
        
    except Exception as e:
        print(f"❌ 載入場地資料時發生錯誤: {e}")
        return pd.DataFrame()

class DataManager:
    """
    資料管理類別，負責處理場地資料的載入、篩選和搜尋功能
    從CSV檔案讀取台北運動場地資料，使用缓存优化性能
    """
    
    def __init__(self):
        # 使用缓存函数载入数据
        self.venues_data = load_venues_data()
        self.sport_types = []
        self.districts = []
        self.facilities = []
        self._extract_metadata()
    
    @staticmethod
    def _normalize_sport_type_static(sport_type):
        """标准化运动类型 - 静态方法"""
        if pd.isna(sport_type) or sport_type == '':
            return '綜合運動'
        
        sport_type = str(sport_type).strip()
        sport_mapping = {
            '羽球': '羽毛球', '羽毛球': '羽毛球', '游泳': '游泳',
            '健身': '健身', '重訓': '健身', '有氧': '有氧運動',
            '瑜珈': '瑜伽', '瑜伽': '瑜伽', '球類': '球類運動',
            '籃球': '籃球', '足球': '足球', '網球': '網球',
            '桌球': '桌球', '撞球': '撞球', '排球': '排球',
            '戶外運動': '戶外運動'
        }
        
        for key, value in sport_mapping.items():
            if key in sport_type:
                return value
        return sport_type if sport_type else '綜合運動'
    
    @staticmethod
    def _extract_price_static(price_range):
        """从价格区间提取平均价格 - 静态方法"""
        if pd.isna(price_range) or price_range == '':
            return random.randint(100, 500)
        
        price_str = str(price_range).strip()
        if '0-200' in price_str:
            return 150
        elif '200-500' in price_str:
            return 350
        elif '500以上' in price_str:
            return 700
        else:
            return random.randint(200, 400)
    
    @staticmethod
    def _normalize_facilities_static(facilities):
        """标准化设施信息 - 静态方法"""
        if pd.isna(facilities) or facilities == '':
            return '基本設施'
        
        facilities_str = str(facilities).strip()
        facility_mapping = {
            '淋浴間': '淋浴間', '置物櫃': '置物櫃', '停車場': '停車場',
            'Wi-Fi': 'Wi-Fi', 'WiFi': 'Wi-Fi', '無障礙設施': '無障礙設施',
            '性別友善設施': '性別友善設施', '寵物友善': '寵物友善', '女性專用': '女性專用'
        }
        
        normalized_facilities = []
        for key, value in facility_mapping.items():
            if key in facilities_str:
                normalized_facilities.append(value)
        
        return '/'.join(normalized_facilities) if normalized_facilities else facilities_str
    
    @staticmethod
    def _get_district_coordinates_static(district):
        """取得地区坐标 - 静态方法"""
        district_coords = {
            '士林區': (25.0881, 121.5256), '大安區': (25.0266, 121.5484),
            '中山區': (25.0633, 121.5267), '大同區': (25.0633, 121.5154),
            '中正區': (25.0364, 121.5161), '信義區': (25.0336, 121.5751),
            '萬華區': (25.0327, 121.5060), '文山區': (24.9906, 121.5420),
            '松山區': (25.0501, 121.5776), '內湖區': (25.0838, 121.5948),
            '南港區': (25.0415, 121.6073), '北投區': (25.1372, 121.5018)
        }
        return district_coords.get(str(district).strip(), (25.0478, 121.5319))
    
    def _extract_metadata(self):
        """从载入的数据中提取元数据"""
        if self.venues_data is not None and not self.venues_data.empty:
            # 运动类型
            if 'sport_type' in self.venues_data.columns:
                self.sport_types = sorted(self.venues_data['sport_type'].dropna().unique().tolist())
            
            # 地区
            if 'district' in self.venues_data.columns:
                self.districts = sorted(self.venues_data['district'].dropna().unique().tolist())
            
            # 设施
            if 'facilities' in self.venues_data.columns:
                all_facilities = []
                for facilities_str in self.venues_data['facilities'].dropna():
                    if '/' in str(facilities_str):
                        all_facilities.extend(str(facilities_str).split('/'))
                    else:
                        all_facilities.append(str(facilities_str))
                self.facilities = sorted(list(set([f.strip() for f in all_facilities if f.strip()])))
    
    def _load_data(self):
        """
        從CSV檔案載入場地資料
        """
        try:
            # 讀取CSV檔案
            csv_path = "attached_assets/finding move - main (1)_1757915289189.csv"
            
            if not os.path.exists(csv_path):
                print(f"CSV檔案不存在: {csv_path}")
                self._create_empty_dataframe()
                return
            
            # 讀取CSV，跳過前面的標題行
            raw_data = pd.read_csv(csv_path, encoding='utf-8', skiprows=5)
            
            # 清理欄位名稱
            raw_data.columns = [
                'name', 'district', 'price_range', 'sport_type', 'opening_hours',
                'facilities', 'venue_scale', 'courses', 'other', 'website',
                'address', 'contact_phone', 'photos'
            ]
            
            # 過濾掉空的場地名稱
            raw_data = raw_data.dropna(subset=['name'])
            raw_data = raw_data[raw_data['name'].str.strip() != '']
            
            # 建立標準化的資料結構
            venues_list = []
            
            for idx, row in raw_data.iterrows():
                venue = {
                    'id': idx + 1,
                    'name': str(row['name']).strip() if pd.notna(row['name']) else '',
                    'district': str(row['district']).strip() if pd.notna(row['district']) else '',
                    'address': str(row['address']).strip() if pd.notna(row['address']) else '',
                    'sport_type': self._normalize_sport_type(row['sport_type']),
                    'price_per_hour': self._extract_price(row['price_range']),
                    'rating': round(random.uniform(3.5, 5.0), 1),  # 模擬評分
                    'facilities': self._normalize_facilities(row['facilities']),
                    'description': str(row['other']).strip() if pd.notna(row['other']) else '',
                    'contact_phone': str(row['contact_phone']).strip() if pd.notna(row['contact_phone']) else '',
                    'opening_hours': str(row['opening_hours']).strip() if pd.notna(row['opening_hours']) else '',
                    'website': str(row['website']).strip() if pd.notna(row['website']) else '',
                    'venue_scale': str(row['venue_scale']).strip() if pd.notna(row['venue_scale']) else '',
                    'courses': str(row['courses']).strip() if pd.notna(row['courses']) else '',
                    'photos': str(row['photos']).strip() if pd.notna(row['photos']) else '',
                    'latitude': self._get_district_coordinates(row['district'])[0],
                    'longitude': self._get_district_coordinates(row['district'])[1]
                }
                venues_list.append(venue)
            
            # 轉換為DataFrame
            self.venues_data = pd.DataFrame(venues_list)
            
            # 更新可用選項
            self._update_available_options()
            
            print(f"成功載入 {len(self.venues_data)} 筆場地資料")
            
        except Exception as e:
            print(f"載入CSV資料時發生錯誤: {e}")
            self._create_empty_dataframe()
    
    def _create_empty_dataframe(self):
        """建立空的DataFrame作為後備"""
        column_names = [
            'id', 'name', 'address', 'district', 'sport_type',
            'price_per_hour', 'rating', 'facilities', 'description',
            'contact_phone', 'opening_hours', 'website',
            'latitude', 'longitude', 'venue_scale', 'courses', 'photos'
        ]
        self.venues_data = pd.DataFrame(columns=column_names)
        self._update_available_options()
    
    def _normalize_sport_type(self, sport_type):
        """標準化運動類型"""
        if pd.isna(sport_type) or sport_type == '':
            return '綜合運動'
        
        sport_type = str(sport_type).strip()
        
        # 運動類型對應表
        sport_mapping = {
            '羽球': '羽毛球',
            '羽毛球': '羽毛球',
            '游泳': '游泳',
            '健身': '健身',
            '重訓': '健身',
            '有氧': '有氧運動',
            '瑜珈': '瑜伽',
            '瑜伽': '瑜伽',
            '球類': '球類運動',
            '籃球': '籃球',
            '足球': '足球',
            '網球': '網球',
            '桌球': '桌球',
            '撞球': '撞球',
            '排球': '排球',
            '戶外運動': '戶外運動'
        }
        
        # 檢查包含的運動類型
        for key, value in sport_mapping.items():
            if key in sport_type:
                return value
        
        # 如果包含多種運動，返回第一個識別到的
        if '/' in sport_type:
            types = sport_type.split('/')
            for t in types:
                t = t.strip()
                for key, value in sport_mapping.items():
                    if key in t:
                        return value
        
        return sport_type if sport_type else '綜合運動'
    
    def _extract_price(self, price_range):
        """從價格區間提取平均價格"""
        if pd.isna(price_range) or price_range == '':
            return random.randint(100, 500)  # 預設價格範圍
        
        price_str = str(price_range).strip()
        
        if '0-200' in price_str:
            return 150
        elif '200-500' in price_str:
            return 350
        elif '500以上' in price_str:
            return 700
        else:
            return random.randint(200, 400)
    
    def _normalize_facilities(self, facilities):
        """標準化設施資訊"""
        if pd.isna(facilities) or facilities == '':
            return '基本設施'
        
        facilities_str = str(facilities).strip()
        
        # 標準化設施名稱
        facility_mapping = {
            '淋浴間': '淋浴間',
            '置物櫃': '置物櫃',
            '停車場': '停車場',
            'Wi-Fi': 'Wi-Fi',
            'WiFi': 'Wi-Fi',
            '無障礙設施': '無障礙設施',
            '性別友善設施': '性別友善設施',
            '寵物友善': '寵物友善',
            '女性專用': '女性專用'
        }
        
        normalized_facilities = []
        for key, value in facility_mapping.items():
            if key in facilities_str:
                normalized_facilities.append(value)
        
        return '/'.join(normalized_facilities) if normalized_facilities else facilities_str
    
    def _get_district_coordinates(self, district):
        """取得地區的座標 (緯度, 經度)"""
        district_coords = {
            '士林區': (25.0881, 121.5256),
            '大安區': (25.0266, 121.5484),
            '中山區': (25.0633, 121.5267),
            '大同區': (25.0633, 121.5154),
            '中正區': (25.0364, 121.5161),
            '信義區': (25.0336, 121.5751),
            '萬華區': (25.0327, 121.5060),
            '文山區': (24.9906, 121.5420),
            '松山區': (25.0501, 121.5776),
            '內湖區': (25.0838, 121.5948),
            '南港區': (25.0415, 121.6073),
            '北投區': (25.1372, 121.5018)
        }
        
        return district_coords.get(str(district).strip(), (25.0478, 121.5319))  # 預設台北市中心
    
    def _update_available_options(self):
        """更新可用的運動類型、地區和設施列表"""
        if self.venues_data is not None and not self.venues_data.empty:
            # 運動類型
            if 'sport_type' in self.venues_data.columns:
                self.sport_types = sorted(self.venues_data['sport_type'].dropna().unique().tolist())
            
            # 地區
            if 'district' in self.venues_data.columns:
                self.districts = sorted(self.venues_data['district'].dropna().unique().tolist())
            
            # 設施
            if 'facilities' in self.venues_data.columns:
                all_facilities = []
                for facilities in self.venues_data['facilities'].dropna():
                    if isinstance(facilities, str) and facilities.strip():
                        all_facilities.extend([f.strip() for f in facilities.split('/')])
                
                self.facilities = sorted(list(set(all_facilities)))
        else:
            # 如果沒有資料，提供一些預設選項
            self.sport_types = [
                "籃球", "足球", "網球", "羽毛球", "游泳", "健身", 
                "跑步", "桌球", "排球", "棒球", "瑜伽", "舞蹈"
            ]
            self.districts = [
                "中正區", "大同區", "中山區", "松山區", "大安區", "萬華區",
                "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"
            ]
            self.facilities = [
                "停車場", "淋浴間", "更衣室", "冷氣", "音響設備", "器材租借",
                "飲水機", "休息區", "無障礙設施", "Wi-Fi", "置物櫃", "觀眾席"
            ]
    
    def get_all_venues(self) -> Optional[pd.DataFrame]:
        """獲取所有場地資料"""
        return self.venues_data.copy() if self.venues_data is not None else None
    
    def get_sport_types(self) -> List[str]:
        """獲取所有可用的運動類型"""
        return self.sport_types.copy()
    
    def get_districts(self) -> List[str]:
        """獲取所有可用的地區"""
        return self.districts.copy()
    
    def get_facilities(self) -> List[str]:
        """獲取所有可用的設施"""
        return self.facilities.copy()
    
    def get_venue_stats(self) -> Dict[str, Any]:
        """獲取場地統計資訊"""
        if self.venues_data is None or self.venues_data.empty:
            return {
                'total_venues': 0,
                'sport_types': 0,
                'districts': 0,
                'avg_price': 0
            }
        
        stats = {
            'total_venues': len(self.venues_data),
            'sport_types': len(self.sport_types),
            'districts': len(self.districts),
            'avg_price': self.venues_data['price_per_hour'].mean() if 'price_per_hour' in self.venues_data.columns else 0
        }
        
        return stats
    
    def search_venues(self, query: str) -> Optional[pd.DataFrame]:
        """
        根據關鍵字搜尋場地
        
        Args:
            query: 搜尋關鍵字
            
        Returns:
            符合搜尋條件的場地資料
        """
        if self.venues_data is None or self.venues_data.empty or not query:
            return None
        
        query = query.lower().strip()
        
        # 在多個欄位中搜尋
        search_columns = ['name', 'address', 'district', 'sport_type', 'facilities', 'description']
        
        mask = pd.Series([False] * len(self.venues_data))
        
        for col in search_columns:
            if col in self.venues_data.columns:
                mask |= self.venues_data[col].astype(str).str.lower().str.contains(query, na=False)
        
        results = self.venues_data[mask].copy()
        
        return results if not results.empty else None
    
    def get_filtered_venues(self, 
                          sport_types: Optional[List[str]] = None,
                          districts: Optional[List[str]] = None,
                          price_range: Optional[List[float]] = None,
                          facilities: Optional[List[str]] = None,
                          min_rating: float = 0.0,
                          search_query: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        根據多個條件篩選場地
        
        Args:
            sport_types: 運動類型列表
            districts: 地區列表
            price_range: 價格範圍 [最低價, 最高價]
            facilities: 設施需求列表
            min_rating: 最低評分要求
            search_query: 搜尋關鍵字
            
        Returns:
            符合篩選條件的場地資料
        """
        if self.venues_data is None or self.venues_data.empty:
            return None
        
        filtered_data = self.venues_data.copy()
        
        # 關鍵字搜尋
        if search_query:
            search_results = self.search_venues(search_query)
            if search_results is not None:
                filtered_data = search_results
            else:
                return None
        
        # 運動類型篩選
        if sport_types and 'sport_type' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['sport_type'].isin(sport_types)]
        
        # 地區篩選
        if districts and 'district' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['district'].isin(districts)]
        
        # 價格範圍篩選
        if price_range and 'price_per_hour' in filtered_data.columns:
            min_price, max_price = price_range
            filtered_data = filtered_data[
                (filtered_data['price_per_hour'] >= min_price) &
                (filtered_data['price_per_hour'] <= max_price)
            ]
        
        # 設施篩選
        if facilities and 'facilities' in filtered_data.columns:
            for facility in facilities:
                filtered_data = filtered_data[
                    filtered_data['facilities'].astype(str).str.contains(facility, na=False, case=False)
                ]
        
        # 評分篩選
        if min_rating > 0 and 'rating' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['rating'] >= min_rating]
        
        return filtered_data if not filtered_data.empty else None
    
    def get_venues_by_ids(self, venue_ids: List[Any]) -> Optional[pd.DataFrame]:
        """
        根據場地ID列表獲取場地資料
        
        Args:
            venue_ids: 場地ID列表
            
        Returns:
            對應的場地資料
        """
        if self.venues_data is None or self.venues_data.empty or not venue_ids:
            return None
        
        # 使用ID欄位篩選
        if 'id' in self.venues_data.columns:
            filtered_data = self.venues_data[self.venues_data['id'].isin(venue_ids)]
        else:
            return None
        
        return filtered_data if not filtered_data.empty else None
    
    def get_venue_by_id(self, venue_id: int) -> Optional[Dict[str, Any]]:
        """根據ID獲取場地詳細資訊"""
        try:
            if self.venues_data is None or self.venues_data.empty:
                return None
            
            venue_data = self.venues_data[self.venues_data['id'] == venue_id]
            
            if venue_data.empty:
                return None
                
            return venue_data.iloc[0].to_dict()
            
        except Exception as e:
            print(f"獲取場地詳細資訊時發生錯誤: {e}")
            return None
    
    def get_popular_searches(self) -> List[str]:
        """
        獲取熱門搜尋關鍵字
        
        Returns:
            熱門搜尋關鍵字列表
        """
        popular_searches = []
        
        # 添加運動類型作為熱門搜尋
        if self.sport_types:
            popular_searches.extend(self.sport_types[:5])
        
        # 添加地區作為熱門搜尋
        if self.districts:
            popular_searches.extend(self.districts[:3])
        
        # 添加一些常見搜尋詞
        common_searches = ["室內", "戶外", "便宜", "高評分", "停車場", "24小時"]
        popular_searches.extend(common_searches)
        
        return popular_searches[:10]  # 返回前10個熱門搜尋