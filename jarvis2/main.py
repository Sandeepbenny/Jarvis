# main.py
"""
Terminal interface for Jarvis.
Usage: python main.py
"""
from backend.orchestrator import Orchestrator


def main() -> None:
    orchestrator = Orchestrator(backend="nvidia")

    print("\n" + "═" * 50)
    print("  J A R V I S  —  Personal AI Assistant")
    print("  LangGraph + NVIDIA + 30 Tools")
    print("═" * 50)
    print("  Commands: 'voice', 'memory', 'clear', 'exit'")
    print("═" * 50 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nShutting down. Goodbye, sir.")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Jarvis: Shutting down. Goodbye, sir.")
            break

        elif user_input.lower() == "voice":
            result = orchestrator.process_voice()

        elif user_input.lower() == "memory":
            stats = orchestrator.agent.memory.get_stats()
            facts = orchestrator.agent.memory.get_all_facts()
            print(f"\n🧠 Memory Stats: {stats}")
            if facts:
                print("📚 Known facts:")
                for k, v in facts.items():
                    print(f"   {k}: {v}")
            print()
            continue

        elif user_input.lower() == "clear":
            orchestrator.agent.memory.clear_session()
            print("Jarvis: Session cleared. Long-term memory preserved.\n")
            continue

        elif user_input.lower().startswith("remember "):
            # e.g. "remember name = Tony"
            rest = user_input[9:]
            if "=" in rest:
                key, value = rest.split("=", 1)
                msg = orchestrator.remember(key.strip(), value.strip())
                print(f"Jarvis: {msg}\n")
            else:
                print("Jarvis: Format: remember key = value\n")
            continue

        else:
            result = orchestrator.process_text(user_input)

        if "error" in result:
            print(f"Jarvis: {result['error']}\n")
        else:
            elapsed = result.get("elapsed_sec", "")
            time_str = f" ({elapsed}s)" if elapsed else ""
            print(f"Jarvis{time_str}: {result['response']}\n")


if __name__ == "__main__":
    main()
