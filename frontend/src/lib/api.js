export async function fetchAnalysis() {
  const res = await fetch('/api/analysis')
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  return res.json()
}

export async function rebuildAnalysis() {
  const res = await fetch('/api/rebuild', { method: 'POST' })
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  return res.json()
}


