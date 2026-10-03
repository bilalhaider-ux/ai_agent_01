import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity, ArrowDownToLine, ArrowRight, BarChart3, BrainCircuit, Check,
  ChevronDown, ChevronRight, CircleHelp, Clock3, Code2, Database, FileBarChart,
  FileText, History, LayoutDashboard, Menu, Moon, MoreHorizontal, Play, Plus,
  RotateCcw, Search, Settings, ShieldCheck, Sparkles, Sun, Table2, UploadCloud,
  X, Zap,
} from 'lucide-react'
import { useLiquidGlass } from './hooks/useLiquidGlass'

const pipeline = [
  ['Context minification', 'Profiled schema, nulls and distributions'],
  ['Intent & plan', 'Formed 3 hypotheses and selected methods'],
  ['Code generation', 'Created Polars + SciPy analysis'],
  ['Isolated execution', 'Completed safely in 4.8 seconds'],
  ['Self-correction', 'No repair needed'],
  ['Output synthesis', 'Decision brief generated'],
]

const reports = [
  { title: 'Revenue drivers & return risk', dataset: 'sample_sales_data.csv', date: 'Today, 9:42 PM', status: 'Ready' },
  { title: 'Regional margin performance', dataset: 'sales_q2.csv', date: 'Sep 29, 4:18 PM', status: 'Ready' },
  { title: 'Customer cohort retention', dataset: 'customers.csv', date: 'Sep 27, 11:03 AM', status: 'Ready' },
]

const categoryData = [
  { name: 'Electronics', value: 100, amount: '$8.2k' },
  { name: 'Home & kitchen', value: 44, amount: '$3.6k' },
  { name: 'Sports', value: 38, amount: '$3.1k' },
  { name: 'Fashion', value: 24, amount: '$2.0k' },
  { name: 'Beauty', value: 18, amount: '$1.5k' },
]

function Logo() {
  return <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>
}

function GlassPanel({ className = '', children, optics = {}, ...props }) {
  const ref = useLiquidGlass({ scale: -72, chroma: 4, blur: 2, fallbackBlur: 18, ...optics })
  return <div ref={ref} className={`glass ${className}`} {...props}>{children}</div>
}

function Sidebar({ page, setPage, open, close }) {
  const nav = [
    ['analysis', LayoutDashboard, 'Workspace'],
    ['reports', FileBarChart, 'Reports'],
    ['datasets', Database, 'Datasets'],
  ]
  return <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
    <div className="brand"><Logo /><span>Lumen</span><button className="icon-button mobile-close" onClick={close}><X size={19}/></button></div>
    <nav className="side-nav" aria-label="Primary navigation">
      <p className="eyebrow">WORKSPACE</p>
      {nav.map(([id, Icon, label]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => { setPage(id); close() }}><Icon size={18}/><span>{label}</span>{id === 'reports' && <small>3</small>}</button>)}
      <p className="eyebrow history-label">RECENT</p>
      <button className="recent-item" onClick={() => { setPage('analysis'); close() }}><History size={17}/><span>Revenue drivers</span></button>
      <button className="recent-item" onClick={() => { setPage('reports'); close() }}><History size={17}/><span>Regional margins</span></button>
    </nav>
    <div className="sidebar-bottom">
      <button><CircleHelp size={18}/><span>Help & docs</span></button>
      <button><Settings size={18}/><span>Settings</span></button>
      <div className="profile"><div className="avatar">BH</div><div><strong>Bilal Haider</strong><small>Personal workspace</small></div><MoreHorizontal size={18}/></div>
    </div>
  </aside>
}

function Header({ page, setSidebar, theme, toggleTheme }) {
  const titles = { analysis: ['Analysis workspace', 'Ask a question. Get a decision, not a dashboard.'], reports: ['Reports', 'Every finished analysis, ready to revisit.'], datasets: ['Datasets', 'Manage the data available to your agent.'] }
  return <header className="topbar">
    <button className="icon-button menu-button" onClick={() => setSidebar(true)} aria-label="Open menu"><Menu size={20}/></button>
    <div><h1>{titles[page][0]}</h1><p>{titles[page][1]}</p></div>
    <div className="header-actions"><button className="icon-button" onClick={toggleTheme} aria-label="Toggle theme" title="Toggle theme">{theme === 'dark' ? <Sun size={19}/> : <Moon size={19}/>}</button><button className="icon-button" aria-label="Notifications" title="Activity"><Activity size={19}/><i/></button><div className="avatar compact">BH</div></div>
  </header>
}

function Uploader({ file, setFile }) {
  const input = useRef(null)
  const glassRef = useLiquidGlass({ scale: -66, chroma: 4, border: .1, blur: 2, saturate: 1.25, fallbackBlur: 18 })
  const choose = (event) => { const next = event.target.files?.[0]; if (next) setFile(next) }
  return <button ref={glassRef} className="upload-zone liquid-surface" onClick={() => input.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]) }}>
    <input ref={input} type="file" accept=".csv,.parquet" onChange={choose}/>
    <div className="upload-icon"><UploadCloud size={21}/></div>
    <div><strong>{file?.name || 'Drop a dataset here'}</strong><span>{file ? `${(file.size / 1024).toFixed(1)} KB · Ready to analyze` : 'or click to browse · CSV or Parquet up to 100 MB'}</span></div>
    {file && <span className="file-ready"><Check size={14}/> Ready</span>}
  </button>
}

function AnalysisSetup({ onRun, running }) {
  const [file, setFile] = useState({ name: 'sample_sales_data.csv', size: 5824 })
  const [query, setQuery] = useState('Which product categories drive the most revenue, and how do customer ratings relate to returns?')
  const [provider, setProvider] = useState('Ollama · llama3.2')
  const providerGlass = useLiquidGlass({ scale: -58, chroma: 3, border: .12, blur: 2, fallbackBlur: 16 })
  return <section className="setup-card panel">
    <div className="section-heading"><div><span className="step-number">01</span><div><h2>Start an analysis</h2><p>Bring your data and describe the decision you need to make.</p></div></div><span className="privacy"><ShieldCheck size={14}/> Runs in an isolated sandbox</span></div>
    <div className="setup-grid">
      <div><label className="field-label">DATASET</label><Uploader file={file} setFile={setFile}/></div>
      <div className="query-field"><label className="field-label">QUESTION</label><textarea value={query} onChange={e => setQuery(e.target.value)} maxLength={500}/><span>{query.length}/500</span></div>
    </div>
    <div className="setup-footer">
      <label ref={providerGlass} className="provider-select liquid-surface"><Zap size={16}/><select value={provider} onChange={e => setProvider(e.target.value)}><option>Ollama · llama3.2</option><option>OpenAI · gpt-4o-mini</option><option>Mock · offline test</option></select><ChevronDown size={15}/></label>
      <button className="run-button" onClick={() => onRun(query)} disabled={running}>{running ? <><span className="spinner"/> Analyzing</> : <><Play size={17} fill="currentColor"/> Run analysis</>}</button>
    </div>
  </section>
}

function Pipeline({ running, stage }) {
  return <section className="panel pipeline-card">
    <div className="card-title"><div><BrainCircuit size={18}/><h3>Agent activity</h3></div><span className={running ? 'status running' : 'status done'}>{running ? 'Running' : 'Completed'}</span></div>
    <div className="pipeline-list">
      {pipeline.map(([title, detail], index) => {
        const complete = !running || index < stage
        const active = running && index === stage
        return <div className={`pipeline-row ${complete ? 'complete' : ''} ${active ? 'current' : ''}`} key={title}>
          <div className="pipeline-rail"><span>{complete ? <Check size={12}/> : index + 1}</span>{index < pipeline.length - 1 && <i/>}</div>
          <div><strong>{title}</strong><small>{complete ? detail : active ? 'Working on this now…' : 'Waiting'}</small></div>
          {complete && index === 4 && <em>0 retries</em>}
        </div>
      })}
    </div>
    <div className="runtime"><Clock3 size={14}/><span>{running ? `${Math.max(1, stage * 2)}s elapsed` : 'Completed in 18.4s'}</span><span>•</span><span>6 stages</span></div>
  </section>
}

function Metric({ label, value, change, icon: Icon }) {
  const glassRef = useLiquidGlass({ scale: -54, chroma: 3, border: .11, blur: 2, fallbackBlur: 17 })
  return <div ref={glassRef} className="metric liquid-surface"><div className="metric-top"><span>{label}</span><Icon size={17}/></div><strong>{value}</strong><small>{change}</small></div>
}

function BarChart() {
  return <div className="bar-chart" aria-label="Revenue by product category bar chart">
    {categoryData.map(row => <div className="bar-row" key={row.name}><span>{row.name}</span><div><i style={{ width: `${row.value}%` }}/></div><strong>{row.amount}</strong></div>)}
  </div>
}

function Donut() {
  return <div className="donut-wrap"><div className="donut"><div><strong>20%</strong><span>Return rate</span></div></div><div className="donut-legend"><span><i className="mint"/>Kept <strong>80%</strong></span><span><i className="coral"/>Returned <strong>20%</strong></span></div></div>
}

function Results({ running, query, notify }) {
  const [tab, setTab] = useState('Overview')
  const [downloadOpen, setDownloadOpen] = useState(false)
  const exportGlass = useLiquidGlass({ scale: -52, chroma: 3, border: .12, blur: 2, fallbackBlur: 16 })
  const download = (format) => {
    const content = `# Analytical Decision Report\n\n## Executive Summary\nElectronics is the primary revenue engine. Customer ratings show a statistically significant positive relationship with revenue, while returns concentrate in lower-rated, heavily discounted orders.\n\n## Recommended Actions\n- Protect Electronics availability.\n- Address Fashion return drivers.\n- Trigger follow-up on low-rating purchases.`
    const blob = new Blob([content], { type: format === 'HTML' ? 'text/html' : 'text/markdown' })
    const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = `lumen-report.${format === 'HTML' ? 'html' : 'md'}`; anchor.click(); URL.revokeObjectURL(anchor.href)
    setDownloadOpen(false); notify(`${format} report downloaded`)
  }
  return <section className={`results ${running ? 'results-dimmed' : ''}`}>
    <div className="results-header"><div><span className="eyebrow">LATEST RESULT</span><h2>Revenue drivers & return risk</h2><p>{query}</p></div><div className="export-wrap"><button ref={exportGlass} className="secondary-button liquid-surface" onClick={() => setDownloadOpen(!downloadOpen)}><ArrowDownToLine size={16}/> Export <ChevronDown size={14}/></button>{downloadOpen && <div className="export-menu"><button onClick={() => download('Markdown')}>Markdown report</button><button onClick={() => download('HTML')}>HTML report</button></div>}</div></div>
    <div className="tabs" role="tablist">{['Overview', 'Visuals', 'Report', 'Run details'].map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>{item}</button>)}</div>
    {tab === 'Overview' && <div className="overview">
      <div className="metrics-grid"><Metric label="Total revenue" value="$18.4K" change="30 transactions analyzed" icon={BarChart3}/><Metric label="Top category" value="Electronics" change="44.6% of total revenue" icon={Sparkles}/><Metric label="Rating correlation" value="+0.64" change="Statistically significant" icon={Activity}/><Metric label="Return rate" value="20.0%" change="6 of 30 transactions" icon={RotateCcw}/></div>
      <div className="insight-grid"><article className="panel narrative"><div className="card-title"><div><Sparkles size={18}/><h3>Executive brief</h3></div><span className="ai-badge">AI SYNTHESIZED</span></div><p>Electronics is the primary revenue engine, combining premium order values with strong customer ratings. Ratings show a meaningful positive relationship with revenue, while returns cluster in lower-rated, heavily discounted orders.</p><div className="callout"><strong>Decision</strong><p>Protect Electronics availability while addressing Fashion’s return drivers before expanding discount-led acquisition.</p></div><h4>Recommended next moves</h4><ul><li><span>1</span>Shift inventory and campaign budget toward high-rated Electronics.</li><li><span>2</span>Review Fashion sizing and quality signals to reduce avoidable returns.</li><li><span>3</span>Trigger proactive support for purchases rated below 4.0.</li></ul></article><aside className="panel evidence"><div className="card-title"><div><ShieldCheck size={18}/><h3>Evidence quality</h3></div><strong>High</strong></div><div className="confidence"><i/><span>92% confidence</span></div><dl><div><dt>Rows profiled</dt><dd>30 / 30</dd></div><div><dt>Missing values</dt><dd>0</dd></div><div><dt>Statistical tests</dt><dd>Pearson r</dd></div><div><dt>Execution</dt><dd>Sandboxed</dd></div></dl></aside></div>
    </div>}
    {tab === 'Visuals' && <div className="visual-grid"><article className="panel chart-card"><div className="card-title"><div><BarChart3 size={18}/><h3>Revenue by category</h3></div><span>USD</span></div><BarChart/></article><article className="panel chart-card"><div className="card-title"><div><RotateCcw size={18}/><h3>Return outcome</h3></div><span>30 orders</span></div><Donut/></article></div>}
    {tab === 'Report' && <article className="panel report-view"><div className="report-kicker">ANALYTICAL DECISION REPORT</div><h2>Revenue drivers & return risk</h2><h3>Executive summary</h3><p>Electronics is the dominant revenue driver with strong average order values. Customer rating has a statistically significant positive correlation with revenue, while returns are disproportionately concentrated in discounted categories.</p><h3>Core findings</h3><p>Product revenue is concentrated in Electronics, followed by Sports and Home & Kitchen. Higher customer ratings correspond with larger transaction amounts, and returns occur predominantly in lower-rated transactions.</p><h3>Statistical insights</h3><ul><li>Electronics leads category revenue with premium unit margins.</li><li>A positive Pearson correlation was observed between rating and order revenue.</li><li>The overall return rate is 20.0%.</li></ul></article>}
    {tab === 'Run details' && <div className="details-grid"><Pipeline running={false} stage={6}/><article className="panel code-panel"><div className="card-title"><div><Code2 size={18}/><h3>Execution contract</h3></div><span>Python</span></div><pre><code>{`Provider     Ollama / llama3.2\nRuntime      Isolated subprocess\nLibraries    Polars, SciPy, Matplotlib\nTimeout      45 seconds\nRetry budget 3 attempts\nExit code    0 (success)`}</code></pre></article></div>}
  </section>
}

function AnalysisPage({ notify }) {
  const [running, setRunning] = useState(false)
  const [stage, setStage] = useState(6)
  const [query, setQuery] = useState('Which product categories drive the most revenue, and how do customer ratings relate to returns?')
  const run = nextQuery => { setQuery(nextQuery); setRunning(true); setStage(0); notify('Analysis started') }
  useEffect(() => {
    if (!running) return undefined
    const timer = setInterval(() => setStage(current => Math.min(current + 1, 6)), 900)
    return () => clearInterval(timer)
  }, [running])
  useEffect(() => {
    if (running && stage === 6) {
      setRunning(false)
      notify('Analysis completed')
    }
  }, [running, stage])
  return <><div className="workspace-grid"><AnalysisSetup onRun={run} running={running}/><Pipeline running={running} stage={stage}/></div><Results running={running} query={query} notify={notify}/></>
}

function ReportsPage({ setPage }) {
  return <section className="page-panel"><div className="page-actions"><div className="search"><Search size={17}/><input placeholder="Search reports"/></div><button className="run-button compact-button" onClick={() => setPage('analysis')}><Plus size={17}/> New analysis</button></div><div className="report-list"><div className="list-head"><span>REPORT</span><span>DATASET</span><span>CREATED</span><span>STATUS</span><span/></div>{reports.map((report, i) => <button className="report-row" key={report.title} onClick={() => setPage('analysis')}><span className="report-name"><span className="doc-icon"><FileText size={18}/></span><span><strong>{report.title}</strong><small>{i === 0 ? 'Revenue, ratings and return behavior' : 'Autonomous analysis report'}</small></span></span><span>{report.dataset}</span><span>{report.date}</span><span className="ready-dot"><i/>{report.status}</span><ChevronRight size={17}/></button>)}</div></section>
}

function DatasetsPage({ setPage }) {
  const data = [{ name: 'sample_sales_data.csv', meta: '30 rows · 13 columns', used: 'Today, 9:42 PM' }, { name: 'sales_q2.csv', meta: '12,480 rows · 18 columns', used: 'Sep 29, 4:18 PM' }, { name: 'customers.csv', meta: '8,204 rows · 11 columns', used: 'Sep 27, 11:03 AM' }]
  return <section className="page-panel"><div className="page-actions"><div><strong>3 datasets</strong><p>CSV and Parquet files available to your analyses.</p></div><button className="run-button compact-button" onClick={() => setPage('analysis')}><UploadCloud size={17}/> Upload dataset</button></div><div className="dataset-grid">{data.map((item, i) => <article className="panel dataset-card" key={item.name}><div className="dataset-top"><div className="dataset-icon"><Table2 size={22}/></div><button className="icon-button"><MoreHorizontal size={18}/></button></div><h3>{item.name}</h3><p>{item.meta}</p><div><span>Last analyzed</span><strong>{item.used}</strong></div><button onClick={() => setPage('analysis')}>Analyze <ArrowRight size={15}/></button>{i === 0 && <span className="sample-tag">SAMPLE</span>}</article>)}</div></section>
}

export default function App() {
  const [page, setPage] = useState('analysis')
  const [sidebar, setSidebar] = useState(false)
  const [theme, setTheme] = useState('light')
  const [toast, setToast] = useState('')
  const notify = message => { setToast(message); setTimeout(() => setToast(''), 2600) }
  useEffect(() => { document.documentElement.dataset.theme = theme }, [theme])
  const content = useMemo(() => page === 'analysis' ? <AnalysisPage notify={notify}/> : page === 'reports' ? <ReportsPage setPage={setPage}/> : <DatasetsPage setPage={setPage}/>, [page])
  return <div className="app-shell">
    <div className="aurora aurora-one"/><div className="aurora aurora-two"/>
    {sidebar && <button className="scrim" onClick={() => setSidebar(false)} aria-label="Close menu"/>}
    <Sidebar page={page} setPage={setPage} open={sidebar} close={() => setSidebar(false)}/>
    <main><Header page={page} setSidebar={setSidebar} theme={theme} toggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}/><div className="content">{content}</div><footer><span><Logo/> Lumen analytics</span><span>Private by design · Built for decisive work</span></footer></main>
    {toast && <GlassPanel className="toast" optics={{ scale: -50 }}><Check size={16}/>{toast}</GlassPanel>}
  </div>
}
