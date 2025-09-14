#!/usr/bin/env python3
"""
Worker Startup Script
Start individual task workers or all workers
"""
import sys
import argparse
import subprocess
import signal
import time
import psutil
from pathlib import Path
from typing import List, Optional
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config.manager import get_config
from worker.task_registry import task_registry


class WorkerManager:
    """Manage Celery worker processes"""

    def __init__(self):
        self.config = get_config().worker
        self.processes: List[subprocess.Popen] = []

    def start_task_worker(self, task_id: str, **kwargs) -> Optional[subprocess.Popen]:
        """Start a worker for a specific task"""
        try:
            task_config = self.config.task_configs.get(task_id)
            if not task_config or not getattr(task_config, 'enabled', True):
                logger.warning(f"Task {task_id} is not enabled or configured")
                return None

            queue = getattr(task_config, 'queue', task_id)
            concurrency = kwargs.get('concurrency', 1)
            log_level = kwargs.get('log_level', 'INFO')

            cmd = [
                sys.executable, '-m', 'celery',
                '-A', 'worker.celery_app:celery_app',
                'worker',
                '--loglevel', log_level,
                '-Q', queue,
                '-c', str(concurrency),
                '-n', f"{task_id}_worker@%h",
                '--without-gossip',
                '--without-mingle',
                '--pool=prefork'  # Use prefork for better isolation
            ]

            # Add memory limit if specified
            if hasattr(task_config, 'memory_limit') and task_config.memory_limit:
                cmd.extend(['--max-memory-per-child', str(task_config.memory_limit)])

            # Add task timeout
            if hasattr(task_config, 'timeout') and task_config.timeout:
                cmd.extend(['--time-limit', str(task_config.timeout)])

            logger.info(f"Starting worker for task {task_id}: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE if kwargs.get('capture_output', False) else None,
                stderr=subprocess.PIPE if kwargs.get('capture_output', False) else None
            )

            self.processes.append(process)
            logger.info(f"Started worker for {task_id} with PID: {process.pid}")
            return process

        except Exception as e:
            logger.error(f"Failed to start worker for {task_id}: {e}")
            return None

    def start_all_workers(self, **kwargs) -> List[subprocess.Popen]:
        """Start workers for all active tasks"""
        started_workers = []

        for task_id in self.config.active_tasks:
            process = self.start_task_worker(task_id, **kwargs)
            if process:
                started_workers.append(process)
                time.sleep(1)  # Stagger startup

        return started_workers

    def stop_all_workers(self):
        """Stop all worker processes"""
        logger.info("Stopping all workers...")

        for process in self.processes:
            try:
                if process.poll() is None:  # Process is still running
                    logger.info(f"Stopping worker with PID: {process.pid}")
                    process.terminate()

                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing worker PID: {process.pid}")
                        process.kill()

            except Exception as e:
                logger.error(f"Error stopping worker {process.pid}: {e}")

        self.processes.clear()

    def monitor_workers(self):
        """Monitor worker health"""
        while True:
            try:
                alive_count = 0
                for i, process in enumerate(self.processes[:]):
                    if process.poll() is None:
                        alive_count += 1
                    else:
                        logger.warning(f"Worker {process.pid} died with exit code {process.returncode}")
                        self.processes.remove(process)

                logger.info(f"Active workers: {alive_count}")
                time.sleep(30)  # Check every 30 seconds

            except KeyboardInterrupt:
                logger.info("Stopping worker monitoring...")
                self.stop_all_workers()
                break
            except Exception as e:
                logger.error(f"Error in worker monitoring: {e}")
                time.sleep(5)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Worker Management Script')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'monitor'],
                       help='Action to perform')
    parser.add_argument('--task', type=str, help='Specific task to manage (default: all)')
    parser.add_argument('--concurrency', type=int, default=1,
                       help='Number of concurrent processes per worker')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Log level')
    parser.add_argument('--capture-output', action='store_true',
                       help='Capture worker output (for debugging)')

    args = parser.parse_args()

    # Configure logging
    logger.add(sys.stdout, level=args.log_level)

    manager = WorkerManager()

    try:
        if args.action == 'start':
            logger.info("Starting workers...")

            # Load and register tasks first
            task_registry.load_and_register_tasks()

            if args.task:
                manager.start_task_worker(
                    args.task,
                    concurrency=args.concurrency,
                    log_level=args.log_level,
                    capture_output=args.capture_output
                )
            else:
                manager.start_all_workers(
                    concurrency=args.concurrency,
                    log_level=args.log_level,
                    capture_output=args.capture_output
                )

            logger.info("Workers started successfully")

        elif args.action == 'stop':
            logger.info("Stopping workers...")
            manager.stop_all_workers()
            logger.info("Workers stopped")

        elif args.action == 'monitor':
            logger.info("Starting worker monitoring...")

            # Start workers if not specified otherwise
            if not args.task:
                task_registry.load_and_register_tasks()
                manager.start_all_workers(
                    concurrency=args.concurrency,
                    log_level=args.log_level
                )

            manager.monitor_workers()

        elif args.action == 'status':
            logger.info("Checking worker status...")

            # Check for running Celery processes
            celery_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'celery' in proc.info['name'] or any('celery' in arg for arg in proc.info['cmdline']):
                        celery_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if celery_processes:
                logger.info(f"Found {len(celery_processes)} running Celery processes:")
                for proc in celery_processes:
                    logger.info(f"  PID {proc.info['pid']}: {' '.join(proc.info['cmdline'])}")
            else:
                logger.info("No Celery processes found")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        manager.stop_all_workers()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()