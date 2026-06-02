"""
Pokemon Showdown Assistant - Metagame Analyzer
Análisis de tendencias y estadísticas del metagame
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime


@dataclass
class PokemonStats:
    """Estadísticas de un Pokemon en el metagame"""
    name: str
    usage_count: int = 0
    win_count: int = 0
    lose_count: int = 0
    avg_hp_percent: float = 0.0
    common_moves: List[str] = field(default_factory=list)
    common_items: List[str] = field(default_factory=list)
    abilities_used: List[str] = field(default_factory=list)
    
    @property
    def win_rate(self) -> float:
        """Calcula tasa de victoria"""
        total = self.win_count + self.lose_count
        return (self.win_count / total * 100) if total > 0 else 0.0


@dataclass
class MatchupData:
    """Datos de matchup entre Pokemon"""
    attacker: str
    defender: str
    wins: int = 0
    losses: int = 0
    avg_damage_dealt: float = 0.0
    avg_damage_taken: float = 0.0


class MetagameAnalyzer:
    """
    Analizador de metagame
    
    Analiza tendencias, matchups y estadísticas de batallas
    para informar decisiones estratégicas
    """
    
    def __init__(self):
        self.pokemon_stats: Dict[str, PokemonStats] = {}
        self.matchups: Dict[Tuple[str, str], MatchupData] = {}
        self.move_counters: Dict[str, Dict[str, int]] = defaultdict(Counter)
        self.team_compositions: List[List[str]] = []
    
    def analyze_battle(self, battle_data: Dict) -> None:
        """
        Analiza una batalla y actualiza estadísticas
        
        Args:
            battle_data: Datos de la batalla
        """
        # Análisis de Pokemon usados
        my_team = battle_data.get('myTeam', {}).get('pokemons', [])
        enemy_team = battle_data.get('enemyTeam', {}).get('pokemons', [])
        
        winner = battle_data.get('winner', None)
        
        # Actualizar stats de Pokemon aliados
        for pkm in my_team:
            self.update_pokemon_stats(pkm, winner == 'player')
        
        # Actualizar stats de Pokemon enemigos
        for pkm in enemy_team:
            self.update_pokemon_stats(pkm, winner == 'enemy')
        
        # Registrar matchups
        if my_team and enemy_team:
            active_me = my_team[0] if my_team else None
            active_enemy = enemy_team[0] if enemy_team else None
            
            if active_me and active_enemy:
                self.record_matchup(
                    active_me['name'],
                    active_enemy['name'],
                    winner == 'player'
                )
        
        # Registrar composición de equipo
        team_names = [pkm.get('name', '').split()[0] for pkm in my_team]
        if team_names:
            self.team_compositions.append(team_names)
    
    def update_pokemon_stats(self, pkm_data: Dict, won: bool) -> None:
        """Actualiza estadísticas de un Pokemon"""
        name = pkm_data.get('name', 'Unknown').split()[0]  # Solo nombre base
        
        if name not in self.pokemon_stats:
            self.pokemon_stats[name] = PokemonStats(name=name)
        
        stats = self.pokemon_stats[name]
        stats.usage_count += 1
        
        if won:
            stats.win_count += 1
        else:
            stats.lose_count += 1
        
        # Actualizar HP promedio
        hp = pkm_data.get('hp', 0)
        max_hp = pkm_data.get('maxHp', 1)
        if max_hp > 0:
            hp_percent = (hp / max_hp) * 100
            stats.avg_hp_percent = (
                (stats.avg_hp_percent * (stats.usage_count - 1) + hp_percent)
                / stats.usage_count
            )
        
        # Actualizar movimientos comunes
        moves = pkm_data.get('moves', [])
        stats.common_moves.extend(moves)
    
    def record_matchup(self, attacker: str, defender: str, won: bool) -> None:
        """Registra resultado de un matchup"""
        key = (attacker, defender)
        
        if key not in self.matchups:
            self.matchups[key] = MatchupData(attacker=attacker, defender=defender)
        
        matchup = self.matchups[key]
        if won:
            matchup.wins += 1
        else:
            matchup.losses += 1
    
    def get_top_pokemon(self, limit: int = 10, by: str = 'usage') -> List[PokemonStats]:
        """
        Obtiene los Pokemon más usados/populares
        
        Args:
            limit: Número de resultados
            by: 'usage', 'wins', o 'winrate'
        """
        if by == 'usage':
            sorted_pkm = sorted(
                self.pokemon_stats.values(),
                key=lambda x: -x.usage_count
            )
        elif by == 'wins':
            sorted_pkm = sorted(
                self.pokemon_stats.values(),
                key=lambda x: -x.win_count
            )
        else:  # winrate
            sorted_pkm = sorted(
                self.pokemon_stats.values(),
                key=lambda x: -x.win_rate
            )
        
        return sorted_pkm[:limit]
    
    def get_matchup_advantage(self, my_pokemon: str, enemy_pokemon: str) -> float:
        """
        Calcula ventaja de matchup entre dos Pokemon
        
        Returns:
            Porcentaje de ventaja (positivo = favorable)
        """
        key = (my_pokemon, enemy_pokemon)
        
        if key not in self.matchups:
            return 0.0
        
        matchup = self.matchups[key]
        total = matchup.wins + matchup.losses
        
        if total < 3:  # Necesita al menos 3 datos
            return 0.0
        
        win_rate = (matchup.wins / total) * 100
        return win_rate - 50  # Desviación de 50%
    
    def suggest_counter(self, enemy_pokemon: str) -> Optional[str]:
        """
        Sugiere un counter para un Pokemon enemigo
        
        Returns:
            Nombre del counter recomendado o None
        """
        # Buscar Pokemon con mejor winrate contra el enemigo
        best_counter = None
        best_winrate = 0
        
        for (attacker, defender), matchup in self.matchups.items():
            if defender == enemy_pokemon:
                total = matchup.wins + matchup.losses
                if total >= 2:
                    winrate = (matchup.wins / total) * 100
                    if winrate > best_winrate:
                        best_winrate = winrate
                        best_counter = attacker
        
        return best_counter
    
    def get_team_suggestions(self, enemy_team: List[str]) -> Dict[str, str]:
        """
        Sugiere equipo basado en equipo enemigo
        
        Args:
            enemy_team: Lista de nombres de Pokemon enemigos
            
        Returns:
            Diccionario de sugerencias por Pokemon enemigo
        """
        suggestions = {}
        
        for enemy in enemy_team:
            counter = self.suggest_counter(enemy)
            if counter:
                suggestions[enemy] = counter
        
        return suggestions
    
    def get_common_counters(self, pokemon_name: str) -> List[Tuple[str, float]]:
        """
        Obtiene los counters más comunes para un Pokemon
        
        Returns:
            Lista de (counter_name, winrate) ordenados por efectividad
        """
        counters = []
        
        for (attacker, defender), matchup in self.matchups.items():
            if defender == pokemon_name:
                total = matchup.wins + matchup.losses
                if total > 0:
                    winrate = matchup.wins / total
                    counters.append((attacker, winrate))
        
        counters.sort(key=lambda x: -x[1])
        return counters[:5]
    
    def get_analysis_report(self) -> Dict:
        """Genera reporte de análisis del metagame"""
        top_usage = self.get_top_pokemon(10, 'usage')
        top_winrate = self.get_top_pokemon(10, 'winrate')
        
        return {
            'total_pokemon_analyzed': len(self.pokemon_stats),
            'total_matchups': len(self.matchups),
            'top_by_usage': [
                {'name': p.name, 'usage': p.usage_count, 'wins': p.win_count}
                for p in top_usage
            ],
            'top_by_winrate': [
                {'name': p.name, 'winrate': f"{p.win_rate:.1f}%", 'games': p.win_count + p.lose_count}
                for p in top_winrate
                if p.usage_count >= 3
            ],
            'generated_at': datetime.now().isoformat()
        }
    
    def reset(self) -> None:
        """Reinicia todas las estadísticas"""
        self.pokemon_stats.clear()
        self.matchups.clear()
        self.move_counters.clear()
        self.team_compositions.clear()
    
    def export_to_dict(self) -> Dict:
        """Exporta todos los datos de análisis"""
        return {
            'pokemon_stats': {
                name: {
                    'usage_count': stats.usage_count,
                    'win_count': stats.win_count,
                    'lose_count': stats.lose_count,
                    'win_rate': stats.win_rate,
                    'avg_hp_percent': stats.avg_hp_percent
                }
                for name, stats in self.pokemon_stats.items()
            },
            'matchups': {
                f"{k[0]} vs {k[1]}": {
                    'wins': v.wins,
                    'losses': v.losses
                }
                for k, v in self.matchups.items()
            }
        }