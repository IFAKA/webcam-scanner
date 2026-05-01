# Data Contracts

All services use stable error codes and explicit scan states.

## Scan States

```text
CREATED
PAIRING
DEVICE_CHECKING
READY
SCANNING
CAPTURE_COMPLETE
UPLOADING
PROCESSING
READY_FOR_REVIEW
EXPORTED
FAILED
```

## Capability Result

```json
{
  "deviceModel": "Redmi Note 14 5G",
  "arcoreSupported": true,
  "depthSupported": true,
  "rawDepthAvailable": true,
  "confidenceAvailable": true,
  "trackingAvailable": true,
  "cameraPermission": true,
  "networkPaired": true,
  "canScan": true,
  "failureReason": null
}
```

## Pairing

The local API owns pairing state. Phones submit the session token from the
desktop UI, and the backend records whether the local pairing requirement is
satisfied before capability reports can enable scanning.

Session creation includes the phone-facing local network configuration. The
desktop UI must show `network_config.api_base_url` for Android pairing because
server-side UI requests may use `127.0.0.1`, which is not reachable from the
phone. Set `ROOM_SCANNER_PUBLIC_API_URL` when automatic LAN detection advertises
a loopback address or the wrong interface.

```json
{
  "api_base_url": "http://192.168.1.20:8000",
  "websocket_base_url": "ws://192.168.1.20:8000",
  "host": "192.168.1.20",
  "port": 8000,
  "detected_interface": "auto",
  "is_loopback": false
}
```

```json
{
  "pairing_token": "local-session-token"
}
```

An invalid token leaves `network_paired` false and returns
`NETWORK_PAIRING_FAILED` at the `pairing` stage.

## Session Snapshot

```json
{
  "session_id": "uuid",
  "state": "DEVICE_CHECKING",
  "last_error": null,
  "capability_report": null,
  "network_paired": true,
  "network_config": {
    "api_base_url": "http://192.168.1.20:8000",
    "websocket_base_url": "ws://192.168.1.20:8000",
    "host": "192.168.1.20",
    "port": 8000,
    "detected_interface": "auto",
    "is_loopback": false
  }
}
```

## Scanner Error

```json
{
  "code": "DEVICE_DEPTH_UNSUPPORTED",
  "message": "This device cannot start a scan because ARCore Depth is unavailable.",
  "stage": "device_check",
  "recoverable": false,
  "details": {},
  "timestamp": "2026-05-01T12:00:00Z",
  "sessionId": "uuid"
}
```
