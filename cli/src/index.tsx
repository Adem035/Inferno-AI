#!/usr/bin/env node
/**
 * Inferno CLI - Main Entry Point
 * Production-grade terminal interface for Inferno Security Scanner
 */

import React, { useState } from 'react';
import { render } from 'ink';
import { Welcome } from './components/Welcome.js';
import { DockerCheck } from './components/DockerCheck.js';
import { TargetInput } from './components/TargetInput.js';
import { ScanDisplay } from './components/ScanDisplay.js';
import type { ScanConfig } from './types.js';

type Screen = 'welcome' | 'docker-check' | 'input' | 'scanning' | 'complete';

const App: React.FC = () => {
    const [screen, setScreen] = useState<Screen>('docker-check');
    const [scanConfig, setScanConfig] = useState<ScanConfig | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Debug logging
    React.useEffect(() => {
        console.error(`[DEBUG] Screen changed to: ${screen}`);
    }, [screen]);

    if (error) {
        console.error(`[ERROR] ${error}`);
        return (
            <React.Fragment>
                <Welcome />
                <Box flexDirection="column" paddingY={1}>
                    <Text color="red" bold>
                        ❌ Error: {error}
                    </Text>
                    <Text dimColor>
                        Please resolve the issue and try again.
                    </Text>
                </Box>
            </React.Fragment>
        );
    }

    switch (screen) {
        case 'welcome':
            return <Welcome />;

        case 'docker-check':
            return (
                <React.Fragment>
                    <Welcome />
                    <DockerCheck
                        onReady={() => setScreen('input')}
                        onError={setError}
                    />
                </React.Fragment>
            );

        case 'input':
            return (
                <React.Fragment>
                    <Welcome />
                    <TargetInput
                        onSubmit={(config) => {
                            setScanConfig(config);
                            setScreen('scanning');
                        }}
                    />
                </React.Fragment>
            );

        case 'scanning':
            return (
                <React.Fragment>
                    <Welcome />
                    {scanConfig && (
                        <ScanDisplay
                            config={scanConfig}
                            onComplete={() => setScreen('complete')}
                        />
                    )}
                </React.Fragment>
            );

        case 'complete':
            return (
                <React.Fragment>
                    <Welcome />
                    <Box paddingY={1}>
                        <Text>Scan complete! Check ctf-logs/ for detailed results.</Text>
                    </Box>
                </React.Fragment>
            );

        default:
            return <Welcome />;
    }
};

// Import Box and Text for error handling
import { Box, Text } from 'ink';

// Render the app
render(<App />);
