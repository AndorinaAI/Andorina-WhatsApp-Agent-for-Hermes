# Migration Guide — Andoriña V1.6 → V2.0

## For V1.6 users

V2.0 migrates Andoriña from a Skill-based architecture to a native Hermes backend plugin.

### Key Changes

| V1 | V2 |
|---|---|
| Skill in `~/.hermes/skills/` | Plugin in `~/.hermes/plugins/` |
| Shell hooks in config.yaml | `ctx.register_hook()` in plugin |
| Tools via terminal + shell scripts | Native `ctx.register_tool()` |
| `SKILL.md` instruction file | Plugin hooks provide context |
| `kind: tool` | `kind: backend` |
| State in plugin directory | State in `~/.hermes/plugin-data/andorina/` |

### Clean install (recommended)

```bash
# 1. Backup data
cp -r ~/.hermes/skills/andorina/state ~/andorina-backup/

# 2. Remove old Skill
rm -rf ~/.hermes/skills/andorina/

# 3. Clone V2 as plugin
git clone https://github.com/AndorinaAI/Andorina-WhatsApp-Agent-for-Hermes.git \
  ~/.hermes/plugins/andorina/

# 4. Restore state (if needed)
cp -r ~/andorina-backup/state/* ~/.hermes/plugins/andorina/state/

# 5. Enable plugin in config.yaml
# Add 'andorina' to plugins.enabled list
```

### Architectural Migration

1. **Hooks**: Shell hooks removed. Plugin hooks registered via `ctx.register_hook()`.
2. **Tools**: Terminal-based calls replaced with `ctx.register_tool()`. `_adapt_handler()` wraps handlers for Hermes v0.21.2 `handler(args_dict)` contract.
3. **Inbox**: Webhook-based processing replaced by `pre_llm_call` hook → `orchestrator_hook.py` → `process_incoming_message()`.
4. **JID Resolution**: Updated for Hermes v0.21.2 payload format (fields at top level vs `extra` dict).
5. **State**: Moved to `~/.hermes/plugin-data/andorina/` per Hermes plugin guidelines.

### Compatibility Notes

- Hermes >= v0.21.2 required
- V1 Skill must be fully removed (not just disabled)
- No duplicate plugins allowed (check `~/.hermes/plugins/`)
- `plugins.enabled` must include `andorina`

### Rollback

To revert to V1, remove the V2 plugin and restore the V1 Skill from backup.
