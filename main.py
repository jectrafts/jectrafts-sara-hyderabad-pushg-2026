import pyaudio
import wave
from faster_whisper import WhisperModel
import edge_tts
import asyncio
import os
import wolframalpha
import groq
import re
import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = "Client_secret.json"
scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
client = gspread.authorize(creds)
spreadsheet = client.open("home_automation_database")
worksheet = spreadsheet.sheet1

client_alpha = wolframalpha.Client('RK43HA-E33E3XRE3J')
client = groq.Client(api_key="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")
model_name = "deepseek-r1-distill-llama-70b"
reply = ""

log_file = "chat_log.txt"
output_file = "human_voice.mp3"
voice = "en-GB-AriaNeural"

model = WhisperModel("base.en", device="cpu", compute_type="int8")
recording_active = False

entry_prompt = (
    "You are a personal multi-use voice assistant called SARA. "
    "Your full form is Science and Robotics Assistant, SARA is an acronym so you will assist me mostly with science, robotics, and news. "
    "You are inspired by AI assistants like Jarvis and Friday from Iron Man. "
    "Answer in clean, plain text without using any special symbols, markdown, emoji, or LaTeX. "
    "When I ask for code, put it inbetween <code> and </code> tags. "
    "For any mathematical or scientific explanations, provide plain text only."
)


conversation_history = [
    {"role": "system", "content": entry_prompt},
]


def update_status(status):
    with open("ui_status.txt", "w") as f:
        f.write(status)


def read_file(file_name):
    with open(str(file_name), 'r') as file:
        lines = file.readlines()
    return "".join(line.strip() for line in lines)


def speak(text, voice="en-US-AriaNeural", output_file="output.mp3"):
    async def create_audio():
        tts = edge_tts.Communicate(text, voice)
        await tts.save(output_file)
    update_status("processing")
    asyncio.run(create_audio())
    update_status("speaking")
    os.system(f"mpg123 {output_file}")
    os.remove(output_file)
    update_status("idle")


def whisper_listen(filename="audio.wav"):
    global recording_active
    CHUNK = 2000
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)
    frames = []
    update_status("listening")
    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        lines2 = read_file('status.txt')
        if lines2 != "spacebar":
            break
    stream.stop_stream()
    stream.close()
    p.terminate()
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    update_status("processing")
    segments, _ = model.transcribe(filename, beam_size=1, vad_filter=True)
    transcription = " ".join(segment.text.strip() for segment in segments).strip()
    update_status("idle")
    return transcription


def save_to_log(user_input, assistant_response, code_snippet):
    log_entry = f"USER: {user_input}\nSARA: {assistant_response}\n"
    if code_snippet:
        log_entry += f"CODE:\n{code_snippet}\n"

    with open(log_file, "a") as file:
        file.write(log_entry + "\n")


def format_conversation_history():
    log_str = "Here’s the conversation log so far:\n"
    last_exchanges = conversation_history[-10:]  # Keep a larger history window
    for item in last_exchanges:
        if item["role"] == "user":
            log_str += f"USER: {item['content']}\n"
        elif item["role"] == "assistant":
            log_str += f"SARA: {item['content']}\n"
    return log_str.strip()


def llm_process(prompt, model_name):
    global conversation_history
    global code_snippet

    # Only keep user prompt without history
    full_prompt = f"{entry_prompt}\nUSER: {prompt}"

    update_status("processing")
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "system", "content": full_prompt}],
    )

    reply = response.choices[0].message.content
    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()

    code_snippet_match = re.search(r"<code>(.*?)</code>", reply, re.DOTALL)
    code_snippet = ""

    if code_snippet_match:
        code_snippet = code_snippet_match.group(1).strip()
        reply = re.sub(r"<code>.*?</code>", "", reply, flags=re.DOTALL).strip()

    print(reply)
    if code_snippet:
        print("Extracted Code Snippet:\n", code_snippet)

    save_to_log(prompt, reply, code_snippet)
    speak(reply)
    return reply


if __name__ == "__main__":
    speak("Sara, your personal voice assistant, is online!")
    update_status("idle")

    while True:
        lines2 = read_file('status.txt')
        if lines2 == "spacebar":
            recording_active = True
            query = whisper_listen().lower()
            recording_active = False
        else:
            query = ""

        if query:
            # if "weather" in query:
            #     try:
            #         res = client_alpha.query(query)
            #         output = next(res.results).text
            #         save_to_log(query, output, "")
            #         print(output)
            #         speak(output)
            #     except Exception:
            #         save_to_log(query, error_msg, "")
            #         error_msg = "Sorry, I could not find that."
            #         speak(error_msg)
            if ("lights" in query) or ("light" in query):
                if "on" in query:
                    speak("turning on lights")
                    worksheet.update_cell(2,1,"0")
                    query = ""
                if "off" in query:
                    speak("turning off lights")
                    worksheet.update_cell(2,1,"1")
                    query = ""
            if query  != "":
                llm_process(query, model_name)
