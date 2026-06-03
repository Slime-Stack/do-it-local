"""GitLab REST API tools wrapping python-gitlab.

Fills gaps in the GitLab MCP server (no file read, tree list, branch
create, or commit tools). Token is read from ADK session state.
"""

import json
import logging
import os

import gitlab
from google.adk.tools import ToolContext

from app.constants.state_keys import GITLAB_TOKEN_KEY, PROJECT_URL_KEY

logger = logging.getLogger(__name__)


def _extract_project_path(project_url: str) -> str:
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    path = str(project_url).strip().rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    for prefix in [f"{gitlab_url}/", "https://gitlab.com/", "http://gitlab.com/"]:
        if path.startswith(prefix):
            path = path[len(prefix) :]
            break
    return path


def _get_client(tool_context: ToolContext) -> tuple[gitlab.Gitlab, str]:
    token = tool_context.state.get(GITLAB_TOKEN_KEY, "")
    if not token:
        raise ValueError("No GitLab token available in session state")

    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    if token.startswith("glpat-"):
        gl = gitlab.Gitlab(gitlab_url, private_token=token)
    else:
        gl = gitlab.Gitlab(gitlab_url, oauth_token=token)

    project_url = tool_context.state.get(PROJECT_URL_KEY, "")
    if not project_url:
        raise ValueError("No project_url found in state")

    path = _extract_project_path(project_url)
    logger.info("Resolved project path: %s", path)
    return gl, path


def list_repo_tree(
    tool_context: ToolContext, path: str = "", recursive: bool = True
) -> dict:
    """List files and directories in a GitLab repository.

    Args:
        path: Subdirectory path to list. Empty string for root.
        recursive: Whether to list recursively.
    """
    try:
        gl, project_path = _get_client(tool_context)
        project = gl.projects.get(project_path)
        items = project.repository_tree(
            path=path, recursive=recursive, per_page=100, get_all=True
        )
        tree = [
            {"name": item["name"], "path": item["path"], "type": item["type"]}
            for item in items
        ]
        return {"status": "success", "total_items": len(tree), "tree": tree}
    except Exception as e:
        logger.error("list_repo_tree failed: %s", e)
        return {"status": "error", "error": str(e)}


def read_file(
    tool_context: ToolContext,
    file_path: str,
    ref: str = "main",
    offset: int = 0,
    limit: int = 500,
) -> dict:
    """Read a file's contents from a GitLab repository.

    Returns up to `limit` lines starting from line `offset`. If the file
    has more lines beyond the returned range, `truncated` will be true
    and you can call again with a higher `offset` to read the rest.

    Args:
        file_path: Path to the file within the repository.
        ref: Branch or commit ref.
        offset: Line to start from (0-based). Default 0.
        limit: Max lines to return. Default 500.
    """
    try:
        gl, project_path = _get_client(tool_context)
        project = gl.projects.get(project_path)
        f = project.files.get(file_path=file_path, ref=ref)
        content = f.decode().decode("utf-8")
        lines = content.splitlines()
        total = len(lines)
        chunk = lines[offset : offset + limit]
        return {
            "status": "success",
            "file_path": file_path,
            "content": "\n".join(chunk),
            "offset": offset,
            "lines_returned": len(chunk),
            "total_lines": total,
            "truncated": (offset + limit) < total,
        }
    except Exception as e:
        logger.error("read_file failed for %s: %s", file_path, e)
        return {"status": "error", "error": str(e)}


def read_files(
    tool_context: ToolContext, file_paths_json: str, ref: str = "main"
) -> dict:
    """Read multiple files at once from a GitLab repository.

    Use this instead of calling read_file multiple times. Returns all
    file contents in a single response.

    Args:
        file_paths_json: JSON array of file path strings, e.g. '["README.md", "package.json"]'
        ref: Branch or commit ref.
    """
    try:
        file_paths = json.loads(file_paths_json)
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"Invalid JSON: {e}"}

    gl, project_path = _get_client(tool_context)
    project = gl.projects.get(project_path)

    results = []
    for fp in file_paths:
        try:
            f = project.files.get(file_path=fp, ref=ref)
            content = f.decode().decode("utf-8")
            lines = content.splitlines()
            total = len(lines)
            chunk = lines[:500]
            results.append(
                {
                    "status": "success",
                    "file_path": fp,
                    "content": "\n".join(chunk),
                    "total_lines": total,
                    "truncated": total > 500,
                }
            )
        except Exception as e:
            results.append({"status": "error", "file_path": fp, "error": str(e)})

    return {
        "status": "success",
        "files_read": len(results),
        "files": results,
    }


def create_branch(
    tool_context: ToolContext, branch_name: str, ref: str = "main"
) -> dict:
    """Create a new branch in the GitLab repository.

    Args:
        branch_name: Name for the new branch.
        ref: Source branch or commit to branch from.
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
    try:
        gl, project_path = _get_client(tool_context)
        project = gl.projects.get(project_path)
        files = json.loads(files_json)
        actions = [
            {"action": "create", "file_path": f["file_path"], "content": f["content"]}
            for f in files
        ]
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
