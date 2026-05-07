"""
Structured logging met structlog.
- Productie: JSON output (parseable door log aggregators)
- Dev: gekleurde console output (leesbaar)
- Elke log entry heeft request_id wanneer beschikbaar
"""
import logging
import sys
import structlog


def setup_logging(level: str = "INFO", fmt: str = "json"):
    """Configureer structlog voor de hele applicatie."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Stdlib logging config (structlog wraps dit)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors voor alle log entries
    shared_processors = [
        structlog.contextvars.merge_contextvars,  # request_id e.d.
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if fmt == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "app"):
    """Haal een logger op."""
    return structlog.get_logger(name)
