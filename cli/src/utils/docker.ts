/**
 * Docker utilities for Inferno CLI
 * Handles detection, installation, and verification
 */

import { execa } from 'execa';
import { platform } from 'os';
import type { DockerStatus } from '../types.js';

export async function checkDockerInstalled(): Promise<boolean> {
    try {
        await execa('docker', ['--version']);
        return true;
    } catch {
        return false;
    }
}

export async function checkDockerRunning(): Promise<boolean> {
    try {
        await execa('docker', ['ps']);
        return true;
    } catch {
        return false;
    }
}

export async function checkImageBuilt(imageName: string = 'inferno-sandbox:latest'): Promise<boolean> {
    try {
        const { stdout } = await execa('docker', ['images', '-q', imageName]);
        return stdout.trim().length > 0;
    } catch {
        return false;
    }
}

export async function getDockerStatus(): Promise<DockerStatus> {
    const installed = await checkDockerInstalled();
    const running = installed ? await checkDockerRunning() : false;
    const imageBuilt = running ? await checkImageBuilt() : false;

    return { installed, running, imageBuilt };
}

export async function installDockerMac(): Promise<void> {
    const os = platform();

    if (os === 'darwin') {
        // Try Homebrew first
        try {
            await execa('brew', ['--version']);
            await execa('brew', ['install', '--cask', 'docker']);
            return;
        } catch {
            throw new Error(
                'Please install Docker Desktop from https://www.docker.com/products/docker-desktop'
            );
        }
    } else if (os === 'linux') {
        // Use Docker's official installation script
        const { stdout: script } = await execa('curl', ['-fsSL', 'https://get.docker.com']);
        await execa('sh', ['-c', script]);
    } else {
        throw new Error(
            'Please install Docker Desktop from https://www.docker.com/products/docker-desktop'
        );
    }
}

export async function startDockerDesktop(): Promise<void> {
    const os = platform();

    if (os === 'darwin') {
        await execa('open', ['-a', 'Docker']);
    } else {
        throw new Error('Please start Docker manually');
    }
}

export async function buildSandboxImage(onProgress?: (message: string) => void): Promise<void> {
    try {
        onProgress?.('Building sandbox image...');

        await execa('docker', [
            'build',
            '-t',
            'inferno-sandbox:latest',
            '/Users/ademkok/Inferno-AI/Inferno'
        ]);

        onProgress?.('Sandbox image built successfully');
    } catch (error) {
        throw new Error(`Failed to build sandbox image: ${error}`);
    }
}

export async function ensureDocker(
    onProgress?: (message: string) => void
): Promise<DockerStatus> {
    const status = await getDockerStatus();

    // Install if not installed
    if (!status.installed) {
        onProgress?.('Installing Docker...');
        await installDockerMac();
        onProgress?.('Docker installed');
        status.installed = true;
    }

    // Start if not running
    if (!status.running) {
        onProgress?.('Starting Docker...');
        await startDockerDesktop();

        // Wait for Docker to start (max 30 seconds)
        for (let i = 0; i < 30; i++) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            if (await checkDockerRunning()) {
                status.running = true;
                break;
            }
        }

        if (!status.running) {
            throw new Error('Docker failed to start within 30 seconds');
        }
        onProgress?.('Docker is running');
    }

    // Build image if not built
    if (!status.imageBuilt) {
        await buildSandboxImage(onProgress);
        status.imageBuilt = true;
    }

    return status;
}
