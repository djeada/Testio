import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "script", type=str, choices=["cli", "fastapi"], help="Script to run"
    )
    args, extra_args = parser.parse_known_args()

    if args.script == "cli":
        from apps.cli.main import main as cli_main

        cli_main(extra_args)

    elif args.script == "fastapi":
        from apps.server.main import main as fastapi_main

        fastapi_main(extra_args)


if __name__ == "__main__":
    main()
