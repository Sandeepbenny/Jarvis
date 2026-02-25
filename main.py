# main.py

from modules.agent import JarvisAgent


def terminal_chat():
    jarvis = JarvisAgent(backend="nvidia")

    print("Welcome to Jarvis Assistant! Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ")

            if user_input.lower().strip() == "exit":
                print("Goodbye!")
                break

            response = jarvis.handle_input(user_input)
            print(f"Jarvis: {response}\n")

        except KeyboardInterrupt:
            print("\nSession terminated.")
            break
        except Exception as e:
            print(f"[System Error] {str(e)}")


if __name__ == "__main__":
    terminal_chat()