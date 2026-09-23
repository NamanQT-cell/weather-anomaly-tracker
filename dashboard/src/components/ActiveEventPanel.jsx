function sevClass(sev) {
  if (sev === 'severe')   return 'tag-pill tag-severe'
  if (sev === 'moderate') return 'tag-pill tag-moderate'
  return 'tag-pill tag-low'
}

function sevLabel(sev) {
  if (sev === 'severe')   return 'Severe'
  if (sev === 'moderate') return 'Moderate'
  return 'Low'
}

function floodGrade(mm) {
  if (mm > 60) return 'Grade 4 (Critical)'
  if (mm > 30) return 'Grade 2 (Moderate)'
  return 'Grade 1 (Low)'
}

export default function ActiveEventPanel({ primary, p, lat, lon, sev, region, features }) {
  const eventId    = primary ? 'IND-2026-' + String(features.length).padStart(2, '0') : '—'
  const horizon    = p.lead_time_days ? p.lead_time_days * 24 + 'h' : '—'
  const rain       = (p.rainfall_mm   ?? '—') + ' mm / 24h'
  const wind       = 'Wind ' + (p.wind_speed_kmh ?? '—') + ' km/h'
  const score      = p.intensity !== undefined ? p.intensity.toFixed(2) + ' / 1.0' : '—'
  const conf       = p.intensity !== undefined ? Math.round(p.intensity * 100) + '%' : '—'
  const radius     = (p.radius_km ?? '—') + ' km'
  const flood      = floodGrade(p.rainfall_mm || 0)
  const locText    = primary
    ? `📍 ${region}, Punjab, India · Lat ${lat.toFixed(2)}°N, Lon ${lon.toFixed(2)}°E`
    : '—'

  return (
    <>
      <div className="event-header">
        ● ACTIVE ANOMALY
        <span id="active-id" style={{ color: 'var(--muted)', marginLeft: 4 }}>{eventId}</span>
        <span className={sevClass(sev)} style={{ marginLeft: 'auto' }}>{sevLabel(sev)}</span>
      </div>

      <h2>{p.event_type || (primary ? 'Extreme Weather Event' : '—')}</h2>
      <div className="event-loc">{locText}</div>

      <div className="kv-grid">
        <div>
          <div className="k">Forecast Horizon</div>
          <div className="v">{horizon}</div>
        </div>
        <div>
          <div className="k">Max Predicted</div>
          <div className="v">{rain}</div>
          <div className="sub">{wind}</div>
        </div>
        <div>
          <div className="k">Anomaly Score</div>
          <div className="v">{score}</div>
          <div className="sub">Critical Outlier</div>
        </div>
        <div>
          <div className="k">Confidence Spread</div>
          <div className="v">{conf}</div>
          <div className="sub">σ = 0.08 (Tight)</div>
        </div>
        <div>
          <div className="k">Affected Radius</div>
          <div className="v">{radius}</div>
          <div className="sub">{region} catchment</div>
        </div>
        <div>
          <div className="k">Flash Flood</div>
          <div className="v">{primary ? flood : '—'}</div>
          <div className="sub">Severity</div>
        </div>
      </div>

      <button className="btn-danger">⚠ Simulate Evacuation Horizon</button>
      <button className="btn-outline">⬇ Export GIS Shapefile / GeoTIFF</button>
    </>
  )
}
