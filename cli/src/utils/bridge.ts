/**
 * Python bridge for Inferno CLI
 * Handles communication with Python backend via stdin/stdout
 */

import { execa } from 'execa';
import type { ScanConfig, ScanEvent } from '../types.js';

export class PythonBridge {
    private process: ReturnType<typeof execa> | null = null;

    async startScan(
        config: ScanConfig,
        onEvent: (event: ScanEvent) => void
    ): Promise<void> {
        try {
            // Start Python CLI wrapper
            this.process = execa(
                'python3',
                ['/Users/ademkok/Inferno-AI/Inferno/inferno_cli.py'],
                {
                    cwd: '/Users/ademkok/Inferno-AI/Inferno',
                    env: {
                        ...process.env,
                        PYTHONUNBUFFERED: '1' // Disable Python output buffering
                    }
                }
            );

            // Send configuration
            this.process.stdin?.write(JSON.stringify(config) + '\n');

            // Stream output line-by-line using readline to handle buffering correctly
            if (this.process.stdout) {
                const readline = await import('readline');
                const rl = readline.createInterface({
                    input: this.process.stdout,
                    crlfDelay: Infinity
                });

                for await (const line of rl) {
                    try {
                        // Skip empty lines
                        if (!line.trim()) continue;

                        const event: ScanEvent = JSON.parse(line);
                        onEvent(event);
                    } catch (e) {
                        // Ignore non-JSON output (debug logs, etc.)
                        // console.error('Failed to parse line:', line);
                    }
                }
            }

            await this.process;
        } catch (error: any) {
            onEvent({
                type: 'error',
                message: error.message || 'Scan failed',
                stack: error.stack
            });
        }
    }

    stop(): void {
        if (this.process) {
            this.process.kill('SIGTERM');
            this.process = null;
        }
    }
}
