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
  "network_paired": true
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
