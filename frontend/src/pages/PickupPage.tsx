import { useEffect, useState } from "react";
import { api } from "../api/client";
type O = { ticket_code: string; garment_name: string; status: string };
type Rail = { id: number; label: string };
type Occ = { rail_id: number; label: string; length_cm: number; segments: { order_id: number; ticket_code: string; garment_name: string; start_cm: number; end_cm: number }[] };
type Slot = Occ["segments"][number] & { rail_label: string };

export default function PickupPage() {
  const [code, setCode] = useState("HR-2001");
  const [declared, setDeclared] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");

  async function loadOccupancy() {
    const rs = await api<Rail[]>("/rails");
    const all = await Promise.all(rs.map(r => api<Occ>(`/occupancy/${r.id}`)));
    setSlots(all.flatMap(m => m.segments.map(s => ({ ...s, rail_label: m.label }))));
  }

  useEffect(() => { loadOccupancy(); }, []);

  async function run() {
    setMsg(""); setErr("");
    const declaredLengthCm = Number(declared);
    if (!Number.isFinite(declaredLengthCm) || declaredLengthCm <= 0) {
      setErr("请输入申报衣长（厘米）");
      return;
    }
    try {
      const o = await api<O>("/pickup", {
        method: "POST",
        body: JSON.stringify({ ticket_code: code, declared_length_cm: declaredLengthCm }),
      });
      setMsg(`已取件释放：${o.ticket_code} · ${o.garment_name}`);
      setSlots(prev => prev.filter(s => s.ticket_code !== o.ticket_code));
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>取件</h2>
    <div className="toolbar">
      <input value={code} onChange={e => setCode(e.target.value)} placeholder="取件票号" />
      <input value={declared} onChange={e => setDeclared(e.target.value)} placeholder="申报衣长 cm"
        type="number" min="0" step="0.1" style={{ width: "8em" }} />
      <button onClick={run}>取件释放占位</button>
    </div>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <h3>当前占位</h3>
    {slots.length === 0 && <p>暂无在挂占位</p>}
    {slots.map(s => (
      <div className="seg-row" key={`${s.rail_label}-${s.ticket_code}`}>
        <span className="mono">{s.ticket_code}</span>
        <span>{s.garment_name}</span>
        <span>{s.rail_label} · {s.start_cm}–{s.end_cm}cm</span>
      </div>
    ))}
  </>);
}
