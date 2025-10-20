const button = document.getElementById("locate");
const resultCard = document.getElementById("result");
const errorBox = document.getElementById("error");

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

  try {
    const response = await fetch("/api/location");
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
