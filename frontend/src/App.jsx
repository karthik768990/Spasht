import React, { useState, useEffect } from 'react';
import { UploadCloud, AlertTriangle, FileText, Activity, Moon, Sun, ChevronDown, Info, CheckCircle2, AlertCircle, TrendingUp, AlertOctagon, MinusCircle } from 'lucide-react';

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
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [samples, setSamples] = useState([]);
  const [showSamples, setShowSamples] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(theme === 'light' ? 'dark' : 'light');

  const fetchTenders = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/tenders`);
      if (!res.ok) throw new Error('Failed to fetch tenders');
      const data = await res.json();
      setTenders(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSamples = async () => {
    try {
      const res = await fetch(`${API_BASE}/upload/samples`);
      if (res.ok) {
        const data = await res.json();
        setSamples(data.samples || []);
      }
    } catch (err) {
      console.error("Failed to fetch samples", err);
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
      alert('Only PDF files are allowed.');
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
      alert(`Scan complete! Tender ID: ${data.tender_id}`);
      fetchTenders();
    } catch (err) {
      alert(`Error: ${err.message}`);
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
      alert(`Sample processed! Tender ID: ${data.tender_id}`);
      fetchTenders();
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

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
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2 text-indigo-900 dark:text-indigo-300">
            <Activity size={24} />
            <h1 className="text-xl font-serif font-bold tracking-tight">Spasht | Civic Ledger</h1>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={toggleTheme} 
              className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 focus-visible:ring-2 focus-visible:ring-indigo-500 outline-none transition-colors"
              aria-label="Toggle Theme"
            >
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>
            
            {samples.length > 0 && (
              <div className="relative">
                <button 
                  onClick={() => setShowSamples(!showSamples)}
                  className="bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 px-4 py-2 rounded shadow-sm text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-600 focus-visible:ring-2 focus-visible:ring-indigo-500 outline-none transition-colors flex items-center gap-2"
                  disabled={uploading}
                >
                  Load Sample <ChevronDown size={16} />
                </button>
                {showSamples && (
                  <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded shadow-lg z-20 py-1">
                    {samples.map(s => (
                      <button 
                        key={s}
                        onClick={() => handleSampleUpload(s)}
                        className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-indigo-50 dark:hover:bg-slate-700 focus-visible:bg-indigo-50 dark:focus-visible:bg-slate-700 outline-none truncate"
                        title={s}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            <label className="cursor-pointer bg-indigo-900 hover:bg-indigo-800 dark:bg-indigo-300 dark:hover:bg-indigo-400 dark:text-indigo-950 text-indigo-50 px-4 py-2 rounded shadow-sm text-sm font-medium focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500 transition-colors flex items-center gap-2">
              {uploading ? 'Scanning...' : <><UploadCloud size={18} /> Scan Award Document</>}
              <input type="file" className="hidden" accept=".pdf" onChange={handleFileUpload} disabled={uploading} />
            </label>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Column: Dashboard List */}
        <div className={`flex-1 flex flex-col gap-4 ${selectedTender ? 'hidden lg:flex lg:w-3/5 xl:w-2/3' : 'w-full'}`}>
          <h2 className="text-xl font-serif font-bold text-slate-800 dark:text-slate-200">Public Procurement Records</h2>
          
          {error && <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-4 rounded border border-red-200 dark:border-red-800">{error}</div>}
          
          {loading ? (
            <div className="flex flex-col gap-3 animate-pulse">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 bg-slate-200 dark:bg-slate-800 rounded w-full"></div>
              ))}
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded border border-slate-300 dark:border-slate-700 overflow-hidden shadow-sm">
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
                  {tenders.map((t) => (
                    <tr 
                      key={t.tender_id} 
                      onClick={() => { setSelectedTender(t); setShowReasoning(false); }}
                      className={`cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${selectedTender?.tender_id === t.tender_id ? 'bg-indigo-50 dark:bg-slate-700' : ''}`}
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
                  {tenders.length === 0 && (
                    <tr>
                      <td colSpan="4" className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                        <div className="flex flex-col items-center gap-3">
                          <FileText size={32} className="text-slate-300 dark:text-slate-600" />
                          <p>No procurement records found.</p>
                          <p className="text-xs">Scan an award document or load a sample to begin analysis.</p>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right Column: The Evidence Ledger */}
        {selectedTender && (
          <div className="w-full lg:w-2/5 xl:w-1/3 bg-white dark:bg-slate-800 rounded border border-slate-300 dark:border-slate-700 flex flex-col sticky top-24 shadow-md">
            <div className="p-4 border-b border-slate-300 dark:border-slate-700 flex justify-between items-center bg-slate-100 dark:bg-slate-900 rounded-t">
              <h3 className="font-serif font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Evidence Ledger: <span className="font-mono text-indigo-700 dark:text-indigo-400">#{selectedTender.tender_id}</span>
              </h3>
              <button 
                onClick={() => setSelectedTender(null)}
                className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 text-sm font-semibold focus-visible:ring-2 focus-visible:ring-indigo-500 outline-none lg:hidden"
              >
                Close
              </button>
            </div>
            
            <div className="p-5 flex flex-col gap-6 overflow-y-auto max-h-[calc(100vh-140px)]">
              {/* Top classification banner */}
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <PatternBadge pattern={selectedTender.pattern_classification} className="text-sm py-1.5 px-3" />
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
                    <strong>Reasoning:</strong> {getReasoningText(selectedTender)}
                  </div>
                )}
              </div>

              {/* Context */}
              <div className="border-l-2 border-slate-300 dark:border-slate-600 pl-3">
                <div className="text-sm font-medium text-slate-600 dark:text-slate-400 uppercase tracking-widest mb-1">Context</div>
                <div className="text-base font-bold text-slate-900 dark:text-slate-100">{selectedTender.department}</div>
                <div className="text-sm text-slate-700 dark:text-slate-300">{selectedTender.category}</div>
                <div className="mt-2 text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Awarded to:</span> <span className="font-semibold text-slate-900 dark:text-slate-100">{selectedTender.winning_vendor}</span>
                </div>
              </div>

              {selectedTender.single_bidder_flag && (
                <div className="flex items-start gap-2 text-amber-900 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 p-3 rounded border border-amber-200 dark:border-amber-800 text-sm shadow-sm">
                  <AlertTriangle size={16} className="mt-0.5 shrink-0"/>
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
                      <span className="font-mono font-bold text-slate-900 dark:text-slate-100 text-base">{selectedTender.category_hhi}</span>
                    </div>
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs text-slate-600 dark:text-slate-400">Dept:</span>
                      <span className="font-mono font-bold text-slate-900 dark:text-slate-100 text-base">{selectedTender.dept_hhi}</span>
                    </div>
                  </div>

                  {/* Score 2: Eligibility Text Deviation */}
                  <div className="flex-1 p-3 rounded border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50 shadow-sm flex flex-col">
                    <h4 className="font-bold text-slate-900 dark:text-slate-100 mb-2 text-sm">Deviation Score</h4>
                    <div className="flex justify-between items-baseline flex-1">
                      <span className="text-xs text-slate-600 dark:text-slate-400">Semantic:</span>
                      {selectedTender.eligibility_deviation_score !== null ? (
                        <span className="font-mono font-bold text-slate-900 dark:text-slate-100 text-base">
                          {selectedTender.eligibility_deviation_score.toFixed(3)}
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
    </div>
  );
}

export default App;
