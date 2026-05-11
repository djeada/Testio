# Contributing to Testio

## Setup
```bash
git clone https://github.com/djeida/Testio.git
cd Testio
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests
```bash
make test
```

## Code style
This project uses [black](https://black.readthedocs.io/) for formatting and [ruff](https://docs.astral.sh/ruff/) for linting.

```bash
make fmt   # format
make lint  # check
```

## Submitting changes
1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure `make test` and `make lint` pass
5. Open a pull request against `main`
