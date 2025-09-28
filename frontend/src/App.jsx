import { useEffect, useState } from 'react'
import WordCloud from './components/WordCloud.jsx'
import { fetchAnalysis, rebuildAnalysis } from './lib/api'

function App() {
  const [words, setWords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchAnalysis()
        setWords(data)
      } catch (e) {
        setError(e.message || 'fetch failed')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleRebuild = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await rebuildAnalysis()
      setWords(data)
      setNonce(n => n + 1)
      setStatus('再集計しました')
      setTimeout(() => setStatus(''), 2000)
    } catch (e) {
      setError(e.message || 'rebuild failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="text-white h-screen overflow-hidden flex flex-col items-center justify-center px-4">
      <h1 className="title-gradient text-2xl md:text-3xl font-extrabold tracking-tight mb-4 text-center">Qiita 人気タイトル分析</h1>

      <div className="relative" style={{ width: 'min(82vw, calc(100vh - 160px))', height: 'min(82vw, calc(100vh - 160px))' }}>
        <button onClick={handleRebuild} disabled={loading} className="glass-btn absolute -top-2 -right-2 z-20 disabled:opacity-60">
          再集計
        </button>

        <div className="rounded-full overflow-hidden ring-1 ring-white/25 shadow-[0_20px_60px_-10px_rgba(0,0,0,0.6)] bg-white/10 backdrop-blur-2xl w-full h-full flex items-center justify-center">
          {loading && <p className="opacity-80">読み込み中...</p>}
          {error && <p className="text-red-300">{error}</p>}
          {!loading && !error && (
            <div className="relative w-full h-full">
              <WordCloud words={words} nonce={nonce} />
            </div>
          )}
        </div>

        {status && (
          <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 text-sm text-white/80">
            {status}
          </div>
        )}
      </div>
    </div>
  )
}

export default App


