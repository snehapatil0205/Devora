from agent.agent import run_agent

print("\n--- Running Devora Agent Test: XO Game in React ---")
result = run_agent(
    "Create a responsive Tic Tac Toe (XO Game) application in React with 2-player and AI opponent modes, score tracking, win celebrations, and a reset button."
)

print("\nStatus:", result.get("status"))
print("Response:\n", result.get("response"))
print("Tool calls count:", len(result.get("tool_calls", [])))
for call in result.get("tool_calls", []):
    print(" - Tool:", call.get("tool"))