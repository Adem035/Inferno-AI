/**
 * Real-time scan display component
 */

import React, { useState, useEffect, useRef } from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import { PythonBridge } from '../utils/bridge.js';
import type { ScanConfig, ScanEvent } from '../types.js';

interface ScanDisplayProps {
    config: ScanConfig;
    onComplete: () => void;
}

export const ScanDisplay: React.FC<ScanDisplayProps> = ({ config, onComplete }) => {
    const [events, setEvents] = useState<ScanEvent[]>([]);
    const [isComplete, setIsComplete] = useState(false);
    // Keep track of unique logs to avoid duplicates if any
    const logsRef = useRef<Set<string>>(new Set());

    useEffect(() => {
        const bridge = new PythonBridge();

        bridge.startScan(config, (event) => {
            // Simple de-duplication based on timestamp + message
            const key = `${event.type}-${event.timestamp}-${(event as any).message}`;
            if (!logsRef.current.has(key)) {
                logsRef.current.add(key);
                setEvents((prev) => [...prev, event]);
            }

            if (event.type === 'complete' || event.type === 'error') {
                setIsComplete(true);
                if (event.type === 'complete') {
                    setTimeout(() => onComplete(), 3000);
                }
            }
        });

        return () => {
            bridge.stop();
        };
    }, [config, onComplete]);

    // Filter relevant events for the log view
    const logEvents = events.filter(e =>
        e.type === 'progress' ||
        e.type === 'vulnerability' ||
        e.type === 'error' ||
        e.type === 'agent_action'
    );

    // Show last 15 events to keep screen clean but provide context
    const displayEvents = logEvents.slice(-15);

    return (
        <Box flexDirection="column" paddingY={1}>
            <Box marginBottom={1}>
                <Text bold color="cyan">
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                </Text>
            </Box>

            <Box marginBottom={1}>
                <Text bold>
                    🔍 Target: <Text color="green">{config.target}</Text>
                </Text>
            </Box>

            {/* Log View */}
            <Box flexDirection="column" borderStyle="round" borderColor="gray" paddingX={1}>
                {displayEvents.map((e, i) => (
                    <LogEntry key={i} event={e} />
                ))}

                {!isComplete && (
                    <Box marginTop={1}>
                        <Text color="yellow">
                            <Spinner type="dots" /> <Text dimColor>Processing...</Text>
                        </Text>
                    </Box>
                )}
            </Box>

            {isComplete && (
                <Box marginTop={1}>
                    <Text bold color="green">✓ Scan Complete</Text>
                </Box>
            )}
        </Box>
    );
};

const LogEntry: React.FC<{ event: ScanEvent }> = ({ event }) => {
    const time = new Date(event.timestamp * 1000).toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    if (event.type === 'progress') {
        let level = 'INFO    ';
        let color = 'blue';
        let message = event.message;

        if (event.step === 'reasoning') {
            level = 'THINK   ';
            color = 'magenta';
        } else if (message.startsWith('Executing:')) {
            level = 'TOOL    ';
            color = 'yellow';
        } else if (message.startsWith('Running:')) {
            level = 'CMD     ';
            color = 'cyan';
        } else if (message.startsWith('Agent says:')) {
            level = 'AGENT   ';
            color = 'green';
        }

        return (
            <Box flexDirection="column">
                <Box>
                    <Text color="gray">[{time}] </Text>
                    <Text color={color} bold>{level} </Text>
                    <Text color="white">
                        {message}
                    </Text>
                </Box>
                {/* Show full reasoning if available */}
                {event.step === 'reasoning' && event.full_reasoning && (
                    <Box marginLeft={13} borderStyle="single" borderColor="gray" paddingX={1}>
                        <Text color="gray" italic>
                            {event.full_reasoning}
                        </Text>
                    </Box>
                )}
            </Box>
        );
    }

    if (event.type === 'vulnerability') {
        return (
            <Box flexDirection="column">
                <Box>
                    <Text color="gray">[{time}] </Text>
                    <Text color="red" bold>VULN    </Text>
                    <Text color={getSeverityColor(event.severity)}>
                        {event.severity}: {event.title}
                    </Text>
                </Box>
                <Box marginLeft={13}>
                    <Text color="gray">└─ {event.endpoint}</Text>
                </Box>
            </Box>
        );
    }

    if (event.type === 'error') {
        return (
            <Box>
                <Text color="gray">[{time}] </Text>
                <Text color="red" bold>ERROR   </Text>
                <Text color="red">{event.message}</Text>
            </Box>
        );
    }

    return null;
};

function getSeverityColor(severity: string): string {
    switch (severity) {
        case 'CRITICAL': return 'redBright';
        case 'HIGH': return 'red';
        case 'MEDIUM': return 'yellow';
        case 'LOW': return 'blue';
        default: return 'white';
    }
}
