import asyncio
from workflows.workflow_engine import WorkflowEngine


def test_workflow_engine_lists_workflows():
    engine = WorkflowEngine()
    workflows = engine.list_workflows()
    assert "coding_mode" in workflows
    assert "focus_mode" in workflows


def test_workflow_engine_executes_known_workflow(monkeypatch):
    engine = WorkflowEngine()
    
    async def fake_run_action(action, *args):
        return f"executed {action} with {args}"

    monkeypatch.setattr(engine, "_run_action", fake_run_action)
    response = asyncio.run(engine.execute_workflow("coding_mode"))
    assert "Workflow 'coding_mode' completed" in response
    assert "executed open_application" in response


def test_workflow_engine_unknown_workflow():
    engine = WorkflowEngine()
    response = asyncio.run(engine.execute_workflow("unknown_mode"))
    assert "do not have a workflow named" in response
