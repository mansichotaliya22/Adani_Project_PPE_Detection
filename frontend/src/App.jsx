import React, { useState, useEffect, useRef } from 'react';
import { 
  Shield, 
  Users, 
  AlertTriangle, 
  Activity, 
  Settings, 
  Play, 
  Square, 
  Bell, 
  Mail,
  Camera,
  Map,
  ChevronRight,
  RefreshCcw,
  Info
} from 'lucide-react';

const API_BASE = 'http://localhost:8001';

function App() {
  const [videoUrl, setVideoUrl] = useState(null);
  const wsRef = useRef(null);

  // Safe default states to prevent ReferenceErrors during first render
  const [stats, setStats] = useState({ 
    people_count: 0, 
    ppe_violations: 0, 
    ppe_current: 0,
    roi_violations: 0, 
    running: false 
  });
  
  const [violations, setViolations] = useState([]);
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('live');
  
  const [settings, setSettings] = useState({
    conf_threshold: 0.5,
    work_area: 'Factory',
    email_alerts: false,
    source: '0'
  });

  // WebSocket for video feed
  useEffect(() => {
    if (stats?.running) {
      const ws = new WebSocket(`ws://${window.location.hostname}:8001/ws/video`);
      ws.binaryType = 'blob';
      
      ws.onmessage = (event) => {
        if (videoUrl) URL.revokeObjectURL(videoUrl);
        setVideoUrl(URL.createObjectURL(event.data));
      };
      
      wsRef.current = ws;
      return () => {
        if (ws.readyState === WebSocket.OPEN) ws.close();
        if (videoUrl) URL.revokeObjectURL(videoUrl);
      };
    } else {
      setVideoUrl(null);
    }
  }, [stats?.running]);

  // Polling for stats and violations
  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_BASE}/api/stats`)
        .then(res => res.json())
        .then(data => {
            if (data) setStats(data);
        })
        .catch(err => console.error("Stats fetch error:", err));

      fetch(`${API_BASE}/api/violations?limit=10`)
        .then(res => res.json())
        .then(data => {
            if (data) setViolations(data);
        })
        .catch(err => console.error("Violations fetch error:", err));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    try {
      await fetch(`${API_BASE}/api/start?source=${settings?.source ?? '0'}&conf=${settings?.conf_threshold ?? 0.5}`, { method: 'POST' });
    } catch (err) {
      console.error("Start error:", err);
    }
  };

  const handleStop = async () => {
    try {
      await fetch(`${API_BASE}/api/stop`, { method: 'POST' });
    } catch (err) {
      console.error("Stop error:", err);
    }
  };

  const updateSetting = async (key, value) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    try {
      await fetch(`${API_BASE}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });
    } catch (err) {
      console.error("Settings update error:", err);
    }
  };

  // Loading Guard: Prevent rendering if critical state is missing
  if (!stats) {
    return (
        <div className="h-screen w-full bg-slate-950 flex flex-col items-center justify-center gap-4">
            <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-400 font-medium animate-pulse">Connecting to SafeSight AI...</p>
        </div>
    );
  }

  return (
    <div style={{background: 'linear-gradient(135deg, #1B3C53, #234C6A)', minHeight: '100vh'}} className="flex h-screen text-white font-sans selection:bg-[#D2C1B6]/30">
      {/* Sidebar */}
      <aside 
        style={{background: 'rgba(255,255,255,0.05)', borderRight: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)'}} 
        className={`transition-all duration-300 ${isSidebarOpen ? 'w-72' : 'w-20'} flex flex-col`}
      >
        <div className="p-6 flex items-center gap-3">
          <div className="w-10 h-10 bg-[#456882] rounded-xl flex items-center justify-center shadow-lg shadow-black/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          {isSidebarOpen && <h1 style={{color: '#D2C1B6'}} className="font-bold text-xl tracking-tight uppercase">SafeSight AI</h1>}
        </div>

        <nav className="flex-1 px-3 space-y-1">
          <SidebarItem icon={<Activity />} label="Live Monitor" active={activeTab === 'live'} onClick={() => setActiveTab('live')} collapsed={!isSidebarOpen} />
          <SidebarItem icon={<AlertTriangle />} label="All Violations" active={activeTab === 'violations'} onClick={() => setActiveTab('violations')} collapsed={!isSidebarOpen} />
          <SidebarItem icon={<Settings />} label="System Config" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} collapsed={!isSidebarOpen} />
        </nav>

        <div className="p-4 border-t border-white/10">
          {isSidebarOpen ? (
            <div style={{background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px'}} className="p-4 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/60">Status</span>
                <span className={`flex items-center gap-1.5 font-medium ${stats?.running ? 'text-emerald-400' : 'text-amber-400'}`}>
                  <div className={`w-2 h-2 rounded-full ${stats?.running ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                  {stats?.running ? 'Active' : 'Idle'}
                </span>
              </div>
              <button 
                onClick={stats?.running ? handleStop : handleStart}
                style={{ 
                  background: stats?.running ? 'rgba(255,71,87,0.1)' : '#456882', 
                  color: stats?.running ? '#ff4757' : '#D2C1B6' 
                }}
                className="w-full py-2.5 rounded-lg flex items-center justify-center gap-2 font-semibold transition-all hover:opacity-80"
              >
                {stats?.running ? <><Square className="w-4 h-4" /> Stop</> : <><Play className="w-4 h-4" /> Start</>}
              </button>
            </div>
          ) : (
            <button 
              onClick={stats?.running ? handleStop : handleStart} 
              style={{ background: stats?.running ? 'rgba(255,71,87,0.1)' : '#456882', color: stats?.running ? '#ff4757' : '#D2C1B6' }}
              className="w-full p-3 rounded-xl flex items-center justify-center transition-all hover:opacity-80"
            >
              {stats?.running ? <Square size={20} /> : <Play size={20} />}
            </button>
          )}
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="mt-4 w-full p-2 text-white/40 hover:text-white transition-colors flex justify-center">
             <ChevronRight className={`transition-transform duration-300 ${isSidebarOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto flex flex-col">
        <header style={{background: 'rgba(27,60,83,0.8)', backdropFilter: 'blur(10px)', borderBottom: '1px solid rgba(255,255,255,0.1)'}} className="h-20 flex items-center justify-between px-8 sticky top-0 z-10">
          <div>
            <h2 style={{color: '#D2C1B6'}} className="text-2xl font-bold uppercase tracking-widest">{activeTab === 'live' ? 'Safety Monitoring Dashboard' : activeTab === 'violations' ? 'Violation Logs' : 'System Settings'}</h2>
            <p className="text-white/60 text-sm italic">Monitoring Area: <span style={{color: '#D2C1B6'}} className="font-medium">{settings?.work_area ?? 'N/A'}</span></p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex -space-x-2">
              {[1, 2, 3].map(i => <div key={i} className="w-8 h-8 rounded-full border-2 border-[#1B3C53] bg-[#456882] flex items-center justify-center text-xs text-white/80">U{i}</div>)}
            </div>
            <div className="w-px h-6 bg-white/10 mx-2" />
            <button className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-white/60 hover:text-white hover:bg-white/10 transition-all">
              <Bell size={20} />
            </button>
          </div>
        </header>

        <div className="p-8 space-y-8">
          {activeTab === 'live' && (
            <>
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard icon={<Users className="text-[#D2C1B6]" />} label="People in View" value={stats?.people_count ?? 0} color="blue" />
                <StatCard icon={<Shield className="text-[#D2C1B6]" />} label="PPE Violations (Total)" value={`${stats?.ppe_violations ?? 0} (${stats?.ppe_current ?? 0} Live)`} color="amber" trend="unsafe" />
                <StatCard icon={<Map className="text-[#D2C1B6]" />} label="ROI Breaches" value={stats?.roi_violations ?? 0} color="rose" trend="unsafe" />
              </div>

              {/* Video Section */}
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                <div className="lg:col-span-3 space-y-4">
                  <div style={{background: '#000', border: '2px solid #456882', borderRadius: '12px', boxShadow: 'inset 0 0 40px rgba(0,0,0,0.8)'}} className="overflow-hidden aspect-video relative group shadow-2xl">
                    {stats?.running ? (
                      <img src={videoUrl || ""} alt="Live Stream" className="w-full h-full object-contain" />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center gap-4 bg-black/40">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center border border-white/10">
                          <Camera className="w-8 h-8 text-white/20" />
                        </div>
                        <div className="text-center">
                          <p className="text-white/40 font-medium text-lg uppercase tracking-widest">System Idle</p>
                          <p className="text-white/20 text-sm italic">Start monitoring to view live feed</p>
                        </div>
                      </div>
                    )}
                    <div className="absolute top-4 left-4 flex items-center gap-2">
                      <div className="px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-lg text-xs font-bold border border-white/10 flex items-center gap-2">
                         <div className={`w-2 h-2 rounded-full ${stats?.running ? 'bg-red-500 animate-pulse' : 'bg-white/20'}`} />
                         LIVE STREAM
                      </div>
                    </div>
                  </div>
                </div>

                {/* Side Logs */}
                <div className="space-y-4">
                  <h3 style={{color: '#D2C1B6'}} className="font-bold flex items-center justify-between uppercase tracking-wider text-sm">
                    Recent Violations
                    <button onClick={() => setActiveTab('violations')} className="text-xs text-white/40 hover:text-[#D2C1B6] transition-colors">View All</button>
                  </h3>
                  <div className="space-y-3 max-h-[480px] overflow-y-auto pr-2 custom-scrollbar">
                    {!violations || violations?.length === 0 ? (
                      <div style={{background: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: '16px'}} className="p-8 text-center">
                        <Info className="w-8 h-8 text-white/10 mx-auto mb-2" />
                        <p className="text-white/20 text-sm italic">Clear area. No recent violations.</p>
                      </div>
                    ) : (
                      violations.map((v, i) => (
                        <div key={v?.id ?? i} style={{background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px'}} className="p-3 hover:bg-white/10 transition-colors">
                          <div className="flex gap-3">
                            <img src={v?.image_path ? `${API_BASE}${v.image_path}` : ""} alt="Violation" className="w-16 h-16 rounded-lg object-cover bg-black/40 border border-white/5" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-bold text-rose-400 truncate">{v?.violation_type ?? 'Unknown'}</p>
                              <p className="text-xs text-white/40 mt-1">{v?.timestamp?.split('_')[1] ?? '--:--:--'}</p>
                              <p style={{color: '#D2C1B6'}} className="text-[10px] font-bold uppercase tracking-widest mt-1 opacity-60">{v?.work_area ?? 'N/A'}</p>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'violations' && (
             <div style={{background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '20px', overflow: 'hidden'}} className="shadow-2xl">
                <table className="w-full text-left">
                  <thead style={{background: '#456882'}} className="text-white text-xs font-bold uppercase tracking-widest">
                    <tr>
                      <th className="px-6 py-4">Snapshot</th>
                      <th className="px-6 py-4">Violation Type</th>
                      <th className="px-6 py-4">Work Area</th>
                      <th className="px-6 py-4">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {violations?.map((v, i) => (
                      <tr key={v?.id ?? i} className="hover:bg-white/5 transition-colors">
                        <td className="px-6 py-4">
                           <img src={v?.image_path ? `${API_BASE}${v.image_path}` : ""} className="w-20 h-12 object-cover rounded-lg bg-black/40 border border-white/10" alt="" />
                        </td>
                        <td className="px-6 py-4 font-semibold text-rose-400">{v?.violation_type ?? 'Unknown'}</td>
                        <td style={{color: '#D2C1B6'}} className="px-6 py-4 font-medium">{v?.work_area ?? 'N/A'}</td>
                        <td className="px-6 py-4 text-white/40 text-sm">{v?.timestamp ?? '--:--:--'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
             </div>
          )}

          {activeTab === 'settings' && (
            <div style={{background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '20px'}} className="max-w-2xl p-8 space-y-8 shadow-2xl backdrop-blur-xl">
               <div className="space-y-4">
                  <h3 style={{color: '#D2C1B6'}} className="text-lg font-bold flex items-center gap-2 uppercase tracking-widest"><Camera size={20} /> Source & Detection</h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-white/40 uppercase tracking-widest">Input Source</label>
                      <select 
                        value={settings?.source ?? '0'}
                        onChange={(e) => updateSetting('source', e.target.value)}
                        style={{background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '10px 16px', color: 'white', outline: 'none'}}
                        className="w-full"
                      >
                        <option value="0">Default Webcam</option>
                        <option value="1">Secondary Cam</option>
                        <option value="demo.mp4">Demo Video</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-white/40 uppercase tracking-widest">Confidence Threshold ({settings?.conf_threshold ?? 0.5})</label>
                      <input 
                        type="range" min="0.1" max="0.9" step="0.1"
                        value={settings?.conf_threshold ?? 0.5}
                        onChange={(e) => updateSetting('conf_threshold', parseFloat(e.target.value))}
                        className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#D2C1B6]" 
                      />
                    </div>
                  </div>
               </div>

               <div className="space-y-4 pt-4 border-t border-white/10">
                  <h3 style={{color: '#D2C1B6'}} className="text-lg font-bold flex items-center gap-2 uppercase tracking-widest"><Mail size={20} /> Notifications</h3>
                  <div style={{background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px'}} className="flex items-center justify-between p-4">
                    <div>
                      <p className="font-bold text-white/80">Email Alerts</p>
                      <p className="text-xs text-white/40 italic">Send snapshots to safety officers on violation</p>
                    </div>
                    <button 
                      onClick={() => updateSetting('email_alerts', !(settings?.email_alerts ?? false))}
                      className={`w-12 h-6 rounded-full transition-all relative ${settings?.email_alerts ? 'bg-[#456882]' : 'bg-white/10'}`}
                    >
                      <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${settings?.email_alerts ? 'left-7' : 'left-1'}`} />
                    </button>
                  </div>
               </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function SidebarItem({ icon, label, active, onClick, collapsed }) {
  return (
    <button 
      onClick={onClick}
      style={active ? {background: '#456882', color: '#D2C1B6', borderRadius: '12px'} : {color: 'rgba(255,255,255,0.6)'}}
      className={`w-full flex items-center gap-3 px-4 py-3 transition-all hover:bg-white/5`}
    >
      <div className={active ? 'text-[#D2C1B6]' : 'text-white/40'}>{icon}</div>
      {!collapsed && <span className="font-bold uppercase tracking-wider text-xs">{label}</span>}
    </button>
  );
}

function StatCard({ icon, label, value, color, trend }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.05)',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '20px',
      padding: '24px',
      boxShadow: '0 8px 32px 0 rgba(0,0,0,0.37)',
      backdropFilter: 'blur(10px)',
      transition: 'transform 0.3s ease',
      cursor: 'default'
    }}
    onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-5px)'}
    onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
        <div style={{padding:'10px', background:'rgba(255,255,255,0.08)', borderRadius:'12px'}}>
          {icon}
        </div>
        {trend && <span style={{fontSize:'10px', fontWeight:'bold', padding:'4px 8px', borderRadius:'4px', background:'rgba(255,71,87,0.1)', color:'#ff4757', textTransform:'uppercase', letterSpacing:'1px'}}>High Risk</span>}
      </div>
      <div style={{marginTop:'16px'}}>
        <p style={{color:'rgba(255,255,255,0.6)', fontSize:'0.85rem', textTransform:'uppercase', letterSpacing:'1px'}}>{label}</p>
        <p style={{fontSize:'2.5rem', fontWeight:'900', color:'#D2C1B6', marginTop:'4px'}}>{value}</p>
      </div>
    </div>
  );
}

export default App;
