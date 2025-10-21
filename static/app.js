const button = document.getElementById("locate");
const resultCard = document.getElementById("result");
const errorBox = document.getElementById("error");
const mapContainer = document.getElementById("map");

let mapInstance;
let mapMarker;
let fallbackFrame;

function updateField(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = value ?? "—";
}

async function fetchLocation() {
  button.disabled = true;
  button.textContent = "Loading...";
  errorBox.hidden = true;
  resultCard.hidden = true;
  hideMap();

  try {
    let clientIp = "";
    try {
      const ipResponse = await fetch("https://api.ipify.org?format=json");
      if (ipResponse.ok) {
        const ipPayload = await ipResponse.json();
        if (typeof ipPayload.ip === "string") {
          const value = ipPayload.ip.trim();
          if (value) {
            clientIp = value;
          }
        }
      }
    } catch (err) {
      console.warn("Unable to determine client IP from ipify", err);
    }

    const response = await fetch(
      clientIp ? `/api/location?ip=${encodeURIComponent(clientIp)}` : "/api/location"
    );
    if (!response.ok) {
      throw new Error("Request failed");
    }
    const payload = await response.json();
    if (payload.error) {
      throw new Error(payload.error);
    }

    updateField("ip", payload.ip || "Unavailable");
    updateField("city", payload.city || "Unavailable");
    updateField("region", payload.region || "Unavailable");
    updateField("country", payload.country || "Unavailable");
    updateField("postal", payload.postal || "Unavailable");
    updateField("latitude", payload.latitude ?? "Unavailable");
    updateField("longitude", payload.longitude ?? "Unavailable");

    if (typeof payload.latitude === "number" && typeof payload.longitude === "number") {
      renderMap(payload.latitude, payload.longitude, payload.city, payload.region, payload.country);
    }

    resultCard.hidden = false;
  } catch (err) {
    errorBox.textContent = err instanceof Error ? err.message : "Unexpected error";
    errorBox.hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = "Find My Location";
  }
}

button?.addEventListener("click", fetchLocation);

function renderMap(latitude, longitude, city, region, country) {
  if (!mapContainer) {
    return;
  }
  mapContainer.hidden = false;
  mapContainer.setAttribute("aria-hidden", "false");

  const coordinates = [latitude, longitude];

  if (typeof L !== "undefined") {
    if (fallbackFrame) {
      fallbackFrame.remove();
      fallbackFrame = undefined;
    }

    if (!mapInstance) {
      mapInstance = L.map("map", { zoomControl: false }).setView(coordinates, 12);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution:
          "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors",
      }).addTo(mapInstance);
    } else {
      mapInstance.setView(coordinates, 12);
    }

    const locationLabel = [city, region, country].filter(Boolean).join(", ") || "You are here";
    if (!mapMarker) {
      mapMarker = L.marker(coordinates).addTo(mapInstance);
    }
    mapMarker.setLatLng(coordinates).bindPopup(locationLabel).openPopup();
    requestAnimationFrame(() => mapInstance.invalidateSize());
    return;
  }

  if (!fallbackFrame) {
    fallbackFrame = document.createElement("iframe");
    fallbackFrame.className = "map-frame";
    fallbackFrame.setAttribute("title", "Approximate location map");
    fallbackFrame.setAttribute("loading", "lazy");
    mapContainer.appendChild(fallbackFrame);
  }

  const delta = 0.1;
  const bounds = [longitude - delta, latitude - delta, longitude + delta, latitude + delta]
    .map((value) => value.toFixed(4))
    .join(",");
  const marker = `${latitude.toFixed(4)},${longitude.toFixed(4)}`;
  fallbackFrame.src = `https://www.openstreetmap.org/export/embed.html?bbox=${bounds}&layer=mapnik&marker=${marker}`;
}

function hideMap() {
  if (mapContainer) {
    mapContainer.hidden = true;
    mapContainer.setAttribute("aria-hidden", "true");
    if (fallbackFrame) {
      fallbackFrame.removeAttribute("src");
    }
  }
}
