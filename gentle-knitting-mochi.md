# Plan : Intégration PostgreSQL avec 2 schemas (admin / users)

## Contexte

- Branche `feat/core-db` - `DatabasePool` existe déjà mais n'est jamais connecté (bug : `on_startup` n'est pas appelé par discord.py)
- asyncpg installé mais absent de `requirements.txt`
- Aucun modèle, aucune migration, aucun schéma SQL n'existe encore
- Choix validés : **asyncpg brut** + **Alembic** pour les migrations

## Bugs existants à corriger

1. `on_startup()` n'est jamais appelé -> `db_pool` reste toujours `None`
2. `on_shutdown()` n'est jamais appelé -> la pool n'est jamais fermée proprement
3. `asyncpg` absent de `requirements.txt`

---

## Étape 1 : Configuration et dépendances

**Fichiers modifiés :**

- `requirements.txt` : ajouter `asyncpg>=0.31.0` et `alembic>=1.15.0`
- `config/.env.example` : ajouter `DATABASE_URL=postgresql://user:password@localhost:5432/pybot`
- `bot/core/config.py` : ajouter `database_url: str` dans `AppEnv` + lecture dans `load_env()`

## Étape 2 : Réécriture de DatabasePool

**Fichier modifié : `bot/db/pool.py`**

- Accepter `database_url` en paramètre direct (plus de `os.getenv` interne)
- `min_size` / `max_size` configurables (défaut 2/10)
- `_init_connection` callback : `SET search_path TO admin, users, public` sur chaque connexion
- Property `pool` avec `RuntimeError` si non connecté
- Méthodes utilitaires : `fetch`, `fetchrow`, `fetchval`, `execute`, `executemany`

**Fichier créé : `bot/db/__init__.py`** (export DatabasePool)

## Étape 3 : Corriger le cycle de vie du bot

**Fichier modifié : `bot/core/app.py`**

- `__init__` : accepter `database_url`, créer `DatabasePool(database_url)`
- `setup_hook()` : appeler `self.db_pool.connect()` **avant** le chargement des features
- `close()` : override pour appeler `self.db_pool.disconnect()` puis `super().close()`
- Supprimer `on_startup()` et `on_shutdown()` (jamais appelées par discord.py)
- `main()` : passer `env.database_url` à `BotApp`

## Étape 4 : Alembic + Migration initiale

**Fichiers créés :**

```
alembic.ini                                          # Config Alembic (racine projet)
bot/db/migrations/env.py                             # Env async (sqlalchemy.ext.asyncio comme runner)
bot/db/migrations/script.py.mako                     # Template de migration
bot/db/migrations/versions/001_create_schemas_and_tables.py
```

**Migration initiale - Schemas et tables :**

### Schema `admin`

| Table | Colonnes | Usage |
|-------|----------|-------|
| `guild_config` | `id, guild_id, key, value, created_at, updated_at` + UNIQUE(guild_id, key) | Config serveur key-value |
| `mod_logs` | `id, guild_id, moderator_id, target_id, action, reason, duration, created_at` | Journal de modération |

### Schema `users`

| Table | Colonnes | Usage |
|-------|----------|-------|
| `members` | `id, discord_id (UNIQUE), username, display_name, joined_at, created_at, updated_at` | Profils membres |
| `warnings` | `id, discord_id (FK), moderator_id, reason, active, created_at` | Avertissements |
| `reminders` | `id, discord_id (FK), channel_id, message, remind_at, fired, created_at` | Rappels persistants |

Index sur les colonnes de recherche fréquentes. Le `downgrade()` drop toutes les tables puis les schemas.

Migrations lancées via CLI uniquement (`alembic upgrade head`), pas au démarrage du bot.

## Étape 5 : Couche Repository (DAO)

**Structure créée :**

```
bot/db/repositories/
  __init__.py
  base.py                 # BaseRepository(pool: DatabasePool)
  guild_config.py          # get, set (UPSERT), delete, get_all
  mod_logs.py              # create, get_by_target, get_recent
  members.py               # upsert, get_by_discord_id
  warnings.py              # create, get_by_discord_id, deactivate
  reminders.py             # create, get_pending, mark_fired, delete
```

**Accès depuis les features :** via `interaction.client.db_pool`
```python
async def some_command(interaction: discord.Interaction):
    repo = MemberRepository(interaction.client.db_pool)
    member = await repo.get_by_discord_id(interaction.user.id)
```

Les repositories sont légers (juste une ref vers le pool), pas besoin de singleton.
Le contrat `register(tree, config)` n'est **pas modifié**.

---

## Fichiers impactés (résumé)

| Action | Fichier |
|--------|---------|
| MODIFIÉ | `requirements.txt` |
| MODIFIÉ | `config/.env.example` |
| MODIFIÉ | `bot/core/config.py` |
| MODIFIÉ | `bot/core/app.py` |
| MODIFIÉ | `bot/db/pool.py` |
| CRÉÉ | `bot/db/__init__.py` |
| CRÉÉ | `alembic.ini` |
| CRÉÉ | `bot/db/migrations/env.py` |
| CRÉÉ | `bot/db/migrations/script.py.mako` |
| CRÉÉ | `bot/db/migrations/versions/001_create_schemas_and_tables.py` |
| CRÉÉ | `bot/db/repositories/__init__.py` |
| CRÉÉ | `bot/db/repositories/base.py` |
| CRÉÉ | `bot/db/repositories/guild_config.py` |
| CRÉÉ | `bot/db/repositories/mod_logs.py` |
| CRÉÉ | `bot/db/repositories/members.py` |
| CRÉÉ | `bot/db/repositories/warnings.py` |
| CRÉÉ | `bot/db/repositories/reminders.py` |

## Vérification

1. `pip install -r requirements.txt` - les dépendances s'installent
2. `alembic upgrade head` - les schemas et tables sont créés dans Postgres
3. `alembic downgrade base` - rollback propre (tout supprimé)
4. Démarrer le bot - le log affiche "Database pool created" au startup
5. Arrêter le bot (Ctrl+C) - le log affiche "Database pool closed"
6. Vérifier dans psql : `\dn` montre les schemas admin et users, `\dt admin.*` et `\dt users.*` montrent les tables
