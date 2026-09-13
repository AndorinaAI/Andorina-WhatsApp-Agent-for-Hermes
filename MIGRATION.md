# 📋 Guía de Migración — Andoriña V1.6 → V2.0

## Para usuarios de V1.6

### Instalación limpia (recomendado)
```bash
# 1. Respaldar datos
cp -r ~/.hermes/skills/andorina/state ~/andorina-backup/
cp ~/.hermes/skills/andorina/.env ~/andorina-backup/

# 2. Instalar V2.0 como plugin
hermes plugin install andorina

# 3. Restaurar datos
cp -r ~/andorina-backup/state ~/.hermes/plugins/platforms/andorina/
cp ~/andorina-backup/.env ~/.hermes/plugins/platforms/andorina/

# 4. Configurar
hermes plugin configure andorina
```

### Migración in-place
```bash
cd ~/.hermes/skills/andorina
git pull origin v2.0
python3 setup.py --migrate-to-plugin
```

## Cambios importantes

### ✅ Lo que sigue igual
- Sub-Souls y personalidades
- RBAC y permisos
- Notas de contactos
- Alertas semánticas
- Agenda y scheduling
- Panel GUI

### 🔄 Lo que cambia
| V1.6 | V2.0 |
|------|------|
| (deprecated patches — removed in V2.0) | Plugin platform nativo |
| `crontab` para scheduling | `hermes cron` (crontab como fallback) |
| Memoria solo Hindsight | Cualquier backend (Hindsight, Mnemosyne, Honcho) |
| Linux (principal) | Linux-first, con componentes multi-OS preparados |
| `python3 setup.py` | `hermes plugin install andorina` |

### 🗑️ Lo que desaparece
- `patch_bridge.py` → removed in V2.0 (plugin platform)
- `patch_whatsapp.py` → removed in V2.0 (plugin platform)
- (deprecated — removed in V2.0) → removed in V2.0 (plugin platform)
- `andorina_updater.py` → reemplazado por `hermes plugin update`

## Soporte

Si encuentras problemas durante la migración:
1. Revisa los logs: `~/.hermes/logs/andorina/`
2. Ejecuta diagnóstico: `python3 scripts/utils/diag.py`
3. Abre un issue en GitHub
