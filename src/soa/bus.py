"""Bus / router: the on-agent interconnect between core parts."""

from __future__ import annotations

from typing import Any

from soa.addons.loader import AddonLoader
from soa.connectors import ConnectorRegistry
from soa.memory import Memory
from soa.skills import SkillLibrary
from soa.types import Message, Result


class Bus:
    """Route messages to memory, skills, connectors, or system helpers."""

    def __init__(
        self,
        memory: Memory,
        skills: SkillLibrary,
        connectors: ConnectorRegistry,
        addons: AddonLoader | None = None,
    ) -> None:
        self.memory = memory
        self.skills = skills
        self.connectors = connectors
        self.addons = addons or AddonLoader()

    def dispatch(self, message: Message) -> Result:
        channel = message.channel
        if channel == "memory":
            return self._memory(message)
        if channel in {"skill", "skills"}:
            return self._skill(message)
        if channel in {"connector", "connectors"}:
            return self._connector(message)
        if channel == "system":
            return self._system(message)
        return Result(ok=False, error=f"unknown channel: {channel}", action=message.action)

    def dispatch_step(self, action: str, args: dict[str, Any] | None = None) -> Result:
        """Translate a planner action into a bus message and dispatch it."""
        args = dict(args or {})
        if action.startswith("memory."):
            return self.dispatch(Message("memory", action.split(".", 1)[1], args))
        if action.startswith("skill."):
            return self.dispatch(Message("skill", action.split(".", 1)[1], args))
        if action.startswith("connector."):
            return self.dispatch(Message("connector", action.split(".", 1)[1], args))
        if action.startswith("system."):
            return self.dispatch(Message("system", action.split(".", 1)[1], args))
        return Result(ok=False, error=f"unknown action: {action}", action=action)

    def _memory(self, message: Message) -> Result:
        action = message.action
        payload = message.payload
        if action == "remember":
            fact = payload.get("fact") or payload.get("text") or ""
            stored = self.memory.remember(str(fact), payload.get("tags") or ())
            return Result(ok=True, data=stored.text, action="memory.remember")
        if action == "recall":
            query = payload.get("query") or payload.get("text") or ""
            hits = self.memory.recall(str(query))
            text = "\n".join(fact.text for fact in hits) if hits else ""
            return Result(ok=True, data=text, action="memory.recall")
        if action == "set":
            self.memory.working.set(payload["key"], payload.get("value"))
            return Result(ok=True, data=payload.get("value"), action="memory.set")
        if action == "get":
            return Result(
                ok=True,
                data=self.memory.working.get(payload["key"]),
                action="memory.get",
            )
        return Result(ok=False, error=f"unknown memory action: {action}", action=action)

    def _skill(self, message: Message) -> Result:
        action = message.action
        payload = dict(message.payload)
        if action in {"run", "call"}:
            name = payload.pop("name")
            result = self.skills.run(name, **payload)
            # Built-in skills that wrap I/O are expanded onto the bus.
            if name == "echo":
                return self.dispatch(
                    Message("connector", "send", {"connector": "echo", "payload": result.data})
                )
            if name == "remember":
                return self.dispatch(
                    Message("memory", "remember", {"fact": result.data})
                )
            if name == "recall":
                return self.dispatch(
                    Message("memory", "recall", {"query": result.data})
                )
            if name == "read_file":
                data = result.data if isinstance(result.data, dict) else {"path": result.data}
                data = {**data, "connector": "file", "method": "read"}
                return self.dispatch(Message("connector", "call", data))
            if name == "write_file":
                data = result.data if isinstance(result.data, dict) else {}
                data = {**data, "connector": "file", "method": "write"}
                return self.dispatch(Message("connector", "call", data))
            return result
        if action == "list":
            return Result(ok=True, data=self.skills.names(), action="skill.list")
        return Result(ok=False, error=f"unknown skill action: {action}", action=action)

    def _connector(self, message: Message) -> Result:
        action = message.action
        payload = dict(message.payload)
        name = payload.pop("connector", payload.pop("name", None))
        if not name:
            return Result(ok=False, error="connector name is required", action=action)
        try:
            connector = self.connectors.get(name)
        except KeyError as exc:
            return Result(ok=False, error=str(exc).strip("\"'"), action=action)
        if action == "send":
            body = payload.pop("payload") if "payload" in payload else payload
            try:
                return connector.send(body, **payload)
            except TypeError:
                return connector.send(body)
        if action == "call":
            method = payload.pop("method", "send")
            if hasattr(connector, "call"):
                return connector.call(method, **payload)  # type: ignore[no-any-return]
            return connector.send(payload, method=method)
        if action == "list":
            return Result(ok=True, data=self.connectors.names(), action="connector.list")
        return Result(ok=False, error=f"unknown connector action: {action}", action=action)

    def _system(self, message: Message) -> Result:
        action = message.action
        if action in {"list_skills", "skills"}:
            return Result(ok=True, data=self.skills.names(), action="system.list_skills")
        if action in {"list_connectors", "connectors"}:
            names = [
                f"{connector.name} ({connector.kind})"
                for connector in self.connectors.list()
            ]
            return Result(ok=True, data=names, action="system.list_connectors")
        if action == "noop":
            return Result(ok=True, data="", action="system.noop")
        return Result(ok=False, error=f"unknown system action: {action}", action=action)
