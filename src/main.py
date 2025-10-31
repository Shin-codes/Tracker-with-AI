from .cli import run_cli
from .chatbot import run_chatbot


def main() -> None:
    print("Choose mode:")
    print("1. CLI Menu")
    print("2. Chatbot Assistant")
    choice = input("> ").strip()
    if choice == "2":
        run_chatbot()
    else:
        run_cli()


if __name__ == "__main__":
    main()


