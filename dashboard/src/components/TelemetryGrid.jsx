function TeleCard({ label, val, delta, warn }) {
  return (
    <div className={`tele-card${warn ? ' warn' : ''}`}>
      <div className="label">{label}</div>
      <div className="val">{val || '—'}</div>
      <div className="delta">{delta || '—'}</div>
    </div>
  )
}

export default function TelemetryGrid({ p }) {
  const intensity = p.intensity !== undefined ? p.intensity.toFixed(2) : undefined
  const conf      = p.intensity !== undefined ? Math.round(p.intensity * 100) + '%' : undefined

  const cards = [
    { label: 'Max Rainfall',        val: p.rainfall_mm    != null ? p.rainfall_mm + ' mm'   : undefined, delta: '↑ anomaly vs norm', warn: true },
    { label: 'Peak Wind Gusts',     val: p.wind_speed_kmh != null ? p.wind_speed_kmh + ' km/h' : undefined, delta: 'gust vector', warn: false },
    { label: 'Temp Anomaly',        val: p.temperature_c  != null ? p.temperature_c + ' °C'  : undefined, delta: 'regional mean', warn: false },
    { label: 'Surface Pressure',    val: p.pressure_hpa   != null ? p.pressure_hpa + ' hPa'  : undefined, delta: 'surface core', warn: false },
    { label: 'Anomaly Intensity',   val: intensity != null ? intensity + ' / 1.0' : undefined, delta: 'critical severity', warn: true },
    { label: 'Ensemble Confidence', val: conf, delta: 'ensemble agreement', warn: false },
  ]

  return (
    <section id="telemetry">
      <div className="panel-title" style={{ padding: '0 0 8px' }}>
        Atmospheric Telemetry &amp; Severe Indices
      </div>
      <div className="tele-grid">
        {cards.map(c => (
          <TeleCard key={c.label} {...c} />
        ))}
      </div>
    </section>
  )
}
