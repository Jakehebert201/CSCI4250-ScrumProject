(function () {
  const REFRESH_SELECTOR = '[data-refresh-location]';
  const DISPLAY_SELECTOR = '[data-location-display]';
  const STUDENT_INPUT_SELECTOR = '[data-student-input]';

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

  async function fetchLocation(studentId, displayNode) {
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
    } catch (error) {
      displayNode.textContent = 'Unable to detect location.';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const refreshButton = document.querySelector(REFRESH_SELECTOR);
    const displayNode = document.querySelector(DISPLAY_SELECTOR);
    const studentInputs = document.querySelectorAll(STUDENT_INPUT_SELECTOR);

    if (!displayNode) {
      return;
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
        fetchLocation(currentStudentId, displayNode);
      });
    }

    if (currentStudentId) {
      fetchLocation(currentStudentId, displayNode);
    }
  });
})();
