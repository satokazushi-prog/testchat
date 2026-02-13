"""
Gemini と会話する Flask Webアプリケーション（マルチモーダル対応）
"""
import os
import io
import base64
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from PIL import Image

# 環境変数 GEMINI_API_KEY があればそれを使う。なければここを書き換える
API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyB6OjkKmtk789gqIkDXUIPgtqc9VszvcTQ"

# システムプロンプト（キャラ設定）
SYSTEM_INSTRUCTION = (
    "あなたはサッカーが大好きな男性です。"
    "好きな選手や好きなチームについて、任意で回答します。"
    "サッカーがとても好きなので、世話焼きな性格でふるまってください。"
)

app = Flask(__name__)


def get_knowledge() -> str:
    """
    knowledge フォルダ内の全ての .txt ファイルを読み込み、
    --- ファイル名 --- のヘッダーを付けて連結して返す。
    フォルダが無い場合や空の場合は空文字を返す。
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    knowledge_dir = os.path.join(base_dir, "knowledge")
    if not os.path.isdir(knowledge_dir):
        return ""
    parts = []
    try:
        entries = sorted(os.listdir(knowledge_dir))
        for name in entries:
            if not name.lower().endswith(".txt"):
                continue
            path = os.path.join(knowledge_dir, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                continue
            parts.append(f"--- {name} ---\n{content}")
        return "\n\n".join(parts) if parts else ""
    except OSError:
        return ""


def _build_message_with_knowledge(user_message: str) -> str:
    """参考情報がある場合、指示と参考情報をユーザーメッセージの先頭に付与する。"""
    knowledge = get_knowledge().strip()
    if not knowledge:
        return user_message
    return (
        "以下の【参考情報】に基づいて回答してください。\n\n"
        "【参考情報】\n"
        f"{knowledge}\n\n"
        "---\n\n"
        f"ユーザー: {user_message}"
    )


def chat_with_gemini(user_message: str, chat_session=None, image=None):
    """
    Gemini モデルと会話する。
    画像がある場合は [message, image] で generate_content、ない場合は send_message。
    """
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=SYSTEM_INSTRUCTION,
    )

    message_to_send = _build_message_with_knowledge(
        user_message or "この画像について何か話してください"
    )
    if image is not None:
        content = [message_to_send, image]
        response = model.generate_content(content)
        return response.text, None
    if chat_session is None:
        chat_session = model.start_chat(history=[])
    response = chat_session.send_message(message_to_send)
    return response.text, chat_session


def decode_base64_to_image(b64_string: str) -> Image.Image:
    """Base64文字列（data URL 可）をデコードして PIL Image に変換する。"""
    if not b64_string or not b64_string.strip():
        raise ValueError("画像データが空です")
    s = b64_string.strip()
    if "," in s and s.startswith("data:"):
        s = s.split(",", 1)[1]
    raw = base64.b64decode(s)
    return Image.open(io.BytesIO(raw)).convert("RGB")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        return jsonify({
            "response": "APIキーが設定されていません。app.py の API_KEY を書き換えるか、環境変数 GEMINI_API_KEY を設定してください。キー取得: https://aistudio.google.com/apikey"
        }), 401

    data = request.get_json()
    if not data:
        return jsonify({"response": "エラー: JSON を送信してください。"}), 400

    user_message = (data.get("message") or "").strip()
    image_b64 = data.get("image")
    has_image = image_b64 and str(image_b64).strip()

    if not user_message and not has_image:
        return jsonify({"response": "メッセージまたは画像を入力してください。"}), 400

    image_obj = None
    if has_image:
        try:
            image_obj = decode_base64_to_image(str(image_b64))
        except Exception as e:
            return jsonify({"response": f"画像のデコードに失敗しました: {e}"}), 400

    try:
        reply, _ = chat_with_gemini(
            user_message or "この画像について何か話してください",
            chat_session=None,
            image=image_obj,
        )
        return jsonify({"response": reply})
    except Exception as e:
        err = str(e)
        if "API key not valid" in err or "API_KEY_INVALID" in err:
            return jsonify({
                "response": "APIキーが無効です。https://aistudio.google.com/apikey で新しいキーを取得し、app.py の API_KEY または環境変数 GEMINI_API_KEY に設定してください。"
            }), 401
        return jsonify({"response": f"エラー: {err}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
