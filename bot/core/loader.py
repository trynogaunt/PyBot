from __future__ import annotations

import importlib
import inspect
import logging
from typing import Dict, List, Tuple
from ..db.feature_pool import FeaturePool

log = logging.getLogger(__name__)


def _command_qualified_keys(tree) -> set[str]:
    return {cmd.name for cmd in tree.get_commands()}


async def load_features(tree, config: Dict, feature_pool, admin_interface,  installed_modules: List[str]) -> Tuple:
    """Dynamically load and register features based on config, return dict of loaded modules and dict of failed ones with error messages

    Each feature module must be located at features/{slug}/feature.py and define:
    - a FEATURE dictionary with keys: slug, name, description, version, author, requires_config (bool), permissions (list of str)
    - a register(tree, config, database_interface) function that registers the feature's commands to the provided tree using the provided config dict

    Parameters:
        tree: the app_commands.CommandTree to register commands to
        config: the full configuration dict loaded from the config file, used to pass feature-specific config to each module

    Returns:
        loaded: dict mapping feature slug to the imported module object for successfully loaded features
        failed: dict mapping feature slug to error message for features that failed to load
    """
    params_needed: List[str] = ["slug", "name", "description", "version", "author", "requires_config", "permissions"]
    enabled: List[str] = config["enabled_features"]
    features_config: Dict = config.get("features", {})
    installed_modules = installed_modules or []

    loaded: Dict[str, object] = {}
    failed: Dict[str, str] = {}
    
    for slug in enabled:
        module_path = f"features.{slug}.feature"
        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            failed[slug] = "ImportError: " + str(e)
            log.error(f"Failed to import feature module {module_path}: {e}")
            continue

        if not hasattr(module, "FEATURE"):
            failed[slug] = "Missing FEATURE dictionary"
            log.error(f"Feature module {module_path} is missing FEATURE dictionary.")
            continue

        if not hasattr(module, "register"):
            failed[slug] = "Missing register function"
            log.error(f"Feature module {module_path} is missing register function.")
            continue

        feature_info: Dict = module.FEATURE

        if not isinstance(feature_info, dict):
            failed[slug] = "FEATURE is not a dictionary"
            log.error(f"Feature module {module_path} FEATURE is not a dictionary.")
            continue

        if not feature_info.get("slug"):
            failed[slug] = "FEATURE missing slug"
            log.error(f"Feature module {module_path} FEATURE dictionary missing slug.")
            continue

        if not all(param in feature_info for param in params_needed):
            missing_params = [param for param in params_needed if param not in feature_info]
            failed[slug] = "Missing parameters: " + ", ".join(missing_params)
            log.error(
                f"Feature module {module_path} FEATURE dictionary missing parameters: {', '.join(missing_params)}."
            )
            continue

        if feature_info.get("slug") != slug:
            failed[slug] = "Slug mismatch"
            log.error(f"Feature module {module_path} slug mismatch: expected {slug}, got {feature_info.get('slug')}.")
            continue

        feature_cfg: Dict = features_config.get(slug, {})

        if feature_info.get("requires_config", True) and not feature_cfg:
            failed[slug] = "Missing required configuration"
            log.error(f"Feature module {module_path} requires configuration but none was provided.")
            continue

        try:

            before = _command_qualified_keys(tree)
            before_cmds = {cmd.name: cmd for cmd in tree.get_commands()}

            register_signature = inspect.signature(module.register)
            params = list(register_signature.parameters.keys())
            if "database_interface" in params:
                feature_db = FeaturePool(feature_pool.pool, schema=slug)
                module.register(tree, feature_cfg, feature_db)
                log.info(f"Registered feature {slug} with database interface.")
                if hasattr(module, "install") and slug not in installed_modules:
                    log.info(f"Installing feature {slug}...")
                    try:
                        await admin_interface._create_schema(slug)  # Ensure the schema exists before installation
                        log.info(f"Schema for feature {slug} created successfully before installation.")
                    except Exception as e:
                        log.error(f"Failed to create schema for feature {slug} before installation: {e}")
                        failed[slug] = "InstallationError: Failed to create database schema: " + str(e)
                        continue
                    
                    installed = await module.install(feature_db)
                    if installed:
                        try:
                            db_install = await admin_interface.set_module_installed(slug, installed=installed)
                        except Exception as e:
                            log.error(f"Failed to mark feature {slug} as installed in database: {e}")
                    else:
                        log.error(f"Installation function for feature {slug} returned False.")
            else:
                module.register(tree, feature_cfg)
            after_cmds = {cmd.name: cmd for cmd in tree.get_commands()}
            duplicates = {
                name for name, cmd in after_cmds.items() if name in before_cmds and before_cmds[name] is not cmd
            }
            if duplicates:
                failed[slug] = "Command name conflict: " + ", ".join(sorted(duplicates))
                log.error(f"Feature module {module_path} command name conflict: {', '.join(sorted(duplicates))}.")

                for cmd_name in duplicates:
                    try:
                        tree.remove_command(cmd_name)
                    except Exception as e:
                        log.error(f"Failed to remove command {cmd_name} after conflict in feature {slug}: {e}")
                continue

            loaded[slug] = module
            log.info(f"Successfully loaded feature module {module_path}.")
        except Exception as e:
            failed[slug] = "RegistrationError: " + str(e)
            log.error(f"Failed to register feature module {module_path}: {e}")

    return loaded, failed, installed_modules
