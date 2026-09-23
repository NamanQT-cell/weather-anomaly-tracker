import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix default marker icon path broken by Vite bundling
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl:       'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl:     'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const TABS = ['Rainfall Anomaly', 'Wind Barbs', 'Pressure Isobars', 'Anomaly Score', 'Risk Index']
const TOTAL_STEPS = 5
const PEAK_IDX    = 2

function buildTrackPoints(total, peakIdx) {
  return Array.from({ length: total }, (_, i) => ({ i, isPeak: i === peakIdx }))
}

export default function MapPanel({ features, lat, lon, SEV_COLOR }) {
  const mapRef    = useRef(null)
  const mapInst   = useRef(null)
  const layersRef = useRef([])
  const [activeTab, setActiveTab] = useState('Rainfall Anomaly')
  const trackPoints = buildTrackPoints(TOTAL_STEPS, PEAK_IDX)

  // Initialise map once
  useEffect(() => {
    if (mapInst.current) return
    mapInst.current = L.map(mapRef.current, { zoomControl: true }).setView([30.7333, 76.7794], 9)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(mapInst.current)
  }, [])

  // Add / refresh markers when features change
  useEffect(() => {
    if (!mapInst.current) return

    // Clear previous layers
    layersRef.current.forEach(l => mapInst.current.removeLayer(l))
    layersRef.current = []

    features.forEach(f => {
      const pp = f.properties
      const [flon, flat] = f.geometry.coordinates
      const color = SEV_COLOR[pp.severity] || SEV_COLOR.low

      const circle = L.circle([flat, flon], {
        radius: (pp.radius_km || 5) * 1000,
        color,
        fillColor: color,
        fillOpacity: .15,
        weight: 1.5,
      }).addTo(mapInst.current)

      const marker = L.circleMarker([flat, flon], {
        radius: 8,
        color,
        fillColor: color,
        fillOpacity: .9,
        weight: 2,
      })
        .addTo(mapInst.current)
        .bindPopup(
          `<b>${pp.region_name || 'Zone'}</b><br>${pp.event_type || ''}<br>${pp.rainfall_mm ?? '—'} mm · ${pp.wind_speed_kmh ?? '—'} km/h`
        )

      layersRef.current.push(circle, marker)
    })
  }, [features, SEV_COLOR])

  const velocity   = features.length ? ((features[0]?.properties?.wind_speed_kmh || 20) / 4).toFixed(1) : '—'
  const pressureHpa = features.length ? (features[0]?.properties?.pressure_hpa ?? '—') : '—'

  return (
    <>
      <div className="tabs">
        {TABS.map(tab => (
          <button
            key={tab}
            className={activeTab === tab ? 'active' : ''}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
        <span className="coord-pill">
          {lat ? `${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E` : '30.73°N, 76.78°E'}
        </span>
      </div>

      <div id="map" ref={mapRef} />

      <div className="scrubber">
        <div className="meta">⟳ Ensemble Trajectory Scrubber<br />Cycle: 00Z</div>
        <div style={{ flex: 1 }}>
          <div className="track">
            <div className="line" />
            {trackPoints.map(({ i, isPeak }) => (
              <div key={i} className={`pt${isPeak ? ' peak' : ''}`} title={`T+${(i + 1) * 24}h`} />
            ))}
          </div>
          <div className="track-labels">
            {trackPoints.map(({ i, isPeak }) => (
              <span key={i}>{isPeak ? `T+${(i + 1) * 24} [PEAK]` : `T+${(i + 1) * 24}`}</span>
            ))}
          </div>
        </div>
        <div className="meta">
          Velocity: {velocity} km/h<br />Min core: {pressureHpa} hPa
        </div>
      </div>
    </>
  )
}
