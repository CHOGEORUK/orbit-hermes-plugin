STATUS = {
    "name": "orbit_status",
    "description": "Check the authenticated ORBIT connection, Mac Studio ComfyUI availability, queue depth, and granted capabilities before controlling generation.",
    "parameters": {"type": "object", "properties": {}},
}

LIST_WORKFLOWS = {
    "name": "orbit_list_workflows",
    "description": "List ComfyUI workflows that this user is allowed to run. Call this before creating a job when the workflow id or required inputs are unknown.",
    "parameters": {"type": "object", "properties": {}},
}

CREATE_JOB = {
    "name": "orbit_create_job",
    "description": "Run one approved ComfyUI image or video workflow on the Mac Studio. Use only a workflow_id and input names returned by orbit_list_workflows; never invent raw ComfyUI nodes.",
    "parameters": {
        "type": "object",
        "properties": {
            "workflow_id": {"type": "string", "description": "Exact approved workflow id from orbit_list_workflows."},
            "inputs": {"type": "object", "description": "Workflow input values keyed by the declared input names."},
        },
        "required": ["workflow_id", "inputs"],
    },
}

LIST_JOBS = {
    "name": "orbit_list_jobs",
    "description": "List this user's recent ORBIT ComfyUI jobs and real states.",
    "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}}},
}

GET_JOB = {"name": "orbit_get_job", "description": "Get one owned ORBIT job, including state, inputs, errors, and timestamps.", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}}
WAIT_JOB = {
    "name": "orbit_wait_job",
    "description": "Wait for an owned ORBIT ComfyUI job to complete, fail, or be cancelled, then return result metadata. Use after orbit_create_job when the user wants the finished output.",
    "parameters": {
        "type": "object",
        "properties": {
            "job_id": {"type": "string"},
            "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600, "default": 300},
            "poll_seconds": {"type": "number", "minimum": 0.5, "maximum": 10, "default": 2},
        },
        "required": ["job_id"],
    },
}
CANCEL_JOB = {"name": "orbit_cancel_job", "description": "Cancel an owned ORBIT job if it is still pending or queued. This does not interrupt another user's work.", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}}
RERUN_JOB = {"name": "orbit_rerun_job", "description": "Create a new ORBIT job from an owned job's saved workflow and inputs.", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}}
LIST_RESULTS = {"name": "orbit_list_results", "description": "List centrally stored output files for a completed owned ORBIT job.", "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}}
DOWNLOAD_RESULT = {"name": "orbit_download_result", "description": "Download one owned ORBIT result file from the Mac Studio to this computer.", "parameters": {"type": "object", "properties": {"result_id": {"type": "string"}, "output_path": {"type": "string", "description": "Destination filename on this computer."}}, "required": ["result_id", "output_path"]}}
FREE_COMFY_MEMORY = {
    "name": "orbit_free_comfy_memory",
    "description": "Unload ComfyUI models and free Mac Studio memory. Admin only; refuses while any ComfyUI job is running or queued.",
    "parameters": {"type": "object", "properties": {}},
}

MEMORY_STATUS = {
    "name": "orbit_memory_status",
    "description": "Check whether this Hermes profile is configured for selective Obsidian capture. Hindsight status is managed by the official Hermes memory provider.",
    "parameters": {"type": "object", "properties": {}},
}

OBSIDIAN_SAVE = {
    "name": "orbit_obsidian_save",
    "description": "Save a durable note to this user's configured Obsidian vault when the user explicitly asks to remember or document it. Never include passwords, API keys, tokens, secrets, or temporary chat.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short stable Korean note title."},
            "content": {"type": "string", "description": "Concise durable fact, decision, procedure, or project update."},
            "score": {"type": "integer", "minimum": 0, "maximum": 100, "description": "Hermes' importance score. 80+ is filed directly, 60-79 goes to the review inbox."},
            "category": {"type": "string", "enum": ["decision", "project", "system", "model", "person", "reference", "other"]},
            "tags": {"type": "array", "items": {"type": "string"}},
            "links": {"type": "array", "items": {"type": "string"}, "description": "Related Obsidian note names without brackets."},
            "reason": {"type": "string", "description": "Short explanation of why this is durable enough to save."},
        },
        "required": ["title", "content", "score"],
    },
}
