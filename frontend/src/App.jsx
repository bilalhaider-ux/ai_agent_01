import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence, useScroll, useSpring, useReducedMotion, useInView, useMotionValue, useTransform, animate as animateValue } from 'framer-motion'
import { Activity, ArrowLeft, ArrowUpRight, BarChart3, BrainCircuit, Check, ChevronRight, Cpu, Database, Download, FileSearch, FileText, Gauge, LineChart, LoaderCircle, Lock, Moon, Play, Plus, Save, ShieldCheck, Sparkles, Sun, Table2, Terminal, UploadCloud, Workflow, X, Zap } from 'lucide-react'
import Lenis from 'lenis'
import 'lenis/dist/lenis.css'
import { listReports, removeReport, saveReport } from './lib/storage'
import LightTunnel from './LightTunnel'

const API_URL = import.meta.env.VITE_AGENT_API_URL || 'http://127.0.0.1:8000'
const DEFAULT_QUERY = 'Analyze revenue by product category and identify return risks'
const STEPS = ['Profile dataset', 'Build analytical plan', 'Generate code', 'Run isolated analysis', 'Synthesize decision brief']

const MARQUEE = [
  { icon: Database, label: 'Polars profiling' },
  { icon: BrainCircuit, label: 'LangGraph planning' },
  { icon: Terminal, label: 'Isolated execution' },
  { icon: LineChart, label: 'Matplotlib visuals' },
  { icon: Gauge, label: 'SciPy statistics' },
  { icon: ShieldCheck, label: 'Verified metrics' },
  { icon: FileText, label: 'Decision reports' },
  { icon: Zap, label: 'Gemini + fallback' },
  { icon: Table2, label: 'CSV · XLSX · Parquet' },
  { icon: Lock, label: 'Private by default' }
]

const FEATURES = [
  { icon: FileSearch, title: 'Automatic data profiling', body: 'Schema, types, nulls, duplicates, distributions and summary statistics are extracted the moment your file lands.' },
  { icon: BrainCircuit, title: 'Reasoned analysis plans', body: 'A LangGraph workflow minifies context, forms intent, and chooses the right statistical approach before any code runs.' },
  { icon: Terminal, title: 'Isolated code execution', body: 'Generated Polars, SciPy and Matplotlib code runs in a timed subprocess that self-corrects runtime failures.' },
  { icon: ShieldCheck, title: 'Machine-verified metrics', body: 'Every number in your brief is computed from your data and JSON-serialized, never hallucinated by the model.' },
  { icon: LineChart, title: 'Visual evidence', body: 'Charts are rendered from the real analysis so you can see the trend behind every recommendation.' },
  { icon: Download, title: 'Portable reports', body: 'Export professional HTML and Markdown, or keep reports in a private browser archive — no account required.' }
]

const HOW = [
  { icon: UploadCloud, kicker: 'STEP 01', title: 'Upload your dataset', body: 'Drag in a CSV, XLSX, Parquet, TSV, JSON or JSONL file. DataSnap profiles it instantly — no schema setup.' },
  { icon: FileText, kicker: 'STEP 02', title: 'Ask your question', body: 'Describe the decision in plain language. Be specific about the outcome you need and the context that matters.' },
  { icon: Workflow, kicker: 'STEP 03', title: 'Let the agent work', body: 'The workflow plans, writes code, executes in isolation, and self-corrects — all while you watch the live progress.' },
  { icon: Activity, kicker: 'STEP 04', title: 'Review the decision brief', body: 'Get an executive summary, direct answer, verified metrics, charts and recommended actions. Save or export in a click.' }
]

const STATS = [
  { value: '6+', label: 'File formats supported' },
  { value: '5', label: 'Workflow stages per run' },
  { value: '100%', label: 'Metrics computed, not guessed' },
  { value: '0', label: 'Accounts required' }
]

/* ---- Pricing (PKR). Yearly ≈ 20% off, shown as the per-month equivalent. ---- */
const PRICING_PLANS = [
  {
    name: 'Starter',
    monthly: 0,
    yearly: 0,
    blurb: 'For individuals exploring what automated analysis can do.',
    cta: 'Get started',
    popular: false,
    features: ['5 analyses per hour', 'All 6+ file formats', 'Isolated code execution', 'Verified metrics & charts', 'Markdown & HTML export']
  },
  {
    name: 'Pro',
    monthly: 2900,
    yearly: 2320,
    blurb: 'For analysts who need more runs and deeper evidence.',
    cta: 'Upgrade to Pro',
    popular: true,
    features: ['Unlimited analyses', 'Priority Gemini throughput', 'Extended execution timeout', 'Larger upload limits', 'Priority support']
  },
  {
    name: 'Teams',
    monthly: 5900,
    yearly: 4720,
    blurb: 'For teams that need shared, scalable decision intelligence.',
    cta: 'Contact sales',
    popular: false,
    features: ['Everything in Pro', 'Up to 15 members', 'Shared report library', 'Role-based access', 'Dedicated support']
  }
]
const pkr = (n) => n === 0 ? 'PKR 0' : `PKR ${n.toLocaleString('en-PK')}`


/* ---- Grounded preview data (sample_sales_data.csv, exactly what the agent computes) ---- */
// Total Revenue by Product Category (Polars group_by, sorted desc)
const PREVIEW_CATEGORIES = [
  { label: 'Electronics', value: 9801.59 },
  { label: 'Home & Kitchen', value: 1789.0 },
  { label: 'Sports', value: 1156.9 },
  { label: 'Fashion', value: 1019.0 },
  { label: 'Beauty', value: 869.15 }
]

/* ---------------------------------------------------------------- motion -- */
const easeOut = [0.22, 1, 0.36, 1]
const pageMotion = {
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: easeOut, staggerChildren: 0.07, delayChildren: 0.05 } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.25, ease: 'easeIn' } }
}
const rise = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: easeOut } }
}
const fadeUpView = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0, transition: { duration: 0.6, ease: easeOut } },
  viewport: { once: true, amount: 0.3 }
}

/* Reusable staggered container + item for scroll-reveal grids */
const staggerParent = {
  initial: {},
  whileInView: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
  viewport: { once: true, amount: 0.25 }
}
const revealItem = {
  initial: { opacity: 0, y: 26, filter: 'blur(6px)' },
  whileInView: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.6, ease: easeOut } }
}

/* Word-level reveal child for the hero headline */
const wordChild = {
  initial: { opacity: 0, y: '0.5em', filter: 'blur(10px)' },
  animate: { opacity: 1, y: '0em', filter: 'blur(0px)', transition: { duration: 0.7, ease: easeOut } }
}
const wordParent = {
  initial: {},
  animate: { transition: { staggerChildren: 0.08, delayChildren: 0.15 } }
}

const MDiv = motion.div
const MSection = motion.section
const MMain = motion.main

/* Headline that reveals word-by-word with a cinematic blur + rise.
   Each word+trailing-space is ONE inline-block so whitespace is preserved
   (nested inline-blocks collapse the gap). No overflow mask → no clipping. */
function WordReveal({ text, className }) {
  const reduce = useReducedMotion()
  if (reduce) return <span className={className}>{text}</span>
  const words = text.split(' ')
  return (
    <motion.span className={className} variants={wordParent} initial="initial" animate="animate">
      {words.map((word, i) => (
        <motion.span key={i} variants={wordChild} style={{ display: 'inline-block', whiteSpace: 'pre', willChange: 'transform, filter' }}>
          {i < words.length - 1 ? `${word} ` : word}
        </motion.span>
      ))}
    </motion.span>
  )
}

/* 3D tilt card that tracks the pointer with spring physics. */
function TiltCard({ children, className, max = 8, scale = 1.02, ...rest }) {
  const reduce = useReducedMotion()
  const ref = useRef(null)
  const mx = useMotionValue(0)
  const my = useMotionValue(0)
  const rx = useSpring(useTransform(my, [-0.5, 0.5], [max, -max]), { stiffness: 220, damping: 18 })
  const ry = useSpring(useTransform(mx, [-0.5, 0.5], [-max, max]), { stiffness: 220, damping: 18 })

  if (reduce) return <div ref={ref} className={className} {...rest}>{children}</div>

  function onMove(e) {
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return
    mx.set((e.clientX - rect.left) / rect.width - 0.5)
    my.set((e.clientY - rect.top) / rect.height - 0.5)
  }
  function onLeave() { mx.set(0); my.set(0) }

  return (
    <motion.div
      ref={ref}
      className={className}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      whileHover={{ scale }}
      style={{ rotateX: rx, rotateY: ry, transformPerspective: 900, transformStyle: 'preserve-3d', willChange: 'transform' }}
      transition={{ type: 'spring', stiffness: 260, damping: 20 }}
      {...rest}
    >
      {children}
    </motion.div>
  )
}

/* Magnetic button — subtly pulls toward the cursor, snaps back with spring. */
function Magnetic({ children, className, strength = 0.4, onClick, type = 'button', disabled, ...rest }) {
  const reduce = useReducedMotion()
  const ref = useRef(null)
  const x = useSpring(useMotionValue(0), { stiffness: 300, damping: 20 })
  const y = useSpring(useMotionValue(0), { stiffness: 300, damping: 20 })

  function onMove(e) {
    // Magnetic cursor-follow disabled: keep the button stationary on hover.
    return
  }
  function onLeave() { x.set(0); y.set(0) }

  return (
    <motion.button
      ref={ref}
      type={type}
      className={className}
      onClick={onClick}
      disabled={disabled}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      style={reduce ? undefined : { x, y }}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      {...rest}
    >
      {children}
    </motion.button>
  )
}

/* Animated number count-up that fires when scrolled into view */
function CountUp({ value, className }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, amount: 0.6 })
  const reduce = useReducedMotion()
  const [display, setDisplay] = useState(value)
  const match = String(value).match(/^(\D*)([\d.,]+)(\D*)$/)

  useEffect(() => {
    if (!match) { setDisplay(value); return }
    const [, prefix, numStr, suffix] = match
    const target = parseFloat(numStr.replace(/,/g, ''))
    const decimals = (numStr.split('.')[1] || '').length
    if (reduce) { setDisplay(value); return }
    if (!inView) { setDisplay(`${prefix}0${suffix}`); return }
    const controls = animateValue(0, target, {
      duration: 1.1, ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setDisplay(`${prefix}${v.toFixed(decimals)}${suffix}`)
    })
    return () => controls.stop()
  }, [inView, reduce]) // eslint-disable-line

  return <strong ref={ref} className={className}>{display}</strong>
}

function Logo() {
  return (
    <div className="logo">
      <span className="logo-mark"><span className="logo-bars"><i /><i /><i /></span></span>
      <strong>DataSnap</strong>
    </div>
  )
}
function dateLabel(value) { return value ? new Date(value).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) : 'Just now' }

/* Theme: localStorage override → else system preference. Persists + applies data-theme. */
function getInitialTheme() {
  try {
    const saved = localStorage.getItem('datasnap-theme')
    if (saved === 'light' || saved === 'dark') return saved
  } catch { /* ignore */ }
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function useTheme() {
  const [theme, setTheme] = useState(getInitialTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#0b0e14' : '#ffffff')
    try { localStorage.setItem('datasnap-theme', theme) } catch { /* ignore */ }
  }, [theme])

  // Follow system changes only when the user hasn't explicitly chosen.
  useEffect(() => {
    if (!window.matchMedia) return
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = (event) => {
      let saved = null
      try { saved = localStorage.getItem('datasnap-theme') } catch { /* ignore */ }
      if (saved !== 'light' && saved !== 'dark') setTheme(event.matches ? 'dark' : 'light')
    }
    mql.addEventListener?.('change', onChange)
    return () => mql.removeEventListener?.('change', onChange)
  }, [])

  const toggle = () => setTheme(current => (current === 'dark' ? 'light' : 'dark'))
  return { theme, toggle }
}

export default function App() {
  const { theme, toggle } = useTheme()
  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, { stiffness: 140, damping: 28, restDelta: 0.001 })
  const lenisRef = useRef(null)

  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      touchMultiplier: 1.5
    })
    lenisRef.current = lenis

    function raf(time) {
      lenis.raf(time)
      requestAnimationFrame(raf)
    }
    const rafId = requestAnimationFrame(raf)

    return () => {
      cancelAnimationFrame(rafId)
      lenis.destroy()
      lenisRef.current = null
    }
  }, [])

  const [page, setPage] = useState(window.location.pathname.startsWith('/reports') ? 'reports' : window.location.pathname.startsWith('/report/') ? 'report' : window.location.pathname === '/analyze' ? 'analyze' : window.location.pathname === '/privacy' ? 'privacy' : window.location.pathname === '/terms' ? 'terms' : window.location.pathname === '/security' ? 'security' : 'landing')
  const [reportId, setReportId] = useState(window.location.pathname.split('/').pop())
  const [reports, setReports] = useState([])
  const [report, setReport] = useState(null)
  const [file, setFile] = useState(null)
  const [query, setQuery] = useState(DEFAULT_QUERY)
  const [running, setRunning] = useState(false)
  const [step, setStep] = useState(0)
  const [error, setError] = useState('')
  const [quota, setQuota] = useState(null)

  useEffect(() => { listReports().then(items => { setReports(items); if (page === 'report') setReport(items.find(item => item.analysis_id === reportId)) }) }, [])
  useEffect(() => { const onPop = () => { const path = window.location.pathname; setPage(path.startsWith('/reports') ? 'reports' : path.startsWith('/report/') ? 'report' : path === '/analyze' ? 'analyze' : path === '/privacy' ? 'privacy' : path === '/terms' ? 'terms' : path === '/security' ? 'security' : 'landing'); setReportId(path.split('/').pop()) }; window.addEventListener('popstate', onPop); return () => window.removeEventListener('popstate', onPop) }, [])

  function navigate(next, id = '') {
    const path = id ? `/report/${id}` : next === 'analyze' ? '/analyze' : next === 'reports' ? '/reports' : next === 'privacy' ? '/privacy' : next === 'terms' ? '/terms' : next === 'security' ? '/security' : '/'
    window.history.pushState({}, '', path)
    setPage(next)
    if (id) setReportId(id)
    if (lenisRef.current) {
      lenisRef.current.scrollTo(0, { immediate: true })
    } else {
      window.scrollTo({ top: 0, behavior: 'instant' })
    }
  }
  function openReport(item) { setReport(item); navigate('report', item.analysis_id) }

  async function runAnalysis() {
    if (!file) return setError('Choose a dataset before continuing.')
    if (!query.trim()) return setError('Add a business question before continuing.')
    setRunning(true); setError(''); setStep(0)
    const payload = new FormData(); payload.append('query', query.trim()); payload.append('dataset', file); payload.append('provider', 'gemini')
    const timer = setInterval(() => setStep(current => Math.min(current + 1, STEPS.length - 1)), 1500)
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 15_000)
    try {
      const response = await fetch(`${API_URL}/api/v1/analyze`, { method: 'POST', body: payload, credentials: 'include', signal: controller.signal })
      clearTimeout(timeout)
      const contentType = response.headers.get('content-type') || ''
      const body = contentType.includes('application/json') ? await response.json() : null
      setQuota({ remaining: response.headers.get('X-RateLimit-Remaining'), limit: response.headers.get('X-RateLimit-Limit') || '5' })
      if (!response.ok) {
        const detail = body?.detail || body?.error?.message
        throw new Error(detail || `Analysis API returned HTTP ${response.status}. Check the backend logs for the upstream provider response.`)
      }
      const jobId = body.analysis_id
      let job = body
      const pollingDeadline = Date.now() + 10 * 60 * 1000
      while (job.status === 'queued' || job.status === 'running') {
        if (Date.now() >= pollingDeadline) throw new Error('The analysis is taking longer than expected. Check the Reports page later or review the backend logs.')
        await new Promise(resolve => setTimeout(resolve, 2000))
        const statusResponse = await fetch(`${API_URL}/api/v1/analyses/${jobId}`, { credentials: 'include' })
        const statusType = statusResponse.headers.get('content-type') || ''
        const statusBody = statusType.includes('application/json') ? await statusResponse.json() : null
        if (!statusResponse.ok) throw new Error(statusBody?.detail || `Analysis status returned HTTP ${statusResponse.status}.`)
        job = statusBody
        if (job.status === 'running') setStep(current => Math.min(current + 1, STEPS.length - 1))
      }
      if (job.status === 'failed') throw new Error(job.error?.message || 'The analysis worker failed. Check the backend logs.')
      setReport(job); navigate('report', job.analysis_id)
    } catch (requestError) {
      const message = requestError.name === 'AbortError'
        ? 'The analysis API did not respond within 15 seconds. Please check the backend deployment and try again.'
        : requestError.message || 'The analysis request could not reach the API.'
      setError(message)
    } finally { clearTimeout(timeout); clearInterval(timer); setRunning(false) }
  }

  async function deleteReport(id) { await removeReport(id); const next = await listReports(); setReports(next); if (report?.analysis_id === id) { setReport(null); navigate('reports') } }
  function download(name, content, type) { const url = URL.createObjectURL(new Blob([content], { type })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click(); URL.revokeObjectURL(url) }

  function scrollToFeatures() {
    if (lenisRef.current) {
      lenisRef.current.scrollTo('#features', { offset: -30, duration: 1.15 })
    } else {
      document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="site-shell">
      <motion.div className="scroll-progress" style={{ scaleX }} aria-hidden />
      <motion.header className="site-nav" initial={{ y: -72, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.5, ease: easeOut }}>
        <motion.button className="brand-button" onClick={() => navigate('landing')} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}><Logo /></motion.button>

        <nav className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-1 md:flex">
          <button className={`rounded-[9px] px-3.5 py-2 text-[13.5px] font-medium transition-colors ${page === 'landing' ? 'text-brand' : 'text-ink-dim hover:text-ink'}`} onClick={() => navigate('landing')}>Overview</button>
          <button className={`rounded-[9px] px-3.5 py-2 text-[13.5px] font-medium transition-colors ${page === 'analyze' ? 'text-brand' : 'text-ink-dim hover:text-ink'}`} onClick={() => navigate('analyze')}>Analyze</button>
          <button className={`flex items-center gap-1.5 rounded-[9px] px-3.5 py-2 text-[13.5px] font-medium transition-colors ${page === 'reports' || page === 'report' ? 'text-brand' : 'text-ink-dim hover:text-ink'}`} onClick={() => navigate('reports')}>Reports <span className="rounded-full bg-brand-soft px-1.5 py-0.5 font-mono text-[10px] text-brand">{reports.length}</span></button>
        </nav>

        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          <span className="hidden font-mono text-[11px] text-ink-dim lg:inline">{quota ? `${quota.remaining}/${quota.limit} left` : '5 / hour'}</span>
          <motion.button
            className="grid h-9 w-9 place-items-center rounded-[10px] border border-hairline-strong bg-panel text-ink-dim shadow-sm transition-colors hover:border-brand-line hover:text-brand"
            onClick={toggle} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
            whileHover={{ y: -1 }} whileTap={{ scale: 0.94 }}
          >
            <AnimatePresence mode="wait" initial={false}>
              {theme === 'dark' ? (
                <motion.span key="sun" initial={{ rotate: -90, opacity: 0, scale: 0.6 }} animate={{ rotate: 0, opacity: 1, scale: 1 }} exit={{ rotate: 90, opacity: 0, scale: 0.6 }} transition={{ duration: 0.25 }} style={{ display: 'grid' }}>
                  <Sun size={16} />
                </motion.span>
              ) : (
                <motion.span key="moon" initial={{ rotate: 90, opacity: 0, scale: 0.6 }} animate={{ rotate: 0, opacity: 1, scale: 1 }} exit={{ rotate: -90, opacity: 0, scale: 0.6 }} transition={{ duration: 0.25 }} style={{ display: 'grid' }}>
                  <Moon size={16} />
                </motion.span>
              )}
            </AnimatePresence>
          </motion.button>
          <button className="rounded-[10px] px-2.5 py-2 text-[13px] font-medium text-ink-dim transition-colors hover:text-ink sm:px-3 sm:text-[13.5px]" onClick={() => navigate('reports')}>Reports</button>
          <motion.button
            className="hidden min-[400px]:inline-flex items-center gap-1.5 rounded-[11px] border border-hairline-strong bg-panel px-3.5 py-2 text-[13px] font-semibold text-ink shadow-sm transition-colors hover:border-brand-line hover:text-brand sm:px-4 sm:text-[13.5px]"
            onClick={() => navigate('analyze')} whileHover={{ y: -1 }} whileTap={{ scale: 0.98 }}
          >
            Start free
          </motion.button>
        </div>
      </motion.header>

      <AnimatePresence mode="wait">
        {page === 'landing' && <Landing key="landing" theme={theme} onStart={() => navigate('analyze')} onReports={() => navigate('reports')} onLearnMore={scrollToFeatures} onNavigate={navigate} />}
        {page === 'analyze' && <Analyze key="analyze" file={file} setFile={setFile} query={query} setQuery={setQuery} running={running} step={step} error={error} onRun={runAnalysis} onReports={() => navigate('reports')} />}
        {page === 'reports' && <Reports key="reports" reports={reports} onOpen={openReport} onDelete={deleteReport} onNew={() => navigate('analyze')} />}
        {page === 'report' && <ReportPage key="report" report={report || reports.find(item => item.analysis_id === reportId)} saved={reports.some(item => item.analysis_id === reportId)} onSave={async item => { await saveReport(item); setReports(await listReports()) }} onBack={() => navigate('reports')} download={download} />}
        {page === 'privacy' && <LegalPage key="privacy" doc={LEGAL_PRIVACY} onBack={() => navigate('landing')} onNavigate={navigate} />}
        {page === 'terms' && <LegalPage key="terms" doc={LEGAL_TERMS} onBack={() => navigate('landing')} onNavigate={navigate} />}
        {page === 'security' && <LegalPage key="security" doc={LEGAL_SECURITY} onBack={() => navigate('landing')} onNavigate={navigate} />}
      </AnimatePresence>
    </div>
  )
}

/* ----------------------------------------------------- Legal / policy -- */
const LEGAL_UPDATED = 'October 2025'

const LEGAL_PRIVACY = {
  key: 'privacy',
  icon: Lock,
  eyebrow: 'LEGAL',
  title: 'Privacy Policy',
  intro: 'DataSnap is built to be private by default. This policy explains what data is processed when you run an analysis, how long it lives, and the third parties involved.',
  sections: [
    { h: 'Data you provide', p: 'When you run an analysis you upload a dataset file (CSV, XLSX, Parquet, TSV, JSON or JSONL) and a business question. These are sent to our API over an encrypted connection solely to produce your decision brief.' },
    { h: 'How your dataset is used', p: 'Your dataset is profiled and analyzed inside a timed, isolated subprocess. It is processed in memory to compute metrics and generate charts. We do not use your uploaded data to train models, and it is not retained as a durable server-side archive.' },
    { h: 'Saved reports stay in your browser', p: 'Reports are only stored when you explicitly save them, and they are kept locally in your browser using IndexedDB (with a localStorage fallback). They never leave your device unless you export them. Clearing site data or switching browser/device removes them.' },
    { h: 'Third-party AI provider', p: 'To plan and synthesize analyses, relevant context is sent to our AI provider (Google Gemini) with an automatic fallback chain for transient failures. Their processing is governed by their own terms and privacy practices.' },
    { h: 'Rate limiting', p: 'To prevent abuse we enforce an anonymous quota (five analyses per rolling hour). This uses a hashed identifier derived from your IP address and a browser token stored via Redis. We do not build advertising profiles from this data.' },
    { h: 'No accounts', p: 'DataSnap requires no sign-up, so we do not collect names, emails, or passwords for this release.' },
    { h: 'Your choices', p: 'You can clear your saved reports at any time from the Reports page or by clearing your browser site data. You control what you upload and what you choose to save.' }
  ]
}

const LEGAL_TERMS = {
  key: 'terms',
  icon: FileText,
  eyebrow: 'LEGAL',
  title: 'Terms of Service',
  intro: 'By using DataSnap you agree to these terms. They cover acceptable use, the limits of the service, and important disclaimers about the results it produces.',
  sections: [
    { h: 'Acceptable use', p: 'Use DataSnap only with data you have the right to analyze. Do not upload content that is illegal, infringing, or contains others’ personal data without authorization. Do not attempt to disrupt, overload, or reverse-engineer the service.' },
    { h: 'Usage limits', p: 'Anonymous use is capped at five analyses per rolling hour. We may adjust limits or temporarily restrict access to protect availability for everyone.' },
    { h: 'Results are decision support, not advice', p: 'Metrics are computed from your data, but statistical significance and correlation do not establish causation. Reports are intended to support human judgment and remain pending human review. DataSnap does not provide legal, financial, medical, or other professional advice.' },
    { h: 'No warranty', p: 'The service is provided “as is” without warranties of any kind. We do not guarantee uninterrupted availability, or that generated code, metrics, or recommendations are free of error.' },
    { h: 'Limitation of liability', p: 'To the maximum extent permitted by law, DataSnap and its contributors are not liable for any indirect, incidental, or consequential damages arising from use of the service or reliance on its output.' },
    { h: 'Changes', p: 'We may update these terms as the product evolves. Continued use after an update constitutes acceptance of the revised terms.' }
  ]
}

const LEGAL_SECURITY = {
  key: 'security',
  icon: ShieldCheck,
  eyebrow: 'TRUST',
  title: 'Security',
  intro: 'Security and verifiability are core to how DataSnap is designed. This page summarizes the controls that protect your data and keep results trustworthy.',
  sections: [
    { h: 'Isolated execution', p: 'Generated Polars, SciPy and Matplotlib code runs in a timed, scoped subprocess separate from the main application, with automatic self-correction on runtime failures. Note: this is a timed sandbox, not a hardened multi-tenant container boundary.' },
    { h: 'Machine-verified metrics', p: 'Every number in a report is computed from your data and JSON-serialized — never fabricated by the language model. This keeps the evidence in your brief grounded in the actual dataset.' },
    { h: 'Encryption in transit', p: 'Traffic between your browser and the API is served over HTTPS in production. Provider API keys, Redis tokens, and signing secrets live only on the backend and are never exposed to the frontend.' },
    { h: 'Data minimization', p: 'Uploaded datasets are processed in memory to produce your brief and are not kept as a durable server archive. Saved reports live only in your browser.' },
    { h: 'Abuse protection', p: 'Anonymous quotas backed by Redis limit automated abuse, using signed, hashed identity keys rather than raw identifiers.' },
    { h: 'Responsible disclosure', p: 'If you believe you have found a security issue, please contact the maintainers through the GitHub profiles linked in the footer so it can be addressed promptly.' }
  ]
}

const LEGAL_DOCS = [LEGAL_PRIVACY, LEGAL_TERMS, LEGAL_SECURITY]

function LegalPage({ doc, onBack, onNavigate }) {
  const Icon = doc.icon
  return (
    <MMain className="legal-page" variants={pageMotion} initial="initial" animate="animate" exit="exit">
      <motion.div className="legal-nav" variants={rise}>
        <button className="text-button" onClick={onBack}><ArrowLeft size={15} /> Back to home</button>
      </motion.div>

      <motion.header className="legal-head" variants={rise}>
        <span className="legal-head-icon"><Icon size={22} /></span>
        <p className="eyebrow"><span /> {doc.eyebrow}</p>
        <h1>{doc.title}</h1>
        <p className="legal-intro">{doc.intro}</p>
        <small className="legal-updated">Last updated: {LEGAL_UPDATED}</small>
      </motion.header>

      <motion.div className="legal-body" variants={rise}>
        {doc.sections.map((s, i) => (
          <motion.section
            key={s.h}
            className="legal-section"
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.45, ease: easeOut, delay: (i % 4) * 0.05 }}
          >
            <h2><span className="legal-section-num">{String(i + 1).padStart(2, '0')}</span>{s.h}</h2>
            <p>{s.p}</p>
          </motion.section>
        ))}
      </motion.div>

      <motion.div className="legal-footer-nav" variants={rise}>
        <span>Related</span>
        <div>
          {LEGAL_DOCS.filter(d => d.key !== doc.key).map(d => (
            <button key={d.key} onClick={() => onNavigate(d.key)}>{d.title} <ChevronRight size={14} /></button>
          ))}
        </div>
      </motion.div>
    </MMain>
  )
}


/* --------------------------------------------------------------- Pricing -- */
function Pricing({ onStart }) {
  const [yearly, setYearly] = useState(false)
  return (
    <section className="section pricing" id="pricing">
      <motion.div className="section-head center" {...fadeUpView}>
        <p className="eyebrow"><span /> PRICING</p>
        <h2>Start free,<br />scale when ready.</h2>
      </motion.div>

      {/* Billing toggle */}
      <motion.div className="pricing-toggle" initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.4, ease: easeOut }}>
        <span className={!yearly ? 'active' : ''}>Monthly</span>
        <button
          type="button"
          className={`pricing-switch ${yearly ? 'on' : ''}`}
          onClick={() => setYearly(v => !v)}
          role="switch"
          aria-checked={yearly}
          aria-label="Toggle yearly billing"
        >
          <motion.span className="pricing-knob" layout transition={{ type: 'spring', stiffness: 500, damping: 32 }} />
        </button>
        <span className={yearly ? 'active' : ''}>Yearly</span>
        <em className="pricing-save">20% OFF</em>
      </motion.div>

      {/* Plan cards */}
      <motion.div className="pricing-grid" variants={staggerParent} initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.2 }}>
        {PRICING_PLANS.map((plan) => {
          const price = yearly ? plan.yearly : plan.monthly
          return (
            <motion.article
              key={plan.name}
              className={`pricing-card ${plan.popular ? 'popular' : ''}`}
              variants={revealItem}
              whileHover={{ y: -6 }}
              transition={{ type: 'spring', stiffness: 300, damping: 22 }}
            >
              <div className="pricing-card-head">
                <h3>{plan.name}</h3>
                {plan.popular && <span className="pricing-badge">POPULAR</span>}
              </div>

              <div className="pricing-price">
                <AnimatePresence mode="wait" initial={false}>
                  <motion.strong
                    key={price}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.25, ease: easeOut }}
                  >
                    {pkr(price)}
                  </motion.strong>
                </AnimatePresence>
                <small>{price === 0 ? 'forever' : 'user / mo'}</small>
              </div>

              <p className="pricing-blurb">{plan.blurb}</p>

              <button className={plan.popular ? 'pricing-cta primary' : 'pricing-cta'} onClick={onStart}>
                {plan.cta}
              </button>

              <ul className="pricing-features">
                {plan.features.map((f) => (
                  <li key={f}><Check size={15} /> {f}</li>
                ))}
              </ul>
            </motion.article>
          )
        })}
      </motion.div>

      <p className="pricing-note">Prices in PKR. {`Yearly plans are billed annually at the discounted rate.`} The free Starter tier needs no account.</p>
    </section>
  )
}



function Landing({ onStart, onReports, onLearnMore, onNavigate, theme }) {
  return (
    <MMain className="landing" variants={pageMotion} initial="initial" animate="animate" exit="exit">
      {/* ============================ HERO (full section) ============================ */}
      <section className="relative flex min-h-[calc(100svh-60px)] flex-col items-center justify-center px-5 py-10 text-center">
        {/* ---------- animated LightTunnel background (full-bleed) ---------- */}
        <div aria-hidden className="pointer-events-none absolute left-1/2 top-0 bottom-0 -z-10 w-screen -translate-x-1/2 overflow-hidden [mask-image:radial-gradient(ellipse_70%_75%_at_50%_45%,#000_45%,transparent_85%)]">
          <LightTunnel
            className="!absolute !inset-0 h-full w-full"
            cableColor="#7c3aed"
            pulseColor="#8b84ff"
            tunnelColor="#4f46e5"
            tunnelOpacity={0}
            speed={0.05}
            flowDirection="outward"
            pulseSpeed={2}
            pulseLength={0.28}
            pulseBlend={1}
            pulseWidth={1}
            cableCount={22}
            thickness={0.32}
            rimWidth={0.14}
            waviness={0.3}
            sway={0.5}
            size={1.0}
            glow={1.1}
            fadeNear={0.45}
            fadeFar={2}
            brightness={theme === 'light' ? 0.9 : 1.0}
            colorVariance
            grain
            grainIntensity={0.05}
            opacity={theme === 'light' ? 0.55 : 0.9}
            mouseInteraction
            mouseStrength={0.12}
            lightMode={theme === 'light'}
          />
        </div>

        <motion.button
          className="group mb-6 inline-flex max-w-full items-center gap-2 whitespace-nowrap rounded-full border border-hairline-strong bg-panel py-1 pl-1.5 pr-3 text-[11.5px] font-medium text-ink-soft shadow-sm transition-colors hover:border-brand-line sm:text-[12px]"
          onClick={onStart} variants={rise}
        >
          <b className="rounded-full bg-brand-soft px-2.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-brand">New</b>
          Agent workflows are now available
          <ArrowUpRight size={14} className="text-ink-dim transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </motion.button>

        <motion.h1 className="m-0 font-display text-[clamp(32px,5vw,58px)] font-medium leading-[1.0] tracking-[-0.04em] text-ink" variants={rise}>
          <WordReveal text="See what your data" />{' '}
          <em className="text-shimmer bg-[linear-gradient(100deg,var(--color-brand),var(--color-brand-hot),var(--color-brand))] bg-clip-text not-italic text-transparent">hides</em>,
          <br className="hidden sm:block" /> <WordReveal text="before you train." />
        </motion.h1>

        <motion.p className="mt-4 max-w-[42ch] text-[clamp(14px,1.3vw,16px)] leading-relaxed text-ink-soft" variants={rise}>
          An all-in-one agent that profiles, analyzes and verifies
          <br className="hidden sm:block" /> your data into a decision-ready brief.
        </motion.p>

        <motion.div className="mt-6 flex flex-row flex-wrap items-center justify-center gap-2.5 sm:gap-3" variants={rise}>
          <Magnetic className="primary-cta justify-center !px-3.5 !py-2 !text-[12px] sm:!px-5 sm:!py-2.5 sm:!text-[13px]" onClick={onStart}>Start an analysis <ArrowUpRight size={14} /></Magnetic>
          <Magnetic className="ghost-cta justify-center !px-3.5 !py-2 !text-[12px] sm:!px-4 sm:!py-2.5 sm:!text-[13px]" onClick={onLearnMore || onReports} strength={0.25}>Learn more <ChevronRight size={14} /></Magnetic>
        </motion.div>

        <motion.div className="mt-7 flex flex-wrap items-center justify-center gap-x-7 gap-y-3 text-xs text-ink-dim" variants={rise}>
          <span className="flex items-center gap-2"><ShieldCheck size={15} className="text-brand" /> Isolated execution</span>
          <span className="flex items-center gap-2"><Check size={15} className="text-brand" /> Machine-verified metrics</span>
          <span className="flex items-center gap-2"><Lock size={15} className="text-brand" /> No account required</span>
        </motion.div>
      </section>

      {/* ====================== LIVE PREVIEW (separate full section) ====================== */}
      <section id="preview" className="relative overflow-x-clip px-5 pt-14 pb-16 sm:pt-16 sm:pb-18">
        <motion.div
          className="mx-auto mb-7 max-w-[640px] text-center"
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.4 }} transition={{ duration: 0.5, ease: easeOut }}
        >
          <p className="eyebrow justify-center"><span /> LIVE PREVIEW</p>
          <h2 className="mt-4 font-display text-[clamp(26px,3.2vw,40px)] font-medium leading-[1.08] tracking-[-0.035em] text-ink">A decision brief, rendered from your rows.</h2>
          <p className="mx-auto mt-3 max-w-[480px] text-[15.5px] leading-relaxed text-ink-soft">One clear view — the signal your data was hiding, computed and verified.</p>
        </motion.div>

        <motion.div
          className="relative mx-auto w-full max-w-[760px]"
          initial={{ opacity: 0, y: 32 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.7, ease: easeOut }}
        >
          {/* soft ambient glow */}
          <div aria-hidden className="pointer-events-none absolute left-1/2 top-8 -z-10 h-[320px] w-[90vw] max-w-[520px] -translate-x-1/2 rounded-full bg-[radial-gradient(50%_50%_at_50%_50%,rgba(79,70,229,0.12),transparent_70%)] blur-2xl" />

          {/* single elegant chart card */}
          <TiltCard className="chart-tilt" max={6} scale={1.015}>
            <figure className="m-0 overflow-hidden rounded-[20px] border border-hairline bg-panel shadow-[0_8px_16px_rgba(16,24,40,0.05),0_36px_80px_-28px_rgba(16,24,40,0.26)]">
              {/* header */}
              <figcaption className="flex items-center justify-between gap-3 border-b border-hairline px-6 py-5 sm:px-8">
                <div>
                  <span className="font-mono text-[10px] tracking-[0.14em] text-ink-dim">TOTAL REVENUE BY CATEGORY</span>
                  <strong className="mt-1.5 block font-display text-[22px] font-extrabold tracking-[-0.03em] text-ink">$14,635.64</strong>
                </div>
                <span className="flex items-center gap-1.5 rounded-full bg-ok-soft px-3 py-1.5 font-mono text-[9px] tracking-[0.12em] text-ok"><Check size={11} /> VERIFIED</span>
              </figcaption>

              {/* chart */}
              <div className="px-6 pt-8 pb-6 sm:px-8">
                <div className="flex items-end gap-3 sm:gap-5" style={{ height: 200 }}>
                  {PREVIEW_CATEGORIES.map((c, i) => {
                    const pct = Math.round((c.value / PREVIEW_CATEGORIES[0].value) * 100)
                    return (
                      <div key={c.label} className="flex flex-1 flex-col items-center justify-end gap-2.5" style={{ height: '100%' }}>
                        <span className="font-mono text-[10px] font-medium text-ink-dim">${(c.value / 1000).toFixed(1)}k</span>
                        <motion.span
                          className="w-full rounded-t-[6px]"
                          style={{ height: `${pct}%`, background: i === 0 ? 'linear-gradient(to top, var(--color-brand), var(--color-brand-hot))' : 'var(--color-brand-line)', transformOrigin: 'bottom' }}
                          initial={{ scaleY: 0 }} whileInView={{ scaleY: 1 }} viewport={{ once: true }}
                          transition={{ delay: 0.3 + i * 0.08, duration: 0.6, ease: easeOut }}
                        />
                      </div>
                    )
                  })}
                </div>
                <div className="mt-3 flex gap-3 border-t border-hairline pt-3 sm:gap-5">
                  {PREVIEW_CATEGORIES.map((c) => (
                    <span key={c.label} className="flex-1 truncate text-center text-[11px] text-ink-dim">{c.label.split(' ')[0]}</span>
                  ))}
                </div>
              </div>
            </figure>
          </TiltCard>

          {/* minimal verified-metric footer */}
          <motion.div
            className="mt-5 grid grid-cols-3 overflow-hidden rounded-[16px] border border-hairline bg-panel shadow-sm"
            initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.5, duration: 0.5, ease: easeOut }}
          >
            {[
              ['Avg rating', '4.33'],
              ['Return rate', '20.0%'],
              ['Rating correlation', '+0.68']
            ].map(([k, v], i) => (
              <div key={k} className={`px-2.5 py-3 sm:px-5 sm:py-4 text-center ${i < 2 ? 'border-r border-hairline' : ''}`}>
                <strong className="block font-display text-[15px] sm:text-[18px] font-extrabold tracking-[-0.02em] text-ink">{v}</strong>
                <small className="mt-1 block truncate text-[10px] sm:text-[11px] text-ink-dim">{k}</small>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      <motion.section className="marquee" {...fadeUpView}>
        <div className="marquee-track">
          {[...MARQUEE, ...MARQUEE].map((item, i) => (
            <span className="marquee-item" key={i}><item.icon size={15} /> {item.label}<i className="marquee-dot" /></span>
          ))}
        </div>
      </motion.section>

      <section className="section features" id="features">
        <motion.div className="section-head center" {...fadeUpView}>
          <p className="eyebrow"><span /> WHAT'S INSIDE</p>
          <h2>Everything you need to turn a dataset into a decision.</h2>
          <p className="section-lead">DataSnap handles the full path — profiling, planning, execution and synthesis — so you can focus on the call you need to make.</p>
        </motion.div>
        <motion.div className="feature-grid" variants={staggerParent} initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.2 }}>
          {FEATURES.map((f) => (
            <motion.article className="feature-card group" key={f.title} variants={revealItem} whileHover={{ y: -6 }} transition={{ type: 'spring', stiffness: 300, damping: 22 }}>
              <motion.span className="feature-icon" whileHover={{ rotate: -8, scale: 1.08 }} transition={{ type: 'spring', stiffness: 400, damping: 12 }}><f.icon size={20} /></motion.span>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </motion.article>
          ))}
        </motion.div>
      </section>

      <section className="section how">
        <motion.div className="section-head center" {...fadeUpView}>
          <p className="eyebrow"><span /> HOW IT WORKS</p>
          <h2>From raw file to decision brief in four steps.</h2>
          <p className="section-lead">A guided, transparent flow. You stay in control at every stage while the agent does the heavy lifting.</p>
        </motion.div>
        <motion.div className="how-steps" variants={staggerParent} initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.2 }}>
          {HOW.map((s, i) => (
            <motion.div className="how-step group" key={s.title} variants={revealItem}>
              <div className="how-step-top">
                <motion.span className="how-icon" whileHover={{ rotate: -8, scale: 1.08 }} transition={{ type: 'spring', stiffness: 400, damping: 12 }}><s.icon size={19} /></motion.span>
                <span className="how-kicker">{String(i + 1).padStart(2, '0')}</span>
              </div>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <motion.section className="stats-band" variants={staggerParent} initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.3 }}>
        {STATS.map((s) => (
          <motion.div className="stat" key={s.label} variants={revealItem}>
            <CountUp value={s.value} /><span>{s.label}</span>
          </motion.div>
        ))}
      </motion.section>

      <Pricing onStart={onStart} />

      <section className="section">
        <motion.div className="cta-band" {...fadeUpView}>
          <div className="cta-glow" aria-hidden />
          <p className="eyebrow"><span /> READY WHEN YOU ARE</p>
          <h2>Ask your data a better question.</h2>
          <p>Upload a dataset and get a decision-ready brief in minutes. No account, no setup, private by default.</p>
          <div className="hero-actions">
            <motion.button className="primary-cta" onClick={onStart} whileTap={{ scale: 0.98 }}>Start an analysis <ArrowUpRight size={17} /></motion.button>
            <motion.button className="ghost-cta" onClick={onReports} whileTap={{ scale: 0.98 }}>View saved reports <ChevronRight size={15} /></motion.button>
          </div>
        </motion.div>
      </section>

      <motion.footer className="site-footer" variants={staggerParent} initial="initial" whileInView="whileInView" viewport={{ once: true, amount: 0.2 }}>
        <motion.div className="footer-brand" variants={revealItem}>
          <Logo />
          <p>Decision intelligence that turns a question and a dataset into verified, decision-ready evidence.</p>
        </motion.div>
        <motion.div className="footer-links" variants={revealItem}>
          <div><h4>Product</h4><button onClick={onStart}>Start analysis</button><button onClick={onReports}>Saved reports</button></div>
          <div><h4>Trust</h4><button onClick={() => onNavigate('security')}>Isolated execution</button><button onClick={() => onNavigate('privacy')}>Private by default</button><button onClick={() => onNavigate('security')}>Verified metrics</button></div>
          <div><h4>Legal</h4><button onClick={() => onNavigate('privacy')}>Privacy Policy</button><button onClick={() => onNavigate('terms')}>Terms of Service</button><button onClick={() => onNavigate('security')}>Security</button></div>
          <div><h4>Formats</h4><span className="lnk">CSV · TSV · JSON</span><span className="lnk">XLSX · Parquet</span><span className="lnk">JSONL</span></div>
        </motion.div>
        <div className="footer-base">
          <span>© {new Date().getFullYear()} DataSnap</span>
          <span className="footer-credit">
            UI/UX by{' '}
            <a href="https://talhairfandev.me" target="_blank" rel="noopener noreferrer">Talha Irfan</a>
            {' · Cloud Engineer '}
            <a href="https://github.com/abdulrdeveloper" target="_blank" rel="noopener noreferrer">@abdulrdeveloper</a>
            {' · Backend Engineer '}
            <a href="https://github.com/bilalhaider-ux" target="_blank" rel="noopener noreferrer">Bilal Haider</a>
          </span>
        </div>
      </motion.footer>
    </MMain>
  )
}

const SAMPLE_SALES_CSV = `transaction_id,date,customer_id,region,product_category,units_sold,unit_price,discount_pct,total_revenue,shipping_cost,payment_method,customer_rating,returned
TXN-1001,2024-01-05,CUST-201,North America,Electronics,3,299.99,0.05,854.97,14.50,Credit Card,4.8,No
TXN-1002,2024-01-07,CUST-202,Europe,Home & Kitchen,1,120.00,0.00,120.00,8.20,PayPal,4.2,No
TXN-1003,2024-01-08,CUST-203,Asia-Pacific,Fashion,5,45.00,0.15,191.25,5.00,Credit Card,3.9,Yes
TXN-1004,2024-01-10,CUST-204,North America,Beauty,2,35.50,0.10,63.90,4.50,Debit Card,4.9,No
TXN-1005,2024-01-12,CUST-205,Europe,Electronics,2,549.00,0.20,878.40,19.00,Credit Card,4.5,No
TXN-1006,2024-01-15,CUST-206,Latin America,Home & Kitchen,4,85.00,0.05,323.00,12.00,PayPal,3.1,Yes
TXN-1007,2024-01-18,CUST-207,North America,Sports,1,150.00,0.00,150.00,9.50,Credit Card,4.7,No
TXN-1008,2024-01-20,CUST-208,Asia-Pacific,Electronics,6,199.99,0.25,899.96,22.00,Credit Card,4.6,No
TXN-1009,2024-01-22,CUST-209,Europe,Sports,2,75.00,0.10,135.00,7.00,Credit Card,4.0,No
TXN-1010,2024-01-25,CUST-210,North America,Fashion,8,25.00,0.30,140.00,6.50,Debit Card,3.5,Yes
TXN-1011,2024-02-01,CUST-211,North America,Electronics,4,349.99,0.10,1259.96,15.00,Credit Card,4.9,No
TXN-1012,2024-02-03,CUST-212,Asia-Pacific,Home & Kitchen,3,110.00,0.00,330.00,11.50,PayPal,4.1,No
TXN-1013,2024-02-05,CUST-213,Europe,Fashion,2,95.00,0.10,171.00,6.00,Credit Card,4.4,No
TXN-1014,2024-02-08,CUST-214,Latin America,Beauty,5,42.00,0.20,168.00,8.00,Debit Card,3.8,No
TXN-1015,2024-02-12,CUST-215,North America,Electronics,1,1200.00,0.05,1140.00,25.00,Credit Card,5.0,No
TXN-1016,2024-02-14,CUST-216,Europe,Sports,3,130.00,0.15,331.50,13.00,PayPal,4.3,No
TXN-1017,2024-02-17,CUST-217,Asia-Pacific,Beauty,4,50.00,0.00,200.00,7.50,Credit Card,4.7,No
TXN-1018,2024-02-20,CUST-218,North America,Home & Kitchen,2,220.00,0.25,330.00,14.00,Credit Card,3.6,Yes
TXN-1019,2024-02-24,CUST-219,Europe,Electronics,3,450.00,0.10,1215.00,18.00,Credit Card,4.6,No
TXN-1020,2024-02-28,CUST-220,Latin America,Fashion,6,38.00,0.00,228.00,9.00,PayPal,4.0,No
TXN-1021,2024-03-02,CUST-221,North America,Sports,4,89.00,0.10,320.40,11.00,Credit Card,4.5,No
TXN-1022,2024-03-05,CUST-222,Asia-Pacific,Electronics,2,699.00,0.15,1188.30,20.00,Credit Card,4.7,No
TXN-1023,2024-03-08,CUST-223,Europe,Beauty,3,65.00,0.05,185.25,5.50,Debit Card,4.8,No
TXN-1024,2024-03-12,CUST-224,North America,Home & Kitchen,5,95.00,0.20,380.00,16.00,PayPal,3.4,Yes
TXN-1025,2024-03-15,CUST-225,Latin America,Sports,2,110.00,0.00,220.00,10.00,Credit Card,4.2,No
TXN-1026,2024-03-18,CUST-226,Europe,Electronics,1,850.00,0.10,765.00,17.00,Credit Card,4.8,No
TXN-1027,2024-03-20,CUST-227,Asia-Pacific,Fashion,7,55.00,0.25,288.75,8.50,Credit Card,3.7,Yes
TXN-1028,2024-03-22,CUST-228,North America,Beauty,4,70.00,0.10,252.00,6.00,Debit Card,4.9,No
TXN-1029,2024-03-25,CUST-229,Europe,Home & Kitchen,2,180.00,0.15,306.00,12.50,PayPal,4.3,No
TXN-1030,2024-03-29,CUST-230,North America,Electronics,5,400.00,0.20,1600.00,24.00,Credit Card,4.9,No`

const PIPELINE_STAGES = [
  { id: 'profile', title: 'Dataset Profiling', detail: 'Schema validation, null checks & Polars type mapping' },
  { id: 'plan', title: 'Analytical Planning', detail: 'Statistical hypothesis formulation & method selection' },
  { id: 'code', title: 'Code Generation', detail: 'Vectorized Polars & SciPy numerical computation script' },
  { id: 'execute', title: 'Sandboxed Execution', detail: 'Isolated subprocess execution, plot generation & AST validation' },
  { id: 'synthesize', title: 'Evidence Synthesis', detail: 'Machine-verified metrics grounding & executive brief' }
]

const QUICK_PROMPTS = [
  { label: 'Category revenue & return risk', text: 'Analyze revenue by product category and identify return risks' },
  { label: 'Rating vs revenue correlation', text: 'Compute Pearson correlation between customer ratings and total order revenue' },
  { label: 'Discount impact on returns', text: 'Evaluate whether higher discount percentages correlate with higher return rates' }
]

function Analyze({ file, setFile, query, setQuery, running, step, error, onRun, onReports }) {
  const [fileMeta, setFileMeta] = useState(null)
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => {
    if (!file) {
      setFileMeta(null)
      return
    }
    const isText = file.name.endsWith('.csv') || file.name.endsWith('.tsv') || file.name.endsWith('.txt') || file.type.includes('csv') || file.type.includes('text')
    if (isText) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target.result || ''
        const lines = text.split(/\r?\n/).filter(line => line.trim().length > 0)
        if (lines.length > 0) {
          const delimiter = file.name.endsWith('.tsv') ? '\t' : ','
          const headers = lines[0].split(delimiter).map(h => h.trim().replace(/^["']|["']$/g, ''))
          setFileMeta({
            headers,
            rowCount: lines.length - 1,
            format: file.name.endsWith('.tsv') ? 'TSV' : 'CSV'
          })
        }
      }
      reader.readAsText(file.slice(0, 65536))
    } else {
      const ext = file.name.split('.').pop()?.toUpperCase() || 'DATA'
      setFileMeta({ headers: [], rowCount: null, format: ext })
    }
  }, [file])

  function handleChooseFile(e) {
    const f = e.target.files?.[0]
    if (f) setFile(f)
  }

  function handleLoadSample() {
    const blob = new Blob([SAMPLE_SALES_CSV], { type: 'text/csv' })
    const sampleFile = new File([blob], 'sample_sales_data.csv', { type: 'text/csv' })
    setFile(sampleFile)
    setQuery('Analyze revenue by product category and identify return risks')
  }

  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && !running) {
      e.preventDefault()
      onRun()
    }
  }

  return (
    <MMain className="studio-workspace" variants={pageMotion} initial="initial" animate="animate" exit="exit">
      {/* Studio Header */}
      <motion.div className="studio-header" variants={rise}>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-dim">Workspace</span>
            <span className="text-ink-dim">/</span>
            <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-brand">Analysis Studio</span>
          </div>
          <h1 className="mt-2 font-display text-[clamp(26px,3.2vw,36px)] font-medium tracking-[-0.03em] text-ink">
            Formulate hypothesis & dataset
          </h1>
          <p className="mt-1 text-[14.5px] text-ink-soft">
            Upload raw rows, state your analytical objective, and execute inside an isolated Polars & SciPy runtime.
          </p>
        </div>
        <button className="studio-reports-btn" onClick={onReports}>
          <FileText size={15} /> Saved Reports <ChevronRight size={14} />
        </button>
      </motion.div>

      {/* 2-column Studio Grid */}
      <div className="studio-grid">
        {/* Left Column: Staging + Query Input */}
        <div className="studio-main-col">
          {/* Section 1: Dataset Staging */}
          <MSection className="studio-card" variants={rise}>
            <div className="studio-card-head">
              <div className="flex items-center gap-2.5">
                <span className="studio-card-icon"><Database size={16} /></span>
                <div>
                  <strong className="block text-[14.5px] font-semibold text-ink">Dataset Staging</strong>
                  <span className="text-[12px] text-ink-dim">Ephemeral local file input for isolated execution</span>
                </div>
              </div>
              <div className="hidden font-mono text-[10.5px] tracking-wider text-ink-dim sm:flex sm:items-center sm:gap-1.5">
                <span className="rounded bg-panel-2 px-1.5 py-0.5 border border-hairline">CSV</span>
                <span className="rounded bg-panel-2 px-1.5 py-0.5 border border-hairline">PARQUET</span>
                <span className="rounded bg-panel-2 px-1.5 py-0.5 border border-hairline">XLSX</span>
                <span className="rounded bg-panel-2 px-1.5 py-0.5 border border-hairline">JSON</span>
              </div>
            </div>

            {/* File Staging State */}
            {file ? (
              <motion.div className="staged-file-card" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
                <div className="staged-file-row flex items-start justify-between gap-4">
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <div className="staged-file-badge">
                      <Table2 size={20} className="text-brand" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex min-w-0 items-center gap-2">
                        <strong className="min-w-0 flex-1 truncate text-[14px] font-semibold text-ink">{file.name}</strong>
                        <span className="shrink-0 rounded bg-brand-soft px-1.5 py-0.5 font-mono text-[10px] font-medium text-brand">
                          {fileMeta?.format || 'DATA'}
                        </span>
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-x-3 text-[12px] text-ink-dim">
                        <span>{(file.size / 1024).toFixed(1)} KB</span>
                        {fileMeta?.rowCount != null && <span>· {fileMeta.rowCount} records</span>}
                        {fileMeta?.headers?.length > 0 && <span>· {fileMeta.headers.length} columns detected</span>}
                      </div>
                    </div>
                  </div>

                  <div className="staged-file-actions flex shrink-0 items-center gap-2">
                    <label className="staged-action-btn">
                      Replace
                      <input type="file" accept=".csv,.xlsx,.parquet,.tsv,.json,.jsonl" onChange={handleChooseFile} />
                    </label>
                    <button className="staged-remove-btn" onClick={() => setFile(null)} aria-label="Remove dataset">
                      <X size={15} />
                    </button>
                  </div>
                </div>

                {/* Detected Schema Tags */}
                {fileMeta?.headers && fileMeta.headers.length > 0 && (
                  <div className="mt-3.5 border-t border-hairline pt-3">
                    <span className="block font-mono text-[10.5px] uppercase tracking-wider text-ink-dim">Detected Columns:</span>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {fileMeta.headers.slice(0, 10).map((h) => (
                        <span key={h} className="rounded border border-hairline bg-panel-2 px-2 py-0.5 font-mono text-[11px] text-ink-soft">
                          {h}
                        </span>
                      ))}
                      {fileMeta.headers.length > 10 && (
                        <span className="rounded border border-hairline bg-panel-2 px-2 py-0.5 font-mono text-[11px] text-ink-dim">
                          +{fileMeta.headers.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </motion.div>
            ) : (
              <div
                className={`studio-dropzone ${isDragging ? 'dragging' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files?.[0]; if (f) setFile(f) }}
              >
                <div className="flex flex-col items-center text-center">
                  <div className="studio-dropzone-icon">
                    <Table2 size={24} />
                  </div>
                  <strong className="mt-3 block text-[14.5px] font-semibold text-ink">
                    Drag and drop your dataset file
                  </strong>
                  <p className="mt-1 text-[12.5px] text-ink-dim">
                    Supports CSV, TSV, Parquet, XLSX, JSON or JSONL up to 100MB
                  </p>
                  <div className="mt-4 flex flex-wrap items-center justify-center gap-2.5">
                    <label className="studio-upload-btn">
                      Choose local file
                      <input type="file" accept=".csv,.xlsx,.parquet,.tsv,.json,.jsonl" onChange={handleChooseFile} />
                    </label>
                    <button type="button" className="studio-sample-btn" onClick={handleLoadSample}>
                      Load sample dataset (Retail 30 rows)
                    </button>
                  </div>
                </div>
              </div>
            )}
          </MSection>

          {/* Section 2: Analytical Objective */}
          <MSection className="studio-card" variants={rise}>
            <div className="studio-card-head">
              <div className="flex items-center gap-2.5">
                <span className="studio-card-icon"><Terminal size={16} /></span>
                <div>
                  <strong className="block text-[14.5px] font-semibold text-ink">Analytical Objective</strong>
                  <span className="text-[12px] text-ink-dim">State the decision question or hypothesis to test</span>
                </div>
              </div>
              <span className="font-mono text-[11px] text-ink-dim">{query.length} / 500</span>
            </div>

            {/* Quick prompt suggestions */}
            <div className="prompt-suggestions">
              <span className="text-[11.5px] font-medium text-ink-dim">Suggested hypotheses:</span>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {QUICK_PROMPTS.map((p) => (
                  <button
                    key={p.label}
                    type="button"
                    className="prompt-chip"
                    onClick={() => setQuery(p.text)}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Query Textarea */}
            <div className="relative mt-3">
              <textarea
                className="studio-query-textarea"
                rows={4}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g. Analyze revenue by product category, compare return rates, and test if customer rating correlates with sales volume."
                maxLength={500}
                disabled={running}
              />
            </div>

            {/* Execution Control Bar */}
            <div className="studio-control-bar">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[12px] text-ink-dim">
                <span className="flex items-center gap-1.5 font-mono text-[11px]">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Python 3.11 · Polars
                </span>
                <span className="hidden font-mono text-[11px] sm:inline">SciPy Stats</span>
                <span className="hidden font-mono text-[11px] sm:inline">Gemini 2.5 Flash</span>
              </div>

              <motion.button
                className="studio-run-btn"
                onClick={onRun}
                disabled={running}
                whileHover={!running ? { y: -1 } : {}}
                whileTap={!running ? { scale: 0.98 } : {}}
              >
                {running ? (
                  <>
                    <LoaderCircle className="spin" size={15} />
                    <span>Executing pipeline…</span>
                  </>
                ) : (
                  <>
                    <Play size={14} fill="currentColor" />
                    <span>Run Analysis</span>
                    <kbd className="hidden sm:inline-block">⌘↵</kbd>
                  </>
                )}
              </motion.button>
            </div>

            {/* Error Line */}
            <AnimatePresence>
              {error && (
                <motion.div className="studio-error-banner" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                  <X size={15} className="mt-0.5 flex-none text-danger" />
                  <div className="flex-1">
                    <strong className="block text-[13px] font-semibold text-danger">Analysis Execution Failed</strong>
                    <p className="mt-0.5 text-[12.5px] text-ink-soft">{error}</p>
                    <button className="mt-2 font-mono text-[11.5px] font-medium text-brand hover:underline" onClick={onRun}>
                      Retry execution →
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </MSection>
        </div>

        {/* Right Column: Telemetry & Safety Inspector */}
        <div className="studio-side-col">
          {/* Pipeline Telemetry Card */}
          <motion.aside className="studio-card" variants={rise}>
            <div className="studio-card-head">
              <div>
                <strong className="block text-[14.5px] font-semibold text-ink">Execution Pipeline</strong>
                <span className="text-[12px] text-ink-dim">Real-time analytical workflow stages</span>
              </div>
              <span className={`studio-status-pill ${running ? 'live' : 'idle'}`}>
                {running ? `STAGE ${step + 1} OF 5` : 'IDLE'}
              </span>
            </div>

            {/* Cinematic progress bar */}
            <div className="studio-progress-track">
              <motion.div
                className="studio-progress-fill"
                initial={false}
                animate={{ width: running ? `${((step + 1) / PIPELINE_STAGES.length) * 100}%` : '0%' }}
                transition={{ type: 'spring', stiffness: 120, damping: 20 }}
              />
            </div>

            {/* Stage Progress List */}
            <div className="studio-pipeline-list">
              {PIPELINE_STAGES.map((s, index) => {
                const isDone = step > index
                const isCurrent = running && step === index
                return (
                  <motion.div
                    key={s.id}
                    layout
                    className={`studio-stage-row ${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}`}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.07, duration: 0.4, ease: easeOut }}
                  >
                    <span className="studio-stage-badge">
                      <AnimatePresence mode="wait" initial={false}>
                        {isDone ? (
                          <motion.span key="done" initial={{ scale: 0, rotate: -90 }} animate={{ scale: 1, rotate: 0 }} exit={{ scale: 0 }} transition={{ type: 'spring', stiffness: 400, damping: 15 }} style={{ display: 'grid' }}>
                            <Check size={12} className="text-ok" />
                          </motion.span>
                        ) : isCurrent ? (
                          <motion.span key="run" initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0 }} style={{ display: 'grid' }}>
                            <LoaderCircle size={12} className="spin text-brand" />
                          </motion.span>
                        ) : (
                          <motion.span key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="font-mono text-[10px] text-ink-dim">0{index + 1}</motion.span>
                        )}
                      </AnimatePresence>
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <strong className="text-[13px] font-medium text-ink">{s.title}</strong>
                        <AnimatePresence mode="wait">
                          {isCurrent && <motion.span key="r" initial={{ opacity: 0, x: 6 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="font-mono text-[9px] uppercase tracking-wider text-brand">Running</motion.span>}
                          {isDone && <motion.span key="p" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="font-mono text-[9px] uppercase tracking-wider text-ok">Passed</motion.span>}
                        </AnimatePresence>
                      </div>
                      <p className="truncate text-[11px] text-ink-dim">{s.detail}</p>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </motion.aside>

          {/* Verification & Safety Guarantees */}
          <motion.aside className="studio-card" variants={rise}>
            <div className="studio-card-head">
              <div>
                <strong className="block text-[14.5px] font-semibold text-ink">Execution Guarantees</strong>
                <span className="text-[12px] text-ink-dim">Architecture standards enforced on every run</span>
              </div>
            </div>

            <div className="studio-guarantees">
              <div className="flex gap-3">
                <ShieldCheck size={16} className="mt-0.5 flex-none text-brand" />
                <div>
                  <strong className="block text-[12.5px] font-medium text-ink">Machine-Verified Numbers</strong>
                  <p className="mt-0.5 text-[11.5px] leading-relaxed text-ink-dim">Every statistic is computed in Python and verified against source arrays — never generated by LLM imagination.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Lock size={16} className="mt-0.5 flex-none text-brand" />
                <div>
                  <strong className="block text-[12.5px] font-medium text-ink">Isolated Ephemeral Process</strong>
                  <p className="mt-0.5 text-[11.5px] leading-relaxed text-ink-dim">Scripts execute in a scoped sandbox subprocess. Uploaded data is not retained for training.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Workflow size={16} className="mt-0.5 flex-none text-brand" />
                <div>
                  <strong className="block text-[12.5px] font-medium text-ink">Automated Recovery Loops</strong>
                  <p className="mt-0.5 text-[11.5px] leading-relaxed text-ink-dim">Code syntax errors or runtime exceptions trigger automatic repair nodes before returning results.</p>
                </div>
              </div>
            </div>
          </motion.aside>
        </div>
      </div>
    </MMain>
  )
}

function Reports({ reports, onOpen, onDelete, onNew }) {
  return (
    <MMain className="reports-page" variants={pageMotion} initial="initial" animate="animate" exit="exit">
      <motion.div className="page-heading" variants={rise}>
        <div>
          <p className="eyebrow"><span /> REPORT LIBRARY</p>
          <h1>Your saved intelligence.</h1>
          <p>Only reports you explicitly saved live here, in this browser.</p>
        </div>
        <motion.button className="primary-cta small" onClick={onNew} whileHover={{ scale: 1.03, y: -2 }} whileTap={{ scale: 0.97 }}><Plus size={16} /> New analysis</motion.button>
      </motion.div>
      {reports.length === 0 ? (
        <motion.div className="empty-library" variants={rise}>
          <FileText size={25} />
          <h2>No saved reports yet</h2>
          <p>Run an analysis, then save the result when you are ready to keep it.</p>
          <button className="text-button" onClick={onNew}>Start your first analysis <ArrowUpRight size={15} /></button>
        </motion.div>
      ) : (
        <motion.div className="report-list" variants={rise}>
          {reports.map((item, index) => (
            <motion.article className="report-row" key={item.analysis_id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}>
              <button onClick={() => onOpen(item)}>
                <span className="report-mark"><BarChart3 size={18} /></span>
                <span><strong>{item.answers_to_query?.slice(0, 85) || 'Decision brief'}</strong><small>{dateLabel(item.saved_at)} · {item.grounding?.data_quality?.row_count || 0} rows analyzed</small></span>
              </button>
              <span className="report-status"><Check size={13} /> Saved</span>
              <button className="delete-button" onClick={() => onDelete(item.analysis_id)} aria-label="Delete report"><X size={16} /></button>
            </motion.article>
          ))}
        </motion.div>
      )}
    </MMain>
  )
}

function ReportPage({ report, saved, onSave, onBack, download }) {
  const [tab, setTab] = useState('overview')
  if (!report) return (
    <MMain className="reports-page" variants={pageMotion} initial="initial" animate="animate" exit="exit">
      <button className="text-button" onClick={onBack}><ArrowLeft size={15} /> Back to reports</button>
      <div className="empty-library"><FileText size={25} /><h2>Report not found</h2><p>This report is not available in this browser.</p></div>
    </MMain>
  )
  const metrics = report.metrics || {}
  const metricRows = Object.entries(metrics)
  const tabs = [['overview', 'Overview'], ['insights', 'Insights & actions'], ['visuals', 'Visual evidence'], ['metrics', 'Verified metrics'], ['details', 'Run details']]
  const tabFade = { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: easeOut } }, exit: { opacity: 0, y: -8, transition: { duration: 0.2 } } }
  return (
    <MMain className="report-page" variants={pageMotion} initial="initial" animate="animate" exit="exit">
      <motion.div className="report-page-nav" variants={rise}>
        <button className="text-button" onClick={onBack}><ArrowLeft size={15} /> All reports</button>
        <div className="report-actions">
          <span className="verified"><Check size={13} /> Verified metrics</span>
          <motion.button className="save-button" onClick={() => onSave(report)} disabled={saved} whileHover={!saved ? { scale: 1.04 } : {}} whileTap={!saved ? { scale: 0.96 } : {}}><Save size={15} /> {saved ? 'Saved locally' : 'Save report'}</motion.button>
          <button className="outline-button" onClick={() => download('datasnap-report.md', report.markdown_report || '', 'text/markdown')}><FileText size={15} /> Markdown</button>
          <button className="outline-button" onClick={() => download('datasnap-report.html', report.html_report || '', 'text/html')}><Download size={15} /> HTML</button>
        </div>
      </motion.div>
      <motion.div className="report-paper" variants={rise}>
        <div className="report-paper-head">
          <div>
            <p className="eyebrow"><span /> ANALYTICAL DECISION REPORT</p>
            <h1>Decision brief</h1>
            <p>Evidence prepared from {report.grounding?.data_quality?.row_count || 0} rows of uploaded data.</p>
          </div>
          <span className="report-stamp"><ShieldCheck size={16} /> Machine verified</span>
        </div>
        <div className="report-tabs">{tabs.map(([id, label]) => <button className={tab === id ? 'active' : ''} onClick={() => setTab(id)} key={id}>{label}</button>)}</div>
        <AnimatePresence mode="wait">
          <motion.div className="report-content" key={tab} variants={tabFade} initial="initial" animate="animate" exit="exit">
            {tab === 'overview' && <><div className="report-lead"><span>EXECUTIVE SUMMARY</span><p>{report.executive_summary}</p></div><div className="report-answer"><span>ANSWER TO YOUR QUESTION</span><p>{report.answers_to_query}</p></div><div className="overview-cards">
              {[['ROWS ANALYZED', report.grounding?.data_quality?.row_count || '—'], ['METRICS VERIFIED', report.grounding?.metric_count || metricRows.length], ['VISUALS GENERATED', report.charts?.length || 0]].map(([label, value], i) => (
                <motion.div key={label} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.08 }}><small>{label}</small><strong>{value}</strong></motion.div>
              ))}
            </div></>}
            {tab === 'insights' && <div className="report-columns full"><section><p className="section-label">STATISTICAL INSIGHTS</p><h2>What the data says</h2><ul>{(report.statistical_insights || []).map(item => <li key={item}>{item}</li>)}</ul></section><section><p className="section-label">RECOMMENDED ACTIONS</p><h2>What to do next</h2><ul>{(report.recommended_actions || []).map(item => <li key={item}>{item}</li>)}</ul></section></div>}
            {tab === 'visuals' && <div className="visual-report-grid">{(report.charts || []).map((chart, index) => <motion.figure key={`${index}-${chart.slice(0, 20)}`} initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: index * 0.08 }}><img src={`data:image/png;base64,${chart}`} alt={`Analysis visualization ${index + 1}`} /><figcaption>Visualization {String(index + 1).padStart(2, '0')}</figcaption></motion.figure>)}</div>}
            {tab === 'metrics' && <div className="metrics-reader">{metricRows.map(([key, value]) => <section key={key}><div className="metric-heading"><span>{key.replaceAll('_', ' ')}</span><em>verified</em></div>{Array.isArray(value) && value.length && typeof value[0] === 'object' ? <div className="metric-table-wrap"><table><thead><tr>{Object.keys(value[0]).map(column => <th key={column}>{column.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{value.map((row, index) => <tr key={index}>{Object.values(row).map((cell, cellIndex) => <td key={cellIndex}>{typeof cell === 'number' ? Number(cell.toFixed(4)) : String(cell)}</td>)}</tr>)}</tbody></table></div> : <strong className="metric-number">{typeof value === 'number' ? Number(value.toFixed(6)) : JSON.stringify(value)}</strong>}</section>)}</div>}
            {tab === 'details' && <div className="details-reader"><div><small>ANALYSIS ID</small><code>{report.analysis_id}</code></div><div><small>PROVIDER</small><strong>{report.grounding?.provenance?.provider || 'Gemini'}</strong></div><div><small>MODEL</small><strong>{report.grounding?.provenance?.model || 'Primary with automatic fallback'}</strong></div><div><small>DATA QUALITY</small><strong>{report.grounding?.data_quality?.status || 'Reviewed'}</strong></div><div><small>DECISION STATUS</small><strong>Pending human review</strong></div></div>}
          </motion.div>
        </AnimatePresence>
      </motion.div>
    </MMain>
  )
}
