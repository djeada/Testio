def main():
    # Parse command-line arguments
    args = parse_args()

    # Dispatch to the appropriate subapplication
    if args.cli:
        cli.run()
    elif args.flask:
        flask_app.run()
    elif args.qt:
        qt_app.run()