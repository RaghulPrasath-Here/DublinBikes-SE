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