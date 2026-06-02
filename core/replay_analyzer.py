"""
Pokemon Showdown Assistant - Replay Analyzer
Analiza replays de batallas para aprender patrones y estrategias
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class ReplayMove:
    """Representa un movimiento en el replay"""
    turn: int
    player: str  # 'player' o 'enemy'
    pokemon: str
    move: str
    result: str  # 'hit', 'miss', 'ko', 'status', 'switch'
    damage_dealt: Optional[int] = None
    effectiveness: Optional[str] = None


@dataclass
class ReplayAnalysis:
    """Análisis de un replay completo"""
    replay_id: str
    date: datetime
    winner: str
    duration_turns: int
    
    # Equipos
    player_team: List[str] = field(default_factory=list)
    enemy_team: List[str] = field(default_factory=list)
    
    # Análisis de movimientos
    total_moves: int = 0
    accurate_moves: int = 0
    ko_moves: int = 0
    super_effective_moves: int = 0
    
    # Análisis de switches
    total_switches: int = 0
    optimal_switches: int = 0
    
    # Patrones detectados
    patterns: List[str] = field(default_factory=list)
    
    # Recomendaciones
    improvements: List[str] = field(default_factory=list)


class ReplayAnalyzer:
    """
    Analizador de replays
    
    Analiza batallas guardadas para identificar:
    - Patrones de juego
    - Errores estratégicos
    - Decisiones subóptimas
    - Oportunidades de mejora
    """
    
    def __init__(self, replay_dir: str = 'data/replays'):
        self.replay_dir = replay_dir
        self.replays: List[ReplayAnalysis] = []
        self.move_patterns: Dict[str, int] = defaultdict(int)
        self.switch_patterns: Dict[str, int] = defaultdict(int)
        
        os.makedirs(replay_dir, exist_ok=True)
    
    def load_replay(self, replay_path: str) -> Optional[ReplayAnalysis]:
        """Carga y analiza un replay desde archivo"""
        if not os.path.exists(replay_path):
            return None
        
        try:
            with open(replay_path, 'r') as f:
                data = json.load(f)
            return self.analyze_replay_data(data)
        except Exception as e:
            print(f"Error loading replay: {e}")
            return None
    
    def analyze_replay_data(self, data: Dict) -> ReplayAnalysis:
        """Analiza datos crudos de un replay"""
        analysis = ReplayAnalysis(
            replay_id=data.get('id', str(datetime.now().timestamp())),
            date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            winner=data.get('winner', 'unknown'),
            duration_turns=data.get('turn', 0),
            player_team=data.get('player_team', []),
            enemy_team=data.get('enemy_team', [])
        )
        
        # Analizar historial de turnos
        history = data.get('history', [])
        moves = [h for h in history if h.get('type') == 'move']
        switches = [h for h in history if h.get('type') == 'switch']
        
        analysis.total_moves = len(moves)
        analysis.total_switches = len(switches)
        
        # Analizar accuracy
        for move in moves:
            if move.get('result') == 'hit':
                analysis.accurate_moves += 1
            if move.get('result') == 'ko':
                analysis.ko_moves += 1
            if move.get('effectiveness') == 'super_effective':
                analysis.super_effective_moves += 1
        
        # Detectar patrones
        analysis.patterns = self.detect_patterns(history)
        
        # Generar mejoras
        analysis.improvements = self.suggest_improvements(analysis)
        
        self.replays.append(analysis)
        return analysis
    
    def detect_patterns(self, history: List[Dict]) -> List[str]:
        """Detecta patrones en el historial"""
        patterns = []
        
        # 1. Patrón de predicción de switch
        switch_count = sum(1 for h in history if h.get('type') == 'switch')
        if switch_count > 3:
            patterns.append(" много переключений (возможно слишком агрессивный стиль)")
        
        # 2. Patrón de uso de mismo movimiento
        move_counts = defaultdict(int)
        for h in history:
            if h.get('type') == 'move':
                move_counts[h.get('move', '')] += 1
        
        for move, count in move_counts.items():
            if count >= 4:
                patterns.append(f"Использовал {move} {count} раз")
        
        # 3. Patrón de estado
        status_moves = [h for h in history if h.get('result') == 'status']
        if len(status_moves) > 2:
            patterns.append(f"Использовал {len(status_moves)} статусных движений")
        
        # 4. Patrón de daño
        ko_count = sum(1 for h in history if h.get('result') == 'ko')
        if ko_count >= 3:
            patterns.append("Высокий показатель KO")
        
        return patterns
    
    def suggest_improvements(self, analysis: ReplayAnalysis) -> List[str]:
        """Sugiere mejoras basadas en el análisis"""
        improvements = []
        
        # 1. Accuracy bajo
        if analysis.total_moves > 0:
            accuracy = analysis.accurate_moves / analysis.total_moves
            if accuracy < 0.8:
                improvements.append("Низкая точность атак - рассмотрите более надежные движения")
        
        # 2. Pocos movimientos superefectivos
        if analysis.total_moves > 5:
            se_ratio = analysis.super_effective_moves / analysis.total_moves
            if se_ratio < 0.15:
                improvements.append("Используйте больше суперэффективных атак против команд противника")
        
        # 3. Muchos switches
        if analysis.total_switches > analysis.duration_turns * 0.3:
            improvements.append("Слишком много переключений - рассмотрите оставление покемона")
        
        # 4. Pocos KOs
        if analysis.ko_moves == 0 and analysis.duration_turns > 10:
            improvements.append("Не добили ни одного KO - увеличьте агрессию")
        
        return improvements
    
    def get_common_mistakes(self) -> Dict[str, List[str]]:
        """Identifica errores comunes en replays"""
        mistakes = defaultdict(list)
        
        for replay in self.replays:
            for imp in replay.improvements:
                # Categorizar mejora como error
                if "точность" in imp.lower():
                    mistakes['accuracy'].append(replay.replay_id)
                elif "суперэффективных" in imp.lower():
                    mistakes['type_matchup'].append(replay.replay_id)
                elif "переключений" in imp.lower():
                    mistakes['over_switching'].append(replay.replay_id)
        
        return dict(mistakes)
    
    def learn_optimal_moves(self, team: List[str]) -> Dict[str, List[Tuple[str, int]]]:
        """
        Aprende movimientos óptimos para un equipo
        
        Returns:
            Diccionario de {pokemon: [(move, win_count)]}
        """
        optimal_moves = defaultdict(list)
        
        for replay in self.replays:
            if replay.winner == 'player':
                for pkm in replay.player_team:
                    # Contar movimientos ganados
                    pass  # Simplificado por ahora
        
        return dict(optimal_moves)
    
    def get_win_rate_by_pokemon(self) -> Dict[str, float]:
        """Calcula win rate por Pokemon"""
        pkm_stats = defaultdict(lambda: {'wins': 0, 'games': 0})
        
        for replay in self.replays:
            for pkm in replay.player_team:
                pkm_stats[pkm]['games'] += 1
                if replay.winner == 'player':
                    pkm_stats[pkm]['wins'] += 1
        
        win_rates = {}
        for pkm, stats in pkm_stats.items():
            if stats['games'] > 0:
                win_rates[pkm] = stats['wins'] / stats['games']
        
        return win_rates
    
    def export_learning(self) -> Dict:
        """Exporta datos de aprendizaje para uso futuro"""
        return {
            'total_replays': len(self.replays),
            'avg_turns': sum(r.duration_turns for r in self.replays) / max(len(self.replays), 1),
            'player_winrate': sum(1 for r in self.replays if r.winner == 'player') / max(len(self.replays), 1),
            'common_mistakes': self.get_common_mistakes(),
            'pokemon_winrates': self.get_win_rate_by_pokemon(),
            'patterns': dict(self.move_patterns),
            'exported_at': datetime.now().isoformat()
        }
    
    def save_replay(self, battle_data: Dict) -> str:
        """Guarda un replay de batalla"""
        replay_id = f"replay_{datetime.now().timestamp()}"
        battle_data['id'] = replay_id
        battle_data['date'] = datetime.now().isoformat()
        
        filepath = os.path.join(self.replay_dir, f"{replay_id}.json")
        
        with open(filepath, 'w') as f:
            json.dump(battle_data, f, indent=2)
        
        return filepath
    
    def load_all_replays(self) -> int:
        """Carga todos los replays del directorio"""
        count = 0
        for filename in os.listdir(self.replay_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.replay_dir, filename)
                if self.load_replay(filepath):
                    count += 1
        return count