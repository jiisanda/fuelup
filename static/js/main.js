let map;
let routeLayer;
let markersLayer;

const startIcon = L.divIcon({
    html: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" fill="#2196F3" stroke="white" stroke-width="2"/>
        <circle cx="12" cy="12" r="4" fill="white"/>
    </svg>`,
    className: 'custom-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
});

const endIcon = L.divIcon({
    html: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" fill="#f44336" stroke="white" stroke-width="2"/>
        <path d="M12 6L16 14H8L12 6Z" fill="white"/>
    </svg>`,
    className: 'custom-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
});

function initMap() {
    map = L.map('map').setView([39.8283, -98.5795], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);
    calculateRoute();
}

// calculate and display route
async function calculateRoute() {
    const button = document.querySelector('button');
    button.classList.add('loading');
    const start = document.getElementById('start').value;
    const end = document.getElementById('end').value;

    try {
        const response = await fetch('/api/optimal-route/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                start_location: start,
                end_location: end
            })
        });

        const data = await response.json();
        displayRoute(data);
    } catch (error) {
        console.error('Error:', error);
        alert('Error calculating route');
    } finally {
        button.classList.remove('loading');
    }
}

// Display route on map
function displayRoute(data) {
    // previous layers
    if (routeLayer) map.removeLayer(routeLayer);
    markersLayer.clearLayers();

    // route line
    const routeCoords = data.route.coordinates.map(coord => [coord.lat, coord.lng]);
    routeLayer = L.polyline(routeCoords, {
        color: '#4CAF50',
        weight: 4
    }).addTo(map);

    // start marker
    const startPoint = routeCoords[0];
    L.marker(startPoint, { icon: startIcon })
        .bindPopup('<strong>Start Location</strong>')
        .addTo(markersLayer);

    // end marker
    const endPoint = routeCoords[routeCoords.length - 1];
    L.marker(endPoint, { icon: endIcon })
        .bindPopup('<strong>End Location</strong>')
        .addTo(markersLayer);

    // fuel stop markers
    data.fuel_stops.forEach((stop, index) => {
        const marker = L.marker([stop.location.lat, stop.location.lng])
            .bindPopup(`
                <strong>${stop.name}</strong><br>
                Price: $${stop.price}/gallon<br>
                Distance: ${Math.round(stop.distance_from_start)} miles from start
            `);
        markersLayer.addLayer(marker);
    });

    // Fit map to route bounds with padding
    map.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });

    document.getElementById('total-distance').textContent = `${Math.round(data.route.total_distance_miles)} miles`;
    document.getElementById('duration').textContent = data.route.duration;
    document.getElementById('fuel-stops').textContent = data.fuel_stops.length;
    document.getElementById('total-cost').textContent = `$${data.summary.total_cost}`;
}

// Initialize map on load
window.onload = initMap;
