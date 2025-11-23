#!/usr/bin/env python3
"""
Inferno CLI Wrapper
Provides JSON-based interface for the Node.js CLI
"""

import json
import sys
import os
import asyncio
from typing import Any, Dict
from datetime import datetime

# Add Inferno directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import existing Inferno modules
from main import run_single_target_scan


def emit_event(event: Dict[str, Any]) -> None:
    """Emit a JSON event to stdout for the CLI to consume."""
    print(json.dumps(event), flush=True)


def emit_progress(step: str, message: str) -> None:
    """Emit a progress event."""
    emit_event({
        'type': 'progress',
        'step': step,
        'message': message,
        'timestamp': int(datetime.now().timestamp())
    })


def emit_error(message: str, stack: str = '') -> None:
    """Emit an error event."""
    emit_event({
        'type': 'error',
        'message': message,
        'stack': stack,
        'timestamp': int(datetime.now().timestamp())
    })


def emit_complete(vulnerabilities: int, time: float, cost: str = '') -> None:
    """Emit a completion event."""
    emit_event({
        'type': 'complete',
        'summary': {
            'vulnerabilities': vulnerabilities,
            'time': time,
            'cost': cost
        },
        'timestamp': int(datetime.now().timestamp())
    })


async def run_scan_cli(config: Dict[str, Any]) -> None:
    """
    Run a security scan with CLI-friendly output.
    
    Args:
        config: Scan configuration with 'target' and optional 'objective'
    """
    target = config.get('target', '')
    objective = config.get('objective', '')
    
    if not target:
        emit_error('Target URL is required')
        return
    
    emit_progress('initialization', f'Starting scan of {target}')
    
    try:
        # Build system prompt with objective if provided
        base_prompt = os.getenv('SYSTEM_PROMPT', '')
        if not base_prompt:
            # Use enhanced Coordinator prompt as default
            from agent_prompts import get_coordinator_system_prompt
            base_prompt = get_coordinator_system_prompt()
            
        if objective:
            custom_prompt = f"{base_prompt}\n\nCUSTOM OBJECTIVE: {objective}"
        else:
            custom_prompt = base_prompt
        
        # Build user prompt
        user_prompt = f"Scan this target: {target}"
        if objective:
            user_prompt += f"\n\nFocus: {objective}"
        
        emit_progress('scanning', 'Agent initialized, starting reconnaissance...')
        
        # Run the scan (reusing existing main.py logic)
        start_time = asyncio.get_event_loop().time()
        
        result = await run_single_target_scan(
            target_url=target,
            system_prompt=custom_prompt,
            base_user_prompt=user_prompt
        )
        
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Emit completion
        emit_complete(
            vulnerabilities=0,  # TODO: Parse from result
            time=elapsed
        )
        
    except Exception as e:
        import traceback
        emit_error(str(e), traceback.format_exc())


def main():
    """Main CLI entry point."""
    try:
        # Read configuration from stdin
        config_line = sys.stdin.readline()
        config = json.loads(config_line)
        
        # Run scan
        asyncio.run(run_scan_cli(config))
        
    except Exception as e:
        import traceback
        emit_error(f'CLI wrapper failed: {e}', traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
