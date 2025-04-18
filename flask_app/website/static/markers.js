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


// PREDICTION FUNCTIONS

// Add the time slider UI to the page
function addTimeSliderUI() {
    // Create slider container
    const sliderContainer = document.createElement('div');
    sliderContainer.className = 'prediction-controls';
    
    // Add inner HTML
    sliderContainer.innerHTML = `
        <div class="prediction-header">
            <span>Showing: </span>
            <span id="prediction-time">Current Data</span>
        </div>
        <input type="range" id="time-slider" min="0" max="23" value="0" class="slider" disabled>
        <div class="prediction-labels">
            <span>Current</span>
            <span>24h Forecast</span>
        </div>
    `;
    
    // Add to page below weather
    const weatherDiv = document.querySelector('.weather');
    if (weatherDiv) {
        weatherDiv.parentNode.insertBefore(sliderContainer, weatherDiv.nextSibling);
    } else {
        // Fallback - add to sidebar
        document.querySelector('.sidebar')?.appendChild(sliderContainer);
    }
    
    // Add slider styles
    const style = document.createElement('style');
    style.textContent = `
.prediction-controls {
    margin-top: 20px;
    padding: 15px;
    background-color: #222;
    border-radius: 8px;
}

.prediction-header {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 10px;
    font-weight: bold;
}

#prediction-time {
    color: #EC1763;
}

.slider {
    width: 100%;
    height: 8px;
    -webkit-appearance: none;
    background: #333;
    outline: none;
    border-radius: 5px;
    margin: 10px 0;
}

.slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #EC1763;
    cursor: pointer;
}

.slider::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #EC1763;
    cursor: pointer;
}

.slider:disabled {
    opacity: 0.5;
}

.slider:disabled::-webkit-slider-thumb {
    background: #999;
}

.slider:disabled::-moz-range-thumb {
    background: #999;
}

.prediction-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #ccc;
}

/* Station chart styling */
.station-chart-container {
    position: absolute;
    bottom: 20px;
    left: 20px;
    width: 300px;
    background-color: #222;
    border-radius: 8px;
    padding: 15px;
    z-index: 1000;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.station-chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.station-chart-header h3 {
    font-size: 14px;
    color: #fff;
    margin: 0;
}

.close-chart {
    background: none;
    border: none;
    color: #ccc;
    cursor: pointer;
    font-size: 16px;
}

.close-chart:hover {
    color: #fff;
}

#station-chart {
    width: 100% !important;
    height: 180px !important;
    background-color: rgba(51, 51, 51, 0.5);
    border-radius: 4px;
}

/* Updated prediction marker styles */
.displayBox.prediction.green {
    background-color: rgba(76, 175, 80, 0.7); /* Lighter green */
}

.displayBox.prediction.orange {
    background-color: rgba(255, 152, 0, 0.7); /* Lighter orange */
}

.displayBox.prediction.red {
    background-color: rgba(244, 67, 54, 0.7); /* Lighter red */
}

.displayBox.prediction.black {
    background-color: rgba(33, 33, 33, 0.7); /* Lighter black (dark grey) */
}
`;

    document.head.appendChild(style);
    
    // Add slider event listener
    const slider = document.getElementById('time-slider');
    slider.addEventListener('input', function() {
        activeTimeIndex = parseInt(this.value);
        updatePredictionDisplay();
    });
}

// Fetch prediction data from API
async function fetchPredictionData() {
    try {
        const response = await fetch('/predict-24h');
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        predictionData = await response.json();
        isDataLoaded = true;
        
        // Enable the slider now that data is loaded
        const slider = document.getElementById('time-slider');
        if (slider) {
            slider.disabled = false;
        }
        
        return true;
    } catch (error) {
        console.error("Error fetching prediction data:", error);
        document.getElementById('prediction-time').textContent = 'Forecast Unavailable';
        throw error;
    }
}

// Process prediction times from the data
function processPredictionTimes() {
    // Get first station's data to extract times (all stations have the same timestamps)
    const firstStationId = Object.keys(predictionData)[0];
    
    if (predictionData[firstStationId] && predictionData[firstStationId].length > 0) {
        predictionTimes = predictionData[firstStationId]
            .map(pred => {
                const date = new Date(pred.forecast_time);
                return {
                    hour: date.getHours(),
                    date: date.toLocaleDateString(),
                    time: date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
                    fullDateTime: date,
                    original: pred.forecast_time
                };
            })
            .filter(time => !(time.hour >= 0 && time.hour < 6)); // Remove midnight-5am (closed hours)
        
        // Update slider max value
        const slider = document.getElementById('time-slider');
        if (slider && predictionTimes.length > 0) {
            slider.max = predictionTimes.length;
        }
    }
}

// Update prediction display based on slider position
function updatePredictionDisplay() {
    const timeDisplay = document.getElementById('prediction-time');
    
    if (activeTimeIndex === 0) {
        // Show current data
        timeDisplay.textContent = 'Current Data';
        resetToCurrentData();
    } else if (predictionTimes.length > 0) {
        // Show prediction for selected time
        const timeInfo = predictionTimes[activeTimeIndex-1]; // -1 because index 0 is "current"
        timeDisplay.textContent = `${timeInfo.date} at ${timeInfo.time}`;
        updateMarkersWithPredictions(timeInfo);
    }
}

// Reset to current data
function resetToCurrentData() {
    allMarkers.forEach((data, stationId) => {
        // Replace marker content with original data
        if (data.marker && data.station) {
            data.marker.content = buildMarkerContent(data.station);
        }
    });
}

// Update markers with prediction data
function updateMarkersWithPredictions(timeInfo) {
    allMarkers.forEach((data, stationId) => {
        // Find prediction for this station
        const prediction = findPrediction(stationId, timeInfo.original);
        
        if (prediction && data.marker && data.station) {
            // Update marker with predicted data
            data.marker.content = buildMarkerContent(
                data.station, 
                prediction.predicted_bikes
            );
        }
    });
}

// Find prediction for a specific station at a specific time
function findPrediction(stationId, timeString) {
    if (!predictionData[stationId]) return null;
    
    return predictionData[stationId].find(p => p.forecast_time === timeString);
}