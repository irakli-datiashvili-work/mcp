# MCP learning notes

Course: Claude Academy, *Building with the Claude API*, lessons 47-56.
Project: a document chatbot. An MCP **server** holds the documents; an MCP **client** lets Claude use them.

Progress: [x] 0 setup  [x] 1 concepts  [x] 2 tools + inspector  [ ] 3 client  [ ] 4 resources  [ ] 5 prompts  [ ] 6 chat loop  [ ] 7 own server

---

## Stage 0: Setup

- `.venv` holds our packages. Run Python as `.\.venv\Scripts\python.exe` (or activate with `.\.venv\Scripts\Activate.ps1`).
- We pin `mcp[cli]>=1.30,<2`. The course code is written for the 1.x SDK; version 2 renamed things, so the course snippets would fail on it.
- `.env` will hold the API key and is git-ignored. Only the chat loop (stage 6) needs it.

---

## Stage 1: The big idea

### The problem MCP solves
Claude can use **tools** (functions it asks you to run). Without MCP, *you* write every tool: a schema that
describes it to Claude, plus the function that does the work. For something like GitHub that is dozens of tools
to write, test, and maintain.

### What MCP changes
Someone else writes those tools and packages them in an **MCP server**. Your app connects to it and gets the
tool schemas and the working functions ready-made.

MCP and tool use are not competitors. Tool use is how Claude *asks* for something to be run. MCP is about
*who wrote and maintains* the tools.

### The two sides

| Piece | What it is | In our project |
|---|---|---|
| **MCP server** | A program that offers tools / resources / prompts for some service | `mcp_server.py`, which offers our documents |
| **MCP client** | The connector inside your app that talks to servers | `mcp_client.py` |

(In real life you usually build only one side. We build both to see how they fit.)

### Three things a server can offer
| Primitive | One-liner | Who decides to use it |
|---|---|---|
| **Tool** | Do an action (edit a document) | The model |
| **Resource** | Fetch data, like a GET request (read a document) | Your app |
| **Prompt** | A ready-made, well-tested instruction template | The user (e.g. `/format`) |

The "who decides" column comes from the MCP spec, not the course. It is a handy way to remember which is which.

### How client and server talk (transport)
- **stdio**: the client starts the server as a subprocess on the same machine and they exchange messages
  through standard input/output. This is the common local setup, and what we use.
- **Network** (HTTP, WebSockets, ...): the server runs elsewhere and the client connects to it.
- The client does not care which one is used.

Rule that follows from stdio: a server must **never `print()`** to stdout. That channel carries the protocol
messages (JSON), and the MCP spec says a server must not write anything else there. We tested this: a server
that printed one stray line made the SDK client log `Failed to parse JSONRPC message from server` with a stack
trace and pass a `ValidationError` to the app. The SDK carried on, but other clients may be stricter, so don't
rely on that. To debug a server, print to **stderr** (`print(..., file=sys.stderr)`) or use `logging`.
(Gotcha: when stdout is a pipe, Python buffers `print`, so the stray line can show up late or not at all.)

### Messages the client sends
- `ListToolsRequest` -> the server answers with the list of tools.
- `CallToolRequest` -> the server runs one tool with given arguments and returns the result.
(Resources and prompts get their own list/read/get requests later.)

### The full flow, when a user asks "What repositories do I have?"
1. User asks your app a question.
2. Your app asks the **client** for the available tools (client -> server `ListTools`).
3. Your app sends the question **plus the tool list** to Claude.
4. Claude replies: "please run tool X with these arguments".
5. Your app asks the **client** to run it (`CallTool`); the server does the real work (e.g. calls GitHub).
6. The result travels back: server -> client -> your app.
7. Your app sends the tool result to Claude.
8. Claude writes the final answer; your app shows it to the user.

Claude never talks to the MCP server directly. **Your app is the middleman**, and the client is the part of
your app that speaks MCP.

---

## Stage 2: Tools + the Inspector

### What `mcp_server.py` does
- `FastMCP("DocumentMCP")` creates a complete MCP server in one line.
- `docs` is a plain dict (id -> text). It lives in memory, so edits vanish when the server restarts.
- `@mcp.tool(name=..., description=...)` turns a Python function into a tool. The SDK writes the JSON schema
  for you from the **description, type hints and `Field(description=...)`**, so those are what Claude reads to
  decide how to call the tool. Write them for Claude, not for yourself.
- Raising `ValueError("Doc with id ... not found")` is deliberate: the message goes back to Claude, which can
  then correct itself.
- `mcp.run()` starts the server on stdio.

Real schema the SDK generated for `read_doc_contents` (we printed it):
`{"properties": {"doc_id": {"description": "Id of the document to read", "type": "string"}}, "required": ["doc_id"]}`
That JSON is exactly what gets sent to Claude as the tool definition.

Small differences from the course: `edit_document` returns `"Edited <id>"` (the course returns nothing, which
shows up as an empty result in the Inspector), and I completed two truncated sample strings in `docs`.

### Running the Inspector (a browser UI to poke at your server without any client or Claude)
The course uses `mcp dev mcp_server.py`, which needs `uv`. We start the Inspector directly. From the project folder:

    npx -y @modelcontextprotocol/inspector@0.22.0 .\.venv\Scripts\python.exe mcp_server.py

- Why `@0.22.0`: the newest release (2.13.0) crashed on this machine with `Cannot find native binding` (an npm
  optional-dependency bug), and 0.22.0 has the same UI as the course. It is marked deprecated (v1 gets security
  fixes only). That is fine here: it only listens on localhost.
- It prints a URL with a token (proxy on port 6277, page on 6274) and opens your browser. Leave that terminal running.
- Press Ctrl+C in the terminal to stop it.

### Stage 2 check (do this in the browser)
1. Click **Connect**. Open the **Tools** tab, click **List Tools**: you should see both tools.
2. Run `read_doc_contents` with `doc_id` = `deposition.md`. You should see "This deposition covers the testimony of Angela Smith, P.E."
3. Run `edit_document` with `doc_id` = `deposition.md`, `old_str` = `Angela Smith`, `new_str` = `Jordan Lee`.
4. Run `read_doc_contents` again. The text should now say Jordan Lee.
5. Try `doc_id` = `nope.md` and read the error. That is what Claude would see too.
