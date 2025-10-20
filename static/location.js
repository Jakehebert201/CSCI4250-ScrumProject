(function () {
  const REFRESH_SELECTOR = '[data-refresh-location]';
  const DISPLAY_SELECTOR = '[data-location-display]';
  const STUDENT_INPUT_SELECTOR = '[data-student-input]';
  const MAP_SELECTOR = '[data-location-map]';
  const LAT_FIELD_SELECTOR = '[data-latitude-field]';
  const LNG_FIELD_SELECTOR = '[data-longitude-field]';

  const DEFAULT_VIEW = { center: [20, 0], zoom: 2 };

  let cachedCoordinates = null;
  let geolocationPromise = null;

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

  function setHiddenCoordinateFields(coords) {
    const latFields = document.querySelectorAll(LAT_FIELD_SELECTOR);
    const lngFields = document.querySelectorAll(LNG_FIELD_SELECTOR);
    cachedCoordinates = coords ? { ...coords } : null;

    latFields.forEach((field) => {
      field.value = coords ? String(coords.latitude) : '';
    });
    lngFields.forEach((field) => {
      field.value = coords ? String(coords.longitude) : '';
    });
  }

  function readHiddenCoordinateFields() {
    const latField = document.querySelector(LAT_FIELD_SELECTOR);
    const lngField = document.querySelector(LNG_FIELD_SELECTOR);
    if (!latField || !lngField) {
      return null;
    }
    const latitude = parseFloat(latField.value);
    const longitude = parseFloat(lngField.value);
    if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
      return null;
    }
    return { latitude, longitude };
  }

  function browserGeolocationAvailable() {
    return typeof navigator !== 'undefined' && 'geolocation' in navigator;
  }

  async function resolveBrowserCoordinates() {
    if (cachedCoordinates) {
      return cachedCoordinates;
    }
    if (!browserGeolocationAvailable()) {
      return null;
    }
    if (geolocationPromise) {
      return geolocationPromise;
    }
    geolocationPromise = new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          };
          setHiddenCoordinateFields(coords);
          resolve(coords);
        },
        () => resolve(null),
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 },
      );
    }).finally(() => {
      geolocationPromise = null;
    });
    return geolocationPromise;
  }

  async function fetchLocation(studentId, displayNode, mapState) {
    if (!studentId) {
      displayNode.textContent = 'Enter a student ID to detect location.';
      return;
    }
    displayNode.textContent = 'Detecting location…';
    try {
      const cached = readHiddenCoordinateFields();
      const coords = cached || (await resolveBrowserCoordinates());
      const response = await fetch('/api/location', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          student_id: studentId,
          latitude: coords ? coords.latitude : undefined,
          longitude: coords ? coords.longitude : undefined,
        }),
      });
      const payload = await response.json();
      if (!response.ok || payload.error) {
        displayNode.textContent = payload.error || 'Unable to detect location.';
        return;
      }
      displayNode.textContent = formatLocation(payload);
      if (typeof payload.latitude === 'number' && typeof payload.longitude === 'number') {
        setHiddenCoordinateFields({ latitude: payload.latitude, longitude: payload.longitude });
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

    const storedCoords = readHiddenCoordinateFields();
    if (storedCoords) {
      cachedCoordinates = storedCoords;
    } else {
      resolveBrowserCoordinates();
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
