"""Default services shared by CLI and HTTP; construction never sends a request."""
from __future__ import annotations
import os
from ..errors import ConfigError
from .transport import RealTransport, resolve_api_key
from .local_compatible import LocalCompatibleTransport
from .dsh_account import DshAccountTransport
from .routing import RoleTransportRouter


def configured_providers(request, workspace):
    from ..pipeline.services import Providers
    if request.profile.value != 'release':
        return Providers(is_stub=request.profile.value == 'smoke')
    config = workspace.config_json('models.json')
    routes = {}
    for role, spec in config.get('roles', {}).items():
        if not isinstance(spec, dict):
            raise ConfigError('Model role must be an object')
        provider = spec.get('provider', config.get('provider', 'deepseek'))
        model = str(spec.get('model') or '')
        if not model:
            raise ConfigError('Model role requires a model')
        if provider == 'deepseek-account':
            routes[role] = DshAccountTransport(model=model,workspace_root=workspace.root)
        elif provider == 'local-compatible':
            base = spec.get('base_url',config.get('base_url'))
            if not base:
                raise ConfigError('Local transport requires explicit base_url')
            ref = spec.get('api_key_ref',config.get('api_key_ref',''))
            if ref and (not isinstance(ref,str) or not ref.startswith('env:')):
                raise ConfigError('Local api_key_ref requires env:NAME')
            key = os.environ.get(ref[4:],'') if ref else ''
            if ref and not key:
                raise ConfigError('Configured local credential is missing')
            routes[role] = LocalCompatibleTransport(model=model,base_url=str(base),api_key=key)
        elif provider == 'deepseek':
            key, _ = resolve_api_key(workspace.root)
            if not key:
                # Preserve the legacy missing-key capability report.
                if all(s.get('provider',config.get('provider','deepseek')) == 'deepseek' for s in config.get('roles',{}).values()):
                    return Providers(llm=None)
                raise ConfigError('Cloud role requires a configured API key')
            routes[role] = RealTransport(model=model,base_url=str(spec.get('base_url',config.get('base_url')) or 'https://api.deepseek.com'),workspace_root=workspace.root,network_wait=True)
        else:
            raise ConfigError('Unsupported model provider')
    if routes and all(route.cache_identity == next(iter(routes.values())).cache_identity for route in routes.values()):
        return Providers(llm=next(iter(routes.values())))
    return Providers(llm=RoleTransportRouter(routes) if routes else None)
