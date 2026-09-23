function CoarseGrid({ rainfallPeak }) {
  const base = Math.max(40, Math.round(rainfallPeak * 0.65))
  const vals = [
    base * 0.5, base * 0.7, base * 0.9,
    base,       base * 0.75, base * 0.4,
    base * 0.3, base * 0.55, base * 0.35,
  ]

  return (
    <div className="grid12">
      {vals.map((v, idx) => {
        const t     = Math.min(1, v / (base * 1.1))
        const color = `rgb(${Math.round(30 + 120 * t)}, ${Math.round(40 + 40 * (1 - t))}, ${Math.round(180 - 100 * t)})`
        return (
          <div key={idx} style={{ background: color }}>
            {Math.round(v)}
          </div>
        )
      })}
    </div>
  )
}

function FineRadial({ rainfallPeak }) {
  return (
    <div className="radial">
      <div
        className="ring"
        style={{
          width: 100, height: 100,
          background: 'radial-gradient(circle, rgba(239,68,68,.05), transparent 70%)',
        }}
      />
      <div
        className="ring"
        style={{
          width: 70, height: 70,
          background: 'radial-gradient(circle, rgba(239,68,68,.25), transparent 70%)',
        }}
      />
      <div
        className="ring"
        style={{
          width: 40, height: 40,
          background: 'radial-gradient(circle, #ef4444, #f97316 80%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 10,
          fontWeight: 700,
          textAlign: 'center',
        }}
      >
        {Math.round(rainfallPeak)}mm
      </div>
    </div>
  )
}

export default function CompareSection({ primary, p, lat, lon, region }) {
  const rainfall = p.rainfall_mm || 60

  return (
    <section id="compare">
      <span className="badge badge-live" style={{ marginBottom: 8, display: 'inline-block' }}>
        Physics-Informed Super-Resolution
      </span>
      <h2>Synoptic NWP vs AI Downscaled Resolution Comparison</h2>
      <div className="sub">
        {primary
          ? `Evaluation grid: ${region} transect (Lat ${lat.toFixed(1)}°N, Lon ${lon.toFixed(1)}°E)`
          : 'Evaluation grid: —'}
      </div>

      <div className="compare-grid">
        <div className="compare-card">
          <div className="ctitle">
            ■ Original NWP — 12 km
            <span style={{ float: 'right', color: 'var(--muted)', fontWeight: 400 }}>
              Standard Global Ensemble
            </span>
          </div>
          <CoarseGrid rainfallPeak={rainfall} />
          <div className="foot">
            {primary
              ? <>Peak estimated: <b>{Math.round(rainfall * 0.65)} mm / 24h</b> · Coarse spatial discretization</>
              : 'Coarse, blocky pixel grid simulation of regional precipitation field. Sub-basin topography is smoothed out.'}
          </div>
        </div>

        <div className="compare-card">
          <div className="ctitle">
            ■ AI Downscaled — 5 km
            <span style={{ float: 'right', color: 'var(--accent2)', fontWeight: 400 }}>
              GNN Super-Resolved
            </span>
          </div>
          <FineRadial rainfallPeak={rainfall} />
          <div className="foot">
            {primary
              ? <>Peak detected: <b>{p.rainfall_mm ?? '—'} mm / 24h</b> · Localized micro-topography risk surfaced</>
              : 'Refined, localized micro-topography risk gradient. Detects acute flash-flood risk pockets.'}
          </div>
        </div>
      </div>
    </section>
  )
}
