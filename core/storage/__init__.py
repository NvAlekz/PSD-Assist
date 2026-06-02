"""
Pokemon Showdown Assistant - Storage Module
Sistema de persistencia para partidas
"""

import json
import os
from typing import List, Optional
from datetime import datetime
from ..battle_state import BattleState


class BattleStorage:
    """
    Almacenamiento de batallas jugadas
    
    Guarda en archivos JSON para facilitar análisis
    """
    
    def __init__(self, storage_dir: str = "data/battles"):
        self.storage_dir = storage_dir
        self.ensure_storage_dir()
    
    def ensure_storage_dir(self) -> None:
        """Crea el directorio de almacenamiento si no existe"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_battle(self, state: BattleState) -> str:
        """
        Guarda una batalla
        
        Args:
            state: Estado final de la batalla
            
        Returns:
            Path del archivo guardado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        battle_id = state.battle_id or f"battle_{timestamp}"
        
        filename = f"{battle_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_battle(self, battle_id: str) -> Optional[BattleState]:
        """
        Carga una batalla guardada
        
        Args:
            battle_id: Identificador de la batalla
            
        Returns:
            BattleState o None si no existe
        """
        filepath = os.path.join(self.storage_dir, f"{battle_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return BattleState.from_dict(data)
    
    def list_battles(self) -> List[Dict]:
        """
        Lista todas las batallas guardadas
        
        Returns:
            Lista de información de batallas
        """
        battles = []
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                battles.append({
                    'id': filename.replace('.json', ''),
                    'timestamp': data.get('timestamp', 0),
                    'turn': data.get('turn', 0),
                    'myPokemon': data.get('myTeam', {}).get('pokemons', [{}])[0].get('name') if data.get('myTeam', {}).get('pokemons') else None,
                    'enemyPokemon': data.get('enemyTeam', {}).get('pokemons', [{}])[0].get('name') if data.get('enemyTeam', {}).get('pokemons') else None,
                    'winner': self.determine_winner(data)
                })
        
        return sorted(battles, key=lambda x: x['timestamp'], reverse=True)
    
    def determine_winner(self, data: Dict) -> Optional[str]:
        """Determina el ganador de una batalla"""
        my_fainted = all(p.get('fainted', False) for p in data.get('myTeam', {}).get('pokemons', []))
        enemy_fainted = all(p.get('fainted', False) for p in data.get('enemyTeam', {}).get('pokemons', []))
        
        if my_fainted:
            return 'enemy'
        elif enemy_fainted:
            return 'player'
        return None
    
    def delete_battle(self, battle_id: str) -> bool:
        """Elimina una batalla guardada"""
        filepath = os.path.join(self.storage_dir, f"{battle_id}.json")
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    
    def export_to_csv(self, filepath: str) -> None:
        """
        Exporta historial de batallas a CSV
        
        Args:
            filepath: Path del archivo CSV
        """
        battles = self.list_battles()
        
        if not battles:
            return
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("ID,Timestamp,Turns,MyPokemon,EnemyPokemon,Winner\n")
            
            for battle in battles:
                timestamp = datetime.fromtimestamp(battle['timestamp'] / 1000).strftime("%Y-%m-%d %H:%M")
                f.write(f"{battle['id']},{timestamp},{battle['turn']},{battle['myPokemon']},{battle['enemyPokemon']},{battle['winner']}\n")
    
    def get_stats(self) -> Dict:
        """Calcula estadísticas del historial"""
        battles = self.list_battles()
        
        if not battles:
            return {
                'total': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0
            }
        
        wins = sum(1 for b in battles if b['winner'] == 'player')
        losses = sum(1 for b in battles if b['winner'] == 'enemy')
        
        return {
            'total': len(battles),
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / len(battles)) * 100 if battles else 0
        }