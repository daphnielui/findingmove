import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os

class WeatherManager:
    """
    天氣資料管理類別，負責處理台北市天氣API資料
    """
    
    def __init__(self):
        self.weather_data = None
        self.districts_weather = {}
        self._load_weather_data()
    
    def _load_weather_data(self):
        """載入天氣API JSON資料"""
        try:
            json_path = "attached_assets/response_1757912291602_1757930584417.json"
            
            if not os.path.exists(json_path):
                print(f"天氣資料檔案不存在: {json_path}")
                return
            
            with open(json_path, 'r', encoding='utf-8') as f:
                self.weather_data = json.load(f)
            
            # 解析各區域天氣資料
            self._parse_weather_data()
            print("成功載入台北市天氣資料")
            
        except Exception as e:
            print(f"載入天氣資料時發生錯誤: {e}")
    
    def _parse_weather_data(self):
        """解析天氣資料"""
        if not self.weather_data:
            return
        
        try:
            locations = self.weather_data.get('records', {}).get('Locations', [])
            
            for location_group in locations:
                if location_group.get('LocationsName') == '臺北市':
                    for location in location_group.get('Location', []):
                        district_name = location.get('LocationName')
                        
                        # 解析各種天氣元素
                        weather_elements = {}
                        for element in location.get('WeatherElement', []):
                            element_name = element.get('ElementName')
                            element_data = element.get('Time', [])
                            
                            weather_elements[element_name] = element_data
                        
                        self.districts_weather[district_name] = {
                            'location_name': district_name,
                            'geocode': location.get('Geocode'),
                            'latitude': location.get('Latitude'),
                            'longitude': location.get('Longitude'),
                            'weather_elements': weather_elements
                        }
            
        except Exception as e:
            print(f"解析天氣資料時發生錯誤: {e}")
    
    def _get_current_time_data(self, time_data: List[Dict], current_time: datetime) -> Optional[Dict]:
        """獲取最接近當前時間的資料"""
        if not time_data:
            return None
        
        closest_data = None
        min_time_diff = float('inf')
        
        for data_point in time_data:
            try:
                data_time_str = data_point.get('DataTime', '')
                data_time = datetime.fromisoformat(data_time_str.replace('+08:00', ''))
                
                time_diff = abs((current_time - data_time).total_seconds())
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_data = data_point
            except:
                continue
        
        return closest_data
    
    def get_current_weather(self, district: str = '中正區') -> Dict[str, Any]:
        """
        獲取指定地區的當前天氣資訊
        
        Args:
            district: 地區名稱，預設為中正區
            
        Returns:
            包含天氣資訊的字典
        """
        if district not in self.districts_weather:
            # 如果找不到指定地區，使用第一個可用的地區
            available_districts = list(self.districts_weather.keys())
            if available_districts:
                district = available_districts[0]
            else:
                return self._get_default_weather()
        
        district_data = self.districts_weather[district]
        weather_elements = district_data['weather_elements']
        current_time = datetime.now()
        
        weather_info = {
            'district': district,
            'temperature': 25,
            'apparent_temperature': 27,
            'humidity': 65,
            'wind_direction': '東北風',
            'wind_speed': 3,
            'precipitation_probability': 10,
            'weather_description': '晴朗',
            'comfort_index': '舒適',
            'update_time': current_time.strftime('%H:%M')
        }
        
        try:
            # 獲取溫度
            if '溫度' in weather_elements:
                temp_data = self._get_current_time_data(weather_elements['溫度'], current_time)
                if temp_data and temp_data.get('ElementValue'):
                    temp_value = temp_data['ElementValue'][0].get('Temperature')
                    if temp_value:
                        weather_info['temperature'] = int(temp_value)
            
            # 獲取體感溫度
            if '體感溫度' in weather_elements:
                apparent_temp_data = self._get_current_time_data(weather_elements['體感溫度'], current_time)
                if apparent_temp_data and apparent_temp_data.get('ElementValue'):
                    apparent_temp_value = apparent_temp_data['ElementValue'][0].get('ApparentTemperature')
                    if apparent_temp_value:
                        weather_info['apparent_temperature'] = int(float(apparent_temp_value))
            
            # 獲取相對濕度
            if '相對濕度' in weather_elements:
                humidity_data = self._get_current_time_data(weather_elements['相對濕度'], current_time)
                if humidity_data and humidity_data.get('ElementValue'):
                    humidity_value = humidity_data['ElementValue'][0].get('RelativeHumidity')
                    if humidity_value:
                        weather_info['humidity'] = int(float(humidity_value))
            
            # 獲取風向
            if '風向' in weather_elements:
                wind_dir_data = self._get_current_time_data(weather_elements['風向'], current_time)
                if wind_dir_data and wind_dir_data.get('ElementValue'):
                    wind_dir_value = wind_dir_data['ElementValue'][0].get('WindDirection')
                    if wind_dir_value:
                        weather_info['wind_direction'] = self._convert_wind_direction(wind_dir_value)
            
            # 獲取風速
            if '風速' in weather_elements:
                wind_speed_data = self._get_current_time_data(weather_elements['風速'], current_time)
                if wind_speed_data and wind_speed_data.get('ElementValue'):
                    wind_speed_value = wind_speed_data['ElementValue'][0].get('BeaufortScale')
                    if wind_speed_value:
                        weather_info['wind_speed'] = int(float(wind_speed_value))
            
            # 獲取降雨機率
            if '3小時降雨機率' in weather_elements:
                precip_data = self._get_current_time_data(weather_elements['3小時降雨機率'], current_time)
                if precip_data and precip_data.get('ElementValue'):
                    precip_value = precip_data['ElementValue'][0].get('ProbabilityOfPrecipitation')
                    if precip_value:
                        weather_info['precipitation_probability'] = int(float(precip_value))
            
            # 獲取天氣現象
            if '天氣現象' in weather_elements:
                weather_data = self._get_current_time_data(weather_elements['天氣現象'], current_time)
                if weather_data and weather_data.get('ElementValue'):
                    weather_value = weather_data['ElementValue'][0].get('Weather')
                    if weather_value:
                        weather_info['weather_description'] = weather_value
            
            # 獲取舒適度指數
            if '舒適度指數' in weather_elements:
                comfort_data = self._get_current_time_data(weather_elements['舒適度指數'], current_time)
                if comfort_data and comfort_data.get('ElementValue'):
                    comfort_value = comfort_data['ElementValue'][0].get('ComfortIndexDescription')
                    if comfort_value:
                        weather_info['comfort_index'] = comfort_value
            
        except Exception as e:
            print(f"解析天氣資料時發生錯誤: {e}")
        
        return weather_info
    
    def _convert_wind_direction(self, wind_direction: str) -> str:
        """轉換風向數值為中文描述"""
        try:
            degrees = float(wind_direction)
            
            directions = [
                "北風", "北北東風", "東北風", "東北東風",
                "東風", "東南東風", "東南風", "南南東風",
                "南風", "南南西風", "西南風", "西南西風",
                "西風", "西北西風", "西北風", "北北西風"
            ]
            
            index = int((degrees + 11.25) / 22.5) % 16
            return directions[index]
            
        except:
            return wind_direction if wind_direction else "微風"
    
    def _get_default_weather(self) -> Dict[str, Any]:
        """返回預設天氣資訊"""
        return {
            'district': '台北市',
            'temperature': 25,
            'apparent_temperature': 27,
            'humidity': 65,
            'wind_direction': '東北風',
            'wind_speed': 3,
            'precipitation_probability': 10,
            'weather_description': '晴朗',
            'comfort_index': '舒適',
            'update_time': datetime.now().strftime('%H:%M')
        }
    
    def get_weather_icon(self, weather_description: str, temperature: int) -> str:
        """根據天氣描述和溫度返回對應的emoji icon"""
        weather_desc = weather_description.lower()
        
        # 根據關鍵字判斷天氣icon
        if '晴' in weather_desc or '陽' in weather_desc:
            return '☀️'
        elif '雲' in weather_desc or '陰' in weather_desc:
            if '多雲' in weather_desc:
                return '⛅'
            else:
                return '☁️'
        elif '雨' in weather_desc:
            if '大雨' in weather_desc or '豪雨' in weather_desc:
                return '🌧️'
            elif '小雨' in weather_desc:
                return '🌦️'
            else:
                return '🌧️'
        elif '雷' in weather_desc:
            return '⛈️'
        elif '雪' in weather_desc:
            return '❄️'
        elif '霧' in weather_desc:
            return '🌫️'
        else:
            # 根據溫度判斷
            if temperature >= 30:
                return '☀️'
            elif temperature >= 25:
                return '⛅'
            else:
                return '☁️'
    
    def get_available_districts(self) -> List[str]:
        """獲取可用的地區列表"""
        return list(self.districts_weather.keys())
    
    def get_hourly_forecast(self, district: str = '中正區', hours: int = 24) -> List[Dict[str, Any]]:
        """
        獲取指定地區的小時預報
        
        Args:
            district: 地區名稱
            hours: 預報小時數
            
        Returns:
            小時預報列表
        """
        if district not in self.districts_weather:
            return []
        
        district_data = self.districts_weather[district]
        weather_elements = district_data['weather_elements']
        forecast_list = []
        
        try:
            if '溫度' in weather_elements:
                temp_data = weather_elements['溫度']
                
                for i, data_point in enumerate(temp_data[:hours]):
                    time_str = data_point.get('DataTime', '')
                    temp_value = data_point.get('ElementValue', [{}])[0].get('Temperature', '25')
                    
                    try:
                        forecast_time = datetime.fromisoformat(time_str.replace('+08:00', ''))
                        temp = int(temp_value)
                        
                        forecast_list.append({
                            'time': forecast_time.strftime('%H:%M'),
                            'date': forecast_time.strftime('%m/%d'),
                            'temperature': temp,
                            'hour': forecast_time.hour
                        })
                    except:
                        continue
            
        except Exception as e:
            print(f"獲取小時預報時發生錯誤: {e}")
        
        return forecast_list
    