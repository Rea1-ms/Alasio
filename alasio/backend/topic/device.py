import trio

from alasio.backend.reactive.base_rpc import rpc
from alasio.backend.reactive.event import RpcValueError
from alasio.backend.reactive.source import KeyedSource
from alasio.backend.topic import _config_event
from alasio.backend.topic._gui_config import GuiConfigSource
from alasio.backend.topic._worker import BACKEND_WORKER_MANAGER
from alasio.backend.topic.config import ConfigArg
from alasio.backend.topic.worker import get_mod
from alasio.config.entry.loader import MOD_LOADER
from alasio.base.timer import getnow


class DeviceSource(KeyedSource, GuiConfigSource):
    """Editable GUI view with the fixed ``device`` navigation layout."""

    TOPIC_NAME = 'Device'

    def __init__(self, mod_name, config_name, lang):
        super().__init__(mod_name, config_name, 'device', lang)


class Device(ConfigArg):
    """Device settings view and its explicit restart actions."""

    TOPIC_NAME = 'Device'
    SOURCE_CLASS = DeviceSource
    FIXED_NAV = 'device'
    ACTION_TASKS = frozenset({'RestartGame', 'RestartDevice'})
    ACTION_WORKER_STATES = frozenset({'idle', 'error', 'starting', 'running', 'scheduler-waiting'})

    @rpc
    async def run_task(self, task: str):
        if task not in self.ACTION_TASKS:
            raise RpcValueError(f'Unsupported device action: "{task}"')

        context = await self._get_view_context()
        if context is None:
            return
        mod_name, config_name, _, _ = context
        mod = await get_mod(config_name)

        states = await trio.to_thread.run_sync(BACKEND_WORKER_MANAGER.get_state_info)
        worker_state = states.get(config_name, 'idle')
        if worker_state not in self.ACTION_WORKER_STATES:
            raise RpcValueError(
                f'Cannot run device action while worker state is "{worker_state}"')

        success, responses = await trio.to_thread.run_sync(
            MOD_LOADER.gui_config_set,
            mod_name, config_name, task, 'Scheduler', 'NextRun', getnow()
        )
        if not success:
            if responses and responses[0].error is not None:
                message = str(responses[0].error)
            else:
                message = f'Failed to schedule task "{task}"'
            raise RpcValueError(message)
        _config_event.on_config_event(config_name, responses)

        if worker_state in {'idle', 'error'}:
            started, message = await trio.to_thread.run_sync(
                BACKEND_WORKER_MANAGER.worker_start, mod, config_name
            )
            if not started:
                states = await trio.to_thread.run_sync(BACKEND_WORKER_MANAGER.get_state_info)
                if states.get(config_name, 'idle') not in self.ACTION_WORKER_STATES - {'idle', 'error'}:
                    raise RpcValueError(message)
