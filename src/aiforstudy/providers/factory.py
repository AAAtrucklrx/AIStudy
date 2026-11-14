"""Default services shared by CLI and HTTP; construction never sends a request."""
from __future__ import annotations

from ..errors import ConfigError
from .transport import RealTransport, resolve_api_key


def configured_providers(request, workspace):
    from ..pipeline.services import Providers
    if request.profile.value != 'release':
        return Providers(is_stub=request.profile.value == 'smoke')
    config = workspace.config_json('models.json')
    key, _ = resolve_api_key(workspace.root)
    transport = None
    if key:
        if config.get('provider', 'deepseek') != 'deepseek':
            raise ConfigError('当前真实传输仅支持已配置的 deepseek 兼容服务')
        transport = RealTransport(
            model=str((config.get('roles', {}).get('lesson') or {}).get('model', '')),
            base_url=str(config.get('base_url') or 'https://api.deepseek.com'),
            workspace_root=workspace.root,
            network_wait=True,
        )
    return Providers(llm=transport)
