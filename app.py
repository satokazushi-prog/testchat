"""
Gemini モデルとターミナルで会話するシンプルなアプリ
"""
import os
import google.generativeai as genai

# 環境変数 GEMINI_API_KEY があればそれを使う。なければここを書き換える
API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyB6OjkKmtk789gqIkDXUIPgtqc9VszvcTQ"


def chat_with_gemini(user_message: str, chat_session=None):
    """
    Gemini モデルと会話する。チャットセッションを渡すと履歴を維持する。
    初回は chat_session=None で呼び、返り値の (response_text, new_chat) の
    new_chat を次回以降渡す。

    Returns:
        tuple: (AIの返答テキスト, 次回用のチャットセッション)
    """
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    if chat_session is None:
        chat_session = model.start_chat(history=[])

    response = chat_session.send_message(user_message)
    return response.text, chat_session


if __name__ == "__main__":
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        print("エラー: APIキーが設定されていません。")
        print("  方法1: 環境変数を設定して実行 → set GEMINI_API_KEY=あなたのキー  (PowerShell: $env:GEMINI_API_KEY=\"あなたのキー\")")
        print("  方法2: app.py の API_KEY を書き換える（環境変数が無い場合）")
        print("  キー取得: https://aistudio.google.com/apikey")
        exit(1)
    print("Gemini と会話します。終了するには 'quit' または 'exit' と入力してください。\n")
    chat_session = None

    while True:
        try:
            user_input = input("あなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("終了します。")
            break

        try:
            reply, chat_session = chat_with_gemini(user_input, chat_session)
            print(f"AI: {reply}\n")
        except Exception as e:
            err = str(e)
            if "API key not valid" in err or "invalid" in err.lower():
                print("エラー: APIキーが無効です。")
                print("  新しいキーを取得: https://aistudio.google.com/apikey")
                print("  取得後、環境変数 GEMINI_API_KEY を設定するか app.py の API_KEY を書き換えてください。\n")
            else:
                print(f"エラー: {e}\n")
