from typing import Any, Dict, List


def reload_modules(locals: Dict[str, Any], package: str, module_names: List[str], forced_module_names: List[str] = []):
    """
    Checks if any of module_names are present in locals, and if so, reloads them using importlib.
    Unconditionally imports everything in forced_module_names in the context of package,
    use that for "from X import Y" imports.
    """
    loaded_modules = [locals[mod_name]
                      for mod_name in module_names if mod_name in locals]
    if len(loaded_modules) > 0 or len(forced_module_names) > 0:
        # we need to reload
        import importlib
        # not sure if this is necessary
        importlib.invalidate_caches()
        for mod in loaded_modules:
            print(f"reloading {mod.__name__}")
            importlib.reload(mod)
        for mod_name in forced_module_names:
            print(f"reloading {mod_name}")
            mod = importlib.import_module(mod_name, package=package)
            importlib.reload(mod)
