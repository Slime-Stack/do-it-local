"""State key constants for ADK session state."""

# Input keys (set before pipeline runs)
PROJECT_URL_KEY = "project_url"
TARGET_BRANCH_KEY = "target_branch"

# NOTE: GitLab PAT is intentionally NOT stored in session state.
# It's kept in an in-memory dict in gitlab_rest.py, keyed by user_id,
# and cleaned up after each pipeline run. This prevents accidental
# persistence to Firestore or serialization in logs.

# Pipeline output keys (set by agents via tools)
SCAN_RESULT_KEY = "scan_result"
DETECTION_RESULT_KEY = "detection_result"
GENERATION_RESULT_KEY = "generation_result"

# Status tracking
PIPELINE_STATUS_KEY = "pipeline_status"
