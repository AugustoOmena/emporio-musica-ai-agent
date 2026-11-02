import sys
from dotenv import load_dotenv
from src.agent import StoreAgent

load_dotenv()


def main():
    print("=" * 60)
    print("🎸 Empório da Música - Terminal Assistant")
    print("Digite 'sair' ou pressione Ctrl+C para encerrar.")
    print("=" * 60)

    agent = StoreAgent()
    history = []

    while True:
        try:
            user_input = input("\nCliente: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["sair", "exit", "quit"]:
                print("Atendimento encerrado.")
                break

            history.append({"role": "user", "content": user_input})
            reply, history = agent.run_conversation_turn(history)
            print(f"\nEmpório da Música: {reply}")

        except KeyboardInterrupt:
            print("\nAtendimento encerrado.")
            sys.exit(0)


if __name__ == "__main__":
    main()