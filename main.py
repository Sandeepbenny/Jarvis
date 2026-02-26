# main.py

from backend.orchestrator import Orchestrator


def main() -> None:
    """
    Temporary terminal interface.

    This simulates frontend behavior until
    FastAPI / UI is connected.
    """

    orchestrator = Orchestrator()

    print("Jarvis Assistant")
    print("Type 'voice' to trigger microphone.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Shutting down...")
            break

        if user_input.lower() == "voice":
            result = orchestrator.process_voice()
        else:
            result = orchestrator.process_text(user_input)

        if "error" in result:
            print("Jarvis:", result["error"])
        else:
            print("Jarvis:", result["response"])


if __name__ == "__main__":
    main()