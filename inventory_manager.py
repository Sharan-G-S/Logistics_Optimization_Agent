"""
Inventory management system for the Logistics Optimization Agent
Handles stock tracking, forecasting, and alerts
"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from models import InventoryItem, Warehouse
import random

class InventoryManager:
    """Manages inventory tracking, forecasting, and alerts"""
    
    def __init__(self):
        self.inventory: Dict[str, InventoryItem] = {}
        self.warehouses: Dict[str, Warehouse] = {}
        self.demand_history: Dict[str, List[Tuple[datetime, int]]] = {}
    
    def add_item(self, item: InventoryItem) -> None:
        """Add or update an inventory item"""
        self.inventory[item.id] = item
        if item.id not in self.demand_history:
            self.demand_history[item.id] = []
    
    def get_item(self, item_id: str) -> Optional[InventoryItem]:
        """Get an inventory item by ID"""
        return self.inventory.get(item_id)
    
    def get_all_items(self) -> List[InventoryItem]:
        """Get all inventory items"""
        return list(self.inventory.values())
    
    def update_quantity(self, item_id: str, quantity_change: int) -> bool:
        """
        Update item quantity (positive for additions, negative for consumption)
        Returns True if successful, False if insufficient stock
        """
        item = self.inventory.get(item_id)
        if not item:
            return False
        
        new_quantity = item.quantity + quantity_change
        if new_quantity < 0:
            return False
        
        item.quantity = new_quantity
        item.last_updated = datetime.now()
        
        # Record demand if it's a consumption
        if quantity_change < 0:
            self.demand_history[item_id].append((datetime.now(), abs(quantity_change)))
        
        return True
    
    def get_low_stock_items(self) -> List[InventoryItem]:
        """Get all items that are at or below reorder point"""
        return [item for item in self.inventory.values() if item.is_low_stock()]
    
    def get_out_of_stock_items(self) -> List[InventoryItem]:
        """Get all items that are out of stock"""
        return [item for item in self.inventory.values() if item.quantity == 0]
    
    def get_items_by_warehouse(self, warehouse: str) -> List[InventoryItem]:
        """Get all items in a specific warehouse"""
        return [item for item in self.inventory.values() if item.warehouse == warehouse]
    
    def get_items_by_category(self, category: str) -> List[InventoryItem]:
        """Get all items in a specific category"""
        return [item for item in self.inventory.values() if item.category == category]
    
    def calculate_inventory_value(self, price_map: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate total inventory value
        If price_map not provided, uses estimated values
        """
        if not price_map:
            # Use estimated prices for demo
            price_map = {item.id: random.uniform(10, 500) for item in self.inventory.values()}
        
        total_value = 0.0
        for item in self.inventory.values():
            price = price_map.get(item.id, 0)
            total_value += price * item.quantity
        
        return total_value
    
    def forecast_demand(self, item_id: str, days_ahead: int = 7) -> Dict[str, any]:
        """
        Forecast demand for an item using moving average
        
        Returns:
            Dictionary with forecast data including predicted demand and reorder recommendation
        """
        item = self.inventory.get(item_id)
        if not item:
            return {"error": "Item not found"}
        
        history = self.demand_history.get(item_id, [])
        
        # If no history, use simple estimation
        if len(history) < 3:
            # Estimate based on current stock and reorder point
            avg_daily_demand = max(1, item.reorder_point // 7)
            predicted_demand = avg_daily_demand * days_ahead
            
            return {
                "item_id": item_id,
                "item_name": item.name,
                "current_quantity": item.quantity,
                "forecast_days": days_ahead,
                "predicted_demand": predicted_demand,
                "estimated_stock_after": max(0, item.quantity - predicted_demand),
                "reorder_recommended": item.quantity < (predicted_demand + item.reorder_point),
                "confidence": "low",
                "method": "estimation"
            }
        
        # Calculate moving average from recent history
        recent_history = history[-30:]  # Last 30 transactions
        total_demand = sum(qty for _, qty in recent_history)
        days_span = (recent_history[-1][0] - recent_history[0][0]).days or 1
        
        avg_daily_demand = total_demand / max(1, days_span)
        predicted_demand = int(avg_daily_demand * days_ahead)
        
        # Calculate stock after forecast period
        estimated_stock = item.quantity - predicted_demand
        
        # Determine if reorder is needed
        safety_stock = item.reorder_point
        reorder_recommended = estimated_stock < safety_stock
        
        # Calculate optimal reorder quantity (Economic Order Quantity simplified)
        if reorder_recommended:
            reorder_quantity = max(
                item.reorder_point * 2,  # At least 2x reorder point
                int(avg_daily_demand * 14)  # Or 2 weeks of demand
            )
        else:
            reorder_quantity = 0
        
        return {
            "item_id": item_id,
            "item_name": item.name,
            "current_quantity": item.quantity,
            "forecast_days": days_ahead,
            "avg_daily_demand": round(avg_daily_demand, 2),
            "predicted_demand": predicted_demand,
            "estimated_stock_after": max(0, estimated_stock),
            "reorder_recommended": reorder_recommended,
            "recommended_order_quantity": reorder_quantity,
            "confidence": "high" if len(history) > 10 else "medium",
            "method": "moving_average",
            "data_points": len(history)
        }
    
    def get_inventory_alerts(self) -> List[Dict[str, any]]:
        """
        Get all inventory alerts (low stock, out of stock, etc.)
        """
        alerts = []
        
        # Out of stock alerts
        for item in self.get_out_of_stock_items():
            alerts.append({
                "severity": "critical",
                "type": "out_of_stock",
                "item_id": item.id,
                "item_name": item.name,
                "message": f"{item.name} is out of stock",
                "warehouse": item.warehouse,
                "timestamp": datetime.now().isoformat()
            })
        
        # Low stock alerts
        for item in self.get_low_stock_items():
            if item.quantity > 0:  # Not already counted in out of stock
                alerts.append({
                    "severity": "warning",
                    "type": "low_stock",
                    "item_id": item.id,
                    "item_name": item.name,
                    "message": f"{item.name} is below reorder point ({item.quantity}/{item.reorder_point})",
                    "warehouse": item.warehouse,
                    "current_quantity": item.quantity,
                    "reorder_point": item.reorder_point,
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def get_inventory_turnover(self, item_id: str, days: int = 30) -> Dict[str, any]:
        """
        Calculate inventory turnover rate for an item
        """
        item = self.inventory.get(item_id)
        if not item:
            return {"error": "Item not found"}
        
        history = self.demand_history.get(item_id, [])
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_demand = [qty for date, qty in history if date >= cutoff_date]
        total_sold = sum(recent_demand)
        
        avg_inventory = item.quantity  # Simplified - would need historical inventory levels
        
        if avg_inventory > 0:
            turnover_rate = total_sold / avg_inventory
        else:
            turnover_rate = 0
        
        return {
            "item_id": item_id,
            "item_name": item.name,
            "period_days": days,
            "total_sold": total_sold,
            "average_inventory": avg_inventory,
            "turnover_rate": round(turnover_rate, 2),
            "turnover_category": self._categorize_turnover(turnover_rate)
        }
    
    def _categorize_turnover(self, rate: float) -> str:
        """Categorize turnover rate"""
        if rate > 4:
            return "fast_moving"
        elif rate > 1:
            return "moderate"
        else:
            return "slow_moving"
    
    def get_warehouse_utilization(self, warehouse_id: str) -> Dict[str, any]:
        """Get warehouse utilization statistics"""
        warehouse = self.warehouses.get(warehouse_id)
        if not warehouse:
            return {"error": "Warehouse not found"}
        
        items = self.get_items_by_warehouse(warehouse.name)
        
        return {
            "warehouse_id": warehouse_id,
            "warehouse_name": warehouse.name,
            "capacity": warehouse.capacity,
            "current_utilization": warehouse.current_utilization,
            "utilization_percentage": round(warehouse.utilization_percentage(), 2),
            "total_items": len(items),
            "low_stock_items": len([i for i in items if i.is_low_stock()]),
            "out_of_stock_items": len([i for i in items if i.quantity == 0])
        }
    
    def add_warehouse(self, warehouse: Warehouse) -> None:
        """Add a warehouse to the system"""
        self.warehouses[warehouse.id] = warehouse
    
    def simulate_demand(self, days: int = 30) -> None:
        """
        Simulate historical demand for demo purposes
        Generates random demand history for all items
        """
        for item_id, item in self.inventory.items():
            # Generate random demand history
            for day in range(days):
                date = datetime.now() - timedelta(days=days - day)
                # Random demand based on item's reorder point
                demand = random.randint(0, max(1, item.reorder_point // 5))
                if demand > 0:
                    self.demand_history[item_id].append((date, demand))
