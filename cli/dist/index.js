#!/usr/bin/env node

// src/index.tsx
import React5, { useState as useState4 } from "react";
import { render } from "ink";

// src/components/Welcome.tsx
import React from "react";
import { Box, Text } from "ink";
import BigText from "ink-big-text";
import Gradient from "ink-gradient";
var Welcome = ({ version = "1.0.0" }) => {
  return /* @__PURE__ */ React.createElement(Box, { flexDirection: "column", paddingY: 1 }, /* @__PURE__ */ React.createElement(Gradient, { name: "passion" }, /* @__PURE__ */ React.createElement(BigText, { text: "Inferno", font: "block" })), /* @__PURE__ */ React.createElement(Box, { marginTop: 1 }, /* @__PURE__ */ React.createElement(Text, { bold: true, color: "gray" }, "Production-Grade Security Scanner v", version)));
};

// src/components/DockerCheck.tsx
import React2, { useState, useEffect } from "react";
import { Box as Box2, Text as Text2 } from "ink";
import Spinner from "ink-spinner";

// src/utils/docker.ts
import { execa } from "execa";
import { platform } from "os";
async function checkDockerInstalled() {
  try {
    await execa("docker", ["--version"]);
    return true;
  } catch {
    return false;
  }
}
async function checkDockerRunning() {
  try {
    await execa("docker", ["ps"]);
    return true;
  } catch {
    return false;
  }
}
async function checkImageBuilt(imageName = "inferno-sandbox:latest") {
  try {
    const { stdout } = await execa("docker", ["images", "-q", imageName]);
    return stdout.trim().length > 0;
  } catch {
    return false;
  }
}
async function getDockerStatus() {
  const installed = await checkDockerInstalled();
  const running = installed ? await checkDockerRunning() : false;
  const imageBuilt = running ? await checkImageBuilt() : false;
  return { installed, running, imageBuilt };
}
async function installDockerMac() {
  const os = platform();
  if (os === "darwin") {
    try {
      await execa("brew", ["--version"]);
      await execa("brew", ["install", "--cask", "docker"]);
      return;
    } catch {
      throw new Error(
        "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
      );
    }
  } else if (os === "linux") {
    const { stdout: script } = await execa("curl", ["-fsSL", "https://get.docker.com"]);
    await execa("sh", ["-c", script]);
  } else {
    throw new Error(
      "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    );
  }
}
async function startDockerDesktop() {
  const os = platform();
  if (os === "darwin") {
    await execa("open", ["-a", "Docker"]);
  } else {
    throw new Error("Please start Docker manually");
  }
}
async function buildSandboxImage(onProgress) {
  try {
    onProgress?.("Building sandbox image...");
    await execa("docker", [
      "build",
      "-t",
      "inferno-sandbox:latest",
      "/Users/ademkok/Inferno-AI/Inferno"
    ]);
    onProgress?.("Sandbox image built successfully");
  } catch (error) {
    throw new Error(`Failed to build sandbox image: ${error}`);
  }
}
async function ensureDocker(onProgress) {
  const status = await getDockerStatus();
  if (!status.installed) {
    onProgress?.("Installing Docker...");
    await installDockerMac();
    onProgress?.("Docker installed");
    status.installed = true;
  }
  if (!status.running) {
    onProgress?.("Starting Docker...");
    await startDockerDesktop();
    for (let i = 0; i < 30; i++) {
      await new Promise((resolve) => setTimeout(resolve, 1e3));
      if (await checkDockerRunning()) {
        status.running = true;
        break;
      }
    }
    if (!status.running) {
      throw new Error("Docker failed to start within 30 seconds");
    }
    onProgress?.("Docker is running");
  }
  if (!status.imageBuilt) {
    await buildSandboxImage(onProgress);
    status.imageBuilt = true;
  }
  return status;
}

// src/components/DockerCheck.tsx
var DockerCheck = ({ onReady, onError }) => {
  const [status, setStatus] = useState("");
  const [dockerStatus, setDockerStatus] = useState(null);
  useEffect(() => {
    let cancelled = false;
    const checkDocker = async () => {
      try {
        const result = await ensureDocker((message) => {
          if (!cancelled)
            setStatus(message);
        });
        if (!cancelled) {
          setDockerStatus(result);
          setStatus("Docker ready \u2713");
          setTimeout(() => onReady(), 2e3);
        }
      } catch (error) {
        if (!cancelled) {
          onError(error.message || "Docker setup failed");
        }
      }
    };
    checkDocker();
    return () => {
      cancelled = true;
    };
  }, [onReady, onError]);
  return /* @__PURE__ */ React2.createElement(Box2, { flexDirection: "column", paddingY: 1 }, /* @__PURE__ */ React2.createElement(Box2, null, /* @__PURE__ */ React2.createElement(Text2, null, /* @__PURE__ */ React2.createElement(Spinner, { type: "dots" }), " ", status || "Checking Docker...")), dockerStatus && /* @__PURE__ */ React2.createElement(Box2, { flexDirection: "column", marginTop: 1 }, /* @__PURE__ */ React2.createElement(Text2, { color: "green" }, "\u2713 Docker: ", dockerStatus.installed ? "Installed" : "Installing..."), dockerStatus.running && /* @__PURE__ */ React2.createElement(Text2, { color: "green" }, "\u2713 Docker: Running"), dockerStatus.imageBuilt && /* @__PURE__ */ React2.createElement(Text2, { color: "green" }, "\u2713 Sandbox: Ready")));
};

// src/components/TargetInput.tsx
import React3, { useState as useState2 } from "react";
import { Box as Box3, Text as Text3 } from "ink";
import TextInput from "ink-text-input";
var TargetInput = ({ onSubmit }) => {
  const [step, setStep] = useState2("target");
  const [target, setTarget] = useState2("");
  const [objective, setObjective] = useState2("");
  const handleTargetSubmit = (value) => {
    console.error(`[DEBUG] Target submitted: "${value}"`);
    setTarget(value);
    setStep("objective");
  };
  const handleObjectiveSubmit = (value) => {
    console.error(`[DEBUG] Objective submitted: "${value}"`);
    setObjective(value);
    onSubmit({
      target,
      objective: value || void 0
    });
  };
  return /* @__PURE__ */ React3.createElement(Box3, { flexDirection: "column", paddingY: 1 }, /* @__PURE__ */ React3.createElement(Box3, { marginBottom: 1 }, /* @__PURE__ */ React3.createElement(Text3, { bold: true, color: "cyan" }, "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501")), /* @__PURE__ */ React3.createElement(Box3, { marginBottom: 1 }, /* @__PURE__ */ React3.createElement(Text3, { bold: true }, "\u{1F4CB} Scan Configuration")), step === "target" ? /* @__PURE__ */ React3.createElement(Box3, null, /* @__PURE__ */ React3.createElement(Text3, { color: "gray" }, "? "), /* @__PURE__ */ React3.createElement(Text3, { bold: true }, "Target URL: "), /* @__PURE__ */ React3.createElement(
    TextInput,
    {
      value: target,
      onChange: setTarget,
      onSubmit: handleTargetSubmit,
      placeholder: "example.com"
    }
  )) : /* @__PURE__ */ React3.createElement(React3.Fragment, null, /* @__PURE__ */ React3.createElement(Box3, { marginBottom: 1 }, /* @__PURE__ */ React3.createElement(Text3, { color: "green" }, "\u2713 Target: ", target)), /* @__PURE__ */ React3.createElement(Box3, null, /* @__PURE__ */ React3.createElement(Text3, { color: "gray" }, "? "), /* @__PURE__ */ React3.createElement(Text3, { bold: true }, "Custom objective (optional): "), /* @__PURE__ */ React3.createElement(
    TextInput,
    {
      value: objective,
      onChange: setObjective,
      onSubmit: handleObjectiveSubmit,
      placeholder: "Focus on OWASP Top 10"
    }
  )), /* @__PURE__ */ React3.createElement(Box3, { marginTop: 1 }, /* @__PURE__ */ React3.createElement(Text3, { dimColor: true }, "Press Enter to skip"))));
};

// src/components/ScanDisplay.tsx
import React4, { useState as useState3, useEffect as useEffect2, useRef } from "react";
import { Box as Box4, Text as Text4 } from "ink";
import Spinner2 from "ink-spinner";

// src/utils/bridge.ts
import { execa as execa2 } from "execa";
var PythonBridge = class {
  process = null;
  async startScan(config, onEvent) {
    try {
      this.process = execa2(
        "python3",
        ["/Users/ademkok/Inferno-AI/Inferno/inferno_cli.py"],
        {
          cwd: "/Users/ademkok/Inferno-AI/Inferno",
          env: {
            ...process.env,
            PYTHONUNBUFFERED: "1"
            // Disable Python output buffering
          }
        }
      );
      this.process.stdin?.write(JSON.stringify(config) + "\n");
      if (this.process.stdout) {
        const readline = await import("readline");
        const rl = readline.createInterface({
          input: this.process.stdout,
          crlfDelay: Infinity
        });
        for await (const line of rl) {
          try {
            if (!line.trim())
              continue;
            const event = JSON.parse(line);
            onEvent(event);
          } catch (e) {
          }
        }
      }
      await this.process;
    } catch (error) {
      onEvent({
        type: "error",
        message: error.message || "Scan failed",
        stack: error.stack
      });
    }
  }
  stop() {
    if (this.process) {
      this.process.kill("SIGTERM");
      this.process = null;
    }
  }
};

// src/components/ScanDisplay.tsx
var ScanDisplay = ({ config, onComplete }) => {
  const [events, setEvents] = useState3([]);
  const [isComplete, setIsComplete] = useState3(false);
  const logsRef = useRef(/* @__PURE__ */ new Set());
  useEffect2(() => {
    const bridge = new PythonBridge();
    bridge.startScan(config, (event) => {
      const key = `${event.type}-${event.timestamp}-${event.message}`;
      if (!logsRef.current.has(key)) {
        logsRef.current.add(key);
        setEvents((prev) => [...prev, event]);
      }
      if (event.type === "complete" || event.type === "error") {
        setIsComplete(true);
        if (event.type === "complete") {
          setTimeout(() => onComplete(), 3e3);
        }
      }
    });
    return () => {
      bridge.stop();
    };
  }, [config, onComplete]);
  const logEvents = events.filter(
    (e) => e.type === "progress" || e.type === "vulnerability" || e.type === "error" || e.type === "agent_action"
  );
  const displayEvents = logEvents.slice(-15);
  return /* @__PURE__ */ React4.createElement(Box4, { flexDirection: "column", paddingY: 1 }, /* @__PURE__ */ React4.createElement(Box4, { marginBottom: 1 }, /* @__PURE__ */ React4.createElement(Text4, { bold: true, color: "cyan" }, "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501")), /* @__PURE__ */ React4.createElement(Box4, { marginBottom: 1 }, /* @__PURE__ */ React4.createElement(Text4, { bold: true }, "\u{1F50D} Target: ", /* @__PURE__ */ React4.createElement(Text4, { color: "green" }, config.target))), /* @__PURE__ */ React4.createElement(Box4, { flexDirection: "column", borderStyle: "round", borderColor: "gray", paddingX: 1 }, displayEvents.map((e, i) => /* @__PURE__ */ React4.createElement(LogEntry, { key: i, event: e })), !isComplete && /* @__PURE__ */ React4.createElement(Box4, { marginTop: 1 }, /* @__PURE__ */ React4.createElement(Text4, { color: "yellow" }, /* @__PURE__ */ React4.createElement(Spinner2, { type: "dots" }), " ", /* @__PURE__ */ React4.createElement(Text4, { dimColor: true }, "Processing...")))), isComplete && /* @__PURE__ */ React4.createElement(Box4, { marginTop: 1 }, /* @__PURE__ */ React4.createElement(Text4, { bold: true, color: "green" }, "\u2713 Scan Complete")));
};
var LogEntry = ({ event }) => {
  const time = new Date(event.timestamp * 1e3).toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
  if (event.type === "progress") {
    let level = "INFO    ";
    let color = "blue";
    let message = event.message;
    if (event.step === "reasoning") {
      level = "THINK   ";
      color = "magenta";
    } else if (message.startsWith("Executing:")) {
      level = "TOOL    ";
      color = "yellow";
    } else if (message.startsWith("Running:")) {
      level = "CMD     ";
      color = "cyan";
    } else if (message.startsWith("Agent says:")) {
      level = "AGENT   ";
      color = "green";
    }
    return /* @__PURE__ */ React4.createElement(Box4, { flexDirection: "column" }, /* @__PURE__ */ React4.createElement(Box4, null, /* @__PURE__ */ React4.createElement(Text4, { color: "gray" }, "[", time, "] "), /* @__PURE__ */ React4.createElement(Text4, { color, bold: true }, level, " "), /* @__PURE__ */ React4.createElement(Text4, { color: "white" }, message)), event.step === "reasoning" && event.full_reasoning && /* @__PURE__ */ React4.createElement(Box4, { marginLeft: 13, borderStyle: "single", borderColor: "gray", paddingX: 1 }, /* @__PURE__ */ React4.createElement(Text4, { color: "gray", italic: true }, event.full_reasoning)));
  }
  if (event.type === "vulnerability") {
    return /* @__PURE__ */ React4.createElement(Box4, { flexDirection: "column" }, /* @__PURE__ */ React4.createElement(Box4, null, /* @__PURE__ */ React4.createElement(Text4, { color: "gray" }, "[", time, "] "), /* @__PURE__ */ React4.createElement(Text4, { color: "red", bold: true }, "VULN    "), /* @__PURE__ */ React4.createElement(Text4, { color: getSeverityColor(event.severity) }, event.severity, ": ", event.title)), /* @__PURE__ */ React4.createElement(Box4, { marginLeft: 13 }, /* @__PURE__ */ React4.createElement(Text4, { color: "gray" }, "\u2514\u2500 ", event.endpoint)));
  }
  if (event.type === "error") {
    return /* @__PURE__ */ React4.createElement(Box4, null, /* @__PURE__ */ React4.createElement(Text4, { color: "gray" }, "[", time, "] "), /* @__PURE__ */ React4.createElement(Text4, { color: "red", bold: true }, "ERROR   "), /* @__PURE__ */ React4.createElement(Text4, { color: "red" }, event.message));
  }
  return null;
};
function getSeverityColor(severity) {
  switch (severity) {
    case "CRITICAL":
      return "redBright";
    case "HIGH":
      return "red";
    case "MEDIUM":
      return "yellow";
    case "LOW":
      return "blue";
    default:
      return "white";
  }
}

// src/index.tsx
import { Box as Box5, Text as Text5 } from "ink";
var App = () => {
  const [screen, setScreen] = useState4("docker-check");
  const [scanConfig, setScanConfig] = useState4(null);
  const [error, setError] = useState4(null);
  React5.useEffect(() => {
    console.error(`[DEBUG] Screen changed to: ${screen}`);
  }, [screen]);
  if (error) {
    console.error(`[ERROR] ${error}`);
    return /* @__PURE__ */ React5.createElement(React5.Fragment, null, /* @__PURE__ */ React5.createElement(Welcome, null), /* @__PURE__ */ React5.createElement(Box5, { flexDirection: "column", paddingY: 1 }, /* @__PURE__ */ React5.createElement(Text5, { color: "red", bold: true }, "\u274C Error: ", error), /* @__PURE__ */ React5.createElement(Text5, { dimColor: true }, "Please resolve the issue and try again.")));
  }
  switch (screen) {
    case "welcome":
      return /* @__PURE__ */ React5.createElement(Welcome, null);
    case "docker-check":
      return /* @__PURE__ */ React5.createElement(React5.Fragment, null, /* @__PURE__ */ React5.createElement(Welcome, null), /* @__PURE__ */ React5.createElement(
        DockerCheck,
        {
          onReady: () => setScreen("input"),
          onError: setError
        }
      ));
    case "input":
      return /* @__PURE__ */ React5.createElement(React5.Fragment, null, /* @__PURE__ */ React5.createElement(Welcome, null), /* @__PURE__ */ React5.createElement(
        TargetInput,
        {
          onSubmit: (config) => {
            setScanConfig(config);
            setScreen("scanning");
          }
        }
      ));
    case "scanning":
      return /* @__PURE__ */ React5.createElement(React5.Fragment, null, /* @__PURE__ */ React5.createElement(Welcome, null), scanConfig && /* @__PURE__ */ React5.createElement(
        ScanDisplay,
        {
          config: scanConfig,
          onComplete: () => setScreen("complete")
        }
      ));
    case "complete":
      return /* @__PURE__ */ React5.createElement(React5.Fragment, null, /* @__PURE__ */ React5.createElement(Welcome, null), /* @__PURE__ */ React5.createElement(Box5, { paddingY: 1 }, /* @__PURE__ */ React5.createElement(Text5, null, "Scan complete! Check ctf-logs/ for detailed results.")));
    default:
      return /* @__PURE__ */ React5.createElement(Welcome, null);
  }
};
render(/* @__PURE__ */ React5.createElement(App, null));
