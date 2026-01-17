/**
 * Logistics Optimization Agent - Frontend JavaScript
 * Handles UI interactions and API communication
 */

const API_BASE_URL = 'http://localhost:5001/api';

// State management
const state = {
    locations: [],
    vehicles: [],
    inventory: [],
    routes: [],
    currentRoute: null
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    loadInitialData();
    setupEventListeners();
});

// Navigation
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const section = item.dataset.section;
            switchSection(section);

            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function switchSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show selected section
    const section = document.getElementById(`section-${sectionName}`);
    if (section) {
        section.classList.add('active');
    }

    // Update page title
    const titles = {
        dashboard: { title: 'Dashboard', subtitle: 'Real-time logistics overview' },
        routes: { title: 'Route Planner', subtitle: 'Optimize delivery routes' },
        inventory: { title: 'Inventory Management', subtitle: 'Track and manage stock levels' },
        analytics: { title: 'Analytics', subtitle: 'Performance insights and metrics' }
    };

    const titleInfo = titles[sectionName] || titles.dashboard;
    document.getElementById('page-title').textContent = titleInfo.title;
    document.getElementById('page-subtitle').textContent = titleInfo.subtitle;

    // Load section-specific data
    if (sectionName === 'inventory') {
        loadInventory();
    } else if (sectionName === 'analytics') {
        loadAnalytics();
    }
}

// Load initial data
async function loadInitialData() {
    try {
        await Promise.all([
            loadLocations(),
            loadVehicles(),
            loadDashboardData()
        ]);
    } catch (error) {
        console.error('Error loading initial data:', error);
        showNotification('Failed to load data. Please refresh the page.', 'error');
    }
}

async function loadLocations() {
    try {
        const response = await fetch(`${API_BASE_URL}/locations`);
        const data = await response.json();
        state.locations = data.locations;

        // Populate location dropdowns
        populateLocationDropdowns();
    } catch (error) {
        console.error('Error loading locations:', error);
    }
}

async function loadVehicles() {
    try {
        const response = await fetch(`${API_BASE_URL}/vehicles`);
        const data = await response.json();
        state.vehicles = data.vehicles;

        // Populate vehicle dropdown
        const vehicleSelect = document.getElementById('vehicle-select');
        vehicleSelect.innerHTML = '<option value="">Auto-assign</option>';
        data.vehicles.forEach(vehicle => {
            const option = document.createElement('option');
            option.value = vehicle.id;
            option.textContent = `${vehicle.name} (${vehicle.capacity}kg capacity)`;
            vehicleSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading vehicles:', error);
    }
}

function populateLocationDropdowns() {
    const startSelect = document.getElementById('start-location');

    // Populate start location (depots only)
    startSelect.innerHTML = '<option value="">Select depot...</option>';
    state.locations.filter(loc => loc.name.includes('Depot')).forEach(loc => {
        const option = document.createElement('option');
        option.value = loc.name;
        option.textContent = loc.name;
        startSelect.appendChild(option);
    });
}

// Dashboard
async function loadDashboardData() {
    try {
        const [analyticsRes, inventoryRes, alertsRes, routesRes] = await Promise.all([
            fetch(`${API_BASE_URL}/analytics`),
            fetch(`${API_BASE_URL}/inventory`),
            fetch(`${API_BASE_URL}/inventory/alerts`),
            fetch(`${API_BASE_URL}/routes`)
        ]);

        const analytics = await analyticsRes.json();
        const inventory = await inventoryRes.json();
        const alerts = await alertsRes.json();
        const routes = await routesRes.json();

        // Update KPIs
        document.getElementById('kpi-routes').textContent = analytics.routes.total;
        document.getElementById('kpi-distance').textContent = `${analytics.routes.average_distance_km.toFixed(1)} km`;
        document.getElementById('kpi-inventory').textContent = inventory.total_items;
        document.getElementById('kpi-low-stock').textContent = `${inventory.low_stock_count} low stock`;

        // Update recent routes
        displayRecentRoutes(routes.routes.slice(-5));

        // Update alerts
        displayAlerts(alerts.alerts);

        state.routes = routes.routes;
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function displayRecentRoutes(routes) {
    const container = document.getElementById('recent-routes-list');

    if (routes.length === 0) {
        container.innerHTML = '<p class="empty-state">No routes yet. Create your first route!</p>';
        return;
    }

    container.innerHTML = routes.map(route => `
        <div class="route-item">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <strong>${route.vehicle_name}</strong>
                <span style="color: var(--accent-primary);">${route.total_distance.toFixed(1)} km</span>
            </div>
            <div style="font-size: 0.875rem; color: var(--text-tertiary);">
                ${route.stops_count} stops • ${route.estimated_time.toFixed(1)} hrs
            </div>
        </div>
    `).join('');
}

function displayAlerts(alerts) {
    const container = document.getElementById('alerts-list');
    const badge = document.getElementById('alerts-count');

    badge.textContent = alerts.length;

    if (alerts.length === 0) {
        container.innerHTML = '<p class="empty-state">All inventory levels are healthy</p>';
        return;
    }

    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.severity}">
            <div style="font-weight: 600; margin-bottom: 0.25rem;">${alert.item_name}</div>
            <div style="font-size: 0.875rem; color: var(--text-tertiary);">${alert.message}</div>
        </div>
    `).join('');
}

// Route Planning
function setupEventListeners() {
    // Add destination button
    document.getElementById('add-destination').addEventListener('click', addDestinationField);

    // Route form submission
    document.getElementById('route-form').addEventListener('submit', handleRouteOptimization);

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadDashboardData();
        showNotification('Data refreshed', 'success');
    });

    // Modal close
    document.getElementById('modal-close').addEventListener('click', closeModal);

    // Inventory search
    document.getElementById('inventory-search').addEventListener('input', filterInventory);
    document.getElementById('category-filter').addEventListener('change', filterInventory);
    document.getElementById('warehouse-filter').addEventListener('change', filterInventory);
    document.getElementById('status-filter').addEventListener('change', filterInventory);
}

function addDestinationField() {
    const container = document.getElementById('destinations-container');
    const destinationItem = document.createElement('div');
    destinationItem.className = 'destination-item';

    const select = document.createElement('select');
    select.className = 'form-control destination-select';
    select.required = true;
    select.innerHTML = '<option value="">Select location...</option>';

    // Add customer locations
    state.locations.filter(loc => !loc.name.includes('Depot')).forEach(loc => {
        const option = document.createElement('option');
        option.value = loc.name;
        option.textContent = loc.name;
        select.appendChild(option);
    });

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn-remove';
    removeBtn.textContent = '×';
    removeBtn.addEventListener('click', () => destinationItem.remove());

    destinationItem.appendChild(select);
    destinationItem.appendChild(removeBtn);
    container.appendChild(destinationItem);
}

async function handleRouteOptimization(e) {
    e.preventDefault();

    const startLocation = document.getElementById('start-location').value;
    const algorithm = document.getElementById('algorithm-select').value;
    const vehicleId = document.getElementById('vehicle-select').value;

    const destinationSelects = document.querySelectorAll('.destination-select');
    const destinations = Array.from(destinationSelects)
        .map(select => select.value)
        .filter(value => value !== '');

    if (!startLocation || destinations.length === 0) {
        showNotification('Please select a start location and at least one destination', 'error');
        return;
    }

    const optimizeBtn = document.getElementById('optimize-btn');
    optimizeBtn.disabled = true;
    optimizeBtn.textContent = '⏳ Optimizing...';

    try {
        const response = await fetch(`${API_BASE_URL}/optimize-route`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start: startLocation,
                destinations: destinations,
                vehicle_id: vehicleId || undefined,
                algorithm: algorithm
            })
        });

        const data = await response.json();

        if (data.success) {
            displayRoute(data.route);
            showNotification('Route optimized successfully!', 'success');
            loadDashboardData(); // Refresh dashboard
        } else {
            showNotification('Failed to optimize route', 'error');
        }
    } catch (error) {
        console.error('Error optimizing route:', error);
        showNotification('Error optimizing route', 'error');
    } finally {
        optimizeBtn.disabled = false;
        optimizeBtn.textContent = '🚀 Optimize Route';
    }
}

function displayRoute(route) {
    const detailsContainer = document.getElementById('route-details');
    const mapContainer = document.getElementById('route-map');

    // Update stats
    document.getElementById('route-distance').textContent = `${route.total_distance} km`;
    document.getElementById('route-time').textContent = `${route.estimated_time} hrs`;
    document.getElementById('route-stops').textContent = route.stops.length;

    // Display route path
    const pathContainer = document.getElementById('route-path');
    pathContainer.innerHTML = `
        <h4 style="margin-bottom: 1rem; font-size: 1rem;">Route Sequence</h4>
        ${route.stops.map((stop, index) => `
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--gradient-primary); display: flex; align-items: center; justify-content: center; font-weight: 700;">
                    ${index + 1}
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600;">${stop.name}</div>
                    <div style="font-size: 0.875rem; color: var(--text-tertiary);">${stop.address}</div>
                </div>
            </div>
        `).join('')}
    `;

    // Create simple map visualization
    mapContainer.innerHTML = createMapVisualization(route.stops);

    detailsContainer.classList.remove('hidden');
}

function createMapVisualization(stops) {
    // Create a simple SVG visualization
    const width = 600;
    const height = 400;
    const padding = 50;

    // Calculate bounds
    const lats = stops.map(s => s.latitude);
    const lons = stops.map(s => s.longitude);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    // Scale coordinates
    const scaleX = (lon) => ((lon - minLon) / (maxLon - minLon)) * (width - 2 * padding) + padding;
    const scaleY = (lat) => height - (((lat - minLat) / (maxLat - minLat)) * (height - 2 * padding) + padding);

    // Create SVG
    let svg = `<svg width="100%" height="400" viewBox="0 0 ${width} ${height}" style="background: var(--bg-tertiary); border-radius: var(--radius-md);">`;

    // Draw route lines
    for (let i = 0; i < stops.length - 1; i++) {
        const x1 = scaleX(stops[i].longitude);
        const y1 = scaleY(stops[i].latitude);
        const x2 = scaleX(stops[i + 1].longitude);
        const y2 = scaleY(stops[i + 1].latitude);

        svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="url(#gradient)" stroke-width="3" stroke-dasharray="5,5">
            <animate attributeName="stroke-dashoffset" from="10" to="0" dur="1s" repeatCount="indefinite"/>
        </line>`;
    }

    // Draw stops
    stops.forEach((stop, index) => {
        const x = scaleX(stop.longitude);
        const y = scaleY(stop.latitude);
        const isDepot = stop.name.includes('Depot');

        svg += `
            <circle cx="${x}" cy="${y}" r="${isDepot ? 12 : 8}" fill="${isDepot ? '#6366f1' : '#8b5cf6'}" stroke="white" stroke-width="2">
                <animate attributeName="r" values="${isDepot ? '12;14;12' : '8;10;8'}" dur="2s" repeatCount="indefinite"/>
            </circle>
            <text x="${x}" y="${y - 20}" text-anchor="middle" fill="white" font-size="12" font-weight="600">${index + 1}</text>
        `;
    });

    // Add gradient definition
    svg = `<defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#6366f1;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
        </linearGradient>
    </defs>` + svg;

    svg += '</svg>';

    return svg;
}

// Inventory Management
async function loadInventory() {
    try {
        const response = await fetch(`${API_BASE_URL}/inventory`);
        const data = await response.json();
        state.inventory = data.items;

        // Populate filters
        populateInventoryFilters(data.items);

        // Display inventory
        displayInventory(data.items);
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

function populateInventoryFilters(items) {
    const categories = [...new Set(items.map(item => item.category))];
    const warehouses = [...new Set(items.map(item => item.warehouse))];

    const categoryFilter = document.getElementById('category-filter');
    categoryFilter.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        categoryFilter.appendChild(option);
    });

    const warehouseFilter = document.getElementById('warehouse-filter');
    warehouseFilter.innerHTML = '<option value="">All Warehouses</option>';
    warehouses.forEach(wh => {
        const option = document.createElement('option');
        option.value = wh;
        option.textContent = wh;
        warehouseFilter.appendChild(option);
    });
}

function displayInventory(items) {
    const container = document.getElementById('inventory-grid');

    if (items.length === 0) {
        container.innerHTML = '<p class="empty-state">No inventory items found</p>';
        return;
    }

    container.innerHTML = items.map(item => {
        const stockPercentage = (item.quantity / (item.reorder_point * 2)) * 100;

        return `
            <div class="inventory-item" onclick="showItemDetails('${item.id}')">
                <div class="inventory-item-header">
                    <div>
                        <div class="item-name">${item.name}</div>
                        <div class="item-sku">${item.sku}</div>
                    </div>
                    <span class="item-status ${item.status}">${item.status.replace('_', ' ')}</span>
                </div>
                <div class="inventory-item-body">
                    <div class="item-info">
                        <span class="item-info-label">Quantity</span>
                        <span class="item-info-value">${item.quantity} ${item.unit}</span>
                    </div>
                    <div class="item-info">
                        <span class="item-info-label">Reorder Point</span>
                        <span class="item-info-value">${item.reorder_point} ${item.unit}</span>
                    </div>
                    <div class="item-info">
                        <span class="item-info-label">Warehouse</span>
                        <span class="item-info-value">${item.warehouse}</span>
                    </div>
                    <div class="quantity-bar">
                        <div class="quantity-fill" style="width: ${Math.min(stockPercentage, 100)}%"></div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function filterInventory() {
    const searchTerm = document.getElementById('inventory-search').value.toLowerCase();
    const categoryFilter = document.getElementById('category-filter').value;
    const warehouseFilter = document.getElementById('warehouse-filter').value;
    const statusFilter = document.getElementById('status-filter').value;

    const filtered = state.inventory.filter(item => {
        const matchesSearch = item.name.toLowerCase().includes(searchTerm) ||
            item.sku.toLowerCase().includes(searchTerm);
        const matchesCategory = !categoryFilter || item.category === categoryFilter;
        const matchesWarehouse = !warehouseFilter || item.warehouse === warehouseFilter;
        const matchesStatus = !statusFilter || item.status === statusFilter;

        return matchesSearch && matchesCategory && matchesWarehouse && matchesStatus;
    });

    displayInventory(filtered);
}

async function showItemDetails(itemId) {
    try {
        const [itemRes, forecastRes] = await Promise.all([
            fetch(`${API_BASE_URL}/inventory/${itemId}`),
            fetch(`${API_BASE_URL}/inventory/forecast/${itemId}?days=7`)
        ]);

        const item = await itemRes.json();
        const forecast = await forecastRes.json();

        const modalBody = document.getElementById('modal-body');
        modalBody.innerHTML = `
            <div style="display: grid; gap: 1rem;">
                <div>
                    <h4 style="margin-bottom: 0.5rem;">Item Information</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.9rem;">
                        <div><strong>SKU:</strong> ${item.sku}</div>
                        <div><strong>Category:</strong> ${item.category}</div>
                        <div><strong>Warehouse:</strong> ${item.warehouse}</div>
                        <div><strong>Status:</strong> <span class="item-status ${item.status}">${item.status.replace('_', ' ')}</span></div>
                    </div>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 0.5rem;">Stock Levels</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.9rem;">
                        <div><strong>Current:</strong> ${item.quantity} ${item.unit}</div>
                        <div><strong>Reorder Point:</strong> ${item.reorder_point} ${item.unit}</div>
                    </div>
                </div>
                
                <div>
                    <h4 style="margin-bottom: 0.5rem;">7-Day Forecast</h4>
                    <div style="padding: 1rem; background: var(--bg-tertiary); border-radius: var(--radius-md);">
                        <div style="margin-bottom: 0.5rem;"><strong>Predicted Demand:</strong> ${forecast.predicted_demand} ${item.unit}</div>
                        <div style="margin-bottom: 0.5rem;"><strong>Estimated Stock After:</strong> ${forecast.estimated_stock_after} ${item.unit}</div>
                        <div style="margin-bottom: 0.5rem;"><strong>Reorder Recommended:</strong> ${forecast.reorder_recommended ? '⚠️ Yes' : '✅ No'}</div>
                        ${forecast.reorder_recommended ? `<div><strong>Recommended Order:</strong> ${forecast.recommended_order_quantity} ${item.unit}</div>` : ''}
                    </div>
                </div>
            </div>
        `;

        document.getElementById('modal-title').textContent = item.name;
        openModal();
    } catch (error) {
        console.error('Error loading item details:', error);
    }
}

// Analytics
async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics`);
        const data = await response.json();

        displayWarehouseStats(data.warehouses);

        // Note: Chart.js would be needed for actual charts
        // For now, we'll show placeholder messages
        displayChartPlaceholders();
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

function displayWarehouseStats(warehouses) {
    const container = document.getElementById('warehouse-stats');

    container.innerHTML = warehouses.map(wh => `
        <div class="warehouse-item">
            <div class="warehouse-name">${wh.warehouse_name}</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.875rem; margin-bottom: 0.5rem;">
                <div>Utilization: ${wh.utilization_percentage}%</div>
                <div>Items: ${wh.total_items}</div>
                <div>Low Stock: ${wh.low_stock_items}</div>
                <div>Out of Stock: ${wh.out_of_stock_items}</div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${wh.utilization_percentage}%"></div>
            </div>
        </div>
    `).join('');
}

function displayChartPlaceholders() {
    const charts = ['efficiency-chart', 'vehicle-chart', 'inventory-chart'];

    charts.forEach(chartId => {
        const canvas = document.getElementById(chartId);
        const ctx = canvas.getContext('2d');

        // Set canvas size
        canvas.width = canvas.offsetWidth;
        canvas.height = 300;

        // Draw placeholder
        ctx.fillStyle = 'rgba(99, 102, 241, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#94a3b8';
        ctx.font = '16px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('📊 Chart visualization', canvas.width / 2, canvas.height / 2 - 10);
        ctx.fillText('(Install Chart.js for interactive charts)', canvas.width / 2, canvas.height / 2 + 15);
    });
}

// Modal
function openModal() {
    document.getElementById('item-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('item-modal').classList.remove('active');
}

// Notifications
function showNotification(message, type = 'info') {
    // Simple console notification for now
    // In production, use a toast library
    console.log(`[${type.toUpperCase()}] ${message}`);

    // You could implement a toast notification here
    const colors = {
        success: 'var(--accent-success)',
        error: 'var(--accent-danger)',
        warning: 'var(--accent-warning)',
        info: 'var(--accent-primary)'
    };

    // Create temporary notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${colors[type]};
        color: white;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-lg);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add initial destination field on load
window.addEventListener('load', () => {
    addDestinationField();
});
