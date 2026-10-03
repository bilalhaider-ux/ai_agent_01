/*
 * Adapted as an ES module from deepika-builds/liquid-glass (MIT).
 * The optics, channel separation, sRGB filter and browser fallback are retained.
 */
const SVG_NS = 'http://www.w3.org/2000/svg'
let uid = 0
let svgDefs = null

const supported = (() => {
  const ua = navigator.userAgent
  const isSafari = /Safari/.test(ua) && !/Chrome|Chromium|Edg/.test(ua)
  const isFirefox = /Firefox/.test(ua)
  if (isSafari || isFirefox || !CSS.supports('backdrop-filter', 'url(#lg)')) return false
  try {
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = 4
    canvas.getContext('2d').getImageData(0, 0, 1, 1)
    return true
  } catch { return false }
})()

function ensureDefs() {
  if (svgDefs) return svgDefs
  const svg = document.createElementNS(SVG_NS, 'svg')
  svg.setAttribute('width', '0')
  svg.setAttribute('height', '0')
  svg.setAttribute('aria-hidden', 'true')
  svg.style.position = 'absolute'
  svgDefs = document.createElementNS(SVG_NS, 'defs')
  svg.appendChild(svgDefs)
  document.body.appendChild(svg)
  return svgDefs
}

function makeMap(width, height, radius, border, mapBlur) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  const gx = ctx.createLinearGradient(0, 0, width, 0)
  gx.addColorStop(0, 'rgb(0,0,0)'); gx.addColorStop(1, 'rgb(255,0,0)')
  ctx.fillStyle = gx; ctx.fillRect(0, 0, width, height)
  const gy = ctx.createLinearGradient(0, 0, 0, height)
  gy.addColorStop(0, 'rgb(0,0,0)'); gy.addColorStop(1, 'rgb(0,0,255)')
  ctx.globalCompositeOperation = 'difference'
  ctx.fillStyle = gy; ctx.fillRect(0, 0, width, height)
  ctx.globalCompositeOperation = 'source-over'
  const inset = border * Math.min(width, height)
  ctx.filter = `blur(${mapBlur}px)`
  ctx.fillStyle = 'rgba(128,128,128,.93)'
  ctx.beginPath()
  ctx.roundRect(inset, inset, width - inset * 2, height - inset * 2, Math.max(radius - inset, 2))
  ctx.fill(); ctx.filter = 'none'
  return canvas.toDataURL()
}

function buildFilter(id, scales) {
  const filter = document.createElementNS(SVG_NS, 'filter')
  Object.entries({ id, x: 0, y: 0, width: '100%', height: '100%', 'color-interpolation-filters': 'sRGB' })
    .forEach(([key, value]) => filter.setAttribute(key, value))
  const image = document.createElementNS(SVG_NS, 'feImage')
  Object.entries({ x: 0, y: 0, result: 'map', preserveAspectRatio: 'none' })
    .forEach(([key, value]) => image.setAttribute(key, value))
  filter.appendChild(image)
  const keep = [
    '1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0',
    '0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0',
    '0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0',
  ]
  scales.forEach((scale, i) => {
    const displacement = document.createElementNS(SVG_NS, 'feDisplacementMap')
    Object.entries({ in: 'SourceGraphic', in2: 'map', scale, xChannelSelector: 'R', yChannelSelector: 'B', result: `d${i}` })
      .forEach(([key, value]) => displacement.setAttribute(key, value))
    filter.appendChild(displacement)
    const matrix = document.createElementNS(SVG_NS, 'feColorMatrix')
    Object.entries({ in: `d${i}`, type: 'matrix', values: keep[i], result: `c${i}` })
      .forEach(([key, value]) => matrix.setAttribute(key, value))
    filter.appendChild(matrix)
  })
  const blendOne = document.createElementNS(SVG_NS, 'feBlend')
  Object.entries({ in: 'c0', in2: 'c1', mode: 'screen', result: 'c01' }).forEach(([k, v]) => blendOne.setAttribute(k, v))
  filter.appendChild(blendOne)
  const blendTwo = document.createElementNS(SVG_NS, 'feBlend')
  Object.entries({ in: 'c01', in2: 'c2', mode: 'screen' }).forEach(([k, v]) => blendTwo.setAttribute(k, v))
  filter.appendChild(blendTwo)
  ensureDefs().appendChild(filter)
  return { filter, image }
}

export function liquidGlass(element, options = {}) {
  const opts = { scale: -112, chroma: 6, border: .07, mapBlur: 12, blur: 3, saturate: 1.5, radius: null, fallbackBlur: 16, ...options }
  if (!supported) {
    const frosted = `blur(${opts.fallbackBlur}px) saturate(${opts.saturate})`
    element.style.backdropFilter = frosted
    element.style.webkitBackdropFilter = frosted
    element.classList.add('lg-fallback')
    return { supported: false, refresh() {}, destroy() {
      element.style.backdropFilter = ''; element.style.webkitBackdropFilter = ''; element.classList.remove('lg-fallback')
    }}
  }
  const id = `lg-filter-${++uid}`
  const parts = buildFilter(id, [opts.scale, opts.scale + opts.chroma, opts.scale + opts.chroma * 2])
  const refresh = () => {
    const width = element.offsetWidth, height = element.offsetHeight
    if (!width || !height) return
    const raw = getComputedStyle(element).borderTopLeftRadius || '0px'
    const radius = opts.radius ?? (raw.trim().endsWith('%') ? parseFloat(raw) / 100 * Math.min(width, height) : parseFloat(raw) || 0)
    parts.image.setAttribute('href', makeMap(width, height, radius, opts.border, opts.mapBlur))
    parts.image.setAttribute('width', width); parts.image.setAttribute('height', height)
  }
  refresh()
  element.style.backdropFilter = `url(#${id}) blur(${opts.blur}px) saturate(${opts.saturate})`
  let timer
  const observer = new ResizeObserver(() => { clearTimeout(timer); timer = setTimeout(refresh, 120) })
  observer.observe(element)
  return { supported: true, refresh, destroy() {
    observer.disconnect(); clearTimeout(timer); parts.filter.remove(); element.style.backdropFilter = ''
  }}
}
