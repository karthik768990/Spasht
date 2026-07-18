import React, { useState, useEffect } from 'react';
import { UploadCloud, AlertTriangle, CheckCircle, FileText, Activity } from 'lucide-react';

const API_BASE = '/api';

function App() {
  const [tenders, setTenders] = useState([]);
  const [selectedTender, setSelectedTender] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

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

  useEffect(() => {
    fetchTenders();
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
      alert(`Upload successful! Tender ID: ${data.tender_id}`);
      fetchTenders();
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
    // reset input
    event.target.value = null;
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      <header className="bg-white shadow-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2 text-indigo-600">
            <Activity size={24} />
            <h1 className="text-xl font-bold tracking-tight">Spasht | Procurement Monitor</h1>
          </div>
          <div>
            <label className="cursor-pointer bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md shadow-sm text-sm font-medium transition flex items-center gap-2">
              {uploading ? 'Processing...' : <><UploadCloud size={18} /> Upload Award PDF</>}
              <input type="file" className="hidden" accept=".pdf" onChange={handleFileUpload} disabled={uploading} />
            </label>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 flex gap-6 items-start">
        {/* Left Column: Dashboard List */}
        <div className={`flex-1 flex flex-col gap-4 ${selectedTender ? 'hidden lg:flex lg:w-2/3' : 'w-full'}`}>
          <h2 className="text-lg font-semibold text-slate-800">Recent Tender Awards</h2>
          
          {error && <div className="bg-red-50 text-red-700 p-3 rounded-md border border-red-200">{error}</div>}
          
          {loading ? (
            <div className="text-slate-500 animate-pulse">Loading data...</div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-100 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">ID / Ref</th>
                    <th className="px-4 py-3">Department & Category</th>
                    <th className="px-4 py-3">Winner</th>
                    <th className="px-4 py-3">Concentration (HHI)</th>
                    <th className="px-4 py-3">Eligibility Dev.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {tenders.map((t) => (
                    <tr 
                      key={t.tender_id} 
                      onClick={() => setSelectedTender(t)}
                      className={`cursor-pointer hover:bg-indigo-50 transition ${selectedTender?.tender_id === t.tender_id ? 'bg-indigo-50' : ''}`}
                    >
                      <td className="px-4 py-3 font-medium text-indigo-600">#{t.tender_id}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-800">{t.department}</div>
                        <div className="text-slate-500 text-xs">{t.category}</div>
                      </td>
                      <td className="px-4 py-3">{t.winning_vendor || 'N/A'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${t.category_hhi_label.includes('HIGH') ? 'bg-red-100 text-red-700' : t.category_hhi_label.includes('INSUFFICIENT') ? 'bg-slate-100 text-slate-600' : t.category_hhi_label.includes('moderate') ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                          {t.category_hhi_label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {t.eligibility_deviation_score !== null ? t.eligibility_deviation_score.toFixed(3) : 'N/A'}
                      </td>
                    </tr>
                  ))}
                  {tenders.length === 0 && (
                    <tr>
                      <td colSpan="5" className="px-4 py-8 text-center text-slate-500">
                        No tenders found. Upload a document to get started.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right Column: Tender Details (Two-Score Transparency) */}
        {selectedTender && (
          <div className="w-full lg:w-1/3 bg-white rounded-lg shadow-md border border-slate-200 flex flex-col sticky top-24">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 rounded-t-lg">
              <h3 className="font-bold text-slate-800 flex items-center gap-2">
                <FileText size={18} className="text-indigo-600"/>
                Tender #{selectedTender.tender_id} Analysis
              </h3>
              <button 
                onClick={() => setSelectedTender(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-semibold lg:hidden"
              >
                Close
              </button>
            </div>
            
            <div className="p-4 flex flex-col gap-6 overflow-y-auto max-h-[calc(100vh-140px)]">
              <div>
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Context</div>
                <div className="text-lg font-bold text-slate-900">{selectedTender.department}</div>
                <div className="text-sm font-medium text-slate-600">{selectedTender.category}</div>
                <div className="mt-2 text-sm">
                  <span className="text-slate-500">Awarded to:</span> <span className="font-semibold text-slate-800">{selectedTender.winning_vendor}</span>
                </div>
                {selectedTender.single_bidder_flag && (
                  <div className="mt-3 flex items-start gap-2 text-amber-700 bg-amber-50 p-2 rounded border border-amber-200 text-xs">
                    <AlertTriangle size={14} className="mt-0.5 shrink-0"/>
                    This tender received exactly 1 bid.
                  </div>
                )}
              </div>

              {/* TRANSPARENCY REQUIREMENT: Strictly separated score displays */}
              <div className="space-y-4">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Independent Risk Signals</div>
                
                {/* Score 1: Concentration (HHI) */}
                <div className="p-4 rounded-lg border border-slate-200 bg-slate-50">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-bold text-slate-800">Vendor Concentration</h4>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${selectedTender.category_hhi_label.includes('HIGH') ? 'bg-red-100 text-red-700' : selectedTender.category_hhi_label.includes('INSUFFICIENT') ? 'bg-slate-200 text-slate-700' : selectedTender.category_hhi_label.includes('moderate') ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                      {selectedTender.category_hhi_label}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-3">
                    Herfindahl-Hirschman Index (HHI) measures structural monopoly risk across historical wins.
                  </p>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Category HHI:</span>
                    <span className="font-mono font-semibold">{selectedTender.category_hhi}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Department HHI:</span>
                    <span className="font-mono font-semibold">{selectedTender.dept_hhi}</span>
                  </div>
                </div>

                {/* Score 2: Eligibility Text Deviation */}
                <div className="p-4 rounded-lg border border-slate-200 bg-slate-50">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-bold text-slate-800">Eligibility Criteria Deviation</h4>
                    {selectedTender.eligibility_deviation_score !== null ? (
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${selectedTender.eligibility_deviation_score > 0.4 ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>
                        {selectedTender.eligibility_deviation_score.toFixed(3)}
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-slate-200 text-slate-700">N/A</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    Semantic deviation (SBERT) from this category's baseline requirements. Higher scores indicate unusually narrow/restrictive criteria.
                    {selectedTender.eligibility_deviation_score === null && " (Insufficient peer tenders to compare against)."}
                  </p>
                </div>
              </div>
              
              <div className="pt-2">
                <p className="text-xs text-slate-400 italic text-center">
                  Notice: These signals are for investigative prioritization only and do not constitute proof of wrongdoing.
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
