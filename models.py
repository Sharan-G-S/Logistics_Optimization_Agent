"""
Data models and structures for the Logistics Optimization Agent
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime
import random

@dataclass
class Location:
    """Represents a geographical location"""
    name: str
    latitude: float
    longitude: float
    address: str = ""
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return isinstance(other, Location) and self.name == other.name

@dataclass
class Vehicle:
    """Represents a delivery vehicle"""
    id: str
    name: str
    capacity: float  # in kg or cubic meters
    current_load: float = 0.0
    status: str = "available"  # available, in_transit, maintenance
    location: Optional[Location] = None
    
    def available_capacity(self) -> float:
        return self.capacity - self.current_load

@dataclass
class Route:
    """Represents a delivery route"""
    id: str
    vehicle: Vehicle
    stops: List[Location]
    total_distance: float
    estimated_time: float  # in hours
    status: str = "planned"  # planned, in_progress, completed
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class InventoryItem:
    """Represents an inventory item"""
    id: str
    name: str
    sku: str
    quantity: int
    unit: str
    reorder_point: int
    warehouse: str
    category: str
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def is_low_stock(self) -> bool:
        return self.quantity <= self.reorder_point
    
    def stock_status(self) -> str:
        if self.quantity == 0:
            return "out_of_stock"
        elif self.is_low_stock():
            return "low_stock"
        else:
            return "in_stock"

@dataclass
class Order:
    """Represents a customer order"""
    id: str
    customer_name: str
    delivery_location: Location
    items: List[Tuple[str, int]]  # (item_id, quantity)
    total_weight: float
    priority: str = "normal"  # low, normal, high, urgent
    status: str = "pending"  # pending, assigned, in_transit, delivered
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Warehouse:
    """Represents a warehouse or depot"""
    id: str
    name: str
    location: Location
    capacity: float
    current_utilization: float = 0.0
    
    def utilization_percentage(self) -> float:
        return (self.current_utilization / self.capacity) * 100 if self.capacity > 0 else 0


# Sample data generators
def generate_sample_locations() -> List[Location]:
    """Generate sample delivery locations"""
    locations = [
        Location("Depot A", 12.9716, 77.5946, "Main Warehouse, Bangalore"),
        Location("Depot B", 13.0358, 77.5970, "North Warehouse, Bangalore"),
        Location("Customer 1", 12.9352, 77.6245, "Electronics Store, Indiranagar"),
        Location("Customer 2", 12.9698, 77.6480, "Retail Shop, Whitefield"),
        Location("Customer 3", 12.9141, 77.6411, "Supermarket, HSR Layout"),
        Location("Customer 4", 13.0189, 77.6410, "Mall, Hebbal"),
        Location("Customer 5", 12.9279, 77.6271, "Office Complex, Koramangala"),
        Location("Customer 6", 12.9833, 77.6412, "Shopping Center, Banaswadi"),
        Location("Customer 7", 12.9539, 77.6619, "Restaurant, Marathahalli"),
        Location("Customer 8", 12.8996, 77.6354, "Warehouse, Bommanahalli"),
    ]
    return locations

def generate_sample_vehicles() -> List[Vehicle]:
    """Generate sample vehicles"""
    vehicles = [
        Vehicle("V001", "Truck Alpha", 1000, 0, "available"),
        Vehicle("V002", "Truck Beta", 1500, 0, "available"),
        Vehicle("V003", "Van Gamma", 500, 0, "available"),
        Vehicle("V004", "Truck Delta", 1200, 0, "available"),
        Vehicle("V005", "Van Epsilon", 600, 0, "maintenance"),
    ]
    return vehicles

def generate_sample_inventory() -> List[InventoryItem]:
    """Generate sample inventory items"""
    categories = ["Electronics", "Food & Beverage", "Clothing", "Hardware", "Medical"]
    items = []
    
    inventory_data = [
        ("Laptop Computer", "ELEC-001", 45, "units", 20, "Depot A", "Electronics"),
        ("Smartphone", "ELEC-002", 120, "units", 50, "Depot A", "Electronics"),
        ("Headphones", "ELEC-003", 15, "units", 30, "Depot B", "Electronics"),
        ("Coffee Beans", "FOOD-001", 200, "kg", 100, "Depot A", "Food & Beverage"),
        ("Bottled Water", "FOOD-002", 500, "units", 200, "Depot B", "Food & Beverage"),
        ("T-Shirts", "CLTH-001", 300, "units", 100, "Depot A", "Clothing"),
        ("Jeans", "CLTH-002", 150, "units", 50, "Depot B", "Clothing"),
        ("Power Tools", "HARD-001", 80, "units", 30, "Depot A", "Hardware"),
        ("Screwdriver Set", "HARD-002", 25, "units", 40, "Depot B", "Hardware"),
        ("First Aid Kit", "MED-001", 60, "units", 50, "Depot A", "Medical"),
        ("Face Masks", "MED-002", 1000, "units", 500, "Depot B", "Medical"),
        ("Hand Sanitizer", "MED-003", 8, "liters", 50, "Depot A", "Medical"),
    ]
    
    for i, (name, sku, qty, unit, reorder, warehouse, category) in enumerate(inventory_data):
        items.append(InventoryItem(
            id=f"INV-{i+1:03d}",
            name=name,
            sku=sku,
            quantity=qty,
            unit=unit,
            reorder_point=reorder,
            warehouse=warehouse,
            category=category
        ))
    
    return items

def generate_sample_warehouses() -> List[Warehouse]:
    """Generate sample warehouses"""
    locations = generate_sample_locations()
    warehouses = [
        Warehouse("WH-001", "Depot A", locations[0], 10000, 6500),
        Warehouse("WH-002", "Depot B", locations[1], 8000, 5200),
    ]
    return warehouses
