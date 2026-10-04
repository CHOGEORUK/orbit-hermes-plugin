from . import memory_bridge, schemas, tools
from .cli import orbit_command, register_cli, slash_command
from .pairing_server import start_pairing_server


def register(ctx):
    ctx.register_tool(name="orbit_status", toolset="orbit_dashboard", schema=schemas.STATUS, handler=tools.get_status)
    ctx.register_tool(name="orbit_list_workflows", toolset="orbit_dashboard", schema=schemas.LIST_WORKFLOWS, handler=tools.list_workflows)
    ctx.register_tool(name="orbit_create_job", toolset="orbit_dashboard", schema=schemas.CREATE_JOB, handler=tools.create_job)
    ctx.register_tool(name="orbit_list_jobs", toolset="orbit_dashboard", schema=schemas.LIST_JOBS, handler=tools.list_jobs)
    ctx.register_tool(name="orbit_get_job", toolset="orbit_dashboard", schema=schemas.GET_JOB, handler=tools.get_job)
    ctx.register_tool(name="orbit_wait_job", toolset="orbit_dashboard", schema=schemas.WAIT_JOB, handler=tools.wait_job)
    ctx.register_tool(name="orbit_cancel_job", toolset="orbit_dashboard", schema=schemas.CANCEL_JOB, handler=tools.cancel_job)
    ctx.register_tool(name="orbit_rerun_job", toolset="orbit_dashboard", schema=schemas.RERUN_JOB, handler=tools.rerun_job)
    ctx.register_tool(name="orbit_list_results", toolset="orbit_dashboard", schema=schemas.LIST_RESULTS, handler=tools.list_results)
    ctx.register_tool(name="orbit_download_result", toolset="orbit_dashboard", schema=schemas.DOWNLOAD_RESULT, handler=tools.download_result)
    ctx.register_tool(name="orbit_free_comfy_memory", toolset="orbit_dashboard", schema=schemas.FREE_COMFY_MEMORY, handler=tools.free_comfy_memory)
    ctx.register_tool(name="orbit_memory_status", toolset="orbit_memory", schema=schemas.MEMORY_STATUS, handler=memory_bridge.memory_status)
    ctx.register_tool(name="orbit_obsidian_save", toolset="orbit_memory", schema=schemas.OBSIDIAN_SAVE, handler=memory_bridge.save_note)
    ctx.register_hook("pre_llm_call", memory_bridge.memory_policy)
    ctx.register_hook("post_llm_call", memory_bridge.capture_turn)
    ctx.register_cli_command(
        name="orbit",
        help="Control Mac Studio ComfyUI through ORBIT",
        setup_fn=register_cli,
        handler_fn=orbit_command,
        description="Run approved ComfyUI workflows, inspect jobs, and download results through ORBIT.",
    )
    ctx.register_command("orbit", handler=slash_command, description="ORBIT와 ComfyUI 상태·워크플로·작업 확인", args_hint="status | workflows | jobs")
    start_pairing_server()
    memory_bridge.start_worker()
