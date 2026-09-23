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

function RegistryRow({ f, SEV_COLOR }) {
  const p   = f.properties
  const sev = p.severity || 'low'
  const [lon, lat] = f.geometry.coordinates

  return (
    <tr>
      <td>
        <div className="region-cell">
          <span className="region-dot" style={{ background: SEV_COLOR[sev] }} />
          <div>
            <div>{p.region_name || 'Unknown region'}, Punjab</div>
            <div className="event-sub">
              {lat.toFixed(2)}°N, {lon.toFixed(2)}°E
            </div>
          </div>
        </div>
      </td>
      <td>{p.event_type || 'Extreme Weather'}</td>
      <td><span className={sevClass(sev)}>{sevLabel(sev)}</span></td>
      <td>{p.lead_time_days ? p.lead_time_days * 24 + 'h' : '—'}</td>
      <td>{p.intensity !== undefined ? Math.round(p.intensity * 100) + '%' : '—'}</td>
      <td><button className="inspect">Inspect</button></td>
    </tr>
  )
}

export default function RegistryTable({ features, SEV_COLOR }) {
  return (
    <section id="registry">
      <h2>Punjab / Chandigarh Anomaly Registry</h2>
      <div className="sub">
        Real-time GNN tracking across the Chandigarh tri-city and Punjab corridor
      </div>
      <table>
        <thead>
          <tr>
            <th>Region / Focal Coordinate</th>
            <th>Event Type</th>
            <th>Severity</th>
            <th>Horizon</th>
            <th>Confidence</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {features.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ color: 'var(--muted)' }}>
                No active anomalies in the latest run.
              </td>
            </tr>
          ) : (
            features.map((f, i) => (
              <RegistryRow key={i} f={f} SEV_COLOR={SEV_COLOR} />
            ))
          )}
        </tbody>
      </table>
    </section>
  )
}
