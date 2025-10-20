(function () {
  const REFRESH_SELECTOR = '[data-refresh-location]';
  const DISPLAY_SELECTOR = '[data-location-display]';
  const STUDENT_INPUT_SELECTOR = '[data-student-input]';
  const MAP_SELECTOR = '[data-location-map]';

  const DEFAULT_VIEW = { center: [20, 0], zoom: 2 };

  function formatLocation(data) {
    if (!data) {
      return 'Unable to detect location.';
    }
    const parts = [data.city, data.region, data.country].filter(Boolean);
    if (parts.length) {
      return parts.join(', ');
    }
    if (typeof data.latitude === 'number' && typeof data.longitude === 'number') {
      return `Latitude ${data.latitude.toFixed(4)}, Longitude ${data.longitude.toFixed(4)}`;
    }
    return 'Location not available.';
  }

  function initializeMap(mapContainer, initialCoords) {
    if (!mapContainer || typeof L === 'undefined') {
      return { map: null, marker: null };
    }

    const map = L.map(mapContainer, {
      zoomControl: true,
      attributionControl: true,
    }).setView(initialCoords || DEFAULT_VIEW.center, initialCoords ? 13 : DEFAULT_VIEW.zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    const marker = initialCoords ? L.marker(initialCoords).addTo(map) : null;
    return { map, marker };
  }

  function updateMapLocation(state, coords) {
    if (!state.map || !coords) {
      return;
    }

    const [latitude, longitude] = coords;
    state.map.setView(coords, 15);
    if (!state.marker) {
      state.marker = L.marker(coords).addTo(state.map);
    } else {
      state.marker.setLatLng(coords);
    }
    const popupContent = `Lat ${latitude.toFixed(4)}, Lng ${longitude.toFixed(4)}`;
    state.marker.bindPopup(popupContent).openPopup();
  }

  async function fetchLocation(studentId, displayNode, mapState) {
    if (!studentId) {
      displayNode.textContent = 'Enter a student ID to detect location.';
      return;
    }
    displayNode.textContent = 'Detecting location…';
    try {
      const response = await fetch('/api/location', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ student_id: studentId }),
      });
      const payload = await response.json();
      if (!response.ok || payload.error) {
        displayNode.textContent = payload.error || 'Unable to detect location.';
        return;
      }
      displayNode.textContent = formatLocation(payload);
      if (typeof payload.latitude === 'number' && typeof payload.longitude === 'number') {
        updateMapLocation(mapState, [payload.latitude, payload.longitude]);
      }
    } catch (error) {
      displayNode.textContent = 'Unable to detect location.';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const refreshButton = document.querySelector(REFRESH_SELECTOR);
    const displayNode = document.querySelector(DISPLAY_SELECTOR);
    const studentInputs = document.querySelectorAll(STUDENT_INPUT_SELECTOR);
    const mapContainer = document.querySelector(MAP_SELECTOR);

    if (!displayNode) {
      return;
    }

    let initialCoords = null;
    if (mapContainer) {
      const { latitude, longitude } = mapContainer.dataset;
      const lat = parseFloat(latitude);
      const lng = parseFloat(longitude);
      if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
        initialCoords = [lat, lng];
      }
    }

    const mapState = initializeMap(mapContainer, initialCoords);

    if (initialCoords) {
      updateMapLocation(mapState, initialCoords);
    }

    let currentStudentId = '';
    studentInputs.forEach((input) => {
      const updateId = () => {
        currentStudentId = input.value.trim();
      };
      updateId();
      input.addEventListener('input', updateId);
      input.addEventListener('change', updateId);
    });

    if (refreshButton) {
      refreshButton.addEventListener('click', () => {
        fetchLocation(currentStudentId, displayNode, mapState);
      });
    }

    if (currentStudentId) {
      fetchLocation(currentStudentId, displayNode, mapState);
    }
  });
})();
