import uuid
from flask import jsonify

def ok(data, meta=None):
    return jsonify({
        "data": data,
        "meta": meta or {},
        "trace_id": str(uuid.uuid4())
    }), 200

def fail(code, message, details=None, status=400):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "details": details or []
        },
        "trace_id": str(uuid.uuid4())
    }), status
