#!/usr/bin/env python3
"""
Logging Configuration Module
Centralized logging setup for the AI Task Worker System
"""
import os
import sys
from pathlib import Path
from loguru import logger


class LoggerConfig:
    """Centralized logger configuration"""

    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root
        self.logs_dir = project_root / "logs"

        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)

        # Log file paths
        self.worker_log = self.logs_dir / "worker.log"
        self.celery_log = self.logs_dir / "celery.log"
        self.system_log = self.logs_dir / "system.log"

    def setup_worker_logging(self, level: str = "INFO", console: bool = True):
        """Setup logging for worker processes"""
        # Remove default logger
        logger.remove()

        # Console logging
        if console:
            logger.add(
                sys.stdout,
                level=level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>WORKER</cyan> | {message}",
                colorize=True
            )

        # File logging
        logger.add(
            self.worker_log,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | WORKER | {message}",
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )

        return logger

    def setup_celery_logging(self, level: str = "INFO", console: bool = True):
        """Setup logging for Celery processes"""
        # Remove default logger
        logger.remove()

        # Console logging
        if console:
            logger.add(
                sys.stdout,
                level=level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <magenta>CELERY</magenta> | {message}",
                colorize=True
            )

        # File logging
        logger.add(
            self.celery_log,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | CELERY | {message}",
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )

        return logger

    def setup_system_logging(self, level: str = "INFO", console: bool = True):
        """Setup logging for system components"""
        # Remove default logger
        logger.remove()

        # Console logging
        if console:
            logger.add(
                sys.stdout,
                level=level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <blue>SYSTEM</blue> | {message}",
                colorize=True
            )

        # File logging
        logger.add(
            self.system_log,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | SYSTEM | {message}",
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )

        return logger

    def setup_generic_logging(self, component: str = "APP", level: str = "INFO", console: bool = True):
        """Setup generic logging for any component"""
        # Remove default logger
        logger.remove()

        # Console logging
        if console:
            logger.add(
                sys.stdout,
                level=level,
                format=f"<green>{{time:YYYY-MM-DD HH:mm:ss}}</green> | <level>{{level: <8}}</level> | <yellow>{component}</yellow> | {{message}}",
                colorize=True
            )

        # File logging - write to system.log for generic components
        logger.add(
            self.system_log,
            level=level,
            format=f"{{time:YYYY-MM-DD HH:mm:ss}} | {{level: <8}} | {component} | {{message}}",
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )

        return logger


# Global logger config instance
logger_config = LoggerConfig()


def get_worker_logger(level: str = "INFO", console: bool = True):
    """Get configured worker logger"""
    return logger_config.setup_worker_logging(level, console)


def get_celery_logger(level: str = "INFO", console: bool = True):
    """Get configured Celery logger"""
    return logger_config.setup_celery_logging(level, console)


def get_system_logger(level: str = "INFO", console: bool = True):
    """Get configured system logger"""
    return logger_config.setup_system_logging(level, console)


def get_logger(component: str = "APP", level: str = "INFO", console: bool = True):
    """Get configured generic logger"""
    return logger_config.setup_generic_logging(component, level, console)


# Environment variable support
def get_log_level():
    """Get log level from environment variable"""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_console_logging():
    """Check if console logging is enabled via environment variable"""
    return os.getenv("LOG_CONSOLE", "true").lower() in ("true", "1", "yes", "on")