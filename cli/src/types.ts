/**
 * Type definitions for Inferno CLI
 */

export interface ScanConfig {
    target: string;
    objective?: string;
    provider?: string;
    model?: string;
}

export interface ProgressEvent {
    type: 'progress';
    step: string;
    message: string;
    timestamp: number;
    full_reasoning?: string;
}

export interface AgentActionEvent {
    type: 'agent_action';
    agent: 'main' | 'sandbox' | 'validator';
    action: string;
    command?: string;
    result?: string;
    timestamp: number;
}

export interface VulnerabilityEvent {
    type: 'vulnerability';
    severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
    title: string;
    endpoint: string;
    evidence: string;
    timestamp: number;
}

export interface CompleteEvent {
    type: 'complete';
    summary: {
        vulnerabilities: number;
        time: number;
        cost?: string;
    };
    timestamp: number;
}

export interface ErrorEvent {
    type: 'error';
    message: string;
    stack?: string;
    timestamp: number;
}

export type ScanEvent =
    | ProgressEvent
    | AgentActionEvent
    | VulnerabilityEvent
    | CompleteEvent
    | ErrorEvent;

export interface DockerStatus {
    installed: boolean;
    running: boolean;
    imageBuilt: boolean;
}

export interface SystemStatus {
    docker: DockerStatus;
    llmConfigured: boolean;
    sandboxReady: boolean;
}
