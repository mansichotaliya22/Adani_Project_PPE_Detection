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
    <div className="flex h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
      {/* Sidebar */}
      <aside className={`transition-all duration-300 ${isSidebarOpen ? 'w-72' : 'w-20'} bg-slate-900/50 border-r border-slate-800 flex flex-col`}>
        <div className="p-6 flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-600/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          {isSidebarOpen && <h1 className="font-bold text-xl tracking-tight">SafeSight AI</h1>}
        </div>

        <nav className="flex-1 px-3 space-y-1">
          <SidebarItem icon={<Activity />} label="Live Monitor" active={activeTab === 'live'} onClick={() => setActiveTab('live')} collapsed={!isSidebarOpen} />
          <SidebarItem icon={<AlertTriangle />} label="All Violations" active={activeTab === 'violations'} onClick={() => setActiveTab('violations')} collapsed={!isSidebarOpen} />
          <SidebarItem icon={<Settings />} label="System Config" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} collapsed={!isSidebarOpen} />
        </nav>

        <div className="p-4 border-t border-slate-800">
          {isSidebarOpen ? (
            <div className="bg-slate-800/50 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Status</span>
                <span className={`flex items-center gap-1.5 font-medium ${stats?.running ? 'text-emerald-400' : 'text-amber-400'}`}>
                  <div className={`w-2 h-2 rounded-full ${stats?.running ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                  {stats?.running ? 'Active' : 'Idle'}
                </span>
              </div>
              <button 
                onClick={stats?.running ? handleStop : handleStart}
                className={`w-full py-2.5 rounded-lg flex items-center justify-center gap-2 font-semibold transition-all ${
                  stats?.running 
                  ? 'bg-rose-500/10 text-rose-500 hover:bg-rose-500 hover:text-white' 
                  : 'bg-indigo-600 text-white hover:bg-indigo-500 shadow-lg shadow-indigo-600/20'
                }`}
              >
                {stats?.running ? <><Square className="w-4 h-4" /> Stop</> : <><Play className="w-4 h-4" /> Start</>}
              </button>
            </div>
          ) : (
            <button onClick={stats?.running ? handleStop : handleStart} className={`w-full p-3 rounded-xl flex items-center justify-center transition-all ${stats?.running ? 'bg-rose-500/10 text-rose-500' : 'bg-indigo-600 text-white'}`}>
              {stats?.running ? <Square size={20} /> : <Play size={20} />}
            </button>
          )}
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="mt-4 w-full p-2 text-slate-500 hover:text-slate-300 transition-colors flex justify-center">
             <ChevronRight className={`transition-transform duration-300 ${isSidebarOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto flex flex-col">
        <header className="h-20 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-950/50 backdrop-blur-md sticky top-0 z-10">
          <div>
            <h2 className="text-2xl font-bold">{activeTab === 'live' ? 'Safety Monitoring Dashboard' : activeTab === 'violations' ? 'Violation Logs' : 'System Settings'}</h2>
            <p className="text-slate-500 text-sm">Monitoring Area: <span className="text-indigo-400 font-medium">{settings?.work_area ?? 'N/A'}</span></p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex -space-x-2">
              {[1, 2, 3].map(i => <div key={i} className="w-8 h-8 rounded-full border-2 border-slate-950 bg-slate-800 flex items-center justify-center text-xs text-slate-400">U{i}</div>)}
            </div>
            <div className="w-px h-6 bg-slate-800 mx-2" />
            <button className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-all">
              <Bell size={20} />
            </button>
          </div>
        </header>

        <div className="p-8 space-y-8">
          {activeTab === 'live' && (
            <>
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatCard icon={<Users className="text-blue-400" />} label="People in View" value={stats?.people_count ?? 0} color="blue" />
                <StatCard icon={<Shield className="text-amber-400" />} label="PPE Violations (Total)" value={`${stats?.ppe_violations ?? 0} (${stats?.ppe_current ?? 0} Live)`} color="amber" trend="unsafe" />
                <StatCard icon={<Map className="text-rose-400" />} label="ROI Breaches" value={stats?.roi_violations ?? 0} color="rose" trend="unsafe" />
              </div>

              {/* Video Section */}
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                <div className="lg:col-span-3 space-y-4">
                  <div className="bg-slate-900 rounded-2xl overflow-hidden border border-slate-800 aspect-video relative group shadow-2xl">
                    {stats?.running ? (
                      <img src={videoUrl || ""} alt="Live Stream" className="w-full h-full object-contain" />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center gap-4 bg-slate-900">
                        <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center">
                          <Camera className="w-8 h-8 text-slate-600" />
                        </div>
                        <div className="text-center">
                          <p className="text-slate-400 font-medium text-lg">System Idle</p>
                          <p className="text-slate-600 text-sm">Start monitoring to view live feed</p>
                        </div>
                      </div>
                    )}
                    <div className="absolute top-4 left-4 flex items-center gap-2">
                      <div className="px-3 py-1.5 bg-slate-950/80 backdrop-blur-md rounded-lg text-xs font-bold border border-white/10 flex items-center gap-2">
                         <div className={`w-2 h-2 rounded-full ${stats?.running ? 'bg-red-500 animate-pulse' : 'bg-slate-600'}`} />
                         LIVE STREAM
                      </div>
                    </div>
                  </div>
                </div>

                {/* Side Logs */}
                <div className="space-y-4">
                  <h3 className="font-bold flex items-center justify-between">
                    Recent Violations
                    <button onClick={() => setActiveTab('violations')} className="text-xs text-indigo-400 hover:text-indigo-300">View All</button>
                  </h3>
                  <div className="space-y-3 max-h-[480px] overflow-y-auto pr-2">
                    {!violations || violations?.length === 0 ? (
                      <div className="bg-slate-900/50 rounded-xl p-8 text-center border border-dashed border-slate-800">
                        <Info className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                        <p className="text-slate-600 text-sm italic">Clear area. No recent violations.</p>
                      </div>
                    ) : (
                      violations.map((v, i) => (
                        <div key={v?.id ?? i} className="bg-slate-900 rounded-xl p-3 border border-slate-800 hover:border-slate-700 transition-colors">
                          <div className="flex gap-3">
                            <img src={v?.image_path ? `${API_BASE}${v.image_path}` : ""} alt="Violation" className="w-16 h-16 rounded-lg object-cover bg-slate-800" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-bold text-rose-400 truncate">{v?.violation_type ?? 'Unknown'}</p>
                              <p className="text-xs text-slate-500 mt-1">{v?.timestamp?.split('_')[1] ?? '--:--:--'}</p>
                              <p className="text-[10px] text-slate-600 font-medium uppercase tracking-wider mt-1">{v?.work_area ?? 'N/A'}</p>
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
             <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
                <table className="w-full text-left">
                  <thead className="bg-slate-800/50 text-slate-400 text-xs font-bold uppercase tracking-widest border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-4">Snapshot</th>
                      <th className="px-6 py-4">Violation Type</th>
                      <th className="px-6 py-4">Work Area</th>
                      <th className="px-6 py-4">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {violations?.map((v, i) => (
                      <tr key={v?.id ?? i} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-4">
                           <img src={v?.image_path ? `${API_BASE}${v.image_path}` : ""} className="w-20 h-12 object-cover rounded-lg bg-slate-800 border border-slate-700" alt="" />
                        </td>
                        <td className="px-6 py-4 font-semibold text-rose-400">{v?.violation_type ?? 'Unknown'}</td>
                        <td className="px-6 py-4 text-slate-300">{v?.work_area ?? 'N/A'}</td>
                        <td className="px-6 py-4 text-slate-500 text-sm">{v?.timestamp ?? '--:--:--'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
             </div>
          )}

          {activeTab === 'settings' && (
            <div className="max-w-2xl bg-slate-900 rounded-2xl border border-slate-800 p-8 space-y-8">
               <div className="space-y-4">
                  <h3 className="text-lg font-bold flex items-center gap-2"><Camera size={20} className="text-indigo-400" /> Source & Detection</h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase">Input Source</label>
                      <select 
                        value={settings?.source ?? '0'}
                        onChange={(e) => updateSetting('source', e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 outline-none focus:border-indigo-500"
                      >
                        <option value="0">Default Webcam</option>
                        <option value="1">Secondary Cam</option>
                        <option value="demo.mp4">Demo Video</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase">Confidence Threshold ({settings?.conf_threshold ?? 0.5})</label>
                      <input 
                        type="range" min="0.1" max="0.9" step="0.1"
                        value={settings?.conf_threshold ?? 0.5}
                        onChange={(e) => updateSetting('conf_threshold', parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600" 
                      />
                    </div>
                  </div>
               </div>

               <div className="space-y-4 pt-4 border-t border-slate-800">
                  <h3 className="text-lg font-bold flex items-center gap-2"><Mail size={20} className="text-emerald-400" /> Notifications</h3>
                  <div className="flex items-center justify-between p-4 bg-slate-950 rounded-xl border border-slate-800">
                    <div>
                      <p className="font-bold">Email Alerts</p>
                      <p className="text-xs text-slate-500">Send snapshots to safety officers on violation</p>
                    </div>
                    <button 
                      onClick={() => updateSetting('email_alerts', !(settings?.email_alerts ?? false))}
                      className={`w-12 h-6 rounded-full transition-all relative ${settings?.email_alerts ? 'bg-indigo-600' : 'bg-slate-800'}`}
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
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
        active 
        ? 'bg-indigo-600/10 text-indigo-400 border-l-4 border-indigo-600 rounded-l-none' 
        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
      }`}
    >
      <div className={active ? 'text-indigo-400' : 'text-slate-500'}>{icon}</div>
      {!collapsed && <span className="font-medium">{label}</span>}
    </button>
  );
}

function StatCard({ icon, label, value, color, trend }) {
  return (
    <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 shadow-xl shadow-black/20">
      <div className="flex items-start justify-between">
        <div className={`p-3 rounded-xl bg-${color}-500/10 border border-${color}-500/20`}>
          {icon}
        </div>
        {trend && (
           <span className="text-[10px] font-bold px-2 py-1 rounded bg-rose-500/10 text-rose-500 uppercase tracking-wider">High Risk</span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-slate-500 text-sm font-medium">{label}</p>
        <p className="text-4xl font-black mt-1 tabular-nums">{value}</p>
      </div>
    </div>
  );
}

export default App;
