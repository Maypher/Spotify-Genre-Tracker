import cli
from dotenv import load_dotenv

def main():
    load_dotenv()

    program = cli.Program()
    program.run()


if __name__ == "__main__":
    main()
