import React, { useState } from 'react';

export default function App() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [isSourcesOpen, setIsSourcesOpen] = useState(true);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();
      setResult({ question, answer: data.answer, sources: data.sources });
      setIsSourcesOpen(true);
    } catch (err) {
      console.error('API Error:', err);
      setResult({ question, answer: 'Connection to backend API failed. Ensure port 8000 is active.', sources: [] });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-gray-100 font-sans relative overflow-hidden flex flex-col items-center">
      
      {/* Luxury Ambient Lighting */}
      <div className="fixed top-[-30%] left-[-10%] w-[60%] h-[60%] bg-red-900/10 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="fixed bottom-[-30%] right-[-10%] w-[60%] h-[60%] bg-amber-700/10 blur-[120px] rounded-full pointer-events-none"></div>

      {/* Glassy Header */}
      <header className="w-full max-w-6xl mt-8 px-8 py-4 bg-white/[0.02] backdrop-blur-3xl border border-white/10 rounded-2xl flex justify-between items-center z-10 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-4">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(239,68,68,0.8)]"></div>
          <h1 className="text-xl font-light tracking-[0.3em] text-white uppercase">
            Byte<span className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-red-500">Vox</span>
          </h1>
        </div>
        <div className="flex gap-4">
          <span className="text-xs tracking-widest uppercase text-amber-500/80 border border-amber-500/20 px-4 py-1.5 rounded-md bg-amber-500/5">
            System Status: Online
          </span>
        </div>
      </header>

      {/* Central Command Interface */}
      <main className={`w-full max-w-5xl px-6 relative z-10 transition-all duration-700 ease-[cubic-bezier(0.4,0,0.2,1)] ${result ? 'mt-12' : 'mt-[25vh]'}`}>
        
        {/* Search Input Panel */}
        <div className="w-full group">
          <form onSubmit={handleQuery} className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-red-800/40 to-amber-600/40 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition duration-700"></div>
            <div className="relative flex bg-[#0a0a0a]/80 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden focus-within:border-amber-500/50 transition-colors">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Query the Nexus Knowledge Graph..."
                className="flex-1 bg-transparent px-8 py-6 text-lg font-light text-white placeholder-gray-600 focus:outline-none"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="px-12 bg-gradient-to-r from-red-900 to-red-800 hover:from-red-800 hover:to-red-700 border-l border-white/10 text-white text-sm font-semibold tracking-[0.2em] uppercase transition-all disabled:opacity-50"
              >
                {loading ? 'Processing' : 'Execute'}
              </button>
            </div>
          </form>
        </div>

        {/* Dynamic Door-Opening Results Container */}
        <div className={`w-full grid transition-[grid-template-rows] duration-1000 ease-[cubic-bezier(0.4,0,0.2,1)] ${result ? 'grid-rows-[1fr] mt-8' : 'grid-rows-[0fr] mt-0'}`}>
          <div className="overflow-hidden">
            {result && (
              <div className="bg-white/[0.02] backdrop-blur-3xl border border-white/10 rounded-3xl overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.5)] flex flex-col md:flex-row">
                
                {/* Left Column: AI Response */}
                <div className="flex-1 p-10 border-b md:border-b-0 md:border-r border-white/10 relative">
                  <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-amber-500/30 to-transparent"></div>
                  
                  <h3 className="text-[10px] tracking-[0.3em] text-red-400 uppercase mb-6 flex items-center gap-3">
                    <span className="w-8 h-[1px] bg-red-400/50"></span>
                    Synthesized Intelligence
                  </h3>
                  
                  <p className="text-lg font-light leading-relaxed text-gray-200 whitespace-pre-line">
                    {result.answer}
                  </p>
                </div>

                {/* Right Column: Source Grounding */}
                <div className="w-full md:w-80 bg-black/40 p-8 flex flex-col">
                  <button 
                    onClick={() => setIsSourcesOpen(!isSourcesOpen)}
                    className="w-full flex items-center justify-between outline-none cursor-pointer group"
                  >
                    <h3 className="text-[10px] tracking-[0.3em] text-amber-500 uppercase flex items-center gap-3">
                      <span className="w-4 h-[1px] bg-amber-500/50"></span>
                      Vector Sources
                    </h3>
                    <span className={`text-amber-500 transition-transform duration-500 ${isSourcesOpen ? 'rotate-180' : ''}`}>
                      ▼
                    </span>
                  </button>

                  {/* Nested Accordion Animation for Sources */}
                  <div className={`grid transition-[grid-template-rows] duration-700 ease-[cubic-bezier(0.4,0,0.2,1)] ${isSourcesOpen ? 'grid-rows-[1fr] mt-6' : 'grid-rows-[0fr] mt-0'}`}>
                    <div className="overflow-hidden flex flex-col gap-3">
                      {result.sources.length > 0 ? (
                        result.sources.map((source, idx) => (
                          <div key={idx} className="bg-white/5 border border-white/10 p-3 rounded-lg flex items-center gap-3 hover:bg-white/10 transition-colors">
                            <div className="w-8 h-8 rounded bg-red-900/30 border border-red-500/20 flex items-center justify-center">
                              <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                            </div>
                            <span className="text-xs font-mono text-gray-300 truncate">{source}</span>
                          </div>
                        ))
                      ) : (
                        <span className="text-xs font-mono text-gray-500">No telemetry data.</span>
                      )}
                    </div>
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}