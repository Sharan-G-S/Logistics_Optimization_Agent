"""
Route optimization algorithms for the Logistics Optimization Agent
Implements Dijkstra's, A*, and Genetic Algorithm for route planning
"""
import math
import random
from typing import List, Tuple, Dict, Optional
from models import Location, Vehicle, Route
import heapq
from datetime import datetime

class RouteOptimizer:
    """Handles route optimization using various algorithms"""
    
    def __init__(self):
        self.distance_cache = {}
    
    def calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate Haversine distance between two locations in kilometers"""
        cache_key = (loc1.name, loc2.name)
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1 = math.radians(loc1.latitude), math.radians(loc1.longitude)
        lat2, lon2 = math.radians(loc2.latitude), math.radians(loc2.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        self.distance_cache[cache_key] = distance
        self.distance_cache[(loc2.name, loc1.name)] = distance  # Symmetric
        
        return distance
    
    def build_distance_matrix(self, locations: List[Location]) -> Dict[Tuple[str, str], float]:
        """Build a distance matrix for all location pairs"""
        matrix = {}
        for i, loc1 in enumerate(locations):
            for loc2 in locations[i:]:
                dist = self.calculate_distance(loc1, loc2)
                matrix[(loc1.name, loc2.name)] = dist
                matrix[(loc2.name, loc1.name)] = dist
        return matrix
    
    def dijkstra(self, start: Location, destinations: List[Location], 
                 all_locations: List[Location]) -> Tuple[List[Location], float]:
        """
        Find shortest path using Dijkstra's algorithm
        Returns: (ordered_locations, total_distance)
        """
        if not destinations:
            return [start], 0.0
        
        # Build graph
        all_locs = [start] + destinations
        distance_matrix = self.build_distance_matrix(all_locs)
        
        # Find shortest path visiting all destinations
        unvisited = set(dest.name for dest in destinations)
        current = start
        path = [start]
        total_distance = 0.0
        
        while unvisited:
            # Find nearest unvisited location
            nearest = None
            min_dist = float('inf')
            
            for loc_name in unvisited:
                dist = distance_matrix.get((current.name, loc_name), float('inf'))
                if dist < min_dist:
                    min_dist = dist
                    nearest = loc_name
            
            if nearest:
                # Find the location object
                next_loc = next(loc for loc in destinations if loc.name == nearest)
                path.append(next_loc)
                total_distance += min_dist
                current = next_loc
                unvisited.remove(nearest)
        
        return path, total_distance
    
    def a_star(self, start: Location, destinations: List[Location],
               all_locations: List[Location]) -> Tuple[List[Location], float]:
        """
        Find optimal path using A* algorithm with heuristic
        Returns: (ordered_locations, total_distance)
        """
        if not destinations:
            return [start], 0.0
        
        # Use nearest neighbor heuristic
        unvisited = set(dest.name for dest in destinations)
        current = start
        path = [start]
        total_distance = 0.0
        
        distance_matrix = self.build_distance_matrix([start] + destinations)
        
        while unvisited:
            # Calculate f(n) = g(n) + h(n) for each unvisited location
            # g(n) = actual distance from current
            # h(n) = heuristic (distance to furthest remaining location)
            
            best_loc = None
            best_score = float('inf')
            
            for loc_name in unvisited:
                loc = next(l for l in destinations if l.name == loc_name)
                g_score = distance_matrix.get((current.name, loc_name), float('inf'))
                
                # Heuristic: average distance to remaining locations
                h_score = 0
                remaining = [l for l in destinations if l.name in unvisited and l.name != loc_name]
                if remaining:
                    h_score = sum(self.calculate_distance(loc, r) for r in remaining) / len(remaining)
                
                f_score = g_score + h_score * 0.5  # Weight the heuristic
                
                if f_score < best_score:
                    best_score = f_score
                    best_loc = loc
                    best_dist = g_score
            
            if best_loc:
                path.append(best_loc)
                total_distance += best_dist
                current = best_loc
                unvisited.remove(best_loc.name)
        
        return path, total_distance
    
    def genetic_algorithm(self, start: Location, destinations: List[Location],
                         all_locations: List[Location], 
                         population_size: int = 50, 
                         generations: int = 100) -> Tuple[List[Location], float]:
        """
        Find optimal route using Genetic Algorithm
        Returns: (ordered_locations, total_distance)
        """
        if not destinations:
            return [start], 0.0
        
        if len(destinations) == 1:
            dist = self.calculate_distance(start, destinations[0])
            return [start, destinations[0]], dist
        
        distance_matrix = self.build_distance_matrix([start] + destinations)
        
        def calculate_route_distance(route: List[Location]) -> float:
            """Calculate total distance for a route"""
            total = 0.0
            for i in range(len(route) - 1):
                total += distance_matrix.get((route[i].name, route[i+1].name), 0)
            return total
        
        def create_individual() -> List[Location]:
            """Create a random route (chromosome)"""
            route = destinations.copy()
            random.shuffle(route)
            return [start] + route
        
        def crossover(parent1: List[Location], parent2: List[Location]) -> List[Location]:
            """Perform ordered crossover"""
            size = len(destinations)
            if size <= 1:
                return parent1
            
            # Select a random subset from parent1
            start_idx = random.randint(1, size)
            end_idx = random.randint(start_idx, size)
            
            child = [start] + [None] * size
            child[start_idx:end_idx+1] = parent1[start_idx:end_idx+1]
            
            # Fill remaining positions from parent2
            p2_idx = 1
            for i in range(1, size + 1):
                if child[i] is None:
                    while parent2[p2_idx] in child:
                        p2_idx += 1
                    child[i] = parent2[p2_idx]
            
            return child
        
        def mutate(route: List[Location], mutation_rate: float = 0.1) -> List[Location]:
            """Swap two random locations"""
            if random.random() < mutation_rate and len(route) > 2:
                route = route.copy()
                idx1, idx2 = random.sample(range(1, len(route)), 2)
                route[idx1], route[idx2] = route[idx2], route[idx1]
            return route
        
        # Initialize population
        population = [create_individual() for _ in range(population_size)]
        
        # Evolution
        for generation in range(generations):
            # Calculate fitness (inverse of distance)
            fitness_scores = [(ind, 1.0 / (calculate_route_distance(ind) + 1)) 
                            for ind in population]
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Selection: keep top 20%
            elite_size = population_size // 5
            new_population = [ind for ind, _ in fitness_scores[:elite_size]]
            
            # Crossover and mutation
            while len(new_population) < population_size:
                parent1 = random.choice(fitness_scores[:population_size//2])[0]
                parent2 = random.choice(fitness_scores[:population_size//2])[0]
                child = crossover(parent1, parent2)
                child = mutate(child)
                new_population.append(child)
            
            population = new_population
        
        # Return best solution
        best_route = min(population, key=calculate_route_distance)
        best_distance = calculate_route_distance(best_route)
        
        return best_route, best_distance
    
    def optimize_route(self, start: Location, destinations: List[Location],
                      vehicle: Optional[Vehicle] = None,
                      algorithm: str = "genetic") -> Route:
        """
        Main optimization method
        
        Args:
            start: Starting location (depot)
            destinations: List of delivery locations
            vehicle: Vehicle to use (optional)
            algorithm: Algorithm to use ('dijkstra', 'astar', 'genetic')
        
        Returns:
            Optimized Route object
        """
        all_locations = [start] + destinations
        
        # Select algorithm
        if algorithm.lower() == "dijkstra":
            optimized_path, total_distance = self.dijkstra(start, destinations, all_locations)
        elif algorithm.lower() == "astar":
            optimized_path, total_distance = self.a_star(start, destinations, all_locations)
        else:  # genetic (default)
            optimized_path, total_distance = self.genetic_algorithm(start, destinations, all_locations)
        
        # Calculate estimated time (assuming average speed of 40 km/h in city)
        avg_speed = 40  # km/h
        estimated_time = total_distance / avg_speed
        
        # Add time for stops (15 minutes per stop)
        estimated_time += (len(destinations) * 0.25)
        
        # Create route object
        route = Route(
            id=f"ROUTE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            vehicle=vehicle or Vehicle("V000", "Unassigned", 1000),
            stops=optimized_path,
            total_distance=round(total_distance, 2),
            estimated_time=round(estimated_time, 2),
            status="planned"
        )
        
        return route
    
    def optimize_multi_vehicle(self, depot: Location, destinations: List[Location],
                              vehicles: List[Vehicle]) -> List[Route]:
        """
        Optimize routes for multiple vehicles
        Distributes destinations among available vehicles
        """
        if not vehicles or not destinations:
            return []
        
        # Simple distribution: divide destinations among vehicles
        routes = []
        dests_per_vehicle = len(destinations) // len(vehicles)
        remainder = len(destinations) % len(vehicles)
        
        start_idx = 0
        for i, vehicle in enumerate(vehicles):
            if vehicle.status != "available":
                continue
            
            # Allocate destinations
            count = dests_per_vehicle + (1 if i < remainder else 0)
            vehicle_dests = destinations[start_idx:start_idx + count]
            start_idx += count
            
            if vehicle_dests:
                route = self.optimize_route(depot, vehicle_dests, vehicle, "genetic")
                routes.append(route)
        
        return routes
