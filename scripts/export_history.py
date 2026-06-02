#!/usr/bin/env python3
"""
Script para exportar historial de batallas a CSV
Uso: python scripts/export_history.py [output_path]
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.storage import BattleStorage


def main():
    storage = BattleStorage()
    
    # Determinar path de salida
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'battles_export.csv')
    
    try:
        storage.export_to_csv(output_path)
        print(f"✅ Historial exportado exitosamente a: {output_path}")
        
        # Mostrar estadísticas
        stats = storage.get_stats()
        print(f"\n📊 Estadísticas:")
        print(f"   Total de batallas: {stats['total']}")
        print(f"   Victorias: {stats['wins']}")
        print(f"   Derrotas: {stats['losses']}")
        print(f"   Tasa de victoria: {stats['win_rate']:.1f}%")
        
    except Exception as e:
        print(f"❌ Error al exportar: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()