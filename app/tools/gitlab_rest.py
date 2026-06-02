"""GitLab REST API tools wrapping python-gitlab.

These fill gaps in the GitLab MCP server which lacks file read, tree list,
branch create, and commit tools.

SECURITY: GitLab PATs are provided per-request by the user and stored in a
module-level dict keyed by session user_id for the duration of the pipeline
run only. Tokens are never stored in ADK session state (which could be
serialized to Firestore), never in environment variables, and never logged.
"""
import logging
import os

import gitlab
from google.adk.tools import ToolContext

from app.constants.state_keys import PROJECT_URL_KEY

logger = logging.getLogger(__name__)

# In-memory PAT store keyed by session user_id. Tokens live only for the
# duration of the pipeline run and are cleaned up by clear_token().
_token_store: dict[str, str] = {}


def set_token(user_id: str, token: str) -> None:
    """Store a GitLab PAT for a pipeline run. Called by pipeline_runner."""
    _token_store[user_id] = token


def clear_token(user_id: str) -> None:
    """Remove a GitLab PAT after pipeline completes. Called by pipeline_runner."""
    _token_store.pop(user_id, None)


def _get_client(tool_context: ToolContext) -> tuple[gitlab.Gitlab, str]:
    """Create a GitLab client and extract project path from state."""
    user_id = getattr(tool_context, "user_id", None) or ""
    token = _token_store.get(user_id)
    if not token:
        raise ValueError(
            "No GitLab token available for this session. "
            "Token must be provided per-request via the API."
        )

    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    gl = gitlab.Gitlab(gitlab_url, private_token=token)

    project_url = tool_context.state.get(PROJECT_URL_KEY, "")
    # Extract project path from URL: https://gitlab.com/group/project -> group/project
    if project_url:
        path = project_url.rstrip("/")
        # Remove .git suffix if present
        if path.endswith(".git"):
            path = path[:-4]
        # Remove protocol and host
        for prefix in [f"{gitlab_url}/", "https://gitlab.com/", "http://gitlab.com/"]:
            if path.startswith(prefix):
                path = path[len(prefix):]
                break
    else:
        raise ValueError("No project_url found in state")

    return gl, path


def list_repo_tree(
    tool_context: ToolContext, path: str = "", recursive: bool = True
) -> dict:
    """List files and directories in a GitLab repository.

    Args:
        path: Subdirectory path to list. Empty string for root.
        recursive: Whether to list recursively. Defaults to True.
    """
    try:
        gl, project_path = _get_client(tool_context)
        project = gl.projects.get(project_path)

        items = project.repository_tree(
            path=path, recursive=recursive, per_page=100, get_all=True
        )

        tree = []
        for item in items:
            tree.append(
                {
                    "name": item["name"],
                    "path": item["path"],
                    "type": item["type"],  # "blob" (file) or "tree" (dir)
                }
            )

        return {
            "status": "success",
            "total_items": len(tree),
            "tree": tree,
        }
    except Exception as e:
        logger.error("list_repo_tree failed: %s", e)
        return {"status": "error", "error": str(e)}


def read_file(tool_context: ToolContext, file_path: str, ref: str = "main") -> dict:
    """Read a file's contents from a GitLab repository.

    Args:
        file_path: Path to the file within the repository.
        ref: Branch or commit ref. Defaults to 'main'.
    """
    try:
        gl, project_path = _get_client(tool_context)
        project = gl.projects.get(project_path)

        f = project.files.get(file_path=file_path, ref=ref)
        content = f.decode().decode("utf-8")

        return {
            "status": "success",
            "file_path": file_path,
            "content": content,
            "size": len(content),
        }
    except Exception as e:
        logger.error("read_file failed for %s: %s", file_path, e)
        return {"status": "error", "error": str(e)}


def create_branch(
    tool_context: ToolContext, branch_name: str, ref: str = "main"
) -> dict:
    """Create a new branch in the GitLab repository.

    Args:
        branch_name: Name for the new branch.
        ref: Source branch or commit to branch from. Defaults to 'main'.
    """
    try:
        gl, project_path = _get_client(tool_context)
        project = gl.projects.get(project_path)

        branch = project.branches.create({"branch": branch_name, "ref": ref})

        return {
            "status": "success",
            "branch_name": branch.name,
            "message": f"Branch '{branch_name}' created from '{ref}'",
        }
    except Exception as e:
        logger.error("create_branch failed: %s", e)
        return {"status": "error", "error": str(e)}


def commit_files(
    tool_context: ToolContext,
    branch_name: str,
    commit_message: str,
    files_json: str,
) -> dict:
    """Commit multiple files to a GitLab repository branch.

    Args:
        branch_name: Target branch name.
        commit_message: Commit message.
        files_json: JSON array of objects with 'file_path' and 'content' keys.
    """
    import json

    try:
        gl, project_path = _get_client(tool_context)
        project = gl.projects.get(project_path)

        files = json.loads(files_json)
        actions = []
        for f in files:
            actions.append(
                {
                    "action": "create",
                    "file_path": f["file_path"],
                    "content": f["content"],
                }
            )

        commit = project.commits.create(
            {
                "branch": branch_name,
                "commit_message": commit_message,
                "actions": actions,
            }
        )

        return {
            "status": "success",
            "commit_id": commit.id,
            "message": f"Committed {len(actions)} files to '{branch_name}'",
        }
    except Exception as e:
        logger.error("commit_files failed: %s", e)
        return {"status": "error", "error": str(e)}
