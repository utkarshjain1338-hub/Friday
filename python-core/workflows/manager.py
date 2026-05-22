class WorkflowManager:
    def __init__(self):
        self.workflows = {}

    def register_workflow(self, name: str, workflow_fn):
        self.workflows[name] = workflow_fn

    async def execute(self, name: str, context: dict = None):
        if name in self.workflows:
            print(f"Executing Workflow: {name}")
            await self.workflows[name](context)
        else:
            print(f"Workflow {name} not found.")

def setup_workflows(router):
    manager = WorkflowManager()
    
    async def coding_mode(context):
        print("-> Running Coding Mode Workflow...")
        # e.g. Open VSCode, Start terminal, Play Spotify
        print("-> VSCode started, Terminal opened.")
        
    manager.register_workflow("coding_mode", coding_mode)
    
    async def on_workflow_trigger(payload):
        name = payload.get("name") if isinstance(payload, dict) else payload
        if name:
            await manager.execute(name)
            
    router.subscribe("WorkflowTriggered", on_workflow_trigger)
