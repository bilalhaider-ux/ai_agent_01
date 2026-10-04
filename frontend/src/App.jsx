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

/* ---------------------------------------------------------------- motion -- */
const easeOut = [0.22, 1, 0.36, 1]
const pageMotion = {
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: easeOut, staggerChildren: 0.07, delayChildren: 0.05 } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.25, ease: 'easeIn' } }
}
const rise = {
  initial: { opacity: 0, y: 22 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: easeOut } }
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
    const timeout = setTimeout(() => controller.abort(), 25_000)
    try {
      const response = await fetch(`${API_URL}/api/v1/analyze`, { method: 'POST', body: payload, credentials: 'include', signal: controller.signal })
      const contentType = response.headers.get('content-type') || ''
      const body = contentType.includes('application/json') ? await response.json() : null
      setQuota({ remaining: response.headers.get('X-RateLimit-Remaining'), limit: response.headers.get('X-RateLimit-Limit') || '5' })
      if (!response.ok) {
        const detail = body?.detail || body?.error?.message
        throw new Error(detail || `Analysis API returned HTTP ${response.status}. Check the backend logs for the upstream provider response.`)
      }
      setReport(body); navigate('report', body.analysis_id)
    } catch (requestError) {
      const message = requestError.name === 'AbortError'
        ? 'The analysis API did not respond within 25 seconds. The backend may be waiting on the AI provider or a platform request timeout.'
        : requestError.message || 'The analysis request could not reach the API.'
      setError(message)
    } finally { clearTimeout(timeout); clearInterval(timer); setRunning(false) }
  }

  async function deleteReport(id) { await removeReport(id); const next = await listReports(); setReports(next); if (report?.analysis_id === id) { setReport(null); navigate('reports') } }
  function download(name, content, type) { const url = URL.createObjectURL(new Blob([content], { type })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click(); URL.revokeObjectURL(url) }

  return (
    <div className="site-shell">
      <motion.header className="site-nav" initial={{ y: -72, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.5, ease: easeOut }}>
        <motion.button className="brand-button" onClick={() => navigate('landing')} whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}><Logo /></motion.button>
        <nav>
          <button className={page === 'analyze' ? 'active' : ''} onClick={() => navigate('analyze')}>Analyze</button>
          <button className={page === 'reports' || page === 'report' ? 'active' : ''} onClick={() => navigate('reports')}>Reports <span>{reports.length}</span></button>
        </nav>
        <div className="nav-actions">
          <span className="privacy"><ShieldCheck size={14} /> Private by default</span>
          <span className="quota">{quota ? `${quota.remaining}/${quota.limit} analyses left` : '5 analyses / hour'}</span>
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
      <section className="hero">
        <div className="hero-copy">
          <motion.div className="hero-badge" variants={rise}><b>NEW</b> Decision intelligence, on tap</motion.div>
          <motion.h1 variants={rise}>Find the signal <em>inside your data.</em></motion.h1>
          <motion.p className="hero-sub" variants={rise}>Upload a dataset, ask a business question, and get a clear decision brief backed by machine-verified evidence.</motion.p>
          <motion.div className="hero-actions" variants={rise}>
            <motion.button className="primary-cta" onClick={onStart} whileHover={{ scale: 1.03, y: -2 }} whileTap={{ scale: 0.97 }}>Start an analysis <ArrowUpRight size={17} /></motion.button>
            <button className="text-button" onClick={onReports}>View saved reports <ChevronRight size={15} /></button>
          </motion.div>
          <motion.div className="hero-trust" variants={rise}>
            <span><ShieldCheck size={15} /> Isolated execution</span>
            <span><Check size={15} /> Evidence-first output</span>
            <span><Zap size={15} /> Built for fast answers</span>
          </motion.div>
        </div>

        <motion.div className="hero-visual" initial={{ opacity: 0, scale: 0.94, y: 24 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.8, ease: easeOut, delay: 0.2 }}>
          <div className="visual-top"><span>● LIVE SIGNAL</span><span>ANALYSIS READY</span></div>
          <motion.div className="signal-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.6, ease: easeOut }}>
            <div className="signal-header"><div><small>REVENUE MOMENTUM</small><strong>+32.8%</strong></div><span className="signal-up">↗</span></div>
            <div className="signal-chart">
              {[26, 38, 31, 47, 44, 64, 57, 76, 92].map((h, i) => (
                <motion.i key={i} initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ delay: 0.7 + i * 0.07, duration: 0.5, ease: easeOut }} style={{ height: `${h}%` }} />
              ))}
            </div>
            <div className="chart-axis"><span>JAN</span><span>APR</span><span>JUL</span><span>OCT</span></div>
          </motion.div>
          <motion.div className="floating-card" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.1, duration: 0.5 }} whileHover={{ y: -4 }}>
            <div className="mini-icon"><BarChart3 size={16} /></div>
            <div><strong>Decision brief</strong><small>6 verified insights</small></div>
            <Check size={16} />
          </motion.div>
          <div className="visual-caption"><span>01</span><p>From raw rows to a decision-ready view.</p></div>
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
        <motion.div className="section-head" {...fadeUpView}>
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
        <motion.div className="section-head" {...fadeUpView}>
          <p className="eyebrow"><span /> HOW IT WORKS</p>
          <h2>From raw file to decision brief in four steps.</h2>
          <p className="section-lead">A guided, transparent flow. You stay in control at every stage while the agent does the heavy lifting.</p>
        </motion.div>
        <div className="how-steps">
          {HOW.map((s, i) => (
            <motion.div className="how-step" key={s.title} initial={{ opacity: 0, y: 26 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.4 }} transition={{ duration: 0.5, ease: easeOut, delay: i * 0.08 }}>
              <div className="how-step-top">
                <span className="how-icon"><s.icon size={19} /></span>
                <span className="how-kicker">{s.kicker}</span>
              </div>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
              {i < HOW.length - 1 && <span className="how-connector" aria-hidden><ChevronRight size={16} /></span>}
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
            <motion.button className="primary-cta" onClick={onStart} whileHover={{ scale: 1.03, y: -2 }} whileTap={{ scale: 0.97 }}>Start an analysis <ArrowUpRight size={17} /></motion.button>
            <button className="text-button" onClick={onReports}>View saved reports <ChevronRight size={15} /></button>
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
              <motion.div className="file-selected" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.3 }}>
                <div className="file-type"><FileText size={21} /></div>
                <div><strong>{file.name}</strong><span>{(file.size / 1024).toFixed(1)} KB · Ready to analyze</span></div>
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
          <h2>{running ? 'Building your brief' : 'A clear path to clarity'}</h2>
          <div className="process-list">
            {STEPS.map((item, index) => (
              <motion.div className={`process-row ${step > index ? 'done' : ''} ${running && step === index ? 'current' : ''}`} key={item} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 + index * 0.06 }}>
                <span>{step > index ? <Check size={12} /> : `0${index + 1}`}</span><strong>{item}</strong>
              </motion.div>
            ))}
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
