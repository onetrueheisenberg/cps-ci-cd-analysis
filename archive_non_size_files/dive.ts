#!/usr/bin/env ts-node
declare function require(name: string): any;

const childProcess = require("child_process");
const os = require("os");

declare const process: {
  argv: string[];
  exit(code?: number): never;
};

interface DockerHistoryEntry {
  Id: string;
  CreatedBy: string;
  Size: number;
  Comment?: string;
  CreatedAt?: string;
  CreatedSince?: string;
}

interface DockerInspectData {
  Id: string;
  RepoTags?: string[];
  RepoDigests?: string[];
  Created: string;
  Size: number;
  VirtualSize: number;
  Architecture: string;
  Os: string;
  RootFS?: {
    Layers?: string[];
  };
  Config?: {
    User?: string;
    WorkingDir?: string;
    Env?: string[];
    Cmd?: string[];
    Entrypoint?: string[];
    Labels?: Record<string, string>;
  };
}

function run(command: string): string {
  try {
    return childProcess.execSync(command, { stdio: ["ignore", "pipe", "pipe"] }).toString("utf8");
  } catch (error: any) {
    const stderr = error?.stderr?.toString?.("utf8") ?? "";
    throw new Error(`Command failed: ${command}\n${stderr}`.trim());
  }
}

function inspectImage(image: string): DockerInspectData {
  const output = run(`docker image inspect ${image}`);
  const parsed = JSON.parse(output);
  if (!Array.isArray(parsed) || parsed.length === 0) {
    throw new Error(`No inspect data returned for image: ${image}`);
  }
  return parsed[0] as DockerInspectData;
}

function loadHistory(image: string): DockerHistoryEntry[] {
  const output = run(`docker history --no-trunc --format '{{json .}}' ${image}`);
  return output
    .trim()
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line) as DockerHistoryEntry);
}

function isFiniteNumber(value: number): boolean {
  return typeof value === "number" && value !== Infinity && value !== -Infinity && !isNaN(value);
}

function humanBytes(bytes: number): string {
  if (!isFiniteNumber(bytes)) {
    return "0 B";
  }
  const abs = Math.abs(bytes);
  if (abs < 1024) {
    return `${bytes.toFixed(0)} B`;
  }
  const units = ["KB", "MB", "GB", "TB", "PB"];
  let value = abs;
  let unitIndex = -1;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const formatted = `${value.toFixed(value >= 100 ? 0 : value >= 10 ? 1 : 2)} ${units[unitIndex]}`;
  return bytes < 0 ? `-${formatted}` : formatted;
}

function formatList(values?: string[]): string {
  if (!values || values.length === 0) {
    return "<none>";
  }
  return values.join(", ");
}

function deriveEnvSummary(env?: string[]): string[] {
  if (!env) {
    return [];
  }
  return env.slice(0, 10);
}

function objectKeys<T>(record: Record<string, T>): string[] {
  return Object.keys(record);
}

function objectEntries<T>(record: Record<string, T>): Array<[string, T]> {
  const keys = objectKeys(record);
  const result: Array<[string, T]> = [];
  for (let index = 0; index < keys.length; index += 1) {
    const key = keys[index];
    result.push([key, record[key]]);
  }
  return result;
}

function repeatChar(char: string, count: number): string {
  let result = "";
  for (let index = 0; index < count; index += 1) {
    result += char;
  }
  return result;
}

function pad(value: string, width: number): string {
  if (value.length >= width) {
    return value;
  }
  return value + repeatChar(" ", width - value.length);
}

function truncate(value: string, width: number): string {
  if (value.length <= width) {
    return value;
  }
  return value.slice(0, Math.max(0, width - 1)) + "…";
}

function renderHistory(entries: DockerHistoryEntry[], layers: string[] | undefined): string {
  if (entries.length === 0) {
    return "No history entries found.";
  }

  const reversed = entries.slice().reverse();
  const rows: Array<[string, string, string, string]> = [];
  let cumulative = 0;

  for (let index = 0; index < reversed.length; index += 1) {
    const entry = reversed[index];
    const size = Number(entry.Size) || 0;
    cumulative += size;

    const layer = layers?.[index] ?? entry.Id ?? "<unknown>";
    const shortLayer = layer.replace(/^sha256:/, "").slice(0, 12) || "<missing>";

    const command = entry.CreatedBy?.replace(/\s+/g, " ").trim() || "<metadata>";
    const comment = entry.Comment ? ` (${entry.Comment})` : "";

    rows.push([
      pad(`${index + 1}`, 4),
      pad(shortLayer, 14),
      pad(humanBytes(size), 10),
      truncate(`${command}${comment}`, 80),
    ]);
  }

  const header = [pad("#", 4), pad("Layer", 14), pad("Size", 10), "Instruction"].join("  ");
  const separator = repeatChar("-", header.length);
  const body = rows
    .map((cols, idx) => {
      const cumulativeSize = reversed
        .slice(0, idx + 1)
        .reduce((total, item) => total + (Number(item.Size) || 0), 0);
      return `${cols.join("  ")}  (cumulative: ${humanBytes(cumulativeSize)})`;
    })
    .join(os.EOL);

  return [header, separator, body].join(os.EOL);
}

function summarize(image: string): void {
  const inspect = inspectImage(image);
  const history = loadHistory(image);

  const repoTags = formatList(inspect.RepoTags);
  const repoDigests = formatList(inspect.RepoDigests);
  const user = inspect.Config?.User || "root";
  const entrypoint = formatList(inspect.Config?.Entrypoint);
  const cmd = formatList(inspect.Config?.Cmd);
  const envSummary = deriveEnvSummary(inspect.Config?.Env);
  const workingDir = inspect.Config?.WorkingDir || "/";

  const infoLines = [
    `Image:          ${image}`,
    `ID:             ${inspect.Id}`,
    `Created:        ${inspect.Created}`,
    `Architecture:   ${inspect.Architecture}`,
    `OS:             ${inspect.Os}`,
    `Size:           ${humanBytes(inspect.Size)}`,
    `Virtual Size:   ${humanBytes(inspect.VirtualSize)}`,
    `Repo Tags:      ${repoTags}`,
    `Repo Digests:   ${repoDigests}`,
    `User:           ${user}`,
    `Working Dir:    ${workingDir}`,
    `Entrypoint:     ${entrypoint}`,
    `Cmd:            ${cmd}`,
  ];

  if (envSummary.length > 0) {
    infoLines.push("Env (first 10):");
    envSummary.forEach((envVar) => infoLines.push(`  ${envVar}`));
  }

  if (inspect.Config?.Labels && Object.keys(inspect.Config.Labels).length > 0) {
    infoLines.push("Labels:");
    objectEntries(inspect.Config.Labels)
      .slice(0, 10)
      .forEach(([key, value]) => infoLines.push(`  ${key}=${value}`));
    if (objectKeys(inspect.Config.Labels).length > 10) {
      infoLines.push("  …");
    }
  }

  console.log(infoLines.join(os.EOL));
  console.log("");
  console.log("Layers:");
  console.log(
    renderHistory(
      history,
      inspect.RootFS?.Layers ?? []
    )
  );
}

function printUsage(): void {
  console.log("Usage: ts-node dive.ts <image>");
  console.log("Provide a Docker image reference (tag, digest, or ID).");
}

function main(): void {
  const [, , ...args] = process.argv;
  const wantsHelp = args.indexOf("-h") !== -1 || args.indexOf("--help") !== -1;
  if (args.length === 0 || wantsHelp) {
    printUsage();
    process.exit(args.length === 0 ? 1 : 0);
  }

  const image = args[0];
  try {
    summarize(image);
  } catch (error: any) {
    console.error(error?.message ?? String(error));
    process.exit(1);
  }
}

main();
