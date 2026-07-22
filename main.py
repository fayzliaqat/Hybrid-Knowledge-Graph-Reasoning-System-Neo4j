import os
from middle_layer import load_kb, load_bot, chat, close_neo4j

def main():
    print("-" * 55)
    print("  NEO4J GRAPH KNOWLEDGE BASE — HYBRID AI CHATBOT")
    print("-" * 55)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path          = os.path.join(base_dir, "family_kb.pl")
    aiml_chat        = os.path.join(base_dir, "chat.aiml")
    aiml_data_entry  = os.path.join(base_dir, "dataentry.aiml")

    try:
        # Initialize and test connection drivers
        load_kb(kb_path)
        load_bot([aiml_chat, aiml_data_entry])
    except FileNotFoundError as e:
        print(f"[ERROR] File execution path error: {e}")
        print("Ensure family_kb.pl, chat.aiml, and dataentry.aiml are inside the workspace folder.")
        close_neo4j()
        return
    except Exception as db_err:
        print(f"[DATABASE ERROR] Connection failed: {db_err}")
        return

    print("\nGraph System ready! Type 'help' for options. Type 'bye' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Allah Hafiz!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"bye", "exit", "quit"}:
            print("\nBot: Allah Hafiz! Come back anytime.")
            break

        response = chat(user_input)
        print(f"\nBot: {response}\n")

    # Safe release of driver pools
    close_neo4j()

if __name__ == "__main__":
    main()