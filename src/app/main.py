import logging

from app.features.scanner import run_scanner_app
from app.shared.config import Settings, get_settings


def main(settings: Settings | None = None) -> None:
    """Composition root: configura logging, carrega Settings e inicia o ClickOn."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    resolved_settings = settings or get_settings()
    run_scanner_app(resolved_settings)


if __name__ == "__main__":
    main()
