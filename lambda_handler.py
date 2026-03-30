import base64
import json
import os

# Import your generator function from your project
# Example:
# from chargenapp.generator_service import generate_pdf_bytes

def _response(status_code: int, body: dict, headers: dict | None = None):
    h = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": os.environ.get("CORS_ORIGIN", "*"),
        "Access-Control-Allow-Headers": "content-type",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
    }
    if headers:
        h.update(headers)
    return {"statusCode": status_code, "headers": h, "body": json.dumps(body)}

def handler(event, context):
    # CORS preflight
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": {
                "Access-Control-Allow-Origin": os.environ.get("CORS_ORIGIN", "*"),
                "Access-Control-Allow-Headers": "content-type",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
            },
            "body": "",
        }

    try:
        raw = event.get("body") or ""
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode("utf-8")

        payload = json.loads(raw)
        # TODO: validate/sanitize payload
        # pdf_bytes = generate_pdf_bytes(payload)

        # Placeholder until wired:
        pdf_bytes = b"%PDF-1.4\n%...\n%%EOF\n"

        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")

        return {
            "statusCode": 200,
            "isBase64Encoded": True,
            "headers": {
                "Content-Type": "application/pdf",
                "Content-Disposition": 'attachment; filename="character-sheet.pdf"',
                "Access-Control-Allow-Origin": os.environ.get("CORS_ORIGIN", "*"),
            },
            "body": pdf_b64,
        }

    except Exception as e:
        return _response(500, {"error": str(e)})
    