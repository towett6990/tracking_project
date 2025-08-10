const map = L.map('map').setView([-1.2833, 36.8167], 12);

// Base layers
const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors'
});
const satelliteLayer = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  maxZoom: 19,
  attribution: 'Tiles © Esri'
});

streetLayer.addTo(map);
L.control.layers({
  "🗺️ Streets": streetLayer,
  "🛰️ Satellite": satelliteLayer
}).addTo(map);

const deviceMarkers = {};

function playAlertSound() {
  const beep = new Audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg");
  beep.play();
}

async function updateAllDeviceLocations() {
  devices.forEach(device => {
    fetch(`/api/device_location/${device.serial_number}`)
      .then(res => res.json())
      .then(data => {
        if (data.latitude && data.longitude) {
          const latlng = [data.latitude, data.longitude];
          const marker = deviceMarkers[device.serial_number];

          if (marker) {
            const prev = marker.getLatLng();
            if (prev.lat !== latlng[0] || prev.lng !== latlng[1]) {
              marker.setLatLng(latlng).setPopupContent(`📱 ${device.serial_number} (Moved!)`);
              playAlertSound();
            }
          } else {
            const newMarker = L.marker(latlng).addTo(map)
              .bindPopup(`📱 ${device.serial_number}`);
            deviceMarkers[device.serial_number] = newMarker;
          }
        }
      });
  });
}

// Auto-focus on device if in hash
window.addEventListener("load", () => {
  const serial = decodeURIComponent(location.hash.slice(1)).toLowerCase();
  if (serial) {
    setTimeout(() => {
      for (let key in deviceMarkers) {
        if (key.toLowerCase() === serial) {
          const marker = deviceMarkers[key];
          map.setView(marker.getLatLng(), 14);
          marker.openPopup();
        }
      }
    }, 1500);
  }
});

updateAllDeviceLocations();
setInterval(updateAllDeviceLocations, 5000);
