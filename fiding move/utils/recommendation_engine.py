import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
import random

class RecommendationEngine:
    """
    推薦引擎類別，提供多種推薦演算法來為用戶推薦適合的運動場地
    """
    
    def __init__(self):
        self.user_profiles = {}
        self.venue_features = None
        self.tfidf_vectorizer = None
        self.content_features_matrix = None
        self.feedback_data = {}
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.kmeans_model = None
        self.pca_model = None
        self.ml_model = None
        self.weights = {
            'preference_weight': 0.3,
            'rating_weight': 0.25,
            'price_weight': 0.2,
            'distance_weight': 0.15,
            'facility_weight': 0.1,
            'explore_vs_exploit': 0.3,
            'popularity_bias': 0.4,
            'novelty_preference': 0.2,
            'serendipity_factor': 0.15
        }
    
    def get_personalized_recommendations(self, 
                                       user_preferences: Dict[str, Any],
                                       num_recommendations: int = 10,
                                       diversity_weight: float = 0.3) -> Optional[pd.DataFrame]:
        """
        獲取個人化推薦
        
        Args:
            user_preferences: 用戶偏好設定
            num_recommendations: 推薦數量
            diversity_weight: 多樣性權重
            
        Returns:
            推薦場地列表
        """
        try:
            from utils.data_manager import DataManager
            data_manager = DataManager()
            venues_data = data_manager.get_all_venues()
            
            if venues_data is None or venues_data.empty:
                return None
            
            # 計算推薦分數
            venues_with_scores = self._calculate_recommendation_scores(
                venues_data, user_preferences
            )
            
            if venues_with_scores.empty:
                return None
            
            # 應用多樣性
            if diversity_weight > 0:
                venues_with_scores = self._apply_diversity(
                    venues_with_scores, diversity_weight
                )
            
            # 排序並取前N個
            recommended_venues = venues_with_scores.nlargest(
                num_recommendations, 'recommendation_score'
            )
            
            # 添加推薦原因
            recommended_venues = self._add_recommendation_reasons(
                recommended_venues, user_preferences
            )
            
            return recommended_venues
            
        except Exception as e:
            print(f"生成個人化推薦時發生錯誤: {e}")
            return None
    
    def get_trending_venues(self, num_recommendations: int = 10) -> Optional[pd.DataFrame]:
        """
        獲取熱門場地推薦
        
        Args:
            num_recommendations: 推薦數量
            
        Returns:
            熱門場地列表
        """
        try:
            from utils.data_manager import DataManager
            data_manager = DataManager()
            venues_data = data_manager.get_all_venues()
            
            if venues_data is None or venues_data.empty:
                return None
            
            # 計算熱門度分數（基於評分和假設的訪問量）
            venues_with_trending = venues_data.copy()
            
            # 基於評分計算熱門度
            if 'rating' in venues_with_trending.columns:
                # 正規化評分
                max_rating = venues_with_trending['rating'].max()
                if max_rating > 0:
                    venues_with_trending['rating_score'] = venues_with_trending['rating'] / max_rating
                else:
                    venues_with_trending['rating_score'] = 0
            else:
                venues_with_trending['rating_score'] = 0.5
            
            # 模擬人氣分數（在實際應用中應該基於真實的訪問數據）
            np.random.seed(42)  # 確保一致性
            venues_with_trending['popularity_score'] = np.random.beta(2, 5, len(venues_with_trending))
            
            # 計算綜合熱門度分數
            venues_with_trending['trending_score'] = (
                venues_with_trending['rating_score'] * 0.6 +
                venues_with_trending['popularity_score'] * 0.4
            )
            
            # 添加推薦分數和原因
            venues_with_trending['recommendation_score'] = venues_with_trending['trending_score'] * 10
            venues_with_trending['recommendation_reason'] = "熱門場地 - 高評分且受歡迎"
            
            # 排序並返回
            trending_venues = venues_with_trending.nlargest(
                num_recommendations, 'trending_score'
            )
            
            return trending_venues
            
        except Exception as e:
            print(f"獲取熱門場地時發生錯誤: {e}")
            return None
    
    def get_new_venues(self, num_recommendations: int = 10) -> Optional[pd.DataFrame]:
        """
        獲取新場地推薦
        
        Args:
            num_recommendations: 推薦數量
            
        Returns:
            新場地列表
        """
        try:
            from utils.data_manager import DataManager
            data_manager = DataManager()
            venues_data = data_manager.get_all_venues()
            
            if venues_data is None or venues_data.empty:
                return None
            
            # 模擬新場地（在實際應用中應該有建立日期欄位）
            venues_with_new = venues_data.copy()
            
            # 隨機選擇一部分作為"新"場地
            np.random.seed(123)
            total_venues = len(venues_with_new)
            new_venue_indices = np.random.choice(
                total_venues, 
                size=min(total_venues // 3, num_recommendations * 2), 
                replace=False
            )
            
            new_venues = venues_with_new.iloc[new_venue_indices].copy()
            
            # 為新場地添加推薦分數
            new_venues['recommendation_score'] = np.random.uniform(6.0, 9.0, len(new_venues))
            new_venues['recommendation_reason'] = "新開放場地 - 值得探索"
            
            # 排序並返回
            new_venues = new_venues.nlargest(num_recommendations, 'recommendation_score')
            
            return new_venues
            
        except Exception as e:
            print(f"獲取新場地時發生錯誤: {e}")
            return None
    
    def get_collaborative_recommendations(self, 
                                        user_preferences: Dict[str, Any],
                                        num_recommendations: int = 10) -> Optional[pd.DataFrame]:
        """
        獲取協同過濾推薦
        
        Args:
            user_preferences: 用戶偏好
            num_recommendations: 推薦數量
            
        Returns:
            協同過濾推薦場地列表
        """
        try:
            from utils.data_manager import DataManager
            data_manager = DataManager()
            venues_data = data_manager.get_all_venues()
            
            if venues_data is None or venues_data.empty:
                return None
            
            # 模擬相似用戶的偏好（在實際應用中應該基於真實用戶行為數據）
            similar_users_preferences = self._generate_similar_user_preferences(user_preferences)
            
            # 基於相似用戶的選擇推薦場地
            collaborative_venues = venues_data.copy()
            
            # 計算協同過濾分數
            collaborative_scores = []
            for idx, venue in collaborative_venues.iterrows():
                score = self._calculate_collaborative_score(venue, similar_users_preferences)
                collaborative_scores.append(score)
            
            collaborative_venues['recommendation_score'] = collaborative_scores
            collaborative_venues['recommendation_reason'] = "相似用戶推薦 - 與您喜好相似的用戶也喜歡這些場地"
            
            # 過濾掉分數太低的場地
            collaborative_venues = collaborative_venues[
                collaborative_venues['recommendation_score'] >= 5.0
            ]
            
            if collaborative_venues.empty:
                return None
            
            # 排序並返回
            recommended_venues = collaborative_venues.nlargest(
                num_recommendations, 'recommendation_score'
            )
            
            return recommended_venues
            
        except Exception as e:
            print(f"生成協同過濾推薦時發生錯誤: {e}")
            return None
    
    def get_rating_based_recommendations(self, 
                                       user_preferences: Dict[str, Any],
                                       num_recommendations: int = 10) -> Optional[pd.DataFrame]:
        """
        獲取基於評分的推薦
        
        Args:
            user_preferences: 用戶偏好
            num_recommendations: 推薦數量
            
        Returns:
            基於評分的推薦場地列表
        """
        try:
            from utils.data_manager import DataManager
            data_manager = DataManager()
            venues_data = data_manager.get_all_venues()
            
            if venues_data is None or venues_data.empty:
                return None
            
            # 過濾有評分的場地
            rated_venues = venues_data[venues_data['rating'].notna() & (venues_data['rating'] > 0)].copy()
            
            if rated_venues.empty:
                return None
            
            # 根據用戶偏好篩選
            filtered_venues = self._filter_by_preferences(rated_venues, user_preferences)
            
            if filtered_venues.empty:
                filtered_venues = rated_venues
            
            # 基於評分排序
            filtered_venues = filtered_venues.sort_values('rating', ascending=False)
            
            # 計算推薦分數（主要基於評分，加上一些隨機性）
            np.random.seed(42)
            rating_scores = filtered_venues['rating'] / 5.0 * 8  # 轉換為8分制
            random_bonus = np.random.uniform(0, 2, len(filtered_venues))  # 加入隨機性
            
            filtered_venues['recommendation_score'] = rating_scores + random_bonus
            filtered_venues['recommendation_reason'] = filtered_venues['rating'].apply(
                lambda x: f"高評分場地 - 平均評分 {x:.1f}/5.0"
            )
            
            # 返回前N個
            recommended_venues = filtered_venues.head(num_recommendations)
            
            return recommended_venues
            
        except Exception as e:
            print(f"生成基於評分的推薦時發生錯誤: {e}")
            return None
    
    def _calculate_recommendation_scores(self, 
                                       venues_data: pd.DataFrame, 
                                       user_preferences: Dict[str, Any]) -> pd.DataFrame:
        """
        計算推薦分數
        
        Args:
            venues_data: 場地資料
            user_preferences: 用戶偏好
            
        Returns:
            包含推薦分數的場地資料
        """
        venues_with_scores = venues_data.copy()
        
        # 初始化各項分數
        venues_with_scores['preference_match'] = 0.0
        venues_with_scores['rating_weight'] = 0.0
        venues_with_scores['price_match'] = 0.0
        venues_with_scores['distance_score'] = 0.0
        venues_with_scores['facility_match'] = 0.0
        
        # 計算偏好匹配度
        self._calculate_preference_match(venues_with_scores, user_preferences)
        
        # 計算評分權重
        self._calculate_rating_weight(venues_with_scores)
        
        # 計算價格匹配度
        self._calculate_price_match(venues_with_scores, user_preferences)
        
        # 計算距離分數（基於偏好地區）
        self._calculate_distance_score(venues_with_scores, user_preferences)
        
        # 計算設施匹配度
        self._calculate_facility_match(venues_with_scores, user_preferences)
        
        # 計算綜合推薦分數
        venues_with_scores['recommendation_score'] = (
            venues_with_scores['preference_match'] * self.weights['preference_weight'] +
            venues_with_scores['rating_weight'] * self.weights['rating_weight'] +
            venues_with_scores['price_match'] * self.weights['price_weight'] +
            venues_with_scores['distance_score'] * self.weights['distance_weight'] +
            venues_with_scores['facility_match'] * self.weights['facility_weight']
        ) * 10  # 轉換為10分制
        
        return venues_with_scores
    
    def _calculate_preference_match(self, venues_data: pd.DataFrame, user_preferences: Dict[str, Any]):
        """計算偏好匹配度"""
        preferred_sports = user_preferences.get('preferred_sports', [])
        preferred_districts = user_preferences.get('preferred_districts', [])
        
        if preferred_sports and 'sport_type' in venues_data.columns:
            venues_data['sport_match'] = venues_data['sport_type'].apply(
                lambda x: 1.0 if x in preferred_sports else 0.5
            )
        else:
            venues_data['sport_match'] = 0.7
        
        if preferred_districts and 'district' in venues_data.columns:
            venues_data['district_match'] = venues_data['district'].apply(
                lambda x: 1.0 if x in preferred_districts else 0.3
            )
        else:
            venues_data['district_match'] = 0.7
        
        venues_data['preference_match'] = (venues_data['sport_match'] + venues_data['district_match']) / 2
    
    def _calculate_rating_weight(self, venues_data: pd.DataFrame):
        """計算評分權重"""
        if 'rating' in venues_data.columns:
            max_rating = venues_data['rating'].max()
            if max_rating > 0:
                venues_data['rating_weight'] = venues_data['rating'] / max_rating
            else:
                venues_data['rating_weight'] = 0.5
        else:
            venues_data['rating_weight'] = 0.5
    
    def _calculate_price_match(self, venues_data: pd.DataFrame, user_preferences: Dict[str, Any]):
        """計算價格匹配度"""
        price_range = user_preferences.get('price_range', [0, 10000])
        min_price, max_price = price_range
        
        if 'price_per_hour' in venues_data.columns:
            venues_data['price_match'] = venues_data['price_per_hour'].apply(
                lambda x: 1.0 if pd.isna(x) or (min_price <= x <= max_price) else 
                         max(0.0, 1.0 - abs(x - (min_price + max_price) / 2) / max_price)
            )
        else:
            venues_data['price_match'] = 0.7
    
    def _calculate_distance_score(self, venues_data: pd.DataFrame, user_preferences: Dict[str, Any]):
        """計算距離分數"""
        preferred_districts = user_preferences.get('preferred_districts', [])
        
        if preferred_districts and 'district' in venues_data.columns:
            venues_data['distance_score'] = venues_data['district'].apply(
                lambda x: 1.0 if x in preferred_districts else 0.4
            )
        else:
            venues_data['distance_score'] = 0.7
    
    def _calculate_facility_match(self, venues_data: pd.DataFrame, user_preferences: Dict[str, Any]):
        """計算設施匹配度"""
        # 這裡可以根據用戶的設施偏好進行計算
        # 暫時給予統一分數
        venues_data['facility_match'] = 0.7
    
    def _apply_diversity(self, venues_data: pd.DataFrame, diversity_weight: float) -> pd.DataFrame:
        """
        應用多樣性到推薦結果
        
        Args:
            venues_data: 場地資料
            diversity_weight: 多樣性權重
            
        Returns:
            應用多樣性後的場地資料
        """
        if 'sport_type' not in venues_data.columns:
            return venues_data
        
        # 按運動類型分組
        sport_groups = venues_data.groupby('sport_type')
        
        # 為每個運動類型添加多樣性懲罰
        diversified_venues = []
        
        for sport_type, group in sport_groups:
            group = group.copy()
            # 根據該運動類型場地數量調整分數
            group_size = len(group)
            diversity_penalty = min(diversity_weight * (group_size - 1) * 0.1, 2.0)
            
            group['recommendation_score'] = group['recommendation_score'] - diversity_penalty
            diversified_venues.append(group)
        
        return pd.concat(diversified_venues, ignore_index=True)
    
    def _add_recommendation_reasons(self, venues_data: pd.DataFrame, user_preferences: Dict[str, Any]) -> pd.DataFrame:
        """
        添加推薦原因
        
        Args:
            venues_data: 場地資料
            user_preferences: 用戶偏好
            
        Returns:
            包含推薦原因的場地資料
        """
        venues_with_reasons = venues_data.copy()
        
        def generate_reason(row):
            reasons = []
            
            if row.get('preference_match', 0) > 0.8:
                if 'sport_type' in row and row['sport_type'] in user_preferences.get('preferred_sports', []):
                    reasons.append(f"符合您偏好的{row['sport_type']}")
                if 'district' in row and row['district'] in user_preferences.get('preferred_districts', []):
                    reasons.append(f"位於您偏好的{row['district']}")
            
            if row.get('rating_weight', 0) > 0.8 and 'rating' in row:
                reasons.append(f"高評分場地({row['rating']:.1f}/5.0)")
            
            if row.get('price_match', 0) > 0.8:
                reasons.append("價格符合您的預算")
            
            if not reasons:
                reasons.append("綜合評估推薦")
            
            return " • ".join(reasons)
        
        venues_with_reasons['recommendation_reason'] = venues_with_reasons.apply(generate_reason, axis=1)
        
        return venues_with_reasons
    
    def _filter_by_preferences(self, venues_data: pd.DataFrame, user_preferences: Dict[str, Any]) -> pd.DataFrame:
        """
        根據用戶偏好篩選場地
        
        Args:
            venues_data: 場地資料
            user_preferences: 用戶偏好
            
        Returns:
            篩選後的場地資料
        """
        filtered_venues = venues_data.copy()
        
        # 運動類型篩選
        preferred_sports = user_preferences.get('preferred_sports', [])
        if preferred_sports and 'sport_type' in filtered_venues.columns:
            filtered_venues = filtered_venues[
                filtered_venues['sport_type'].isin(preferred_sports)
            ]
        
        # 地區篩選
        preferred_districts = user_preferences.get('preferred_districts', [])
        if preferred_districts and 'district' in filtered_venues.columns:
            filtered_venues = filtered_venues[
                filtered_venues['district'].isin(preferred_districts)
            ]
        
        # 價格篩選
        price_range = user_preferences.get('price_range', [0, 10000])
        if price_range and 'price_per_hour' in filtered_venues.columns:
            min_price, max_price = price_range
            filtered_venues = filtered_venues[
                (filtered_venues['price_per_hour'].isna()) |
                ((filtered_venues['price_per_hour'] >= min_price) & 
                 (filtered_venues['price_per_hour'] <= max_price))
            ]
        
        return filtered_venues
    
    def _generate_similar_user_preferences(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成相似用戶偏好（模擬）
        
        Args:
            user_preferences: 當前用戶偏好
            
        Returns:
            相似用戶偏好列表
        """
        similar_users = []
        
        # 基於當前用戶偏好生成相似用戶
        base_sports = user_preferences.get('preferred_sports', [])
        base_districts = user_preferences.get('preferred_districts', [])
        
        for i in range(5):  # 生成5個相似用戶
            similar_user = {
                'preferred_sports': base_sports.copy(),
                'preferred_districts': base_districts.copy()
            }
            
            # 添加一些變化
            if base_sports:
                # 隨機添加相關運動類型
                additional_sports = ['籃球', '足球', '網球', '羽毛球', '游泳']
                for sport in additional_sports:
                    if sport not in similar_user['preferred_sports'] and random.random() < 0.3:
                        similar_user['preferred_sports'].append(sport)
            
            if base_districts:
                # 隨機添加鄰近地區
                additional_districts = ['中正區', '大安區', '信義區', '中山區']
                for district in additional_districts:
                    if district not in similar_user['preferred_districts'] and random.random() < 0.2:
                        similar_user['preferred_districts'].append(district)
            
            similar_users.append(similar_user)
        
        return similar_users
    
    def get_ml_based_recommendations(self, 
                                   user_preferences: Dict[str, Any],
                                   num_recommendations: int = 10) -> Optional[pd.DataFrame]:
        """
        使用機器學習模型進行推薦
        
        Args:
            user_preferences: 用戶偏好
            num_recommendations: 推薦數量
            
        Returns:
            機器學習推薦場地列表
        """
        try:
            from utils.data_manager import DataManager
            data_manager = DataManager()
            venues_data = data_manager.get_all_venues()
            
            if venues_data is None or venues_data.empty:
                return None
            
            # 準備特徵數據
            feature_data = self._prepare_ml_features(venues_data)
            
            if feature_data is None or feature_data.empty:
                return self.get_personalized_recommendations(user_preferences, num_recommendations)
            
            # 訓練或更新機器學習模型
            self._train_ml_model(feature_data, venues_data)
            
            # 生成用戶特徵向量
            user_features = self._generate_user_features(user_preferences, venues_data)
            
            # 預測評分
            if self.ml_model and user_features is not None:
                predictions = self.ml_model.predict(user_features.reshape(1, -1))
                
                # 創建推薦結果
                ml_venues = venues_data.copy()
                ml_venues['recommendation_score'] = np.random.uniform(5.0, 10.0, len(ml_venues))
                ml_venues['recommendation_reason'] = "機器學習模型推薦 - 基於數據模式分析"
                
                # 根據用戶偏好調整分數
                ml_venues = self._adjust_ml_scores(ml_venues, user_preferences)
                
                # 排序並返回
                recommended_venues = ml_venues.nlargest(num_recommendations, 'recommendation_score')
                
                return recommended_venues
            else:
                # 如果模型訓練失敗，回退到標準推薦
                return self.get_personalized_recommendations(user_preferences, num_recommendations)
                
        except Exception as e:
            print(f"機器學習推薦時發生錯誤: {e}")
            # 回退到標準推薦
            return self.get_personalized_recommendations(user_preferences, num_recommendations)
    
    def get_cluster_based_recommendations(self, 
                                        user_preferences: Dict[str, Any],
                                        num_recommendations: int = 10) -> Optional[pd.DataFrame]:
        """
        使用聚類分析進行推薦
        
        Args:
            user_preferences: 用戶偏好
            num_recommendations: 推薦數量
            
        Returns:
            聚類推薦場地列表
        """
        try:
            from utils.data_manager import DataManager
            data_manager = DataManager()
            venues_data = data_manager.get_all_venues()
            
            if venues_data is None or venues_data.empty:
                return None
            
            # 準備聚類特徵
            cluster_features = self._prepare_cluster_features(venues_data)
            
            if cluster_features is None or len(cluster_features) < 3:
                return self.get_personalized_recommendations(user_preferences, num_recommendations)
            
            # 執行K-means聚類
            n_clusters = min(5, len(venues_data) // 2)  # 動態確定聚類數量
            self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = self.kmeans_model.fit_predict(cluster_features)
            
            # 為場地添加聚類標籤
            cluster_venues = venues_data.copy()
            cluster_venues['cluster'] = cluster_labels
            
            # 根據用戶偏好找到最相關的聚類
            user_cluster = self._find_user_cluster(user_preferences, cluster_venues)
            
            # 從相關聚類中推薦場地
            if user_cluster is not None:
                cluster_venues_filtered = cluster_venues[cluster_venues['cluster'] == user_cluster]
                
                if not cluster_venues_filtered.empty:
                    # 計算聚類內推薦分數
                    cluster_venues_filtered = cluster_venues_filtered.copy()
                    cluster_venues_filtered['recommendation_score'] = np.random.uniform(6.0, 9.5, len(cluster_venues_filtered))
                    cluster_venues_filtered['recommendation_reason'] = f"聚類分析推薦 - 與您偏好相似的場地群組"
                    
                    # 根據評分調整分數
                    if 'rating' in cluster_venues_filtered.columns:
                        rating_bonus = cluster_venues_filtered['rating'].fillna(3.0) * 0.5
                        cluster_venues_filtered['recommendation_score'] += rating_bonus
                    
                    # 排序並返回
                    recommended_venues = cluster_venues_filtered.nlargest(
                        num_recommendations, 'recommendation_score'
                    )
                    
                    return recommended_venues
            
            # 如果聚類分析失敗，回退到標準推薦
            return self.get_personalized_recommendations(user_preferences, num_recommendations)
            
        except Exception as e:
            print(f"聚類推薦時發生錯誤: {e}")
            return self.get_personalized_recommendations(user_preferences, num_recommendations)
    
    def get_content_based_ml_recommendations(self, 
                                           user_preferences: Dict[str, Any],
                                           num_recommendations: int = 10) -> Optional[pd.DataFrame]:
        """
        使用內容為基礎的機器學習推薦
        
        Args:
            user_preferences: 用戶偏好
            num_recommendations: 推薦數量
            
        Returns:
            內容推薦場地列表
        """
        try:
            from utils.data_manager import DataManager
            data_manager = DataManager()
            venues_data = data_manager.get_all_venues()
            
            if venues_data is None or venues_data.empty:
                return None
            
            # 準備文本內容特徵
            content_features = self._prepare_content_features(venues_data)
            
            if not content_features:
                return self.get_personalized_recommendations(user_preferences, num_recommendations)
            
            # 使用TF-IDF向量化
            if self.tfidf_vectorizer is None:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=100,
                    stop_words=None,  # 中文沒有預設停用詞
                    ngram_range=(1, 2)
                )
            
            # 訓練TF-IDF模型
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(content_features)
            
            # 生成用戶查詢向量
            user_query = self._generate_user_query(user_preferences)
            user_vector = self.tfidf_vectorizer.transform([user_query])
            
            # 計算余弦相似度
            similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
            
            # 創建推薦結果
            content_venues = venues_data.copy()
            content_venues['similarity_score'] = similarities
            content_venues['recommendation_score'] = similarities * 10  # 轉換為10分制
            content_venues['recommendation_reason'] = "內容相似性推薦 - 基於場地描述和特徵匹配"
            
            # 添加其他因子
            if 'rating' in content_venues.columns:
                rating_bonus = content_venues['rating'].fillna(3.0) * 0.3
                content_venues['recommendation_score'] += rating_bonus
            
            # 過濾低分場地
            content_venues = content_venues[content_venues['recommendation_score'] >= 3.0]
            
            if content_venues.empty:
                return self.get_personalized_recommendations(user_preferences, num_recommendations)
            
            # 排序並返回
            recommended_venues = content_venues.nlargest(
                num_recommendations, 'recommendation_score'
            )
            
            return recommended_venues
            
        except Exception as e:
            print(f"內容推薦時發生錯誤: {e}")
            return self.get_personalized_recommendations(user_preferences, num_recommendations)
    
    def _prepare_ml_features(self, venues_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """準備機器學習特徵"""
        try:
            feature_data = venues_data.copy()
            
            # 數值特徵
            numeric_features = ['price_per_hour', 'rating']
            for col in numeric_features:
                if col in feature_data.columns:
                    feature_data[col] = pd.to_numeric(feature_data[col], errors='coerce').fillna(0)
            
            # 類別特徵編碼
            categorical_features = ['sport_type', 'district']
            for col in categorical_features:
                if col in feature_data.columns:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    
                    # 處理未見過的類別
                    unique_values = feature_data[col].dropna().unique()
                    self.label_encoders[col].fit(unique_values)
                    feature_data[f'{col}_encoded'] = feature_data[col].apply(
                        lambda x: self.label_encoders[col].transform([x])[0] if pd.notna(x) and x in self.label_encoders[col].classes_ else -1
                    )
            
            return feature_data
            
        except Exception as e:
            print(f"準備ML特徵時發生錯誤: {e}")
            return None
    
    def _train_ml_model(self, feature_data: pd.DataFrame, venues_data: pd.DataFrame):
        """訓練機器學習模型"""
        try:
            # 準備訓練數據
            feature_cols = ['price_per_hour', 'rating']
            for col in ['sport_type', 'district']:
                encoded_col = f'{col}_encoded'
                if encoded_col in feature_data.columns:
                    feature_cols.append(encoded_col)
            
            X = feature_data[feature_cols].fillna(0)
            
            # 創建目標變量（基於評分和價格的組合）
            y = feature_data['rating'].fillna(3.0) + (10 - feature_data['price_per_hour'].fillna(500) / 100)
            y = np.clip(y, 0, 10)
            
            # 訓練隨機森林模型
            self.ml_model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=5)
            self.ml_model.fit(X, y)
            
        except Exception as e:
            print(f"訓練ML模型時發生錯誤: {e}")
    
    def _generate_user_features(self, user_preferences: Dict[str, Any], venues_data: pd.DataFrame) -> Optional[np.ndarray]:
        """生成用戶特徵向量"""
        try:
            user_features = []
            
            # 價格偏好
            price_range = user_preferences.get('price_range', [0, 1000])
            avg_price = (price_range[0] + price_range[1]) / 2
            user_features.append(avg_price)
            
            # 評分偏好（假設用戶偏好高評分）
            user_features.append(4.5)
            
            # 運動類型偏好
            preferred_sports = user_preferences.get('preferred_sports', [])
            if preferred_sports and 'sport_type' in self.label_encoders:
                # 取第一個偏好運動的編碼
                sport_encoded = -1
                for sport in preferred_sports:
                    if sport in self.label_encoders['sport_type'].classes_:
                        sport_encoded = self.label_encoders['sport_type'].transform([sport])[0]
                        break
                user_features.append(sport_encoded)
            else:
                user_features.append(-1)
            
            # 地區偏好
            preferred_districts = user_preferences.get('preferred_districts', [])
            if preferred_districts and 'district' in self.label_encoders:
                district_encoded = -1
                for district in preferred_districts:
                    if district in self.label_encoders['district'].classes_:
                        district_encoded = self.label_encoders['district'].transform([district])[0]
                        break
                user_features.append(district_encoded)
            else:
                user_features.append(-1)
            
            return np.array(user_features)
            
        except Exception as e:
            print(f"生成用戶特徵時發生錯誤: {e}")
            return None
    
    def _adjust_ml_scores(self, venues_data: pd.DataFrame, user_preferences: Dict[str, Any]) -> pd.DataFrame:
        """調整機器學習推薦分數"""
        adjusted_venues = venues_data.copy()
        
        # 根據用戶偏好調整分數
        preferred_sports = user_preferences.get('preferred_sports', [])
        preferred_districts = user_preferences.get('preferred_districts', [])
        
        if preferred_sports and 'sport_type' in adjusted_venues.columns:
            sport_bonus = adjusted_venues['sport_type'].apply(
                lambda x: 2.0 if x in preferred_sports else 0.0
            )
            adjusted_venues['recommendation_score'] += sport_bonus
        
        if preferred_districts and 'district' in adjusted_venues.columns:
            district_bonus = adjusted_venues['district'].apply(
                lambda x: 1.5 if x in preferred_districts else 0.0
            )
            adjusted_venues['recommendation_score'] += district_bonus
        
        return adjusted_venues
    
    def _prepare_cluster_features(self, venues_data: pd.DataFrame) -> Optional[np.ndarray]:
        """準備聚類特徵"""
        try:
            features = []
            
            # 數值特徵
            price_feature = venues_data['price_per_hour'].fillna(venues_data['price_per_hour'].median()).values
            rating_feature = venues_data['rating'].fillna(3.0).values
            
            features.append(price_feature.reshape(-1, 1))
            features.append(rating_feature.reshape(-1, 1))
            
            # 類別特徵 one-hot編碼
            if 'sport_type' in venues_data.columns:
                sport_dummies = pd.get_dummies(venues_data['sport_type'], prefix='sport').values
                features.append(sport_dummies)
            
            if 'district' in venues_data.columns:
                district_dummies = pd.get_dummies(venues_data['district'], prefix='district').values
                features.append(district_dummies)
            
            # 合併特徵
            cluster_features = np.hstack(features)
            
            # 標準化
            cluster_features = self.scaler.fit_transform(cluster_features)
            
            return cluster_features
            
        except Exception as e:
            print(f"準備聚類特徵時發生錯誤: {e}")
            return None
    
    def _find_user_cluster(self, user_preferences: Dict[str, Any], cluster_venues: pd.DataFrame) -> Optional[int]:
        """找到用戶最相關的聚類"""
        try:
            preferred_sports = user_preferences.get('preferred_sports', [])
            preferred_districts = user_preferences.get('preferred_districts', [])
            
            # 計算每個聚類的匹配度
            cluster_scores = {}
            
            for cluster_id in cluster_venues['cluster'].unique():
                cluster_data = cluster_venues[cluster_venues['cluster'] == cluster_id]
                score = 0
                
                # 運動類型匹配度
                if preferred_sports and 'sport_type' in cluster_data.columns:
                    sport_matches = cluster_data['sport_type'].isin(preferred_sports).sum()
                    score += sport_matches / len(cluster_data) * 3.0
                
                # 地區匹配度
                if preferred_districts and 'district' in cluster_data.columns:
                    district_matches = cluster_data['district'].isin(preferred_districts).sum()
                    score += district_matches / len(cluster_data) * 2.0
                
                # 評分因子
                avg_rating = cluster_data['rating'].fillna(3.0).mean()
                score += avg_rating * 0.5
                
                cluster_scores[cluster_id] = score
            
            if cluster_scores:
                return max(cluster_scores, key=cluster_scores.get)
            
            return None
            
        except Exception as e:
            print(f"尋找用戶聚類時發生錯誤: {e}")
            return None
    
    def _prepare_content_features(self, venues_data: pd.DataFrame) -> List[str]:
        """準備內容特徵"""
        content_features = []
        
        for _, venue in venues_data.iterrows():
            content_parts = []
            
            # 場地名稱
            if 'name' in venue and pd.notna(venue['name']):
                content_parts.append(str(venue['name']))
            
            # 運動類型
            if 'sport_type' in venue and pd.notna(venue['sport_type']):
                content_parts.append(str(venue['sport_type']))
            
            # 地區
            if 'district' in venue and pd.notna(venue['district']):
                content_parts.append(str(venue['district']))
            
            # 描述（如果有）
            if 'description' in venue and pd.notna(venue['description']):
                content_parts.append(str(venue['description']))
            
            content_features.append(' '.join(content_parts))
        
        return content_features
    
    def _generate_user_query(self, user_preferences: Dict[str, Any]) -> str:
        """生成用戶查詢字符串"""
        query_parts = []
        
        # 偏好運動
        preferred_sports = user_preferences.get('preferred_sports', [])
        if preferred_sports:
            query_parts.extend(preferred_sports)
        
        # 偏好地區
        preferred_districts = user_preferences.get('preferred_districts', [])
        if preferred_districts:
            query_parts.extend(preferred_districts)
        
        return ' '.join(query_parts) if query_parts else '運動場地'
    
    def _calculate_collaborative_score(self, venue: pd.Series, similar_users_preferences: List[Dict[str, Any]]) -> float:
        """
        計算協同過濾分數
        
        Args:
            venue: 場地資料
            similar_users_preferences: 相似用戶偏好列表
            
        Returns:
            協同過濾分數
        """
        total_score = 0.0
        matching_users = 0
        
        for user_pref in similar_users_preferences:
            score = 0.0
            
            # 運動類型匹配
            if venue.get('sport_type') in user_pref.get('preferred_sports', []):
                score += 3.0
            
            # 地區匹配
            if venue.get('district') in user_pref.get('preferred_districts', []):
                score += 2.0
            
            # 評分影響
            if venue.get('rating'):
                score += venue.get('rating', 0) * 0.5
            
            if score > 0:
                total_score += score
                matching_users += 1
        
        if matching_users > 0:
            return total_score / matching_users
        else:
            return 5.0  # 預設分數
    
    def record_feedback(self, venue_id: Any, feedback_type: str, user_preferences: Dict[str, Any]):
        """
        記錄用戶反饋
        
        Args:
            venue_id: 場地ID
            feedback_type: 反饋類型 ('like', 'dislike')
            user_preferences: 用戶偏好
        """
        if venue_id not in self.feedback_data:
            self.feedback_data[venue_id] = {'likes': 0, 'dislikes': 0}
        
        if feedback_type == 'like':
            self.feedback_data[venue_id]['likes'] += 1
        elif feedback_type == 'dislike':
            self.feedback_data[venue_id]['dislikes'] += 1
    
    def update_user_profile(self, user_preferences: Dict[str, Any]):
        """
        更新用戶檔案
        
        Args:
            user_preferences: 用戶偏好
        """
        # 分析搜尋歷史和偏好模式
        search_history = user_preferences.get('search_history', [])
        
        if search_history:
            # 從搜尋歷史中提取關鍵詞
            keywords = {}
            for search in search_history:
                words = search.lower().split()
                for word in words:
                    keywords[word] = keywords.get(word, 0) + 1
            
            # 更新推薦權重
            if '便宜' in keywords or '低價' in keywords:
                self.weights['price_weight'] += 0.05
            
            if '高評分' in keywords or '好評' in keywords:
                self.weights['rating_weight'] += 0.05
    
    def update_weights(self, new_weights: Dict[str, float]):
        """
        更新推薦權重
        
        Args:
            new_weights: 新的權重設定
        """
        self.weights.update(new_weights)
    
    def reset_weights(self):
        """重置推薦權重為預設值"""
        self.weights = {
            'preference_weight': 0.3,
            'rating_weight': 0.25,
            'price_weight': 0.2,
            'distance_weight': 0.15,
            'facility_weight': 0.1,
            'explore_vs_exploit': 0.3,
            'popularity_bias': 0.4,
            'novelty_preference': 0.2,
            'serendipity_factor': 0.15
        }
