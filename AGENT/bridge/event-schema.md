# Event Schema

## Envelope
WebSocket messages use a JSON envelope:

```json
{
  "event": "eventName",
  "data": {}
}
```

Some error messages also include:
- `code`
- `detail`
- `correlation_id`

## WebSocket Endpoint
- Endpoint: `/api/ws`
- Current frontend behavior appends `?token=...`
- Current backend endpoint does not validate the token yet; do not assume real WS auth enforcement without checking source

## Device Events
- `deviceAdded`
  - Payload: full `Device` object
- `deviceStatusChanged`
  - Payload: `{ mac, status, device }`
- `deviceUpdated`
  - Payload varies by source, but commonly includes `mac` plus changed display/manual fields
- `recognitionOverridden`
  - Payload: `{ mac, vendor, model, device_type, confidence, manual_override }`
- `deviceListCleared`
  - Payload: `{ deleted_count, timestamp }`

## Scan Events
- `scanStarted`
  - May be minimal (`type`, `timestamp`) or extended (`id`, `type`, `mode`, `timestamp`)
- `scanCompleted`
  - Success payload includes `id`, `status`, `devices_found`, `timestamp`, and sometimes `succeed`
  - Failure payload includes `id`, `status`, `error`, `timestamp`, and sometimes `error_type`
- `scanLog`
  - Payload contains human-readable progress log data

## Active Defense Events
- `activeDefenseStarted`
  - Payload: `{ mac, type, duration, intensity, start_time }`
- `activeDefenseStopped`
  - Payload: `{ mac, timestamp }`
- `activeDefenseLog`
  - Payload: `{ level, message, mac, operation_type, timestamp, error? }`
- Legacy event names may still exist in frontend enums for backward compatibility

## Log and Utility Events
- `logAdded`
  - Payload: full `SystemLog`
- `ping`
  - Keepalive event emitted by the WS endpoint
- `error`
  - Standardized WS error envelope

## Event Discipline
- Do not casually rename events
- Do not narrow payloads without checking all listeners
- Update frontend types and AGENT bridge docs together when event shapes change
