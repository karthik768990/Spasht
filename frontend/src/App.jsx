import React, { useState, useEffect } from 'react';
import { UploadCloud, AlertTriangle, FileText, Moon, Sun, ChevronDown, Info, CheckCircle2, AlertCircle, TrendingUp, AlertOctagon, MinusCircle } from 'lucide-react';
import { Logo } from './components/Logo';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const PatternBadge = ({ pattern, className = '' }) => {
  let colors = '';
  let Icon = null;

  if (!pattern || pattern === 'Insufficient Data') {
    colors = 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700';
    Icon = MinusCircle;
  } else if (pattern.includes('Strong Signal')) {
    colors = 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/50';
    Icon = AlertOctagon;
  } else if (pattern.includes('Partial Signal')) {
    colors = 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/40 dark:text-orange-400 dark:border-orange-900/50';
    Icon = TrendingUp;
  } else if (pattern === 'Moderate Pattern') {
    colors = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-900/50';
    Icon = AlertCircle;
  } else if (pattern === 'Usual Pattern') {
    colors = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/50';
    Icon = CheckCircle2;
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-semibold tracking-wide ${colors} ${className}`}>
      {Icon && <Icon size={14} className="shrink-0" />}
      {pattern || 'Insufficient Data'}
    </span>
  );
};

function App() {
  const [tenders, setTenders] = useState([]);
  const [selectedTender, setSelectedTender] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendWakingUp, setBackendWakingUp] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [samples, setSamples] = useState([]);
  const [showSamples, setShowSamples] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
  };

  // Batch Mode State
  const [activeTab, setActiveTab] = useState('dashboard');
  const [batchTenders, setBatchTenders] = useState(() => {
    const saved = sessionStorage.getItem('batchTenders');
    return saved ? JSON.parse(saved) : [];
  });
  const [batchSelectedTender, setBatchSelectedTender] = useState(null);
  const [batchUploading, setBatchUploading] = useState(false);

  useEffect(() => {
    sessionStorage.setItem('batchTenders', JSON.stringify(batchTenders));
  }, [batchTenders]);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(theme === 'light' ? 'dark' : 'light');

  const fetchTenders = async (isRetry = false) => {
    if (!isRetry) {
      setLoading(true);
      setBackendWakingUp(false);
    }
    setError(null);

    const wakeUpTimer = setTimeout(() => {
      setBackendWakingUp(true);
      setLoading(false);
    }, 5000);

    try {
      const res = await fetch(`${API_BASE}/tenders`);
      clearTimeout(wakeUpTimer);
      if (!res.ok) {
        if (res.status >= 500) {
          throw new Error('Server starting up...');
        }
        throw new Error('Failed to fetch tenders');
      }
      const data = await res.json();
      setTenders(data);
      setBackendWakingUp(false);
      setLoading(false);
    } catch (err) {
      clearTimeout(wakeUpTimer);
      if ((err.name === 'TypeError' && err.message.includes('fetch')) || err.message === 'Server starting up...') {
        setBackendWakingUp(true);
        setLoading(false);
        setTimeout(() => fetchTenders(true), 5000);
      } else {
        setError(err.message);
        setLoading(false);
        setBackendWakingUp(false);
      }
    }
  };
  console.alert("Hi this is mani from the user ")
  const fetchSamples = async (isRetry = false) => {
    try {
      const res = await fetch(`${API_BASE}/upload/samples`);
      if (res.ok) {
        const data = await res.json();
        setSamples(data.samples || []);
      } else if (res.status >= 500 && !isRetry) {
        setTimeout(() => fetchSamples(true), 5000);
      }
    } catch (err) {
      if ((err.name === 'TypeError' && err.message.includes('fetch')) && !isRetry) {
        setTimeout(() => fetchSamples(true), 5000);
      } else {
        console.error("Failed to fetch samples", err);
      }
    }
  };

  useEffect(() => {
    fetchTenders();
    fetchSamples();
  }, []);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      showNotification('Only PDF files are allowed.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      showNotification(`Scan complete! Tender ID: ${data.tender_id}`, 'success');
      fetchTenders();
    } catch (err) {
      showNotification(`Error: ${err.message}`, 'error');
    } finally {
      setUploading(false);
    }
    event.target.value = null;
  };

  const handleSampleUpload = async (filename) => {
    setShowSamples(false);
    setUploading(true);
    try {
      const res = await fetch(`${API_BASE}/upload/samples/${filename}`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Sample upload failed');
      showNotification(`Sample processed! Tender ID: ${data.tender_id}`, 'success');
      fetchTenders();
    } catch (err) {
      showNotification(`Error: ${err.message}`, 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleBatchUpload = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    if (files.length > 25) {
      showNotification('Maximum 25 files allowed per batch.', 'error');
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      if (files[i].type !== 'application/pdf') {
        showNotification('Only PDF files are allowed.', 'error');
        return;
      }
      formData.append('files', files[i]);
    }

    setBatchUploading(true);
    setBatchTenders([]);
    setBatchSelectedTender(null);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/scan-batch`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Batch upload failed');

      showNotification(`Batch analysis complete! Processed ${data.results?.length || 0} documents.`, 'success');
      setBatchTenders(data.results || []);
    } catch (err) {
      setError(`Batch Error: ${err.message}`);
    } finally {
      setBatchUploading(false);
    }
    event.target.value = null;
  };

  const displayTenders = activeTab === 'dashboard' ? tenders : batchTenders;
  const displaySelected = activeTab === 'dashboard' ? selectedTender : batchSelectedTender;
  const setDisplaySelected = activeTab === 'dashboard' ? setSelectedTender : setBatchSelectedTender;
  const isDisplayLoading = activeTab === 'dashboard' ? loading : batchUploading;

  const getReasoningText = (t) => {
    const dh = t.dept_hhi_label;
    const ch = t.category_hhi_label;
    const dev = t.eligibility_deviation_score;
    const devStr = dev !== null ? (dev > 0.4 ? `high (${dev.toFixed(3)} > 0.4)` : `low (${dev.toFixed(3)} ≤ 0.4)`) : 'unavailable';
    return `${t.pattern_classification}: Department concentration is ${dh} (${t.dept_hhi}), Category concentration is ${ch} (${t.category_hhi}), and semantic eligibility deviation is ${devStr}.`;
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-sans transition-colors duration-200 motion-reduce:transition-none">
      <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-300 dark:border-slate-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-indigo-900 dark:text-indigo-300 shrink-0">
                <Logo size={24} />
                <h1 className="text-xl font-serif font-bold tracking-tight">Spasht</h1>
              </div>

              <nav className="flex gap-1 overflow-x-auto">
                <button
                  onClick={() => { setActiveTab('dashboard'); setError(null); }}
                  className={`whitespace-nowrap px-3 py-1.5 text-sm font-medium rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500 outline-none ${activeTab === 'dashboard' ? 'bg-slate-100 dark:bg-slate-700 text-indigo-900 dark:text-indigo-100' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                >
                  Shared Ledger
                </button>
                <button
                  onClick={() => { setActiveTab('batch'); setError(null); }}
                  className={`whitespace-nowrap px-3 py-1.5 text-sm font-medium rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500 outline-none ${activeTab === 'batch' ? 'bg-slate-100 dark:bg-slate-700 text-indigo-900 dark:text-indigo-100' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                >
                  Isolated Batch Analysis
                </button>
              </nav>
            </div>

            <div className="flex items-center gap-2 md:gap-4 self-end md:self-auto w-full md:w-auto justify-end">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 focus-visible:ring-2 focus-visible:ring-indigo-500 outline-none transition-colors shrink-0"
                aria-label="Toggle Theme"
              >
                {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
              </button>

              {activeTab === 'dashboard' ? (
                <>
                  {samples.length > 0 && (
                    <div className="relative shrink-0">
                      <button
                        onClick={() => setShowSamples(!showSamples)}
                        className="bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 min-h-[44px] px-3 sm:px-4 py-2 rounded shadow-sm text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-600 focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-1 dark:focus-visible:ring-offset-slate-800 outline-none transition-colors flex items-center gap-2"
                        disabled={uploading}
                      >
                        <span className="hidden sm:inline">Load Sample</span>
                        <span className="sm:hidden">Sample</span>
                        <ChevronDown size={16} />
                      </button>
                      {showSamples && (
                        <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded shadow-lg z-20 py-1">
                          {samples.map(s => (
                            <button
                              key={s}
                              onClick={() => handleSampleUpload(s)}
                              className="w-full text-left px-4 py-3 min-h-[44px] text-sm text-slate-700 dark:text-slate-300 hover:bg-indigo-50 dark:hover:bg-slate-700 focus-visible:bg-indigo-50 dark:focus-visible:bg-slate-700 outline-none truncate"
                              title={s}
                            >
                              {s}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <label key="single-upload" className="shrink-0 cursor-pointer bg-indigo-900 hover:bg-indigo-800 dark:bg-indigo-300 dark:hover:bg-indigo-400 dark:text-indigo-950 text-indigo-50 min-h-[44px] px-3 sm:px-4 py-2 rounded shadow-sm text-sm font-medium focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500 dark:focus-within:ring-offset-slate-800 transition-colors flex items-center gap-2">
                    {uploading ? (
                      <>
                        <UploadCloud size={18} className="animate-bounce" />
                        <span className="hidden sm:inline">Scanning...</span>
                      </>
                    ) : (
                      <>
                        <UploadCloud size={18} />
                        <span className="hidden sm:inline">Scan Award Document</span>
                        <span className="sm:hidden">Scan</span>
                      </>
                    )}
                    <input type="file" className="hidden" accept=".pdf" onChange={handleFileUpload} disabled={uploading} />
                  </label>
                </>
              ) : (
                <label key="batch-upload" className="shrink-0 cursor-pointer bg-indigo-900 hover:bg-indigo-800 dark:bg-indigo-300 dark:hover:bg-indigo-400 dark:text-indigo-950 text-indigo-50 min-h-[44px] px-3 sm:px-4 py-2 rounded shadow-sm text-sm font-medium focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500 dark:focus-within:ring-offset-slate-800 transition-colors flex items-center gap-2">
                  {batchUploading ? (
                    <>
                      <UploadCloud size={18} className="animate-bounce" />
                      <span className="hidden sm:inline">Processing Batch...</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud size={18} />
                      <span className="hidden sm:inline">Upload Batch (Max 25)</span>
                      <span className="sm:hidden">Upload Batch</span>
                    </>
                  )}
                  <input type="file" className="hidden" accept=".pdf" multiple onChange={handleBatchUpload} disabled={batchUploading} />
                </label>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Column: Dashboard List */}
        <div className={`flex-1 flex flex-col gap-4 ${displaySelected ? 'hidden lg:flex lg:w-3/5 xl:w-2/3' : 'w-full'}`}>
          <h2 className="text-xl font-serif font-bold text-slate-800 dark:text-slate-200">
            {activeTab === 'dashboard' ? 'Public Procurement Records' : 'Batch Analysis Results'}
          </h2>

          {activeTab === 'batch' && (
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 p-4 rounded text-sm text-blue-800 dark:text-blue-200 flex items-start gap-3 shadow-sm">
              <Info size={20} className="shrink-0 mt-0.5 text-blue-600 dark:text-blue-400" />
              <p>
                <strong>Isolated Analysis Mode:</strong> Scores shown below are computed <em>strictly relative to this uploaded batch of {displayTenders.length} documents</em>.
                They are <strong>not</strong> compared against the full seeded dataset. An extreme concentration score here may simply reflect a small sample size.
              </p>
            </div>
          )}

          {error && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-4 rounded border border-red-200 dark:border-red-800">{error}</div>}

          {activeTab === 'dashboard' && backendWakingUp && !error && (
            <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 p-4 rounded text-sm text-amber-800 dark:text-amber-200 flex items-start gap-3 shadow-sm mb-4">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-amber-600 dark:border-amber-400 shrink-0 mt-0.5"></div>
              <p>
                <strong>Backend is waking up:</strong> The server is on a free tier and is currently waking up from sleep. This may take up to a minute. Loading data in the background...
              </p>
            </div>
          )}

          {isDisplayLoading ? (
            <div className="flex flex-col gap-3 animate-pulse">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 bg-slate-200 dark:bg-slate-800 rounded w-full"></div>
              ))}
            </div>
          ) : (
            <>
              {/* Mobile Card Layout */}
              <div className="lg:hidden flex flex-col gap-4">
                {displayTenders.map((t) => (
                  <button
                    key={t.tender_id}
                    onClick={() => { setDisplaySelected(t); setShowReasoning(false); }}
                    className={`w-full text-left p-4 rounded-lg border shadow-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500 ${displaySelected?.tender_id === t.tender_id
                      ? 'bg-indigo-50 dark:bg-slate-700 border-indigo-200 dark:border-indigo-600'
                      : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-500'
                      }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="font-mono text-xs font-semibold text-slate-500 dark:text-slate-400">#{t.tender_id}</span>
                        <h3 className="font-medium text-slate-900 dark:text-slate-100">{t.department}</h3>
                      </div>
                      <PatternBadge pattern={t.pattern_classification} />
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                      {t.category}
                    </div>
                    <div className="text-sm mb-4">
                      <span className="text-slate-500 dark:text-slate-400">Awarded to: </span>
                      <span className="font-semibold text-slate-900 dark:text-slate-100">{t.winning_vendor || 'N/A'}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-100 dark:border-slate-700">
                      <div>
                        <div className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Concentration</div>
                        <div className="flex items-baseline gap-1">
                          <span className="font-mono text-sm font-semibold">{t.category_hhi}</span>
                          <span className="text-xs text-slate-500">HHI</span>
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Deviation</div>
                        <div className="flex items-baseline gap-1">
                          {t.eligibility_deviation_score !== null ? (
                            <span className="font-mono text-sm font-semibold">{t.eligibility_deviation_score.toFixed(3)}</span>
                          ) : (
                            <span className="font-mono text-sm font-semibold text-slate-400">N/A</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
                {displayTenders.length === 0 && (
                  <div className="bg-white dark:bg-slate-800 rounded border border-slate-300 dark:border-slate-700 p-8 text-center text-slate-500 dark:text-slate-400">
                    <div className="flex flex-col items-center gap-3">
                      <FileText size={32} className="text-slate-300 dark:text-slate-600" />
                      <p>{activeTab === 'dashboard' ? (backendWakingUp ? 'Waiting for backend...' : 'No procurement records found.') : 'No batch results yet.'}</p>
                      <p className="text-xs">
                        {activeTab === 'dashboard' ? (backendWakingUp ? 'The results will appear here automatically once the server is ready.' : 'Scan an award document or load a sample to begin analysis.') : 'Upload a batch of up to 25 PDF documents to analyze them together.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Desktop Table Layout */}
              <div className="hidden lg:block bg-white dark:bg-slate-800 rounded border border-slate-300 dark:border-slate-700 overflow-hidden shadow-sm">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-300 dark:border-slate-700">
                    <tr>
                      <th className="px-4 py-3">Record ID</th>
                      <th className="px-4 py-3">Context</th>
                      <th className="px-4 py-3">Awarded Vendor</th>
                      <th className="px-4 py-3">Analysis Pattern</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                    {displayTenders.map((t) => (
                      <tr
                        key={t.tender_id}
                        onClick={() => { setDisplaySelected(t); setShowReasoning(false); }}
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setDisplaySelected(t);
                            setShowReasoning(false);
                          }
                        }}
                        className={`cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${displaySelected?.tender_id === t.tender_id ? 'bg-indigo-50 dark:bg-slate-700' : ''}`}
                      >
                        <td className="px-4 py-3 font-mono font-medium text-slate-600 dark:text-slate-400">#{t.tender_id}</td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-slate-900 dark:text-slate-100">{t.department}</div>
                          <div className="text-slate-500 dark:text-slate-400 text-xs">{t.category}</div>
                        </td>
                        <td className="px-4 py-3 text-slate-800 dark:text-slate-200">{t.winning_vendor || 'N/A'}</td>
                        <td className="px-4 py-3">
                          <PatternBadge pattern={t.pattern_classification} />
                        </td>
                      </tr>
                    ))}
                    {displayTenders.length === 0 && (
                      <tr>
                        <td colSpan="4" className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                          <div className="flex flex-col items-center gap-3">
                            <FileText size={32} className="text-slate-300 dark:text-slate-600" />
                            <p>{activeTab === 'dashboard' ? (backendWakingUp ? 'Waiting for backend...' : 'No procurement records found.') : 'No batch results yet.'}</p>
                            <p className="text-xs">
                              {activeTab === 'dashboard' ? (backendWakingUp ? 'The results will appear here automatically once the server is ready.' : 'Scan an award document or load a sample to begin analysis.') : 'Upload a batch of up to 25 PDF documents to analyze them together.'}
                            </p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        {/* Right Column: The Evidence Ledger */}
        {displaySelected && (
          <div className="fixed inset-0 z-50 lg:static lg:w-2/5 xl:w-1/3 bg-white dark:bg-slate-800 lg:rounded lg:border border-slate-300 dark:border-slate-700 flex flex-col lg:sticky top-24 shadow-2xl lg:shadow-md transition-all">
            <div className="p-4 border-b border-slate-300 dark:border-slate-700 flex justify-between items-center bg-slate-100 dark:bg-slate-900 lg:rounded-t">
              <h3 className="font-serif font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Evidence Ledger: <span className="font-mono text-indigo-700 dark:text-indigo-400">#{displaySelected.tender_id}</span>
              </h3>
              <button
                onClick={() => setDisplaySelected(null)}
                className="text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 p-2 -mr-2 rounded text-sm font-semibold focus-visible:ring-2 focus-visible:ring-indigo-500 outline-none lg:hidden transition-colors"
                aria-label="Close"
              >
                Close
              </button>
            </div>

            <div className="p-5 flex flex-col gap-6 overflow-y-auto flex-1 lg:max-h-[calc(100vh-140px)]">
              {/* Top classification banner */}
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <PatternBadge pattern={displaySelected.pattern_classification} className="text-sm py-1.5 px-3" />
                  <button
                    onClick={() => setShowReasoning(!showReasoning)}
                    className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 focus-visible:ring-2 focus-visible:ring-indigo-500 outline-none rounded p-1 transition-colors"
                    aria-label="Toggle Reasoning"
                  >
                    <Info size={18} />
                  </button>
                </div>

                {showReasoning && (
                  <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 p-3 rounded text-sm text-indigo-900 dark:text-indigo-200 leading-relaxed shadow-inner">
                    <strong>Reasoning:</strong> {getReasoningText(displaySelected)}
                  </div>
                )}
              </div>

              {/* Context */}
              <div className="border-l-2 border-slate-300 dark:border-slate-600 pl-3">
                <div className="text-sm font-medium text-slate-600 dark:text-slate-400 uppercase tracking-widest mb-1">Context</div>
                <div className="text-base font-bold text-slate-900 dark:text-slate-100">{displaySelected.department}</div>
                <div className="text-sm text-slate-700 dark:text-slate-300">{displaySelected.category}</div>
                <div className="mt-2 text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Awarded to:</span> <span className="font-semibold text-slate-900 dark:text-slate-100">{displaySelected.winning_vendor}</span>
                </div>
              </div>

              {displaySelected.single_bidder_flag && (
                <div className="flex items-start gap-2 text-amber-900 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 p-3 rounded border border-amber-200 dark:border-amber-800 text-sm shadow-sm">
                  <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                  <span>This tender received <strong>exactly 1 bid</strong>.</span>
                </div>
              )}

              {/* TRANSPARENCY REQUIREMENT: Strictly separated score displays side-by-side or stacked cleanly */}
              <div className="flex flex-col gap-4">
                <div className="text-sm font-medium text-slate-600 dark:text-slate-400 uppercase tracking-widest border-b border-slate-200 dark:border-slate-700 pb-1">Raw Evidence</div>

                <div className="flex flex-col sm:flex-row gap-4">
                  {/* Score 1: Concentration (HHI) */}
                  <div className="flex-1 p-3 rounded border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 shadow-sm">
                    <h4 className="font-bold text-slate-900 dark:text-slate-100 mb-2 text-sm">Concentration (HHI)</h4>
                    <div className="flex justify-between items-baseline mb-1">
                      <span className="text-xs text-slate-600 dark:text-slate-400">Category:</span>
                      <span className="font-mono font-bold text-slate-900 dark:text-slate-100 text-base">{displaySelected.category_hhi}</span>
                    </div>
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs text-slate-600 dark:text-slate-400">Dept:</span>
                      <span className="font-mono font-bold text-slate-900 dark:text-slate-100 text-base">{displaySelected.dept_hhi}</span>
                    </div>
                  </div>

                  {/* Score 2: Eligibility Text Deviation */}
                  <div className="flex-1 p-3 rounded border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 shadow-sm flex flex-col">
                    <h4 className="font-bold text-slate-900 dark:text-slate-100 mb-2 text-sm">Deviation Score</h4>
                    <div className="flex justify-between items-baseline flex-1">
                      <span className="text-xs text-slate-600 dark:text-slate-400">Semantic:</span>
                      {displaySelected.eligibility_deviation_score !== null ? (
                        <span className="font-mono font-bold text-slate-900 dark:text-slate-100 text-base">
                          {displaySelected.eligibility_deviation_score.toFixed(3)}
                        </span>
                      ) : (
                        <span className="font-mono font-bold text-slate-500 dark:text-slate-500 text-base">N/A</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  <strong>Notice:</strong> These signals are derived strictly from computational comparisons and are for investigative prioritization only. They do not constitute proof of wrongdoing.
                </p>
              </div>

            </div>
          </div>
        )}
      </main>

      {/* Notification Toast */}
      {notification && (
        <div className={`fixed bottom-4 right-4 max-w-sm w-full shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5 transition-all transform z-50 ${notification.type === 'error' ? 'bg-red-50 dark:bg-red-900 border-l-4 border-red-500' :
          notification.type === 'success' ? 'bg-emerald-50 dark:bg-emerald-900 border-l-4 border-emerald-500' :
            'bg-blue-50 dark:bg-blue-900 border-l-4 border-blue-500'
          }`}>
          <div className="flex-1 w-0 p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 pt-0.5">
                {notification.type === 'error' && <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />}
                {notification.type === 'success' && <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />}
                {notification.type === 'info' && <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
              </div>
              <div className="ml-3 flex-1">
                <p className={`text-sm font-medium ${notification.type === 'error' ? 'text-red-800 dark:text-red-200' :
                  notification.type === 'success' ? 'text-emerald-800 dark:text-emerald-200' :
                    'text-blue-800 dark:text-blue-200'
                  }`}>
                  {notification.message}
                </p>
              </div>
            </div>
          </div>
          <div className="flex border-l border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setNotification(null)}
              className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-500 dark:hover:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
