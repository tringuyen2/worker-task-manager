# api_server.py - REST API Server for AI Task Worker
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any
import threading
import time

from config import load_config, TaskConfig
from database import DatabaseManager
from storage import StorageManager
from ai_worker import AIWorker

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global worker instance
worker: AIWorker = None
db_manager: DatabaseManager = None
storage_manager: StorageManager = None

def initialize_services():
    """Initialize all services"""
    global worker, db_manager, storage_manager
    
    try:
        # Load config
        config = load_config("config/api.json")
        
        # Initialize managers
        db_manager = DatabaseManager(config)
        storage_manager = StorageManager(config)
        
        # Initialize worker
        worker = AIWorker("config/api.json")
        
        if not worker.initialize():
            logger.error("Failed to initialize AI Worker")
            return False
        
        logger.info("✅ API services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        return False

# API Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check worker status
        worker_status = "healthy" if worker and worker.running else "unhealthy"
        
        # Check database connection
        db_status = "healthy" if db_manager and db_manager.client else "unhealthy"
        
        # Check storage connection
        storage_status = "healthy" if storage_manager and storage_manager.client else "unhealthy"
        
        overall_status = "healthy" if all([
            worker_status == "healthy",
            db_status == "healthy", 
            storage_status == "healthy"
        ]) else "unhealthy"
        
        return jsonify({
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "worker": worker_status,
                "database": db_status,
                "storage": storage_status
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """List all available tasks"""
    try:
        if not worker:
            return jsonify({"error": "Worker not initialized"}), 500
        
        result = worker.list_tasks()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/registered', methods=['GET'])
def list_registered_tasks():
    """List all registered tasks in database"""
    try:
        if not db_manager:
            return jsonify({"error": "Database not initialized"}), 500
        
        tasks = db_manager.list_all_tasks()
        
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": task.task_id,
                "task_name": task.task_name,
                "description": task.description,
                "version": task.version,
                "enabled": task.enabled,
                "created_at": task.created_at.isoformat(),
                "requirements": task.requirements,
                "metadata": task.metadata
            })
        
        return jsonify({
            "tasks": task_list,
            "total": len(task_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing registered tasks: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_info(task_id: str):
    """Get detailed information about a task"""
    try:
        if not db_manager:
            return jsonify({"error": "Database not initialized"}), 500
        
        task_config = db_manager.get_task(task_id)
        if not task_config:
            return jsonify({"error": f"Task not found: {task_id}"}), 404
        
        # Check if task is loaded
        is_loaded = worker and worker.task_loader and task_id in worker.task_loader.list_loaded_tasks()
        
        # Get execution history
        execution_history = db_manager.get_execution_history(task_id, limit=10)
        
        return jsonify({
            "task_id": task_config.task_id,
            "task_name": task_config.task_name,
            "description": task_config.description,
            "version": task_config.version,
            "enabled": task_config.enabled,
            "loaded": is_loaded,
            "created_at": task_config.created_at.isoformat(),
            "updated_at": task_config.updated_at.isoformat(),
            "requirements": task_config.requirements,
            "metadata": task_config.metadata,
            "execution_count": len(execution_history),
            "recent_executions": [
                {
                    "execution_id": exec.execution_id,
                    "status": exec.status,
                    "execution_time": exec.execution_time,
                    "timestamp": exec.timestamp.isoformat(),
                    "error_message": exec.error_message
                } for exec in execution_history
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting task info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/<task_id>/process', methods=['POST'])
def process_task(task_id: str):
    """Process a task with input data"""
    try:
        if not worker:
            return jsonify({"error": "Worker not initialized"}), 500
        
        # Get input data from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        input_data = data.get('input')
        async_mode = data.get('async', False)
        
        if async_mode:
            # Process asynchronously
            execution_id = worker.process_task_async(task_id, input_data)
            return jsonify({
                "async": True,
                "execution_id": execution_id,
                "message": "Task started asynchronously"
            })
        else:
            # Process synchronously
            result = worker.process_task(task_id, input_data)
            return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/executions/<execution_id>', methods=['GET'])
def get_execution_result(execution_id: str):
    """Get execution result by execution ID"""
    try:
        if not db_manager:
            return jsonify({"error": "Database not initialized"}), 500
        
        # Find execution in database
        execution = db_manager.executions_collection.find_one({"execution_id": execution_id})
        
        if not execution:
            return jsonify({"error": f"Execution not found: {execution_id}"}), 404
        
        execution.pop("_id", None)  # Remove MongoDB _id
        
        return jsonify(execution)
        
    except Exception as e:
        logger.error(f"Error getting execution result: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/<task_id>/reload', methods=['POST'])
def reload_task(task_id: str):
    """Reload a specific task"""
    try:
        if not worker:
            return jsonify({"error": "Worker not initialized"}), 500
        
        result = worker.reload_task(task_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error reloading task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/register', methods=['POST'])
def register_task():
    """Register a new task via API"""
    try:
        if not request.files.get('task_zip'):
            return jsonify({"error": "No task zip file provided"}), 400
        
        task_zip = request.files['task_zip']
        task_info = request.form.to_dict()
        
        if not all(key in task_info for key in ['task_id', 'task_name', 'description']):
            return jsonify({"error": "Missing required task information"}), 400
        
        # Save uploaded file
        temp_zip_path = f"/tmp/{task_info['task_id']}.zip"
        task_zip.save(temp_zip_path)
        
        # Upload to storage
        if not storage_manager.upload_task_zip(task_info['task_id'], temp_zip_path):
            os.remove(temp_zip_path)
            return jsonify({"error": "Failed to upload task to storage"}), 500
        
        # Create task config
        task_config = TaskConfig(
            task_id=task_info['task_id'],
            task_name=task_info['task_name'],
            description=task_info['description'],
            version=task_info.get('version', '1.0.0'),
            zip_file=f"{task_info['task_id']}.zip",
            entry_point=task_info.get('entry_point', 'task.py'),
            requirements=task_info.get('requirements', '').split(',') if task_info.get('requirements') else [],
            metadata={}
        )
        
        # Register in database
        if not db_manager.register_task(task_config):
            return jsonify({"error": "Failed to register task in database"}), 500
        
        # Cleanup temp file
        os.remove(temp_zip_path)
        
        return jsonify({
            "success": True,
            "message": f"Task registered successfully: {task_info['task_id']}",
            "task_id": task_info['task_id']
        })
        
    except Exception as e:
        logger.error(f"Error registering task: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tasks/<task_id>/download', methods=['GET'])
def download_task_zip(task_id: str):
    """Download task zip file"""
    try:
        if not storage_manager:
            return jsonify({"error": "Storage not initialized"}), 500
        
        # Download from storage to temp file
        temp_zip_path = f"/tmp/{task_id}_download.zip"
        
        if not storage_manager.download_task_zip(task_id, temp_zip_path):
            return jsonify({"error": "Failed to download task"}), 404
        
        return send_file(
            temp_zip_path,
            as_attachment=True,
            download_name=f"{task_id}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Error downloading task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/workers', methods=['GET'])
def list_workers():
    """List all registered workers"""
    try:
        if not db_manager:
            return jsonify({"error": "Database not initialized"}), 500
        
        workers = list(db_manager.workers_collection.find())
        
        worker_list = []
        for w in workers:
            w.pop("_id", None)
            worker_list.append(w)
        
        return jsonify({
            "workers": worker_list,
            "total": len(worker_list)
        })
        
    except Exception as e:
        logger.error(f"Error listing workers: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        if not db_manager:
            return jsonify({"error": "Database not initialized"}), 500
        
        # Count tasks
        total_tasks = db_manager.tasks_collection.count_documents({})
        enabled_tasks = db_manager.tasks_collection.count_documents({"enabled": True})
        
        # Count executions
        total_executions = db_manager.executions_collection.count_documents({})
        successful_executions = db_manager.executions_collection.count_documents({"status": "success"})
        failed_executions = db_manager.executions_collection.count_documents({"status": "error"})
        
        # Count workers
        total_workers = db_manager.workers_collection.count_documents({})
        online_workers = db_manager.workers_collection.count_documents({"status": "running"})
        
        return jsonify({
            "tasks": {
                "total": total_tasks,
                "enabled": enabled_tasks,
                "disabled": total_tasks - enabled_tasks
            },
            "executions": {
                "total": total_executions,
                "successful": successful_executions,
                "failed": failed_executions,
                "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0
            },
            "workers": {
                "total": total_workers,
                "online": online_workers,
                "offline": total_workers - online_workers
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Initialize services
    if not initialize_services():
        logger.error("Failed to initialize API server")
        exit(1)
    
    # Start API server
    logger.info("🚀 Starting AI Task API Server...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)