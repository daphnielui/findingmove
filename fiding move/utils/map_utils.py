import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import math

class MapUtils:
    """
    地圖工具類別，提供地圖相關的功能和座標計算
    """
    
    def __init__(self):
        # 台北市各區中心座標
        self.district_centers = {
            "台北市中心": [25.0330, 121.5654],
            "中正區": [25.0320, 121.5200],
            "大同區": [25.0632, 121.5138],
            "中山區": [25.0642, 121.5326],
            "松山區": [25.0497, 121.5746],
            "大安區": [25.0263, 121.5436],
            "萬華區": [25.0338, 121.5014],
            "信義區": [25.0308, 121.5645],
            "士林區": [25.0876, 121.5258],
            "北投區": [25.1174, 121.4985],
            "內湖區": [25.0695, 121.5945],
            "南港區": [25.0547, 121.6066],
            "文山區": [24.9887, 121.5706]
        }
        
        # 運動類型對應的地圖標記顏色
        self.sport_colors = {
            "籃球": "blue",
            "足球": "green", 
            "網球": "red",
            "羽毛球": "orange",
            "游泳": "lightblue",
            "健身房": "purple",
            "跑步": "gray",
            "桌球": "pink",
            "排球": "darkblue",
            "棒球": "darkgreen",
            "瑜伽": "lightgreen",
            "舞蹈": "violet",
            "其他": "black"
        }
        
        # 台北市邊界座標（大約範圍）
        self.taipei_bounds = {
            "north": 25.3,
            "south": 24.9,
            "east": 121.65,
            "west": 121.45
        }
    
    def get_district_center(self, district_name: str) -> List[float]:
        """
        獲取指定地區的中心座標
        
        Args:
            district_name: 地區名稱
            
        Returns:
            [緯度, 經度] 座標列表
        """
        return self.district_centers.get(district_name, self.district_centers["台北市中心"])
    
    def get_sport_colors(self) -> Dict[str, str]:
        """
        獲取運動類型對應的顏色映射
        
        Returns:
            運動類型到顏色的映射字典
        """
        return self.sport_colors.copy()
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        計算兩點間的距離（使用 Haversine 公式）
        
        Args:
            lat1: 第一點緯度
            lon1: 第一點經度
            lat2: 第二點緯度
            lon2: 第二點經度
            
        Returns:
            距離（公里）
        """
        # 將度轉換為弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine 公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公里）
        r = 6371
        
        return r * c
    
    def find_nearest_venue(self, venues_df: pd.DataFrame, target_lat: float, target_lon: float) -> Optional[Dict[str, Any]]:
        """
        尋找距離指定座標最近的場地
        
        Args:
            venues_df: 場地資料 DataFrame
            target_lat: 目標緯度
            target_lon: 目標經度
            
        Returns:
            最近場地的資料字典
        """
        if venues_df is None or venues_df.empty:
            return None
        
        if 'latitude' not in venues_df.columns or 'longitude' not in venues_df.columns:
            return None
        
        min_distance = float('inf')
        nearest_venue = None
        
        for idx, venue in venues_df.iterrows():
            if pd.notna(venue['latitude']) and pd.notna(venue['longitude']):
                distance = self.calculate_distance(
                    target_lat, target_lon,
                    venue['latitude'], venue['longitude']
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_venue = venue.to_dict()
                    nearest_venue['distance'] = distance
        
        return nearest_venue
    
    def get_venues_in_radius(self, venues_df: pd.DataFrame, center_lat: float, center_lon: float, radius_km: float) -> pd.DataFrame:
        """
        獲取指定半徑內的場地
        
        Args:
            venues_df: 場地資料 DataFrame
            center_lat: 中心點緯度
            center_lon: 中心點經度
            radius_km: 半徑（公里）
            
        Returns:
            半徑內的場地資料
        """
        if venues_df is None or venues_df.empty:
            return pd.DataFrame()
        
        if 'latitude' not in venues_df.columns or 'longitude' not in venues_df.columns:
            return venues_df
        
        venues_in_radius = []
        
        for idx, venue in venues_df.iterrows():
            if pd.notna(venue['latitude']) and pd.notna(venue['longitude']):
                distance = self.calculate_distance(
                    center_lat, center_lon,
                    venue['latitude'], venue['longitude']
                )
                
                if distance <= radius_km:
                    venue_data = venue.to_dict()
                    venue_data['distance'] = distance
                    venues_in_radius.append(venue_data)
        
        return pd.DataFrame(venues_in_radius)
    
    def generate_coordinates_for_district(self, district: str, num_points: int = 1) -> List[Tuple[float, float]]:
        """
        為指定地區生成隨機座標點
        
        Args:
            district: 地區名稱
            num_points: 要生成的點數
            
        Returns:
            座標點列表 [(緯度, 經度), ...]
        """
        center = self.get_district_center(district)
        center_lat, center_lon = center[0], center[1]
        
        # 生成區域內隨機點（約0.01度範圍內）
        coordinates = []
        np.random.seed(hash(district) % 1000)  # 確保每個區域的座標一致
        
        for _ in range(num_points):
            # 在中心點周圍生成隨機偏移
            lat_offset = np.random.uniform(-0.01, 0.01)
            lon_offset = np.random.uniform(-0.01, 0.01)
            
            lat = center_lat + lat_offset
            lon = center_lon + lon_offset
            
            # 確保座標在台北市範圍內
            lat = max(self.taipei_bounds["south"], min(self.taipei_bounds["north"], lat))
            lon = max(self.taipei_bounds["west"], min(self.taipei_bounds["east"], lon))
            
            coordinates.append((lat, lon))
        
        return coordinates
    
    def assign_coordinates_to_venues(self, venues_df: pd.DataFrame) -> pd.DataFrame:
        """
        為沒有座標的場地分配座標
        
        Args:
            venues_df: 場地資料 DataFrame
            
        Returns:
            包含座標的場地資料
        """
        if venues_df is None or venues_df.empty:
            return venues_df
        
        venues_with_coords = venues_df.copy()
        
        # 確保座標欄位存在
        if 'latitude' not in venues_with_coords.columns:
            venues_with_coords['latitude'] = None
        if 'longitude' not in venues_with_coords.columns:
            venues_with_coords['longitude'] = None
        
        # 為沒有座標的場地分配座標
        for idx, venue in venues_with_coords.iterrows():
            if pd.isna(venue['latitude']) or pd.isna(venue['longitude']):
                district = venue.get('district', '台北市中心')
                
                # 為該地區生成一個座標點
                coords = self.generate_coordinates_for_district(district, 1)
                if coords:
                    lat, lon = coords[0]
                    venues_with_coords.at[idx, 'latitude'] = lat
                    venues_with_coords.at[idx, 'longitude'] = lon
        
        return venues_with_coords
    
    def get_district_bounds(self, district: str) -> Dict[str, float]:
        """
        獲取指定地區的邊界座標
        
        Args:
            district: 地區名稱
            
        Returns:
            邊界座標字典 {'north': ..., 'south': ..., 'east': ..., 'west': ...}
        """
        center = self.get_district_center(district)
        center_lat, center_lon = center[0], center[1]
        
        # 每個區域約0.02度的範圍
        bounds = {
            'north': center_lat + 0.01,
            'south': center_lat - 0.01,
            'east': center_lon + 0.01,
            'west': center_lon - 0.01
        }
        
        return bounds
    
    def cluster_venues_by_proximity(self, venues_df: pd.DataFrame, max_distance_km: float = 0.5) -> Dict[str, List[int]]:
        """
        根據距離將場地分群
        
        Args:
            venues_df: 場地資料 DataFrame
            max_distance_km: 最大群集距離（公里）
            
        Returns:
            群集字典，key為群集ID，value為場地索引列表
        """
        if venues_df is None or venues_df.empty:
            return {}
        
        if 'latitude' not in venues_df.columns or 'longitude' not in venues_df.columns:
            return {}
        
        clusters = {}
        cluster_id = 0
        assigned_venues = set()
        
        for idx, venue in venues_df.iterrows():
            if idx in assigned_venues:
                continue
            
            if pd.isna(venue['latitude']) or pd.isna(venue['longitude']):
                continue
            
            # 開始新的群集
            cluster_venues = [idx]
            assigned_venues.add(idx)
            
            # 尋找附近的場地
            for other_idx, other_venue in venues_df.iterrows():
                if other_idx in assigned_venues:
                    continue
                
                if pd.isna(other_venue['latitude']) or pd.isna(other_venue['longitude']):
                    continue
                
                distance = self.calculate_distance(
                    venue['latitude'], venue['longitude'],
                    other_venue['latitude'], other_venue['longitude']
                )
                
                if distance <= max_distance_km:
                    cluster_venues.append(other_idx)
                    assigned_venues.add(other_idx)
            
            clusters[f"cluster_{cluster_id}"] = cluster_venues
            cluster_id += 1
        
        return clusters
    
    def get_route_waypoints(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float], num_waypoints: int = 3) -> List[Tuple[float, float]]:
        """
        獲取兩點間的路線途經點
        
        Args:
            start_coords: 起點座標 (緯度, 經度)
            end_coords: 終點座標 (緯度, 經度)
            num_waypoints: 途經點數量
            
        Returns:
            途經點座標列表
        """
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        
        waypoints = []
        
        for i in range(1, num_waypoints + 1):
            # 簡單的線性插值
            ratio = i / (num_waypoints + 1)
            
            waypoint_lat = start_lat + (end_lat - start_lat) * ratio
            waypoint_lon = start_lon + (end_lon - start_lon) * ratio
            
            waypoints.append((waypoint_lat, waypoint_lon))
        
        return waypoints
    
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        驗證座標是否在台北市範圍內
        
        Args:
            lat: 緯度
            lon: 經度
            
        Returns:
            是否為有效座標
        """
        return (self.taipei_bounds["south"] <= lat <= self.taipei_bounds["north"] and
                self.taipei_bounds["west"] <= lon <= self.taipei_bounds["east"])
    
    def get_map_zoom_level(self, bounds: Dict[str, float]) -> int:
        """
        根據邊界範圍計算適當的地圖縮放級別
        
        Args:
            bounds: 邊界座標字典
            
        Returns:
            縮放級別
        """
        lat_range = bounds["north"] - bounds["south"]
        lon_range = bounds["east"] - bounds["west"]
        
        max_range = max(lat_range, lon_range)
        
        if max_range > 0.1:
            return 10
        elif max_range > 0.05:
            return 12
        elif max_range > 0.02:
            return 14
        elif max_range > 0.01:
            return 15
        else:
            return 16
    
    def get_distance_description(self, distance_km: float) -> str:
        """
        將距離轉換為人性化的描述
        
        Args:
            distance_km: 距離（公里）
            
        Returns:
            距離描述字串
        """
        if distance_km < 0.5:
            return f"{int(distance_km * 1000)}公尺"
        elif distance_km < 1.0:
            return f"{distance_km:.1f}公里"
        else:
            return f"{distance_km:.1f}公里"
