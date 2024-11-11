$body = @"
[{
    "eventType": "Microsoft.Communication.IncomingCall",
    "data": {
        "from": {
            "kind": "phoneNumber",
            "phoneNumber": {
                "value": "+1234567890"
            }
        },
        "to": {
            "kind": "phoneNumber",
            "phoneNumber": {
                "value": "+0987654321"
            }
        },
        "incomingCallContext": "test-call-id"
    }
}]
"@

Invoke-RestMethod -Uri "http://localhost:8000/api/incomingCall" -Method Post -Body $body -ContentType "application/json"