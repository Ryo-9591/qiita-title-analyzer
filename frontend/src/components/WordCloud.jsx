import { useEffect, useMemo, useRef } from 'react'
import * as d3 from 'd3'
import cloud from 'd3-cloud'

// words: [{ text, value }]
function WordCloud({ words, nonce = 0 }) {
  const containerRef = useRef(null)

  const layoutSize = useMemo(() => {
    return 500 // レイアウト計算用の仮想サイズ（描画はSVGのviewBoxでスケール）
  }, [])

  const sorted = useMemo(() => {
    const copy = Array.isArray(words) ? [...words] : []
    copy.sort((a, b) => b.value - a.value)
    return copy.slice(0, 120) // 上位N語に制限
  }, [words])

  const fontSize = useMemo(() => {
    const values = sorted.map(w => w.value)
    const max = d3.max(values) || 1
    const min = d3.min(values) || 1
    const domainMin = Math.min(min, max === min ? Math.max(1, min - 1) : min)
    return d3.scaleSqrt().domain([domainMin, max]).range([12, 72]).clamp(true)
  }, [sorted])

  useEffect(() => {
    if (!containerRef.current) return
    if (!sorted.length) return

    const layout = cloud()
      .size([layoutSize, layoutSize])
      .words(sorted.map(d => ({ ...d, size: fontSize(d.value) })))
      .padding(3)
      .rotate(() => 0)
      .font('ui-sans-serif, system-ui')
      .fontSize(d => d.size)
      .on('end', draw)

    layout.start()

    function draw(wordsPlaced) {
      const width = layoutSize
      const height = layoutSize
      const svg = d3.select(containerRef.current)
        .html('')
        .append('svg')
        .attr('viewBox', `${-width / 2} ${-height / 2} ${width} ${height}`)
        .attr('width', '100%')
        .attr('height', '100%')

      const radius = Math.min(width, height) * 0.7

      // 先に定義（フィルタ・グラデーション・クリップ）
      const defs = svg.append('defs')
      const filter = defs.append('filter').attr('id', 'shadow')
      filter.append('feDropShadow')
        .attr('dx', 0).attr('dy', 2).attr('stdDeviation', 4)
        .attr('flood-color', '#000').attr('flood-opacity', 0.25)

      const grad = defs.append('radialGradient').attr('id', 'glassGrad')
      grad.attr('cx', '45%').attr('cy', '35%').attr('r', '65%')
      grad.append('stop').attr('offset', '0%').attr('stop-color', 'rgba(255,255,255,0.38)')
      grad.append('stop').attr('offset', '60%').attr('stop-color', 'rgba(255,255,255,0.20)')
      grad.append('stop').attr('offset', '100%').attr('stop-color', 'rgba(255,255,255,0.10)')

      const clipId = 'wc-clip'
      defs.append('clipPath').attr('id', clipId)
        .append('circle').attr('cx', 0).attr('cy', 0).attr('r', radius)

      // 背景のガラス風円のみ表示
      svg.append('circle')
        .attr('cx', 0)
        .attr('cy', 0)
        .attr('r', radius)
        .attr('fill', 'url(#glassGrad)')
        .attr('stroke', 'rgba(255,255,255,0.45)')
        .attr('stroke-width', 1)
        .attr('filter', 'url(#shadow)')

      // ハイライト（円内にクリップ）
      svg.append('g')
        .attr('clip-path', `url(#${clipId})`)
        .append('ellipse')
        .attr('cx', -radius * 0.25)
        .attr('cy', -radius * 0.25)
        .attr('rx', radius * 0.5)
        .attr('ry', radius * 0.38)
        .attr('fill', 'rgba(255,255,255,0.18)')
        .attr('opacity', 0.35)

      const values = sorted.map(d => d.value)
      const vmin = d3.min(values) || 1
      const vmax = d3.max(values) || 1
      const color = d3.scaleSequential(d3.interpolateTurbo)
        .domain([vmin, vmax])

      svg.append('g')
        .attr('clip-path', `url(#${clipId})`)
        .selectAll('text')
        .data(wordsPlaced)
        .enter()
        .append('text')
        .style('font-family', 'ui-sans-serif, system-ui')
        .style('font-weight', 700)
        .style('fill', d => color(d.value))
        .attr('text-anchor', 'middle')
        .attr('transform', d => `translate(${d.x}, ${d.y}) rotate(${d.rotate})`)
        .style('font-size', d => `${d.size}px`)
        .text(d => d.text)
        .append('title')
        .text(d => `${d.text}: ${d.value}`)
    }
  }, [sorted, fontSize, layoutSize, nonce])

  return <div ref={containerRef} className="w-full h-full" />
}

export default WordCloud


