import { useState, useEffect } from 'react'
import TopBar from './components/TopBar'
import AlertBanner from './components/AlertBanner'
import FiltersPanel from './components/FiltersPanel'
import MapPanel from './components/MapPanel'
import ActiveEventPanel from './components/ActiveEventPanel'
import CompareSection from './components/CompareSection'
import TelemetryGrid from './components/TelemetryGrid'
import RegistryTable from './components/RegistryTable'

const SEV_COLOR = { low: '#eab308', moderate: '#f97316', severe: '#ef4444' }

function derivePrimary(features) {
  if (!features.length) return null
  return [...features].sort(
    (a, b) => (b.properties.intensity || 0) - (a.properties.intensity || 0)
  )[0]
}

export default function App() {
  const [features, setFeatures] = useState([])
  const [error, setError] = useState(null)
  const [latency, setLatency] = useState('—')
  const [activeTab, setActiveTab] = useState('Dashboard')

  useEffect(() => {
    const t0 = Date.now()
    fetch('/output/alerts.geojson')
      .then(r => r.json())
      .then(data => {
        setLatency((Date.now() - t0) + 'ms')
        setFeatures(data.features || [])
      })
      .catch(() => setError('No output/alerts.geojson found — run scripts/run_demo.py first.'))
  }, [])

  const primary = derivePrimary(features)
  const p = primary?.properties ?? {}
  const [lon, lat] = primary?.geometry?.coordinates ?? [76.7794, 30.7333]
  const sev = p.severity || 'low'
  const region = p.region_name || 'Chandigarh'

  return (
    <>
      <TopBar
        latency={latency}
        nodeCount={features.length}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        coord={lat && lon ? `${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E` : '30.73°N, 76.78°E'}
      />

      <AlertBanner
        error={error}
        primary={primary}
        region={region}
        p={p}
      />

      <div id="layout">
        <section id="left">
          <FiltersPanel p={p} sev={sev} onReload={() => window.location.reload()} />
        </section>

        <section id="center">
          <MapPanel
            features={features}
            lat={lat}
            lon={lon}
            SEV_COLOR={SEV_COLOR}
          />
        </section>

        <section id="right">
          <ActiveEventPanel
            primary={primary}
            p={p}
            lat={lat}
            lon={lon}
            sev={sev}
            region={region}
            features={features}
          />
        </section>
      </div>

      <CompareSection primary={primary} p={p} lat={lat} lon={lon} region={region} />
      <TelemetryGrid p={p} />
      <RegistryTable features={features} SEV_COLOR={SEV_COLOR} />
    </>
  )
}
