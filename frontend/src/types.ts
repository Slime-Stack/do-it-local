export interface ToolCallEvent {
  agent: string
  type: 'tool_call'
  content: { name: string; args: Record<string, unknown> }
}

export interface ToolResultEvent {
  agent: string
  type: 'tool_result'
  content: { name: string; result: string }
}

export interface TextEvent {
  agent: string
  type: 'text'
  content: string
}

export interface StatusEvent {
  type: 'status'
  status: string
}

export interface DoneEvent {
  type: 'done'
  results: {
    scan_result?: Record<string, unknown>
    detection_result?: Record<string, unknown>
    generation_result?: Record<string, unknown>
  }
}

export interface ErrorEvent {
  type: 'error'
  error: string
}

export type PipelineEvent =
  | ToolCallEvent
  | ToolResultEvent
  | TextEvent
  | StatusEvent
  | DoneEvent
  | ErrorEvent
