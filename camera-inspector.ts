import net from "net";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export interface CameraProbeResult {
  reachable: boolean;
  vendor?: string;
  model?: string;
  firmware?: string;
  serial_number?: string;
  mac_address?: string;
  source?: string;
  main?: {
    codec?: string;
    width?: number;
    height?: number;
    fps?: number;
    bitrate?: number;
    gop?: number;
  };
  sub?: {
    codec?: string;
    width?: number;
    height?: number;
    fps?: number;
    bitrate?: number;
    gop?: number;
  };
  profiles?: Array<{
    name?: string;
    codec?: string;
    width?: number;
    height?: number;
    fps?: number;
    bitrate?: number;
    gop?: number;
    source?: string;
  }>;
  transport?: "tcp" | "udp";
  onvif?: boolean;
  sourceLabel?: "onvif" | "rtsp" | "template" | "manual";
  errors?: string[];
}

const VENDOR_TEMPLATES: Record<string, any> = {
  "DS-2CD2386G2-IU": {
    vendor: "Hikvision",
    model: "DS-2CD2386G2-IU (8MP)",
    main: { codec: "H.265", width: 3840, height: 2160, fps: 25, bitrate: 8192, gop: 50 },
    sub: { codec: "H.264", width: 640, height: 360, fps: 15, bitrate: 512, gop: 30 },
  },
  "DS-2CD2143G2-I": {
    vendor: "Hikvision",
    model: "DS-2CD2143G2-I (4MP)",
    main: { codec: "H.265", width: 2560, height: 1440, fps: 25, bitrate: 4096, gop: 50 },
    sub: { codec: "H.264", width: 640, height: 360, fps: 15, bitrate: 512, gop: 30 },
  },
  "IPC3238EA-ADZK": {
    vendor: "UNV",
    model: "IPC3238EA-ADZK (8MP)",
    main: { codec: "H.265", width: 3840, height: 2160, fps: 30, bitrate: 8192, gop: 60 },
    sub: { codec: "H.265", width: 720, height: 576, fps: 15, bitrate: 768, gop: 30 },
  },
  "IPC2122SR3-ADZK": {
    vendor: "UNV",
    model: "IPC2122SR3-ADZK (2MP)",
    main: { codec: "H.265", width: 1920, height: 1080, fps: 25, bitrate: 3072, gop: 50 },
    sub: { codec: "H.264", width: 640, height: 360, fps: 15, bitrate: 512, gop: 30 },
  },
  "IPC-HDW2441T-ZS": {
    vendor: "Dahua",
    model: "IPC-HDW2441T-ZS (4MP)",
    main: { codec: "H.265", width: 2560, height: 1440, fps: 25, bitrate: 4096, gop: 50 },
    sub: { codec: "H.264", width: 640, height: 480, fps: 15, bitrate: 512, gop: 30 },
  },
};

function checkPort(host: string, port: number, timeoutMs = 1500): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    const timer = setTimeout(() => {
      socket.destroy();
      resolve(false);
    }, timeoutMs);
    socket.connect(port, host, () => {
      clearTimeout(timer);
      socket.destroy();
      resolve(true);
    });
    socket.on("error", () => {
      clearTimeout(timer);
      socket.destroy();
      resolve(false);
    });
  });
}

function parseResolution(res?: string): { width?: number; height?: number } {
  if (!res) return {};
  const m = res.match(/(\d+)\s*[x×]\s*(\d+)/);
  if (!m) return {};
  return { width: parseInt(m[1], 10), height: parseInt(m[2], 10) };
}

function matchTemplate(modelName?: string) {
  if (!modelName) return null;
  const lower = modelName.toLowerCase();
  for (const [key, template] of Object.entries(VENDOR_TEMPLATES)) {
    if (lower.includes(key.toLowerCase())) {
      return { ...template, sourceLabel: "template" as const };
    }
  }
  return null;
}

async function probeRtsp(source: string): Promise<Partial<CameraProbeResult>> {
  const probePath = getFfprobePath();
  const args = [
    "-v",
    "error",
    "-select_streams",
    "v:0",
    "-show_entries",
    "stream=codec_name,width,height,r_frame_rate,bit_rate",
    "-of",
    "default=noprint_wrappers=1",
    "-rtsp_transport",
    "tcp",
    "-timeout",
    "15000000",
    "-i",
    source,
  ];
  try {
    const { stdout } = await execAsync(`"${probePath}" ${args.map((a) => `"${a}"`).join(" ")}`, {
      timeout: 10000,
    });
    const info: any = {};
    for (const line of stdout.split(/\r?\n/)) {
      const [key, ...rest] = line.split("=");
      if (key && rest.length) info[key.trim()] = rest.join("=").trim();
    }
    const width = info.width ? parseInt(info.width, 10) : undefined;
    const height = info.height ? parseInt(info.height, 10) : undefined;
    let fps: number | undefined;
    if (info.r_frame_rate) {
      const [n, d] = info.r_frame_rate.split("/").map(Number);
      if (n && d) fps = Math.round(n / d);
    }
    return {
      main: {
        codec: info.codec_name,
        width,
        height,
        fps,
        bitrate: info.bit_rate ? parseInt(info.bit_rate, 10) : undefined,
      },
      transport: "tcp",
      sourceLabel: "rtsp",
    };
  } catch (e: any) {
    return { errors: [e.message || String(e)] };
  }
}

let onvifCam: any = null;
let onvifWarned = false;

function getOnvifCam() {
  if (onvifCam) return onvifCam;
  try {
    const { Cam } = require("onvif");
    onvifCam = Cam;
    return onvifCam;
  } catch (e) {
    if (!onvifWarned) {
      console.warn("ONVIF provider unavailable:", (e as Error).message);
      onvifWarned = true;
    }
    return null;
  }
}

async function onvifProbe(ip: string, port = 80, username?: string, password?: string): Promise<Partial<CameraProbeResult>> {
  const Cam = getOnvifCam();
  if (!Cam) return {};

  const paths = ["/onvif/device_service", "/cgi-bin/onvif.cgi"];
  const errors: string[] = [];

  for (const path of paths) {
    const cam = new Cam({ hostname: ip, username, password, port, path });
    const connected = await Promise.race([
      new Promise<boolean>((resolve) => {
        cam.once("connected", () => resolve(true));
        cam.once("error", () => resolve(false));
        try {
          cam.connect();
        } catch {
          resolve(false);
        }
        setTimeout(() => {
          try { cam.disconnect(); } catch {}
          resolve(false);
        }, 4000);
      }),
    ]);

    if (!connected) continue;

    try {
      const info = await Promise.race([
        new Promise<any>((resolve) => {
          cam.getDeviceInformation((err: any, data: any) => {
            if (err) resolve({});
            else resolve(data || {});
          });
        }),
        new Promise<any>((resolve) => setTimeout(() => resolve({}), 4000)),
      ]);

      const profiles: any[] = await Promise.race([
        new Promise<any>((resolve) => {
          cam.getProfiles((err: any, data: any) => {
            if (err) resolve([]);
            else resolve(Array.isArray(data) ? data : []);
          });
        }),
        new Promise<any>((resolve) => setTimeout(() => resolve([]), 4000)),
      ]);

      const mappedProfiles = profiles.map((p: any) => {
        const cfg = p?.VideoEncoderConfiguration || {};
        const width = cfg?.Resolution?.["Width"] || cfg?.width;
        const height = cfg?.Resolution?.["Height"] || cfg?.height;
        return {
          name: p?.Name,
          codec: cfg?.Encoding,
          width: typeof width === "number" ? width : Number(width),
          height: typeof height === "number" ? height : Number(height),
          fps: cfg?.FrameRateLimit || cfg?.fps,
          bitrate: cfg?.Bitrate || cfg?.bitrate,
          gop: cfg?.GovLength || cfg?.gop,
          source: "onvif",
        };
      }).filter((p: any) => p.width && p.height);

      if (mappedProfiles.length === 0) continue;

      const main = mappedProfiles[0];
      const sub = mappedProfiles[1] || mappedProfiles[0];

      return {
        vendor: info.Manufacturer,
        model: info.Model,
        firmware: info.FirmwareVersion,
        serial_number: info.SerialNumber,
        mac_address: info.MACAddress,
        main: { ...main },
        sub: { ...sub },
        profiles: mappedProfiles,
        onvif: true,
        sourceLabel: "onvif",
      };
    } catch (e) {
      errors.push(`ONVIF ${path}: ${(e as Error).message}`);
      continue;
    }
  }

  return { errors: errors.length ? errors : ["ONVIF not reachable"] };
}

export async function inspectCamera(ip: string, port = 554, username?: string, password?: string): Promise<CameraProbeResult> {
  const result: CameraProbeResult = {
    reachable: false,
    errors: [],
  };

  const portOpen = await checkPort(ip, port, 1500);
  if (!portOpen) {
    result.errors?.push(`Port ${port} closed`);
    return result;
  }
  result.reachable = true;

  const candidates = [
    `rtsp://${username ? encodeURIComponent(username) + ":" + encodeURIComponent(password) + "@" : ""}${ip}:${port}/Streaming/Channels/101?tcp_transport=tcp`,
    `rtsp://${username ? encodeURIComponent(username) + ":" + encodeURIComponent(password) + "@" : ""}${ip}:${port}/stream/101`,
    `rtsp://${username ? encodeURIComponent(username) + ":" + encodeURIComponent(password) + "@" : ""}${ip}:${port}/live.sdp`,
  ];

  const onvifResult = await onvifProbe(ip, 80, username, password);
  const rtspPort = port;

  for (const source of candidates) {
    const probe = await probeRtsp(source);
    if (probe.main?.codec || probe.main?.width) {
      Object.assign(result, probe, { source });
      break;
    }
  }

  if (onvifResult.main || onvifResult.profiles?.length) {
    Object.assign(result, onvifResult);
    if (!result.source && onvifResult.profiles?.length) {
      result.source = `rtsp://${username ? encodeURIComponent(username) + ":" + encodeURIComponent(password) + "@" : ""}${ip}:${rtspPort}/Streaming/Channels/101?tcp_transport=tcp`;
    }
  }

  if (!result.source && !result.profiles?.length) {
    result.errors?.push("No RTSP stream detected");
  }

  return result;
}

export async function autoFillCamera(input: { ip?: string; port?: number; username?: string; password?: string; model?: string }): Promise<CameraProbeResult> {
  const result: CameraProbeResult = { reachable: false, errors: [] };

  const template = matchTemplate(input.model);
  if (template) {
    result.vendor = template.vendor;
    result.model = template.model;
    result.main = template.main;
    result.sub = template.sub;
    result.sourceLabel = "template";
  }

  if (input.ip) {
    const probe = await inspectCamera(input.ip, input.port || 554, input.username, input.password);
    Object.assign(result, probe);
    if (result.main && !template) {
      result.sourceLabel = result.sourceLabel || "rtsp";
    }
  }

  return result;
}

function getFfprobePath(): string {
  const candidates = [
    "ffprobe",
    "./bin/ffprobe.exe",
    "./bin/ffmpeg-master-latest-win64-gpl/bin/ffprobe.exe",
  ];
  for (const p of candidates) {
    try {
      const { execSync } = require("child_process");
      execSync(`"${p}" -version`, { stdio: "ignore", timeout: 2000 });
      return p;
    } catch {
      continue;
    }
  }
  return "ffprobe";
}
