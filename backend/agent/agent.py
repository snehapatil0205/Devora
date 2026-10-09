import json
from pathlib import Path
from agent.llm import client, MODEL
from agent.tools.registry import execute_tool


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file in the workspace (e.g. index.html, style.css, app.js). Use this to write code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path inside the workspace, e.g. 'index.html'."},
                    "content": {"type": "string", "description": "The complete source code or text content."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read an existing workspace file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path inside workspace."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file or directory from the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path to delete."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run an allowed development command in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to run, e.g. 'python script.py'"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_project",
            "description": "Search workspace files for text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."}
                },
                "required": ["query"],
            },
        },
    },
]


SYSTEM_INSTRUCTIONS = """
You are Devora, an elite AI software engineering agent.
Your goal is to build complete, functional, modern, and visually stunning web applications and games that run immediately in the live preview.

PRIMARY DIRECTIVE — LIVE APPLICATION PREVIEW:
1. The user views their application in a real-time browser preview iframe.
2. For any web application, UI, or game request (e.g. Todo App, Tic-Tac-Toe / XO game, Calculator, Weather app, Notes app, Dashboard, etc.), you MUST create or update `index.html` in the root of the workspace.
3. The preview directly renders `index.html`. Always ensure `index.html` exists and is a complete, working HTML5 document.
4. If the user mentions React, JSX, or modern frameworks:
   - Build a real, working React application that runs directly in the browser!
   - Load React 18 and Babel Standalone via CDN in `index.html`:
     <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
     <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
     <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
   - Include a root element: `<div id="root"></div>`
   - Use `<script type="text/babel">` with full React state, hooks (useState, useEffect, useMemo), components, animations, and clean styling.
   - This provides a genuine, zero-latency React application that runs instantly in the preview without complex build steps failing.

5. DESIGN & QUALITY STANDARDS:
   - Provide a polished, high-end user interface with modern fonts, vibrant accents, smooth hover states, responsive layouts, and dark/light polish.
   - Fully interactive: make sure every button, input, toggle, and feature works end-to-end.
   - Never write placeholders, stubs, or comments like "TODO: implement this". Deliver complete, working code.

6. FAST & PROACTIVE EXECUTION:
   - Immediately use `write_file` to create the necessary files (`index.html`, etc.).
   - Do not waste iterations reading empty folders or unnecessary files.
   - When finished, summarize the application features and let the user know they can interact with it in the Live Preview.
"""


def run_agent(user_request: str):
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": user_request[:6000]},
    ]

    executed_tools = []
    max_iterations = 15

    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=4000,
            temperature=0.3,
        )

        message = response.choices[0].message
        message_dict = message.model_dump(exclude_none=True)
        messages.append(message_dict)

        tool_calls = message.tool_calls or []

        if not tool_calls:
            return {
                "status": "completed",
                "response": message.content or "Application created successfully! Check the live preview.",
                "tool_calls": executed_tools,
            }

        for tool_call in tool_calls:
            name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                if not isinstance(arguments, dict):
                    arguments = {}

                result = execute_tool(name, arguments)

            except Exception as error:
                result = {
                    "success": False,
                    "error": f"{type(error).__name__}: {error}",
                }

            result_text = json.dumps(result, default=str)

            executed_tools.append({
                "tool": name,
                "result": result_text[:1200],
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_text[:4000],
            })

    return {
        "status": "completed",
        "response": (
            "Devora finished building the application files. "
            "You can now test it in the Live Preview panel."
        ),
        "tool_calls": executed_tools,
    }
