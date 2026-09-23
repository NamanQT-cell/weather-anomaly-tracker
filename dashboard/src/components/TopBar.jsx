const NAV_LINKS = ['Dashboard', 'Events', 'Forecast', 'Alerts', 'Analytics']

export default function TopBar({ latency, nodeCount, activeTab, onTabChange, coord }) {
  return (
    <div id="topbar">
      <div className="brand">🌩️ WeatherAI <span className="badge badge-ok">OPERATIONAL</span></div>
      <div className="stat">Live: <b>00Z</b></div>
      <div className="stat">Latency <b>{latency}</b></div>
      <div className="stat">Nodes <b>{nodeCount > 0 ? `${nodeCount}/${nodeCount}` : '—'}</b></div>

      <nav>
        {NAV_LINKS.map(link => (
          <a
            key={link}
            className={activeTab === link ? 'active' : ''}
            onClick={() => onTabChange(link)}
          >
            {link}
          </a>
        ))}
      </nav>

      <div className="spacer" />
      <div className="search">Coord: {coord}</div>
      <div className="stat">Ensemble <b>12km</b></div>
    </div>
  )
}
