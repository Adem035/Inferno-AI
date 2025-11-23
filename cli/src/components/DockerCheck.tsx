/**
 * Docker verification and auto-install component
 */

import React, { useState, useEffect } from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import { ensureDocker } from '../utils/docker.js';
import type { DockerStatus } from '../types.js';

interface DockerCheckProps {
    onReady: () => void;
    onError: (error: string) => void;
}

export const DockerCheck: React.FC<DockerCheckProps> = ({ onReady, onError }) => {
    const [status, setStatus] = useState('');
    const [dockerStatus, setDockerStatus] = useState<DockerStatus | null>(null);

    useEffect(() => {
        let cancelled = false;

        const checkDocker = async () => {
            try {
                const result = await ensureDocker((message) => {
                    if (!cancelled) setStatus(message);
                });

                if (!cancelled) {
                    setDockerStatus(result);
                    setStatus('Docker ready ✓');
                    // Give user time to see the status before progressing
                    setTimeout(() => onReady(), 2000);
                }
            } catch (error: any) {
                if (!cancelled) {
                    onError(error.message || 'Docker setup failed');
                }
            }
        };

        checkDocker();

        return () => {
            cancelled = true;
        };
    }, [onReady, onError]);

    return (
        <Box flexDirection="column" paddingY={1}>
            <Box>
                <Text>
                    <Spinner type="dots" />
                    {' '}
                    {status || 'Checking Docker...'}
                </Text>
            </Box>

            {dockerStatus && (
                <Box flexDirection="column" marginTop={1}>
                    <Text color="green">
                        ✓ Docker: {dockerStatus.installed ? 'Installed' : 'Installing...'}
                    </Text>
                    {dockerStatus.running && (
                        <Text color="green">
                            ✓ Docker: Running
                        </Text>
                    )}
                    {dockerStatus.imageBuilt && (
                        <Text color="green">
                            ✓ Sandbox: Ready
                        </Text>
                    )}
                </Box>
            )}
        </Box>
    );
};
