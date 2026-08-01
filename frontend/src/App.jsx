import { useState } from 'react'

const API_URL = 'https://news-research-agent.agreeableriver-806102e7.eastus.azurecontainerapps.io'

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setReport(null)

    try {
      const response = await fetch(`${API_URL}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`)
      }

      const data = await response.json()
      setReport(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: '2rem auto', fontFamily: 'sans-serif', padding: '0 1rem' }}>
      <h1>News Research Agent</h1>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. latest developments in AI coding agents"
          style={{ flex: 1, padding: '0.5rem' }}
        />
        <button type="submit" disabled={loading || !query}>
          {loading ? 'Researching...' : 'Research'}
        </button>
      </form>

      {loading && <p>Searching, analyzing, and writing a report — this can take 15-30s...</p>}

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {report && (
        <div>
          <h2>{report.headline}</h2>

          <ul>
            {report.key_developments.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>

          <img
            src={`${API_URL}${report.image_url}`}
            alt="Generated infographic"
            style={{ maxWidth: '100%', borderRadius: 8 }}
          />

          <h3>Sources</h3>
          <ul>
            {report.sources.map((src, i) => (
              <li key={i}>
                {src.startsWith('http') ? (
                  <a href={src} target="_blank" rel="noopener noreferrer">
                    {src}
                  </a>
                ) : (
                  src
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default App
