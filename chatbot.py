import tkinter as tk
from tkinter import scrolledtext
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import os
import threading

# ========== Setup Gemini API ==========
genai.configure(api_key=os.getenv("GEMINI_API_KEY") or "AIzaSyBhP4-zGDNln9jFISGZOkdDD6VaioVO5T0")
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")
chat = model.start_chat(history=[])

# ========== Setup TTS ==========
engine = pyttsx3.init()
engine.setProperty('rate', 170)
speech_active = False

# ========== Logic Helpers ==========
def is_math_question(text):
    math_keywords = ['add', 'sum', 'plus', 'subtract', 'minus', 'multiply', 'divide', '+', '-', '*', '/', 'calculate']
    return any(kw in text.lower() for kw in math_keywords)

def format_prompt(user_input):
    if is_math_question(user_input):
        return f"The user asked a math question: '{user_input}'. Politely refuse to solve it and suggest using a calculator."
    else:
        return f"Explain the following step-by-step:\nQuestion: {user_input}\nAnswer:"

def get_response(user_input):
    prompt = format_prompt(user_input)
    try:
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"[Error] {e}"

# ========== Send Message ==========
def send_message():
    user_input = entry.get().strip()
    if not user_input:
        return
    add_message(user_input, sender="You")
    entry.delete(0, tk.END)

    response = get_response(user_input)
    add_message(response, sender="Bot")

    global last_bot_response
    last_bot_response = response

    with open("interaction_logs.txt", "a") as f:
        f.write(f"You: {user_input}\nBot: {response}\n\n")

# ========== Speak Toggle ==========
def toggle_speech():
    global speech_active
    if speech_active:
        engine.stop()
        speech_active = False
    else:
        speech_active = True
        threading.Thread(target=speak_response).start()

def speak_response():
    if last_bot_response:
        engine.say(last_bot_response)
        engine.runAndWait()
        global speech_active
        speech_active = False

# ========== Voice Input ==========
def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        # Show "Listening..." before recording begins
        add_message("🎤 Listening... (Speak now)", "Bot")
        root.update()  # Force GUI to refresh before listening
        
        try:
            audio = recognizer.listen(source, timeout=5)
            user_input = recognizer.recognize_google(audio)
            add_message(user_input, "You")
            entry.delete(0, tk.END)

            response = get_response(user_input)
            add_message(response, "Bot")

            global last_bot_response
            last_bot_response = response

            with open("interaction_logs.txt", "a") as f:
                f.write(f"You: {user_input}\nBot: {response}\n\n")
        except sr.WaitTimeoutError:
            add_message("🛑 Timeout: No speech detected.", "Bot")
        except sr.UnknownValueError:
            add_message("🛑 Could not understand audio.", "Bot")
        except sr.RequestError as e:
            add_message(f"🛑 Speech service error: {e}", "Bot")


# ========== GUI Layout ==========
root = tk.Tk()
root.title("🧠 LLM Smart Assistant (Level 1)")
root.geometry("650x600")
root.configure(bg="#1e1e1e")

last_bot_response = ""

# Chat Display
chat_frame = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#121212", fg="#f0f0f0", font=("Consolas", 12))
chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
chat_frame.config(state=tk.DISABLED)

# Input Row
input_frame = tk.Frame(root, bg="#1e1e1e")
input_frame.pack(fill=tk.X, padx=10, pady=10)

entry = tk.Entry(input_frame, font=("Arial", 14), bg="#2e2e2e", fg="#ffffff", insertbackground="#ffffff")
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
entry.bind("<Return>", lambda e: send_message())

send_btn = tk.Button(input_frame, text="Send", font=("Arial", 12), bg="#1E88E5", fg="white", command=send_message)
send_btn.pack(side=tk.LEFT)

speak_btn = tk.Button(input_frame, text="🔊 Speak", font=("Arial", 12), bg="#43A047", fg="white", command=toggle_speech)
speak_btn.pack(side=tk.LEFT, padx=(10, 0))

mic_btn = tk.Button(input_frame, text="🎤 Mic", font=("Arial", 12), bg="#FB8C00", fg="white", command=voice_input)
mic_btn.pack(side=tk.LEFT, padx=(10, 0))

# ========== Message Display ==========
def add_message(text, sender="Bot"):
    chat_frame.config(state=tk.NORMAL)
    if sender == "You":
        chat_frame.insert(tk.END, f"\n🧑 You:\n", "user")
    else:
        chat_frame.insert(tk.END, f"\n🤖 Bot:\n", "bot")
    chat_frame.insert(tk.END, f"{text}\n", "msg")
    chat_frame.see(tk.END)
    chat_frame.config(state=tk.DISABLED)

chat_frame.tag_config("user", foreground="#90CAF9", font=("Consolas", 11, "bold"))
chat_frame.tag_config("bot", foreground="#A5D6A7", font=("Consolas", 11, "bold"))
chat_frame.tag_config("msg", foreground="#E0E0E0")

# ========== Run App ==========
root.mainloop()
