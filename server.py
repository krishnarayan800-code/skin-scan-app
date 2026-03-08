"""
DermAI Backend Server
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import anthropic
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load .env with robust parser ──
def load_env():
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8-sig") as f:  # utf-8-sig strips BOM
            for line in f:
                line = line.rstrip("\r\n").strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")  # remove any surrounding quotes
                if k and v:
                    os.environ[k] = v  # always override, not setdefault

load_env()

app = Flask(__name__)
CORS(app)

def get_client():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key or key == "sk-ant-your-real-key-here" or key == "sk-ant-paste-your-key-here":
        return None, "API key not set. Edit your .env file with a real key from console.anthropic.com"
    return anthropic.Anthropic(api_key=key), None

def find_index():
    for p in [
        os.path.join(BASE_DIR, "index.html"),
        os.path.join(BASE_DIR, "..", "index.html"),
        os.path.join(BASE_DIR, "..", "Frontend", "index.html"),
    ]:
        p = os.path.normpath(p)
        if os.path.exists(p):
            return p
    return None

# Print startup info
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
print("\n" + "="*55)
print("  DermAI Server Starting")
print("="*55)
print(f"  Folder     : {BASE_DIR}")
print(f"  index.html : {'FOUND ✅' if find_index() else 'MISSING ❌ — put it next to server.py'}")
print(f"  API Key    : {api_key[:20]}... ✅" if len(api_key) > 20 else f"  API Key    : MISSING ❌")
print("="*55 + "\n")


@app.route("/")
def index():
    path = find_index()
    if not path:
        return f"<h2>Put index.html in: {BASE_DIR}</h2>", 404
    return send_file(path)


@app.route("/analyze", methods=["POST"])
def analyze():
    client, err = get_client()
    if err:
        return jsonify({"success": False, "error": err}), 401

    try:
        data = request.get_json()
        images = data.get("images", {})
        content = []

        for angle, data_url in images.items():
            if "," in data_url:
                b64 = data_url.split(",")[1]
                mime = data_url.split(";")[0].split(":")[1]
            else:
                b64 = data_url
                mime = "image/jpeg"
            content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}})
            content.append({"type": "text", "text": f"Above image: {angle} angle view of face."})

        content.append({"type": "text", "text": """You are an expert AI dermatologist. Analyze the skin in these images.
Respond ONLY with valid JSON, no markdown, no extra text:
{
  "skinScore": <0-100>,
  "skinType": "<Oily|Dry|Combination|Normal|Sensitive>",
  "skinTypeSummary": "<2-3 sentences>",
  "conditions": [{"name":"<n>","severity":"<Mild|Moderate|Severe>","confidence":<0-1>,"color":"<hex>"}],
  "zones": {"forehead":"<text>","leftCheek":"<text>","rightCheek":"<text>","nose":"<text>","chin":"<text>"},
  "metrics": {"hydration":<0-100>,"oiliness":<0-100>,"poreVisibility":<0-100>,"evenness":<0-100>},
  "insights": "<3-5 sentences>",
  "morningRoutine": [{"step":"<n>","product":"<type>","note":"<why>"}],
  "eveningRoutine": [{"step":"<n>","product":"<type>","note":"<why>"}],
  "treatments": [{"name":"<n>","icon":"<emoji>","description":"<desc>","tags":["<tag>"]}],
  "goodIngredients": ["<ingredient>"],
  "badIngredients": ["<ingredient>"],
  "totalIssues": <number>
}"""})

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": content}]
        )
        text = msg.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return jsonify({"success": True, "data": json.loads(text.strip())})

    except anthropic.AuthenticationError as e:
        return jsonify({"success": False, "error": f"Invalid API key: {str(e)}"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health")
def health():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return jsonify({
        "status": "ok",
        "api_key_set": bool(key),
        "api_key_preview": key[:20] + "..." if len(key) > 20 else "NOT SET",
        "index_html": find_index() or "NOT FOUND",
        "server_folder": BASE_DIR
    })


@app.route("/analyze-text", methods=["POST"])
def analyze_text():
    """Text-only endpoint for recommendation engine (no images)."""
    client, err = get_client()
    if err:
        return jsonify({"success": False, "error": err}), 401
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return jsonify({"success": True, "data": json.loads(text.strip())})
    except anthropic.AuthenticationError:
        return jsonify({"success": False, "error": "Invalid API key."}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"  → http://localhost:{port}\n")

    app.run(host="0.0.0.0", port=port, debug=False)
