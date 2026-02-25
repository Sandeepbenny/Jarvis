# Main Entry Point for Jarvis Assistant

from modules.agent import JarvisAgent

def terminal_chat():
    # Initialize Jarvis Agent
    jarvis = JarvisAgent(backend="nvidia")

    print("Welcome to Jarvis Assistant! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # Get response from Jarvis
        response = jarvis.handle_input(user_input)
        print(f"Jarvis: {response}")

if __name__ == "__main__":
    terminal_chat()