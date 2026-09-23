import { useState } from 'react'

const HORIZONS = ['24h', '48h', '72h', '5 days', '7 days', '10 days']

const PIPELINE_STEPS = [
  'NWP Data',
  'Anomaly Detection',
  'GNN Tracking',
  'Downscaling (12km→5km)',
  'Physics Validation',
  'Risk Generation',
]

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

export default function FiltersPanel({ p, sev, onReload }) {
  const [horizon, setHorizon] = useState('72h')

  const rainfallSev  = (p.rainfall_mm  || 0) > 50 ? 'severe' : 'moderate'
  const windSev      = (p.wind_speed_kmh || 0) > 50 ? 'severe' : 'moderate'
  const heatwaveText = (p.temperature_c || 0) > 32 ? 'High' : 'Low'

  return (
    <>
      <div className="panel-title">Parameters &amp; Horizons</div>
      <h2>Anomaly Filters</h2>
      <div style={{ color: 'var(--muted)', fontSize: 11, marginBottom: 12 }}>
        Configure physics thresholds and GNN bounds
      </div>

      <div className="panel-title">Atmospheric Event Classes</div>
      <div className="filter-row">
        <span>🌧️ Extreme Rainfall</span>
        <span className={sevClass(rainfallSev)}>{sevLabel(rainfallSev)}</span>
      </div>
      <div className="filter-row">
        <span>🌡️ Heatwave</span>
        <span className={heatwaveText === 'High' ? 'tag-pill tag-moderate' : 'tag-pill tag-low'}>
          {heatwaveText}
        </span>
      </div>
      <div className="filter-row">
        <span>❄️ Cold Wave</span>
        <span className="tag-pill tag-low">Low</span>
      </div>
      <div className="filter-row">
        <span>💨 Extreme Wind</span>
        <span className={sevClass(windSev)}>{sevLabel(windSev)}</span>
      </div>
      <div className="filter-row">
        <span>🌀 Cyclone</span>
        <span className="tag-pill tag-low">Low</span>
      </div>

      <div className="panel-title">Prediction Horizon</div>
      <div className="chip-grid">
        {HORIZONS.map(h => (
          <div
            key={h}
            className={`chip${horizon === h ? ' active' : ''}`}
            onClick={() => setHorizon(h)}
          >
            {h}
          </div>
        ))}
      </div>

      <div className="panel-title">Severity Threshold Filter</div>
      <div className="check-row"><span className="dot" style={{ background: 'var(--ok)' }} />Low (Norm)</div>
      <div className="check-row"><span className="dot" style={{ background: 'var(--mod)' }} />Moderate</div>
      <div className="check-row"><span className="dot" style={{ background: 'var(--sev)' }} />High Risk</div>
      <div className="check-row"><span className="dot" style={{ background: '#b91c1c' }} />Severe</div>

      <button className="btn-primary" onClick={onReload}>⟳ Execute Model</button>
      <div className="cycle-note">Cycle: 00:00 UTC · Grid: 5km GNN</div>

      <div className="panel-title">AI Pipeline Engine</div>
      <div style={{ fontSize: 10, color: 'var(--ok)', marginBottom: 6 }}>ALL VALIDATED</div>
      {PIPELINE_STEPS.map(step => (
        <div className="pipeline-row" key={step}>
          <span>{step}</span>
          <span className="ok">
            {step === 'NWP Data' ? 'Loaded ✓' : 'Complete ✓'}
          </span>
        </div>
      ))}
    </>
  )
}
