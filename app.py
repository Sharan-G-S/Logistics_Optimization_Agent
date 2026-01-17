"""
Flask API for Logistics Optimization Agent
Provides REST endpoints for route optimization and inventory management
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

from models import (
    generate_sample_locations, generate_sample_vehicles, 
    generate_sample_inventory, generate_sample_warehouses,
    Location, Vehicle
)
from route_optimizer import RouteOptimizer
from inventory_manager import InventoryManager
from ml_predictor import MLDemandPredictor

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize systems
route_optimizer = RouteOptimizer()
inventory_manager = InventoryManager()
ml_predictor = MLDemandPredictor()

# Load sample data
locations = generate_sample_locations()
vehicles = generate_sample_vehicles()
inventory_items = generate_sample_inventory()
warehouses = generate_sample_warehouses()

# Initialize inventory manager
for item in inventory_items:
    inventory_manager.add_item(item)

for warehouse in warehouses:
    inventory_manager.add_warehouse(warehouse)

# Simulate some demand history for better forecasting
inventory_manager.simulate_demand(30)

# Store routes in memory (in production, use a database)
routes_db = []


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Logistics Optimization Agent"
    })


@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all available locations"""
    return jsonify({
        "locations": [
            {
                "name": loc.name,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "address": loc.address
            }
            for loc in locations
        ]
    })


@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    """Get all vehicles"""
    return jsonify({
        "vehicles": [
            {
                "id": v.id,
                "name": v.name,
                "capacity": v.capacity,
                "current_load": v.current_load,
                "available_capacity": v.available_capacity(),
                "status": v.status
            }
            for v in vehicles
        ]
    })


@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    """
    Optimize delivery route
    
    Request body:
    {
        "start": "Depot A",
        "destinations": ["Customer 1", "Customer 2", ...],
        "vehicle_id": "V001",  # optional
        "algorithm": "genetic"  # dijkstra, astar, or genetic
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('start') or not data.get('destinations'):
            return jsonify({"error": "Missing required fields: start and destinations"}), 400
        
        # Find locations
        start_loc = next((loc for loc in locations if loc.name == data['start']), None)
        if not start_loc:
            return jsonify({"error": f"Start location '{data['start']}' not found"}), 404
        
        dest_locs = []
        for dest_name in data['destinations']:
            dest = next((loc for loc in locations if loc.name == dest_name), None)
            if dest:
                dest_locs.append(dest)
        
        if not dest_locs:
            return jsonify({"error": "No valid destinations found"}), 404
        
        # Find vehicle if specified
        vehicle = None
        if data.get('vehicle_id'):
            vehicle = next((v for v in vehicles if v.id == data['vehicle_id']), None)
        
        # Get algorithm
        algorithm = data.get('algorithm', 'genetic')
        
        # Optimize route
        route = route_optimizer.optimize_route(
            start_loc, dest_locs, vehicle, algorithm
        )
        
        # Store route
        routes_db.append(route)
        
        # Return result
        return jsonify({
            "success": True,
            "route": {
                "id": route.id,
                "vehicle": {
                    "id": route.vehicle.id,
                    "name": route.vehicle.name
                },
                "stops": [
                    {
                        "name": stop.name,
                        "latitude": stop.latitude,
                        "longitude": stop.longitude,
                        "address": stop.address
                    }
                    for stop in route.stops
                ],
                "total_distance": route.total_distance,
                "estimated_time": route.estimated_time,
                "status": route.status,
                "algorithm_used": algorithm
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/routes', methods=['GET'])
def get_routes():
    """Get all routes"""
    return jsonify({
        "routes": [
            {
                "id": route.id,
                "vehicle_id": route.vehicle.id,
                "vehicle_name": route.vehicle.name,
                "stops_count": len(route.stops),
                "total_distance": route.total_distance,
                "estimated_time": route.estimated_time,
                "status": route.status,
                "created_at": route.created_at.isoformat()
            }
            for route in routes_db
        ]
    })


@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get all inventory items"""
    items = inventory_manager.get_all_items()
    
    return jsonify({
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "sku": item.sku,
                "quantity": item.quantity,
                "unit": item.unit,
                "reorder_point": item.reorder_point,
                "warehouse": item.warehouse,
                "category": item.category,
                "status": item.stock_status(),
                "is_low_stock": item.is_low_stock(),
                "last_updated": item.last_updated.isoformat()
            }
            for item in items
        ],
        "total_items": len(items),
        "low_stock_count": len(inventory_manager.get_low_stock_items()),
        "out_of_stock_count": len(inventory_manager.get_out_of_stock_items())
    })


@app.route('/api/inventory/<item_id>', methods=['GET'])
def get_inventory_item(item_id):
    """Get specific inventory item"""
    item = inventory_manager.get_item(item_id)
    
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify({
        "id": item.id,
        "name": item.name,
        "sku": item.sku,
        "quantity": item.quantity,
        "unit": item.unit,
        "reorder_point": item.reorder_point,
        "warehouse": item.warehouse,
        "category": item.category,
        "status": item.stock_status(),
        "is_low_stock": item.is_low_stock(),
        "last_updated": item.last_updated.isoformat()
    })


@app.route('/api/inventory/<item_id>/update', methods=['POST'])
def update_inventory(item_id):
    """
    Update inventory quantity
    
    Request body:
    {
        "quantity_change": 10  # positive for additions, negative for consumption
    }
    """
    try:
        data = request.get_json()
        quantity_change = data.get('quantity_change', 0)
        
        success = inventory_manager.update_quantity(item_id, quantity_change)
        
        if success:
            item = inventory_manager.get_item(item_id)
            return jsonify({
                "success": True,
                "item": {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "status": item.stock_status()
                }
            })
        else:
            return jsonify({"error": "Failed to update inventory"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/inventory/forecast/<item_id>', methods=['GET'])
def forecast_inventory(item_id):
    """Get demand forecast for an item"""
    days = request.args.get('days', default=7, type=int)
    
    forecast = inventory_manager.forecast_demand(item_id, days)
    
    if "error" in forecast:
        return jsonify(forecast), 404
    
    return jsonify(forecast)


@app.route('/api/inventory/alerts', methods=['GET'])
def get_inventory_alerts():
    """Get all inventory alerts"""
    alerts = inventory_manager.get_inventory_alerts()
    
    return jsonify({
        "alerts": alerts,
        "total_alerts": len(alerts),
        "critical_count": len([a for a in alerts if a['severity'] == 'critical']),
        "warning_count": len([a for a in alerts if a['severity'] == 'warning'])
    })


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get logistics analytics and KPIs"""
    
    # Calculate various metrics
    total_routes = len(routes_db)
    total_distance = sum(route.total_distance for route in routes_db)
    avg_distance = total_distance / total_routes if total_routes > 0 else 0
    
    active_vehicles = len([v for v in vehicles if v.status == "available"])
    total_vehicles = len(vehicles)
    
    inventory_items_count = len(inventory_manager.get_all_items())
    low_stock_count = len(inventory_manager.get_low_stock_items())
    out_of_stock_count = len(inventory_manager.get_out_of_stock_items())
    
    # Get warehouse stats
    warehouse_stats = []
    for wh in warehouses:
        stats = inventory_manager.get_warehouse_utilization(wh.id)
        warehouse_stats.append(stats)
    
    return jsonify({
        "routes": {
            "total": total_routes,
            "total_distance_km": round(total_distance, 2),
            "average_distance_km": round(avg_distance, 2),
            "total_estimated_hours": round(sum(r.estimated_time for r in routes_db), 2)
        },
        "vehicles": {
            "total": total_vehicles,
            "available": active_vehicles,
            "in_use": len([v for v in vehicles if v.status == "in_transit"]),
            "maintenance": len([v for v in vehicles if v.status == "maintenance"])
        },
        "inventory": {
            "total_items": inventory_items_count,
            "low_stock": low_stock_count,
            "out_of_stock": out_of_stock_count,
            "stock_health_percentage": round(
                ((inventory_items_count - low_stock_count - out_of_stock_count) / 
                 inventory_items_count * 100) if inventory_items_count > 0 else 0, 
                2
            )
        },
        "warehouses": warehouse_stats
    })


@app.route('/api/analytics/route-efficiency', methods=['GET'])
def get_route_efficiency():
    """Get route efficiency metrics over time"""
    
    # Group routes by date
    route_data = []
    for route in routes_db[-10:]:  # Last 10 routes
        route_data.append({
            "date": route.created_at.strftime("%Y-%m-%d %H:%M"),
            "distance": route.total_distance,
            "time": route.estimated_time,
            "stops": len(route.stops)
        })
    
    return jsonify({
        "route_history": route_data
    })


@app.route('/api/gps/vehicles', methods=['GET'])
def get_gps_tracking():
    """Get real-time GPS tracking data for all vehicles"""
    import random
    import time
    
    # Simulate GPS coordinates for vehicles
    # In production, this would connect to actual GPS devices
    gps_data = []
    
    for vehicle in vehicles:
        if vehicle.status in ["available", "in_transit"]:
            # Base coordinates (Bangalore area)
            base_lat = 12.9716
            base_lng = 77.5946
            
            # Add random offset to simulate movement
            offset = hash(vehicle.id + str(int(time.time() / 10))) % 1000 / 10000
            
            gps_data.append({
                "vehicle_id": vehicle.id,
                "vehicle_name": vehicle.name,
                "latitude": base_lat + offset,
                "longitude": base_lng + offset,
                "speed": random.randint(20, 60),  # km/h
                "status": vehicle.status,
                "last_update": datetime.now().isoformat(),
                "battery": random.randint(60, 100),  # percentage
                "current_load": vehicle.current_load,
                "capacity": vehicle.capacity
            })
    
    return jsonify({
        "vehicles": gps_data,
        "total_tracked": len(gps_data),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/ml/predict/<item_id>', methods=['GET'])
def ml_predict_demand(item_id):
    """Get ML-based demand prediction for an item"""
    try:
        item = inventory_manager.get_item(item_id)
        
        if not item:
            return jsonify({"error": "Item not found"}), 404
        
        # Get ML prediction
        prediction = ml_predictor.predict_item(item_id, item.quantity)
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy types
                return obj.item()
            elif isinstance(obj, (bool, int, float, str)):
                return obj
            else:
                return str(obj)
        
        prediction_json = convert_numpy_types(prediction)
        
        return jsonify(prediction_json)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/ml/insights', methods=['GET'])
def ml_get_insights():
    """Get overall ML insights for all inventory items"""
    try:
        items = inventory_manager.get_all_items()
        
        insights = []
        for item in items[:5]:  # Top 5 items for performance
            prediction = ml_predictor.predict_item(item.id, item.quantity)
            insights.append({
                "item_id": item.id,
                "item_name": item.name,
                "current_quantity": int(item.quantity),
                "predicted_7day_demand": float(prediction['insights']['predicted_7day_demand']),
                "days_until_stockout": int(prediction['insights']['days_until_stockout']),
                "should_reorder": bool(prediction['insights']['should_reorder']),
                "trend": str(prediction['insights']['trend'])
            })
        
        return jsonify({
            "insights": insights,
            "total_items_analyzed": len(insights),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚚 Logistics Optimization Agent - Backend Server")
    print("=" * 60)
    print(f"Server starting at: http://localhost:5001")
    print(f"Loaded {len(locations)} locations")
    print(f"Loaded {len(vehicles)} vehicles")
    print(f"Loaded {len(inventory_items)} inventory items")
    print(f"Loaded {len(warehouses)} warehouses")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
