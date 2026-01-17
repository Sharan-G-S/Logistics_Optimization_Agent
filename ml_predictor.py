"""
Machine Learning Demand Predictor
Uses Linear Regression to predict future inventory demand based on historical patterns
"""

import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class MLDemandPredictor:
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        
    def generate_historical_data(self, item_id, current_quantity, days=60):
        """Generate synthetic historical sales data for demonstration"""
        np.random.seed(hash(item_id) % 2**32)
        
        # Base demand with trend and seasonality
        base_demand = current_quantity * 0.1
        trend = np.random.uniform(-0.5, 0.5)
        
        history = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            
            # Day of week effect (higher on weekdays)
            day_of_week = date.weekday()
            weekday_factor = 1.2 if day_of_week < 5 else 0.8
            
            # Monthly seasonality
            month_factor = 1 + 0.2 * np.sin(2 * np.pi * date.month / 12)
            
            # Random variation
            noise = np.random.normal(0, base_demand * 0.2)
            
            demand = max(0, base_demand * weekday_factor * month_factor + trend * i + noise)
            
            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'demand': round(demand, 2),
                'day_of_week': day_of_week,
                'month': date.month,
                'day_of_month': date.day
            })
        
        return history
    
    def prepare_features(self, history):
        """Extract features for ML model"""
        X = []
        y = []
        
        for i, record in enumerate(history):
            features = [
                i,  # Time index (trend)
                record['day_of_week'],  # Day of week
                record['month'],  # Month
                record['day_of_month'],  # Day of month
                np.sin(2 * np.pi * record['day_of_week'] / 7),  # Weekly cycle
                np.cos(2 * np.pi * record['day_of_week'] / 7),
                np.sin(2 * np.pi * record['month'] / 12),  # Monthly cycle
                np.cos(2 * np.pi * record['month'] / 12)
            ]
            X.append(features)
            y.append(record['demand'])
        
        return np.array(X), np.array(y)
    
    def train(self, history):
        """Train the ML model on historical data"""
        X, y = self.prepare_features(history)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Calculate R² score
        score = self.model.score(X_scaled, y)
        return score
    
    def predict_future(self, history, days_ahead=30):
        """Predict future demand"""
        predictions = []
        last_date = datetime.strptime(history[-1]['date'], '%Y-%m-%d')
        last_index = len(history) - 1
        
        for i in range(1, days_ahead + 1):
            future_date = last_date + timedelta(days=i)
            
            features = [
                last_index + i,
                future_date.weekday(),
                future_date.month,
                future_date.day,
                np.sin(2 * np.pi * future_date.weekday() / 7),
                np.cos(2 * np.pi * future_date.weekday() / 7),
                np.sin(2 * np.pi * future_date.month / 12),
                np.cos(2 * np.pi * future_date.month / 12)
            ]
            
            X_pred = self.scaler.transform([features])
            demand = max(0, self.model.predict(X_pred)[0])
            
            predictions.append({
                'date': future_date.strftime('%Y-%m-%d'),
                'predicted_demand': round(demand, 2),
                'day_name': future_date.strftime('%A')
            })
        
        return predictions
    
    def get_insights(self, history, predictions, current_quantity):
        """Generate insights from predictions"""
        # Calculate average predicted demand
        avg_demand = np.mean([p['predicted_demand'] for p in predictions[:7]])
        total_7day_demand = sum([p['predicted_demand'] for p in predictions[:7]])
        total_30day_demand = sum([p['predicted_demand'] for p in predictions])
        
        # Days until stockout
        days_until_stockout = int(current_quantity / avg_demand) if avg_demand > 0 else 999
        
        # Reorder recommendation
        reorder_point = avg_demand * 7  # 7 days safety stock
        should_reorder = current_quantity < reorder_point
        recommended_quantity = max(0, total_30day_demand - current_quantity)
        
        # Trend analysis
        recent_avg = np.mean([h['demand'] for h in history[-7:]])
        trend = "increasing" if avg_demand > recent_avg else "decreasing" if avg_demand < recent_avg else "stable"
        
        return {
            'average_daily_demand': round(avg_demand, 2),
            'predicted_7day_demand': round(total_7day_demand, 2),
            'predicted_30day_demand': round(total_30day_demand, 2),
            'days_until_stockout': days_until_stockout,
            'should_reorder': should_reorder,
            'recommended_order_quantity': round(recommended_quantity, 2),
            'trend': trend,
            'confidence': 'high' if len(history) >= 30 else 'medium'
        }
    
    def predict_item(self, item_id, current_quantity):
        """Complete prediction pipeline for an item"""
        # Generate historical data
        history = self.generate_historical_data(item_id, current_quantity)
        
        # Train model
        score = self.train(history)
        
        # Make predictions
        predictions_7day = self.predict_future(history, days_ahead=7)
        predictions_30day = self.predict_future(history, days_ahead=30)
        
        # Get insights
        insights = self.get_insights(history, predictions_30day, current_quantity)
        
        return {
            'item_id': item_id,
            'current_quantity': current_quantity,
            'model_accuracy': round(score * 100, 2),
            'historical_data': history[-14:],  # Last 14 days
            'predictions_7day': predictions_7day,
            'predictions_30day': predictions_30day,
            'insights': insights
        }
