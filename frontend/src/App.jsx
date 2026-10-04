import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, ArrowLeft, ArrowUpRight, BarChart3, BrainCircuit, Check, ChevronRight, Database, Download, FileSearch, FileText, Gauge, LineChart, LoaderCircle, Lock, Play, Plus, Save, ShieldCheck, Sparkles, Table2, Terminal, UploadCloud, Workflow, X, Zap } from 'lucide-react'
import { listReports, removeReport, saveReport } from './lib/storage'

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

const MDiv = motion.div
const MSection = motion.section
const MMain = motion.main

function Logo() {
  return (
    <div className="logo">
      <span className="logo-mark"><span className="logo-bars"><i /><i /><i /></span></span>
      <strong>DataSnap</strong>
    </div>
  )
}
function dateLabel(value) { return value ? new Date(value).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) : 'Just now' }

export default function App() {
  const [page, setPage] = useState(window.location.pathname.startsWith('/reports') ? 'reports' : window.location.pathname.startsWith('/report/') ? 'report' : window.location.pathname === '/analyze' ? 'analyze' : 'landing')
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
  useEffect(() => { const onPop = () => { const path = window.location.pathname; setPage(path.startsWith('/reports') ? 'reports' : path.startsWith('/report/') ? 'report' : path === '/analyze' ? 'analyze' : 'landing'); setReportId(path.split('/').pop()) }; window.addEventListener('popstate', onPop); return () => window.removeEventListener('popstate', onPop) }, [])

  function navigate(next, id = '') { const path = id ? `/report/${id}` : next === 'analyze' ? '/analyze' : next === 'reports' ? '/reports' : '/'; window.history.pushState({}, '', path); setPage(next); if (id) setReportId(id); window.scrollTo({ top: 0, behavior: 'smooth' }) }
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

  return (
    <div className="site-shell">
      <motion.header className="site-nav" initial={{ y: -72, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.5, ease: easeOut }}>
        <motion.button className="brand-button" onClick={() => navigate('landing')} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}><Logo /></motion.button>

        <nav className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-1 md:flex">
          <button className={`rounded-[9px] px-3.5 py-2 text-[13.5px] font-medium transition-colors ${page === 'landing' ? 'text-brand' : 'text-ink-dim hover:text-ink'}`} onClick={() => navigate('landing')}>Overview</button>
          <button className={`rounded-[9px] px-3.5 py-2 text-[13.5px] font-medium transition-colors ${page === 'analyze' ? 'text-brand' : 'text-ink-dim hover:text-ink'}`} onClick={() => navigate('analyze')}>Analyze</button>
          <button className={`flex items-center gap-1.5 rounded-[9px] px-3.5 py-2 text-[13.5px] font-medium transition-colors ${page === 'reports' || page === 'report' ? 'text-brand' : 'text-ink-dim hover:text-ink'}`} onClick={() => navigate('reports')}>Reports <span className="rounded-full bg-brand-soft px-1.5 py-0.5 font-mono text-[10px] text-brand">{reports.length}</span></button>
        </nav>

        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          <span className="hidden font-mono text-[11px] text-ink-dim lg:inline">{quota ? `${quota.remaining}/${quota.limit} left` : '5 / hour'}</span>
          <button className="hidden rounded-[10px] px-3 py-2 text-[13.5px] font-medium text-ink-dim transition-colors hover:text-ink sm:inline" onClick={() => navigate('reports')}>Reports</button>
          <motion.button
            className="inline-flex items-center gap-1.5 rounded-[11px] border border-hairline-strong bg-panel px-4 py-2 text-[13.5px] font-semibold text-ink shadow-sm transition-colors hover:border-brand-line hover:text-brand"
            onClick={() => navigate('analyze')} whileHover={{ y: -1 }} whileTap={{ scale: 0.98 }}
          >
            Start free
          </motion.button>
        </div>
      </motion.header>

      <AnimatePresence mode="wait">
        {page === 'landing' && <Landing key="landing" onStart={() => navigate('analyze')} onReports={() => navigate('reports')} />}
        {page === 'analyze' && <Analyze key="analyze" file={file} setFile={setFile} query={query} setQuery={setQuery} running={running} step={step} error={error} onRun={runAnalysis} onReports={() => navigate('reports')} />}
        {page === 'reports' && <Reports key="reports" reports={reports} onOpen={openReport} onDelete={deleteReport} onNew={() => navigate('analyze')} />}
        {page === 'report' && <ReportPage key="report" report={report || reports.find(item => item.analysis_id === reportId)} saved={reports.some(item => item.analysis_id === reportId)} onSave={async item => { await saveReport(item); setReports(await listReports()) }} onBack={() => navigate('reports')} download={download} />}
      </AnimatePresence>
    </div>
  )
}

function Landing({ onStart, onReports }) {
  return (
    <MMain className="landing" variants={pageMotion} initial="initial" animate="animate" exit="exit">
      {/* ============================ HERO (full section) ============================ */}
      <section className="relative flex min-h-[calc(100svh-60px)] flex-col items-center justify-center px-5 py-10 text-center">
        {/* animated ambient glow */}
        <div aria-hidden className="pointer-events-none absolute left-1/2 top-[-60px] -z-10 h-[460px] w-[760px] max-w-[120vw] -translate-x-1/2 rounded-full bg-[radial-gradient(50%_50%_at_50%_50%,rgba(124,58,237,0.22),transparent_70%)] blur-2xl motion-safe:animate-[var(--animate-blob)]" />

        <motion.button
          className="group mb-6 inline-flex max-w-full items-center gap-2 whitespace-nowrap rounded-full border border-hairline-strong bg-panel py-1 pl-1.5 pr-3 text-[11.5px] font-medium text-ink-soft shadow-sm transition-colors hover:border-brand-line sm:text-[12px]"
          onClick={onStart} variants={rise}
        >
          <b className="rounded-full bg-brand-soft px-2.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-brand">New</b>
          Agent workflows are now available
          <ArrowUpRight size={14} className="text-ink-dim transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </motion.button>

        <motion.h1 className="m-0 font-display text-[clamp(32px,5vw,58px)] font-medium leading-[1.0] tracking-[-0.04em] text-ink" variants={rise}>
          See what your data <em className="bg-[linear-gradient(100deg,var(--color-brand),var(--color-brand-hot))] bg-clip-text not-italic text-transparent">hides</em>,
          <br className="hidden sm:block" /> before you train.
        </motion.h1>

        <motion.p className="mt-4 max-w-[42ch] text-[clamp(14px,1.3vw,16px)] leading-relaxed text-ink-soft" variants={rise}>
          An all-in-one agent that profiles, analyzes and verifies
          <br className="hidden sm:block" /> your data into a decision-ready brief.
        </motion.p>

        <motion.div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-3" variants={rise}>
          <motion.button className="primary-cta w-full justify-center !px-5 !py-2.5 !text-[13px] sm:w-auto" onClick={onStart} whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }}>Start an analysis <ArrowUpRight size={15} /></motion.button>
          <motion.button className="ghost-cta w-full justify-center !px-4 !py-2.5 !text-[13px] sm:w-auto" onClick={onReports} whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }}>Learn more <ChevronRight size={14} /></motion.button>
        </motion.div>

        <motion.div className="mt-7 flex flex-wrap items-center justify-center gap-x-7 gap-y-3 text-xs text-ink-dim" variants={rise}>
          <span className="flex items-center gap-2"><ShieldCheck size={15} className="text-brand" /> Isolated execution</span>
          <span className="flex items-center gap-2"><Check size={15} className="text-brand" /> Machine-verified metrics</span>
          <span className="flex items-center gap-2"><Lock size={15} className="text-brand" /> No account required</span>
        </motion.div>
      </section>

      {/* ====================== LIVE PREVIEW (separate full section) ====================== */}
      <section className="relative px-5 pt-14 pb-16 sm:pt-16 sm:pb-18">
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
          <div aria-hidden className="pointer-events-none absolute left-1/2 top-8 -z-10 h-[320px] w-[560px] max-w-[110vw] -translate-x-1/2 rounded-full bg-[radial-gradient(50%_50%_at_50%_50%,rgba(79,70,229,0.12),transparent_70%)] blur-2xl" />

          {/* single elegant chart card */}
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
                        style={{ height: `${pct}%`, background: i === 0 ? 'linear-gradient(to top, var(--color-brand), var(--color-brand-hot))' : '#e7e9fb', transformOrigin: 'bottom' }}
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

          {/* minimal verified-metric footer */}
          <motion.div
            className="mt-5 grid grid-cols-3 overflow-hidden rounded-[16px] border border-hairline bg-panel shadow-sm"
            initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.5, duration: 0.5, ease: easeOut }}
          >
            {[
              ['Avg rating', '4.33'],
              ['Return rate', '20.0%'],
              ['Rating ↔ revenue', 'r +0.68']
            ].map(([k, v], i) => (
              <div key={k} className={`px-5 py-4 text-center ${i < 2 ? 'border-r border-hairline' : ''}`}>
                <strong className="block font-display text-[18px] font-extrabold tracking-[-0.02em] text-ink">{v}</strong>
                <small className="mt-1 block text-[11px] text-ink-dim">{k}</small>
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

      <section className="section features">
        <motion.div className="section-head center" {...fadeUpView}>
          <p className="eyebrow"><span /> WHAT'S INSIDE</p>
          <h2>Everything you need to turn a dataset into a decision.</h2>
          <p className="section-lead">DataSnap handles the full path — profiling, planning, execution and synthesis — so you can focus on the call you need to make.</p>
        </motion.div>
        <div className="feature-grid">
          {FEATURES.map((f, i) => (
            <motion.article className="feature-card" key={f.title} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ duration: 0.5, ease: easeOut, delay: (i % 3) * 0.08 }} whileHover={{ y: -5 }}>
              <span className="feature-icon"><f.icon size={20} /></span>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </motion.article>
          ))}
        </div>
      </section>

      <section className="section how">
        <motion.div className="section-head center" {...fadeUpView}>
          <p className="eyebrow"><span /> HOW IT WORKS</p>
          <h2>From raw file to decision brief in four steps.</h2>
          <p className="section-lead">A guided, transparent flow. You stay in control at every stage while the agent does the heavy lifting.</p>
        </motion.div>
        <div className="how-steps">
          {HOW.map((s, i) => (
            <motion.div className="how-step" key={s.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.4 }} transition={{ duration: 0.45, ease: easeOut, delay: i * 0.07 }}>
              <div className="how-step-top">
                <span className="how-icon"><s.icon size={19} /></span>
                <span className="how-kicker">{String(i + 1).padStart(2, '0')}</span>
              </div>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <motion.section className="stats-band" {...fadeUpView}>
        {STATS.map((s, i) => (
          <motion.div className="stat" key={s.label} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08, duration: 0.5 }}>
            <strong>{s.value}</strong><span>{s.label}</span>
          </motion.div>
        ))}
      </motion.section>

      <section className="section">
        <motion.div className="cta-band" {...fadeUpView}>
          <div className="cta-glow" aria-hidden />
          <p className="eyebrow"><span /> READY WHEN YOU ARE</p>
          <h2>Ask your data a better question.</h2>
          <p>Upload a dataset and get a decision-ready brief in minutes. No account, no setup, private by default.</p>
          <div className="hero-actions">
            <motion.button className="primary-cta" onClick={onStart} whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }}>Start an analysis <ArrowUpRight size={17} /></motion.button>
            <motion.button className="ghost-cta" onClick={onReports} whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }}>View saved reports <ChevronRight size={15} /></motion.button>
          </div>
        </motion.div>
      </section>

      <footer className="site-footer">
        <div className="footer-brand">
          <Logo />
          <p>Decision intelligence that turns a question and a dataset into verified, decision-ready evidence.</p>
        </div>
        <div className="footer-links">
          <div><h4>Product</h4><button onClick={onStart}>Start analysis</button><button onClick={onReports}>Saved reports</button></div>
          <div><h4>Trust</h4><span>Isolated execution</span><span>Private by default</span><span>Verified metrics</span></div>
          <div><h4>Formats</h4><span>CSV · TSV · JSON</span><span>XLSX · Parquet</span><span>JSONL</span></div>
        </div>
        <div className="footer-base"><span>© {new Date().getFullYear()} DataSnap</span><span>Built for fast, evidence-first decisions.</span></div>
      </footer>
    </MMain>
  )
}

function Analyze({ file, setFile, query, setQuery, running, step, error, onRun, onReports }) {
  const chooseFile = event => setFile(event.target.files?.[0] || null)
  return (
    <MMain className="workspace" variants={pageMotion} initial="initial" animate="animate" exit="exit">
      <motion.div className="workspace-intro" variants={rise}>
        <div>
          <p className="eyebrow"><span /> NEW ANALYSIS</p>
          <h1>What decision are you making?</h1>
          <p>Bring the data. DataSnap will structure the analysis and return the evidence.</p>
        </div>
        <button className="text-button" onClick={onReports}>Open saved reports <ChevronRight size={15} /></button>
      </motion.div>

      <div className="analyze-grid">
        <MSection className="input-panel" variants={rise}>
          <div className="panel-step"><span>01</span><div><strong>Dataset</strong><small>CSV, XLSX, Parquet, TSV, JSON or JSONL</small></div></div>
          <div className={`upload-box ${file ? 'selected' : ''}`} onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); setFile(event.dataTransfer.files[0]) }}>
            {file ? (
              <motion.div className={`file-selected ${running ? 'scanning' : ''}`} initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.3 }}>
                <div className="file-type"><FileText size={21} /></div>
                <div><strong>{file.name}</strong><span>{running ? 'Analyzing…' : `${(file.size / 1024).toFixed(1)} KB · Ready to analyze`}</span></div>
                <label className="change-file">Change<input type="file" accept=".csv,.xlsx,.parquet,.tsv,.json,.jsonl" onChange={chooseFile} /></label>
                <button className="remove-file" onClick={() => setFile(null)} aria-label="Remove selected file"><X size={16} /></button>
              </motion.div>
            ) : (
              <>
                <div className="upload-symbol"><UploadCloud size={23} /></div>
                <strong>Drop your dataset here</strong>
                <span>or browse from your computer</span>
                <input type="file" accept=".csv,.xlsx,.parquet,.tsv,.json,.jsonl" onChange={chooseFile} />
              </>
            )}
          </div>
          <div className="panel-step question-step"><span>02</span><div><strong>Business question</strong><small>Be specific about the decision you need to make</small></div></div>
          <textarea className="question-box" value={query} onChange={event => setQuery(event.target.value)} maxLength={500} />
          <div className="input-footer">
            <span className="fallback-note"><Zap size={15} /> Gemini primary + automatic fallback</span>
            <motion.button className="primary-cta small" onClick={onRun} disabled={running} whileHover={!running ? { scale: 1.03, y: -2 } : {}} whileTap={!running ? { scale: 0.97 } : {}}>
              {running ? <><LoaderCircle className="spin" size={16} /> Analyzing</> : <><Play size={16} fill="currentColor" /> Run analysis</>}
            </motion.button>
          </div>
          <AnimatePresence>
            {error && (
              <motion.div className="error-line" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                <X size={15} />
                <div><strong>Analysis could not be completed</strong><span>{error}</span><button onClick={onRun}>Try again</button></div>
              </motion.div>
            )}
          </AnimatePresence>
        </MSection>

        <motion.aside className="process-panel" variants={rise}>
          <p className="eyebrow"><Sparkles size={13} /> YOUR ANALYSIS</p>
          <h2>
            {running ? 'Building your brief' : 'A clear path to clarity'}
            {running && <span className="working-dots" aria-hidden><i /><i /><i /></span>}
          </h2>
          <div className="process-progress" role="progressbar" aria-valuemin={0} aria-valuemax={STEPS.length} aria-valuenow={running ? step + 1 : 0}>
            <div className={`process-progress-fill ${running ? 'live' : ''}`} style={{ width: `${running ? ((step + 1) / STEPS.length) * 100 : 0}%` }} />
          </div>
          <div className="process-list">
            {STEPS.map((item, index) => {
              const done = step > index
              const current = running && step === index
              return (
                <motion.div className={`process-row ${done ? 'done' : ''} ${current ? 'current' : ''}`} key={item} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 + index * 0.06 }}>
                  <span>
                    <AnimatePresence mode="wait" initial={false}>
                      {done ? (
                        <motion.span key="done" initial={{ scale: 0, rotate: -45 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: 'spring', stiffness: 500, damping: 22 }} style={{ display: 'grid', placeItems: 'center' }}>
                          <Check size={12} />
                        </motion.span>
                      ) : current ? (
                        <motion.span key="run" style={{ display: 'grid', placeItems: 'center' }}>
                          <LoaderCircle className="spin" size={13} />
                        </motion.span>
                      ) : (
                        <motion.span key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>{`0${index + 1}`}</motion.span>
                      )}
                    </AnimatePresence>
                  </span>
                  <strong>{item}</strong>
                  {current && (
                    <motion.span className="step-status" initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }}>
                      working
                    </motion.span>
                  )}
                </motion.div>
              )
            })}
          </div>
          <div className="process-note"><ShieldCheck size={17} /><p>Your dataset is executed in an isolated runtime. Reports are saved only when you choose to save them.</p></div>
        </motion.aside>
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
