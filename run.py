import argparse

import uvicorn

from app.core.settings.app import app_settings
import logging

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Laptrinhai Mezon Bot server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload on code changes"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of worker processes (default: 1)"
    )
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()

    reload = args.reload if args.reload is not None else app_settings.debug

    logger.info(f"Starting {app_settings.app_name} on {args.host}:{args.port}")
    logger.info(f"Debug mode: {reload}")
    logger.info(f"Workers: {args.workers}")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=reload,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
