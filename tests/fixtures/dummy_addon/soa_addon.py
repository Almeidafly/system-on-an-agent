"""A tiny add-on used only in tests."""

from soa.addons import AddonManifest


class Addon:
    manifest = AddonManifest(
        name="dummy",
        version="0.1.0",
        description="Test add-on that records hook calls.",
        hooks=("before_plan", "after_plan", "before_step", "after_step", "on_error"),
    )

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def before_plan(self, plan, context):
        self.calls.append(("before_plan", plan.goal))
        context.extras["dummy"] = True
        return plan

    def after_plan(self, plan, report, context):
        self.calls.append(("after_plan", plan.goal))
        return report

    def before_step(self, step, context):
        self.calls.append(("before_step", step.action))
        return step

    def after_step(self, step, result, context):
        self.calls.append(("after_step", step.action))
        return result

    def on_error(self, step, error, context):
        self.calls.append(("on_error", step.action))
