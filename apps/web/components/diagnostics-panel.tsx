import type { SessionSnapshot } from "../lib/contracts";

export function DiagnosticsPanel({ session }: { session: SessionSnapshot }) {
  return (
    <section className="panel">
      <h2>Developer Diagnostics</h2>
      <pre>{JSON.stringify(session, null, 2)}</pre>
    </section>
  );
}
