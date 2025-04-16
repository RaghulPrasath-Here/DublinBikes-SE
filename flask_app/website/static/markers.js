// markers.js - Complete bike station marker system with prediction functionality
let allStationHistory = {}; // Cache for all historical data
let directionsService;
let directionsRenderer;
let autocompleteStart;
let activeMarker = null;
let stationDataDropDown = [];
let endLat, endLng;
let map;

// Prediction data and tracking
let predictionData = {};
let predictionTimes = [];
let activeTimeIndex = 0;
let isDataLoaded = false;
let allMarkers = new Map(); // Will store all created markers by station ID

async function initMap() {
    try {
        // Import required libraries
        const { Map } = await google.maps.importLibrary("maps");
        const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
        
        // Initialize map
        map = new Map(document.getElementById("map"), {
            center: { lat: 53.34538557113246, lng: -6.26967543135754 },
            zoom: 14.13,
            mapId: "2f641e0543b71d2f",
            gestureHandling: 'greedy', // Enable scrolling without Ctrl key
            scrollwheel: true          // Enable mouse wheel zooming
        });

        // Initialize directions service
        directionsService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer();
        directionsRenderer.setMap(map);

        // Fetch station data
        const response = await fetch('/available');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const stationsData = await response.json();
        
        // Load Chart.js library for station-specific charts
        try {
            await loadChartJsLibrary();
        } catch (error) {
            console.error("Failed to load charts:", error);
        }
        
        // Process stations for markers and dropdown
        createBatchedMarkers(stationsData, AdvancedMarkerElement);
        
        // Map click event to clear active marker
        map.addListener("click", () => {
            if (activeMarker) {
                activeMarker.content.classList.remove("highlight");
                activeMarker.zIndex = null;
                
                // Clear any station chart
                const chartContainer = document.querySelector('.station-chart-container');
                if (chartContainer) {
                    chartContainer.remove();
                }
                
                activeMarker = null;
            }
        });

        // Initialize autocomplete
        await google.maps.importLibrary("places");
        initializeAutocomplete();

        // Add prediction slider and load prediction data
        addTimeSliderUI();
        try {
            await fetchPredictionData();
            processPredictionTimes();
        } catch (error) {
            console.warn("Prediction data not available:", error);
        }

        // Preload all station history data at startup
        try {
            const historyResponse = await fetch('/station-history-all');
            if (historyResponse.ok) {
                allStationHistory = await historyResponse.json();
            } else {
                console.warn("Failed to preload station history data");
            }
        } catch (err) {
            console.error("Error fetching all station history:", err);
        }  
        
    } catch (err) {
        console.error("Error initializing map:", err);
    }
}

function createBatchedMarkers(stations, AdvancedMarkerElement) {
    // Clear previous dropdown data
    stationDataDropDown = [];
    allMarkers.clear();
    
    // Process stations in batches
    const BATCH_SIZE = 20;
    let currentIndex = 0;
    
    function processBatch() {
        const endIndex = Math.min(currentIndex + BATCH_SIZE, stations.length);
        
        for (let i = currentIndex; i < endIndex; i++) {
            const station = stations[i];
            
            if (station.position && station.position.lat && station.position.lng) {
                // Add to dropdown data
                if (station.available_bikes>0){
                    stationDataDropDown.push({
                        name: station.name,
                        lat: station.position.lat,
                        lng: station.position.lng
                    });
                }
                
                // Create marker with immediate styling
                const marker = new AdvancedMarkerElement({
                    map,
                    content: buildMarkerContent(station),
                    position: { 
                        lat: station.position.lat, 
                        lng: station.position.lng 
                    },
                    title: station.name,
                });

                // Store marker in our tracking Map
                if (station.number) {
                    allMarkers.set(station.number.toString(), {
                        marker: marker,
                        station: station
                    });
                }

                // Add click event
                marker.addListener("click", () => {
                    toggle(marker, station);
                });
            }
        }
        
        currentIndex = endIndex;
        
        // If more stations to process, continue in next frame
        if (currentIndex < stations.length) {
            requestAnimationFrame(processBatch);
        } else {
            // Update dropdown when all markers are created
            dropDownStation();
            
            // Enable the prediction slider if data is loaded
            if (isDataLoaded) {
                const slider = document.getElementById('time-slider');
                if (slider) {
                    slider.disabled = false;
                }
            }
        }
    }
    
    // Start processing
    processBatch();
}

// Build marker content 
function buildMarkerContent(station, predictedBikes = null) {
    const content = document.createElement("div");
    content.classList.add("displayBox");

    // Get station details
    const name = station.name;
    const bike_stands = station.bike_stands || 0;
    const status = station.status || "Unknown";
    
    // Determine if showing prediction and calculate values
    const isPrediction = predictedBikes !== null;
    const available_bikes = isPrediction ? predictedBikes : station.available_bikes;
    
    // Calculate available stands - for predictions, recalculate from total stands
    const available_bike_stands = isPrediction 
        ? bike_stands - available_bikes 
        : station.available_bike_stands;
    
    if (isPrediction) {
        content.classList.add("prediction");
    }

    // Color logic based on availability
    if (available_bikes === 0 || status === "CLOSED") {
        content.classList.add("black");
    } else if (bike_stands <= 15) {
        // Small station
        if (available_bikes <= 2) {
            content.classList.add("red");
        } else if (available_bikes <= 4) {
            content.classList.add("orange");
        } else {
            content.classList.add("green");
        }
    } else {
        // Medium/large station
        if (available_bikes <= 4) {
            content.classList.add("red");
        } else if (available_bikes <= 7) {
            content.classList.add("orange");
        } else {
            content.classList.add("green");
        }
    }

    content.innerHTML = `
        <div class='details'>
            <h2>${name}<br></h2> 
            <p><strong>${isPrediction ? 'Predicted' : 'Free'} Bikes:</strong> ${available_bikes}<br></p>
            <p><strong>Free Stands:</strong> ${available_bike_stands}<br></p>
            <p><strong>Total Stands:</strong> ${bike_stands}<br></p>
        </div>
    `;

    return content;
}

// Toggle marker highlight and show station-specific historical data
async function toggle(marker, station) {
    // Remove existing chart if present
    const existingChart = document.querySelector('.station-chart-container');
    if (existingChart) {
        existingChart.remove();
    }
    
    if (activeMarker && activeMarker !== marker) {
        activeMarker.content.classList.remove("highlight");
        activeMarker.zIndex = null;
    }

    if (marker.content.classList.contains("highlight")) {
        marker.content.classList.remove("highlight");
        marker.zIndex = null;
        activeMarker = null;
    } else {
        marker.content.classList.add("highlight");
        marker.zIndex = 1;
        marker.content.style.display = "block";
        activeMarker = marker;
        
        // Show historical data for this station
        if (window.Chart && station && station.number) {
            try {
                // Try to use preloaded data first, then individual fetch if not available
                let stationHistory;
                if (allStationHistory[station.number]) {
                    stationHistory = allStationHistory[station.number];
                } else {
                    stationHistory = await fetchStationHistoricalData(station.number);
                }
                
                if (stationHistory) {
                    showStationChart(marker, station, stationHistory);
                } else {
                    console.warn(`No history data found for station ${station.number}`);
                }
            } catch (error) {
                console.warn("Could not load station history:", error);
            }
        }
    }
}
