export default function AlertBanner({ error, primary, region, p }) {
  const bannerText = error
    ? error
    : primary
      ? <>
          <b>Punjab</b> — {p.event_type || 'Extreme Weather'} &amp; Flash Flood Horizon: +{p.rainfall_mm ?? '—'} mm / 24h peak predicted in {region} Corridor
        </>
      : 'Loading latest tracked anomaly…'

  const confidence = primary
    ? `Model Confidence: ${p.intensity !== undefined ? Math.round(p.intensity * 100) : '—'}%`
    : 'Model Confidence: —'

  return (
    <div id="banner">
      <span
        className="badge badge-live"
        style={{ background: 'rgba(239,68,68,.18)', color: '#ff8a8a' }}
      >
        ⚠ CRITICAL ANOMALY DETECTED
      </span>
      <span>{bannerText}</span>
      <div className="spacer" />
      <span className="cta">{confidence}</span>
    </div>
  )
}
