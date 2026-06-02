# PSD-Assist

Asistente inteligente para Pokemon Showdown que analiza batallas y recomienda jugadas.

## Características

- 📊 Detección automática de estado de batalla
- 🎯 Recomendaciones basadas en tipo y HP
- 🧠 Motor de decisión heurístico
- 📈 Historial de partidas
- 🎨 Interfaz visual (overlay)

## Inicio Rápido

1. Instala la extensión en tu navegador
2. Abre Pokemon Showdown
3. Comienza una batalla
4. ¡Listo! El asistente mostrará recomendaciones

## Documentación

- [Proyecto](./docs/PROJECT_GOAL.md)
- [Guía de Instalación](./docs/INSTALL.md)
- [Documentación Técnica](./docs/TECHNICAL.md)
- [Backlog](./BACKLOG.md)

## Estructura

```
├── extension/      # Extensión de navegador (Manifest V3)
├── core/            # Lógica de negocio (Python)
├── tests/           # Tests unitarios
└── docs/            # Documentación
```

## Tests

```bash
python -m unittest tests.test_core -v
```