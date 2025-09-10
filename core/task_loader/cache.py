"""
Task cache management for local storage
"""
import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger


class TaskCache:
    """Task cache manager for local file system storage"""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self._cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Dict[str, str]]:
        """Load cache index from file"""
        try:
            if self.cache_index_file.exists():
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load cache index: {e}")
            return {}
    
    def _save_cache_index(self):
        """Save cache index to file"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self._cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def get_cache_path(self, item_id: str) -> str:
        """Get cache path for item"""
        return str(self.cache_dir / item_id)
    
    def is_cached(self, item_id: str) -> bool:
        """Check if item is cached"""
        cache_path = Path(self.get_cache_path(item_id))
        return cache_path.exists() and item_id in self._cache_index
    
    def mark_cached(self, item_id: str, metadata: Optional[Dict[str, str]] = None):
        """Mark item as cached in index"""
        self._cache_index[item_id] = {
            "cached_at": datetime.utcnow().isoformat(),
            "path": self.get_cache_path(item_id),
            **(metadata or {})
        }
        self._save_cache_index()
    
    def get_cache_info(self, item_id: str) -> Optional[Dict[str, str]]:
        """Get cache information for item"""
        return self._cache_index.get(item_id)
    
    def remove_from_cache(self, item_id: str) -> bool:
        """Remove item from cache"""
        try:
            cache_path = Path(self.get_cache_path(item_id))
            if cache_path.exists():
                shutil.rmtree(cache_path)
            
            if item_id in self._cache_index:
                del self._cache_index[item_id]
                self._save_cache_index()
            
            logger.info(f"Removed from cache: {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove from cache {item_id}: {e}")
            return False
    
    def clear_cache(self):
        """Clear entire cache"""
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            self._cache_index = {}
            self._save_cache_index()
            logger.info("Cache cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cached_items(self) -> List[str]:
        """Get list of cached item IDs"""
        return list(self._cache_index.keys())
    
    def get_cache_size(self) -> int:
        """Get total cache size in bytes"""
        try:
            total_size = 0
            for item_id in self._cache_index:
                cache_path = Path(self.get_cache_path(item_id))
                if cache_path.exists():
                    for file_path in cache_path.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
            return total_size
        except Exception as e:
            logger.error(f"Failed to calculate cache size: {e}")
            return 0
    
    def cleanup_old_cache(self, days: int = 7) -> int:
        """Cleanup cache items older than specified days"""
        try:
            from datetime import timedelta
            
            threshold = datetime.utcnow() - timedelta(days=days)
            removed_count = 0
            
            items_to_remove = []
            for item_id, info in self._cache_index.items():
                try:
                    cached_at = datetime.fromisoformat(info.get("cached_at", ""))
                    if cached_at < threshold:
                        items_to_remove.append(item_id)
                except ValueError:
                    # Invalid date format, remove it
                    items_to_remove.append(item_id)
            
            for item_id in items_to_remove:
                if self.remove_from_cache(item_id):
                    removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} old cache items")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old cache: {e}")
            return 0
    
    def validate_cache_integrity(self) -> List[str]:
        """Validate cache integrity and return list of corrupted items"""
        corrupted_items = []
        
        for item_id in list(self._cache_index.keys()):
            cache_path = Path(self.get_cache_path(item_id))
            
            # Check if path exists
            if not cache_path.exists():
                logger.warning(f"Cache path missing for {item_id}: {cache_path}")
                corrupted_items.append(item_id)
                continue
            
            # Check if required files exist (depending on type)
            required_files = []
            if (cache_path / "task.py").exists():
                required_files = ["task.py"]
            elif (cache_path / "pipeline.py").exists():
                required_files = ["pipeline.py"]
            
            for required_file in required_files:
                if not (cache_path / required_file).exists():
                    logger.warning(f"Required file missing for {item_id}: {required_file}")
                    corrupted_items.append(item_id)
                    break
        
        # Remove corrupted items from index
        for item_id in corrupted_items:
            if item_id in self._cache_index:
                del self._cache_index[item_id]
        
        if corrupted_items:
            self._save_cache_index()
            logger.info(f"Removed {len(corrupted_items)} corrupted cache entries")
        
        return corrupted_items