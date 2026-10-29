from mcp.server.fastmcp import FastMCP
from pydantic import Field

# log_level="ERROR" keeps the SDK quiet. Reminder: stdout is the protocol channel,
# so a stdio server must never print() to it.
mcp = FastMCP("DocumentMCP", log_level="ERROR")

# In-memory "database": document id -> content.
docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditure",
    "outlook.pdf": "This document presents the projected future performance of the company.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment",
}


# The decorator registers the function as a tool. The SDK builds the JSON schema
# Claude sees from the name, description, type hints and Field descriptions.
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string.",
)
def read_document(doc_id: str = Field(description="Id of the document to read")):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    return docs[doc_id]


@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string.",
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(
        description="The text to replace. Must match exactly, including whitespace."
    ),
    new_str: str = Field(
        description="The new text to insert in place of the old text."
    ),
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    docs[doc_id] = docs[doc_id].replace(old_str, new_str)
    return f"Edited {doc_id}"


if __name__ == "__main__":
    # Default transport is stdio: the client launches this file as a subprocess.
    mcp.run()
