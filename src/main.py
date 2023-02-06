import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "script", type=str, choices=["cli", "flask", "gui"], help="Script to run"
    )
    args, extra_args = parser.parse_known_args()

    if args.script == "cli":
        from apps.cli.main import main as cli_main

        cli_main(extra_args)

    elif args.script == "flask":
        from apps.server.main import main as flask_main

        flask_main(extra_args)

    elif args.script == "gui":
        from apps.gui.main import main as gui_main

        gui_main(extra_args)


if __name__ == "__main__":
    main()
