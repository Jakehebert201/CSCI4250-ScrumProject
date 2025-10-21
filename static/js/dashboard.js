document.addEventListener("DOMContentLoaded", () => {
    const mapElement = document.getElementById("location-map");
    const latElement = document.getElementById("latitude");
    const lngElement = document.getElementById("longitude");
    const accuracyElement = document.getElementById("accuracy");
    const timestampElement = document.getElementById("timestamp");
    const messageElement = document.getElementById("location-message");

    if (!mapElement) {
        return;
    }

    if (typeof L === "undefined") {
        messageElement.textContent = "Map failed to load. Check your network connection and refresh.";
        messageElement.classList.add("dashboard__message--error");
        return;
    }

    const map = L.map(mapElement).setView([0, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap contributors",
    }).addTo(map);

    const marker = L.marker([0, 0]).addTo(map);
    const accuracyCircle = L.circle([0, 0], { radius: 0 }).addTo(map);

    const updateStatus = (coords) => {
        const { latitude, longitude, accuracy } = coords;
        const timestamp = new Date().toLocaleTimeString();

        latElement.textContent = latitude.toFixed(5);
        lngElement.textContent = longitude.toFixed(5);
        accuracyElement.textContent = `${Math.round(accuracy)} m`;
        timestampElement.textContent = timestamp;

        marker.setLatLng([latitude, longitude]);
        accuracyCircle.setLatLng([latitude, longitude]);
        accuracyCircle.setRadius(accuracy);
        map.setView([latitude, longitude], 16);

        messageElement.textContent = "Location updated.";
        messageElement.classList.remove("dashboard__message--error");
    };

    const handleError = (error) => {
        const messages = {
            1: "Permission denied. Enable location access to view your position.",
            2: "Location unavailable. Check your device settings.",
            3: "Location request timed out. Try again.",
        };
        messageElement.textContent = messages[error.code] || "Unable to retrieve location.";
        messageElement.classList.add("dashboard__message--error");
    };

    if (!("geolocation" in navigator)) {
        messageElement.textContent = "Geolocation is not supported by this browser.";
        messageElement.classList.add("dashboard__message--error");
        return;
    }

    const geoOptions = {
        enableHighAccuracy: true,
        maximumAge: 1000,
        timeout: 15000,
    };

    let hasFix = false;

    const notifyStalledFix = () => {
        if (!hasFix) {
            messageElement.textContent = "Still waiting for a location fix... move closer to a window or check device location settings.";
            messageElement.classList.remove("dashboard__message--error");
        }
    };

    setTimeout(notifyStalledFix, 7000);

    const wrappedUpdate = (position) => {
        hasFix = true;
        updateStatus(position.coords);
    };

    navigator.geolocation.getCurrentPosition(wrappedUpdate, handleError, geoOptions);

    navigator.geolocation.watchPosition(wrappedUpdate, handleError, geoOptions);
});
