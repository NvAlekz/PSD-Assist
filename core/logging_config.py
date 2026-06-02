"""
Pokemon Showdown Assistant - Logging Module
Sistema de logging estructurado con niveles configurables
"""

import logging
import os
from typing import Optional
from datetime import datetime
from pathlib import Path


class BattleLogger:
    """
    Logger estructurado para el asistente
    
    Proporciona logging con niveles configurables,
    rotación de archivos y formateo consistente
    """
    
    _instance: Optional['BattleLogger'] = None
    
    def __init__(self, name: str = 'PSD-Assist', log_dir: str = 'logs'):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    @classmethod
    def get_instance(cls, **kwargs) -> 'BattleLogger':
        """Obtiene instancia singleton del logger"""
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance
    
    def _setup_handlers(self):
        """Configura los handlers de logging"""
        # Handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Handler de archivo
        log_file = self.log_dir / f'{self.name}_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """Log de información"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log de warning"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log de error"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log de error crítico"""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Formatea mensaje con contexto adicional"""
        parts = [message]
        if kwargs:
            context = ', '.join(f'{k}={v}' for k, v in kwargs.items())
            parts.append(f'[{context}]')
        return ' '.join(parts)
    
    def log_battle_event(self, event_type: str, data: dict):
        """Log específico para eventos de batalla"""
        self.info(f"BATTLE_EVENT: {event_type}", **data)
    
    def log_recommendation(self, recommendation: dict):
        """Log específico para recomendaciones"""
        self.debug(
            f"RECOMMENDATION: {recommendation.get('action', 'unknown')}",
            score=recommendation.get('score', 0),
            reason=recommendation.get('reason', 'N/A')
        )
    
    def set_level(self, level: str):
        """Cambia el nivel de logging"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
    
    def rotate_logs(self, keep: int = 7):
        """Rota los logs, manteniendo los últimos N archivos"""
        log_files = sorted(
            self.log_dir.glob(f'{self.name}_*.log'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for old_file in log_files[keep:]:
            old_file.unlink()
            self.info(f"Rotated out: {old_file.name}")
    
    def get_recent_logs(self, lines: int = 100) -> str:
        """Obtiene las últimas líneas de log"""
        today_log = self.log_dir / f'{self.name}_{datetime.now().strftime("%Y%m%d")}.log'
        
        if not today_log.exists():
            return ""
        
        with open(today_log, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])


# Función helper para uso rápido
def get_logger(name: str = 'PSD-Assist', **kwargs) -> BattleLogger:
    """Obtiene o crea un logger"""
    return BattleLogger.get_instance(name=name, **kwargs)