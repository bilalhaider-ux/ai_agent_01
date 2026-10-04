const DB_NAME = 'datasnap-analytics'
const STORE_NAME = 'reports'

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1)
    request.onupgradeneeded = () => request.result.createObjectStore(STORE_NAME, { keyPath: 'analysis_id' })
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

export async function saveReport(report) {
  try {
    const db = await openDatabase()
    await new Promise((resolve, reject) => {
      const request = db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).put({ ...report, saved_at: Date.now() })
      request.onsuccess = resolve
      request.onerror = () => reject(request.error)
    })
  } catch {
    const reports = JSON.parse(localStorage.getItem('datasnap_reports') || '[]')
    localStorage.setItem('datasnap_reports', JSON.stringify([{ ...report, saved_at: Date.now() }, ...reports.filter(item => item.analysis_id !== report.analysis_id)].slice(0, 20)))
  }
}

export async function listReports() {
  try {
    const db = await openDatabase()
    return await new Promise((resolve, reject) => {
      const request = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).getAll()
      request.onsuccess = () => resolve(request.result.sort((a, b) => b.saved_at - a.saved_at))
      request.onerror = () => reject(request.error)
    })
  } catch {
    return JSON.parse(localStorage.getItem('datasnap_reports') || '[]')
  }
}

export async function removeReport(id) {
  try {
    const db = await openDatabase()
    db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).delete(id)
  } catch {
    const reports = JSON.parse(localStorage.getItem('datasnap_reports') || '[]')
    localStorage.setItem('datasnap_reports', JSON.stringify(reports.filter(item => item.analysis_id !== id)))
  }
}
