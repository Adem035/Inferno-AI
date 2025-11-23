/**
 * Interactive target and objective input component
 */

import React, { useState } from 'react';
import { Box, Text } from 'ink';
import TextInput from 'ink-text-input';
import type { ScanConfig } from '../types.js';

interface TargetInputProps {
    onSubmit: (config: ScanConfig) => void;
}

export const TargetInput: React.FC<TargetInputProps> = ({ onSubmit }) => {
    const [step, setStep] = useState<'target' | 'objective'>('target');
    const [target, setTarget] = useState('');
    const [objective, setObjective] = useState('');

    const handleTargetSubmit = (value: string) => {
        console.error(`[DEBUG] Target submitted: "${value}"`);
        setTarget(value);
        setStep('objective');
    };

    const handleObjectiveSubmit = (value: string) => {
        console.error(`[DEBUG] Objective submitted: "${value}"`);
        setObjective(value);
        onSubmit({
            target,
            objective: value || undefined
        });
    };

    return (
        <Box flexDirection="column" paddingY={1}>
            <Box marginBottom={1}>
                <Text bold color="cyan">
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                </Text>
            </Box>

            <Box marginBottom={1}>
                <Text bold>📋 Scan Configuration</Text>
            </Box>

            {step === 'target' ? (
                <Box>
                    <Text color="gray">? </Text>
                    <Text bold>Target URL: </Text>
                    <TextInput
                        value={target}
                        onChange={setTarget}
                        onSubmit={handleTargetSubmit}
                        placeholder="example.com"
                    />
                </Box>
            ) : (
                <>
                    <Box marginBottom={1}>
                        <Text color="green">✓ Target: {target}</Text>
                    </Box>
                    <Box>
                        <Text color="gray">? </Text>
                        <Text bold>Custom objective (optional): </Text>
                        <TextInput
                            value={objective}
                            onChange={setObjective}
                            onSubmit={handleObjectiveSubmit}
                            placeholder="Focus on OWASP Top 10"
                        />
                    </Box>
                    <Box marginTop={1}>
                        <Text dimColor>Press Enter to skip</Text>
                    </Box>
                </>
            )}
        </Box>
    );
};
