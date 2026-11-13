// Fetch helpers + the shared error banner.
export function banner(msg) {
  const b = document.getElementById('banner');
  if (!msg) { b.hidden = true; b.textContent = ''; return; }
  b.textContent = msg; b.hidden = false;
}

export async function getJSON(url) {
  const r = await fetch(url);
  return parse(r);
}
export async function postJSON(url, body) {
  const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  return parse(r);
}
async function parse(r) {
  let data = null;
  try { data = await r.json(); } catch { /* not json */ }
  if (!r.ok) throw new Error((data && data.error) || `${r.status} ${r.statusText}`);
  return data;
}

// Minimal SSE reader over fetch (gives real error messages and abortability).
export async function sse(url, handlers, signal) {
  const r = await fetch(url, { signal });
  if (!r.ok) { await parse(r); }
  const reader = r.body.getReader(), dec = new TextDecoder();
  let buf = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf('\n\n')) >= 0) {
      const block = buf.slice(0, i); buf = buf.slice(i + 2);
      let ev = 'message', data = '';
      for (const line of block.split('\n')) {
        if (line.startsWith('event: ')) ev = line.slice(7);
        else if (line.startsWith('data: ')) data += line.slice(6);
      }
      const h = handlers[ev];
      if (h) h(data ? JSON.parse(data) : null);
    }
  }
}
