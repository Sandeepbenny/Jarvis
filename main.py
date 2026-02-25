import threading
from modules.agent import JarvisAgent
from modules.voice_engine import VoiceEngine

def voice_handler(agent, voice):
    while True:
        command = voice.listen()
        if command:
            print(f"User (Voice): {command}")
            reply = agent.handle_input(command)
            voice.speak(reply)

def main():
    # Force use of NVIDIA NIM for the brain
    jarvis = JarvisAgent(backend="nvidia")
    voice = VoiceEngine()

    # Start the "Ears" in the background
    threading.Thread(target=voice_handler, args=(jarvis, voice), daemon=True).start()

    print("--- JARVIS ONLINE (Voice & Terminal Active) ---")
    while True:
        text_input = input("You (Type): ")
        if text_input.lower() == "exit": break
        response = jarvis.handle_input(text_input)
        print(f"Jarvis: {response}")
        voice.speak(response) # He will also speak his typed replies

if __name__ == "__main__":
    main()