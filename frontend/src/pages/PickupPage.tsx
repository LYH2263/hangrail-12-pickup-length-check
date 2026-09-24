import { useState } from "react";
import { api } from "../api/client";
type O = { ticket_code: string; garment_name: string; status: string };
export default function PickupPage() {
  const [code, setCode] = useState("HR-2001");
  const [length, setLength] = useState("");
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  async function run() {
    setMsg(""); setErr("");
    const cm = Number(length);
    if (!length.trim() || !Number.isFinite(cm) || cm <= 0) {
      setErr("请输入申报衣长（厘米）");
      return;
    }
    try {
      const o = await api<O>("/pickup", { method: "POST", body: JSON.stringify({ ticket_code: code, length_cm: cm }) });
      setMsg(`已取件释放：${o.ticket_code} · ${o.garment_name}，占位图已移除该票`);
      setLength("");
      window.dispatchEvent(new Event("hangrail:pickup"));
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>取件</h2>
    <div className="toolbar">
      <input value={code} onChange={e => setCode(e.target.value)} placeholder="取件票号" />
      <input value={length} onChange={e => setLength(e.target.value)} placeholder="申报衣长 cm"
        type="number" min="1" step="0.1" style={{ width: "9rem" }} />
      <button onClick={run}>取件释放占位</button>
    </div>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
  </>);
}
