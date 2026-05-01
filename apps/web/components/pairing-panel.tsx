import type { CreateSessionResponse } from "../lib/contracts";

export function PairingPanel({
  serverApiUrl,
  session,
}: {
  serverApiUrl: string;
  session: CreateSessionResponse;
}) {
  const phoneApiUrl = session.network_config.api_base_url;
  const websocketUrl = `${session.network_config.websocket_base_url}${session.websocket_path}`;
  const isLoopback = session.network_config.is_loopback;

  return (
    <section className="panel pairing-panel">
      <div className="panel-heading">
        <h2>Phone Pairing</h2>
        <span className={isLoopback ? "status fail" : "status wait"}>
          {isLoopback ? "LAN URL needed" : "Waiting for phone"}
        </span>
      </div>

      {isLoopback ? (
        <p className="network-note error" role="status">
          The API is only advertising a loopback address. Set{" "}
          <code translate="no">ROOM_SCANNER_PUBLIC_API_URL</code> to the laptop LAN URL before pairing.
        </p>
      ) : (
        <p className="network-note" role="status">
          Use the phone API URL below from the Android scanner on the same Wi-Fi network.
        </p>
      )}

      <div className="pairing-fields">
        <PairingValue label="Phone API URL" value={phoneApiUrl} />
        <PairingValue label="Session ID" value={session.session_id} />
        <PairingValue label="Pairing token" value={session.pairing_token} />
        <PairingValue label="Telemetry path" value={websocketUrl} />
        <PairingValue label="Desktop API source" value={serverApiUrl} />
      </div>
    </section>
  );
}

function PairingValue({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="pairing-value">
      <span>{label}</span>
      <code>{value}</code>
    </div>
  );
}
