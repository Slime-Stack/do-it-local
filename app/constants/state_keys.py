"""State key constants for ADK session state.

GitLab PAT is intentionally NOT in session state — it's kept in an
in-memory dict in gitlab_rest.py to prevent Firestore persistence.
"""

PROJECT_URL_KEY = "project_url"
TARGET_BRANCH_KEY = "target_branch"
SCAN_RESULT_KEY = "scan_result"
DETECTION_RESULT_KEY = "detection_result"
GENERATION_RESULT_KEY = "generation_result"
PIPELINE_STATUS_KEY = "pipeline_status"
