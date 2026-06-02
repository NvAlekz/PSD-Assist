#!/usr/bin/env python3
"""
Script para calcular estadísticas de batallas
Uso: python scripts/stats.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.storage import BattleStorage


def print_stats():
    storage = BattleStorage()
    battles = storage.list_battles()
    
    if not battles:
        print("📭 No hay batallas registradas")
        return
    
    print("=" * 50)
    print("📊 ESTADÍSTICAS DE BATALLAS")
    print("=" * 50)
    
    # Stats básicos
    stats = storage.get_stats()
    print(f"\n📈 Totales:")
    print(f"   Batallas jugadas: {stats['total']}")
    print(f"   Victorias: {stats['wins']} ({stats['win_rate']:.1f}%)")
    print(f"   Derrotas: {stats['losses']}")
    
    # Análisis por Pokemon
    print(f"\n🎮 Pokemon más usados:")
    pokemon_usage = {}
    for battle in battles:
        if battle['myPokemon']:
            pkm_name = battle['myPokemon'].split()[0]
            pokemon_usage[pkm_name] = pokemon_usage.get(pkm_name, 0) + 1
    
    for pkm, count in sorted(pokemon_usage.items(), key=lambda x: -x[1])[:5]:
        print(f"   {pkm}: {count} veces")
    
    # Duración promedio
    turns = [b['turn'] for b in battles if b['turn'] > 0]
    if turns:
        avg_turns = sum(turns) / len(turns)
        print(f"\n⏱️ Duración promedio: {avg_turns:.1f} turnos")
    
    # Victorias por resultado
    wins_by_pokemon = {}
    for battle in battles:
        if battle['winner'] == 'player' and battle['myPokemon']:
            pkm_name = battle['myPokemon'].split()[0]
            wins_by_pokemon[pkm_name] = wins_by_pokemon.get(pkm_name, 0) + 1
    
    if wins_by_pokemon:
        print(f"\n🏆 Victorias por Pokemon:")
        for pkm, wins in sorted(wins_by_pokemon.items(), key=lambda x: -x[1])[:5]:
            total = pokemon_usage.get(pkm, 1)
            wr = (wins / total) * 100
            print(f"   {pkm}: {wins} victorias ({wr:.1f}% winrate)")
    
    print("\n" + "=" * 50)


if __name__ == '__main__':
    print_stats()