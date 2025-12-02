from dockerfile_optimizer import *  # Re-export core analysis helpers


def main() -> None:
    """
    Thin wrapper around `dockerfile_optimizer.main`.

    This keeps backward compatibility for any scripts that still invoke
    `optimizer.py` directly, while avoiding duplicate logic.
    """
    from dockerfile_optimizer import main as _main

    _main()


if __name__ == "__main__":
    main()