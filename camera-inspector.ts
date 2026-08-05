import net from "net";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export interface StreamProfile {
  id: string;
  name: string;
  type: "main" | "sub" | string;
  codec: string;
  resolutions: Array<{ width: number; height: number; label: string }>;
  fps: { min?: number; max?: number; current?: number };
  bitrate?: number;
  gop?: number;
  source: "onvif" | "rtsp" | "template" | "manual";
  profile_token?: string;
}

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
  profiles?: StreamProfile[];
  onvif_profiles?: any[];
  rtsp_profiles?: any[];
  conflicts?: Array<{ index: number; name?: string; type: string; differences: string[] }>;
  transport?: "tcp" | "udp";
  onvif?: boolean;
  sourceLabel?: "onvif" | "rtsp" | "template" | "manual";
  data_confidence?: "real" | "probed" | "template" | "manual" | "conflict" | "unknown";
  last_verified_at?: string;
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

function buildResolutionLabel(width: number, height: number): string {
  const area = width * height;
  if (area >= 7680 * 4320) return "4320p";
  if (area >= 3840 * 2160) return "4K";
  if (area >= 2560 * 1440) return "4MP";
  if (area >= 2048 * 1536) return "3MP";
  if (area >= 1920 * 1080) return "HD1080";
  if (area >= 1280 * 720) return "HD720";
  if (area >= 640 * 360) return "360p";
  if (width === 352 && height === 288) return "CIF";
  return `${width}x${height}`;
}

function classifyProfileType(index: number, name?: string): "main" | "sub" | string {
  if (!name) return index === 0 ? "main" : "sub";
  const lower = name.toLowerCase();
  if (lower.includes("main") || lower.includes("primary") || lower.includes("profile_1")) return "main";
  if (lower.includes("sub") || lower.includes("secondary") || lower.includes("profile_2")) return "sub";
  return index === 0 ? "main" : "sub";
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
    "-v", "error",
    "-select_streams", "v:0",
    "-show_entries", "stream=codec_name,width,height,r_frame_rate,bit_rate",
    "-of", "default=noprint_wrappers=1",
    "-rtsp_transport", "tcp",
    "-timeout", "15000000",
    "-i", source,
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
    const profile: StreamProfile = {
      id: "rtsp_0",
      name: "RTSP Stream",
      type: "main",
      codec: info.codec_name || "H.264",
      resolutions: width && height ? [{ width, height, label: buildResolutionLabel(width, height) }] : [],
      fps: { current: fps, min: fps, max: fps },
      bitrate: info.bit_rate ? parseInt(info.bit_rate, 10) : undefined,
      source: "rtsp",
    };
    return {
      main: { codec: profile.codec, width, height, fps, bitrate: profile.bitrate },
      profiles: [profile],
      transport: "tcp",
      sourceLabel: "rtsp",
    };
  } catch (e: any) {
    return { errors: [e.message || String(e)] };
  }
}

async function probeRtspChannel(sourceBase: string, pathSuffix: string, username?: string, password?: string): Promise<StreamProfile | null> {
  const source = `${sourceBase}${pathSuffix}?tcp_transport=tcp`;
  const probePath = getFfprobePath();
  const args = [
    "-v", "error",
    "-select_streams", "v:0",
    "-show_entries", "stream=codec_name,width,height,r_frame_rate,bit_rate",
    "-of", "default=noprint_wrappers=1",
    "-rtsp_transport", "tcp",
    "-timeout", "15000000",
    "-i", source,
  ];
  try {
    const { stdout } = await execAsync(`"${probePath}" ${args.map((a) => `"${a}"`).join(" ")}`, {
      timeout: 8000,
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
    if (!width || !height) return null;
    const channelId = pathSuffix.replace(/[^0-9]/g, "") || "0";
    return {
      id: `rtsp_${channelId}`,
      name: channelId === "101" ? "MainStream" : channelId === "102" ? "SubStream" : `Channel ${channelId}`,
      type: channelId === "101" ? "main" : "sub",
      codec: info.codec_name || "H.264",
      resolutions: [{ width, height, label: buildResolutionLabel(width, height) }],
      fps: { current: fps, min: fps, max: fps },
      bitrate: info.bit_rate ? parseInt(info.bit_rate, 10) : undefined,
      source: "rtsp",
    };
  } catch {
    return null;
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

      const mappedProfiles: StreamProfile[] = [];
      for (const p of profiles) {
        const cfg = p?.VideoEncoderConfiguration || {};
        const width = cfg?.Resolution?.["Width"] || cfg?.width;
        const height = cfg?.Resolution?.["Height"] || cfg?.height;
        const w = typeof width === "number" ? width : Number(width);
        const h = typeof height === "number" ? height : Number(height);
        if (!w || !h) continue;
        const codec = cfg?.Encoding || "H.264";
        const fps = cfg?.FrameRateLimit || cfg?.fps;
        const bitrate = cfg?.Bitrate || cfg?.bitrate;
        const gop = cfg?.GovLength || cfg?.gop;
        const profileName = p?.Name || `Profile_${mappedProfiles.length + 1}`;
        mappedProfiles.push({
          id: profileName,
          name: profileName,
          type: classifyProfileType(mappedProfiles.length, profileName),
          codec,
          resolutions: [{ width: w, height: h, label: buildResolutionLabel(w, h) }],
          fps: { current: fps, min: fps, max: fps },
          bitrate,
          gop,
          source: "onvif",
          profile_token: p?.token || p?.Name,
        });
      }

      if (mappedProfiles.length === 0) continue;

      const main = mappedProfiles[0];
      const sub = mappedProfiles[1] || mappedProfiles[0];

      return {
        vendor: info.Manufacturer,
        model: info.Model,
        firmware: info.FirmwareVersion,
        serial_number: info.SerialNumber,
        mac_address: info.MACAddress,
        main: { ...main, codec: main.codec, width: main.resolutions[0]?.width, height: main.resolutions[0]?.height, fps: main.fps.current, bitrate: main.bitrate, gop: main.gop },
        sub: { ...sub, codec: sub.codec, width: sub.resolutions[0]?.width, height: sub.resolutions[0]?.height, fps: sub.fps.current, bitrate: sub.bitrate, gop: sub.gop },
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

function normalizeCodec(codec?: string): string {
  if (!codec) return "unknown";
  const lower = codec.toLowerCase();
  if (lower.includes("h265") || lower.includes("hevc")) return "H.265";
  if (lower.includes("h264") || lower.includes("avc")) return "H.264";
  if (lower.includes("mpeg4") || lower.includes("mp4")) return "MPEG4";
  if (lower.includes("mjpg") || lower.includes("jpeg")) return "MJPEG";
  return codec.toUpperCase();
}

function profileEquals(a: any, b: any): boolean {
  if (!a || !b) return false;
  if (normalizeCodec(a.codec) !== normalizeCodec(b.codec)) return false;
  if ((a.width || 0) !== (b.width || 0)) return false;
  if ((a.height || 0) !== (b.height || 0)) return false;
  if ((a.fps || 0) !== (b.fps || 0)) return false;
  return true;
}

export function compareProbeResults(onvifResult: Partial<CameraProbeResult>, rtspResult: Partial<CameraProbeResult>): Array<{ index: number; name?: string; type: string; differences: string[] }> {
  const conflicts: Array<{ index: number; name?: string; type: string; differences: string[] }> = [];
  const onvifProfiles = onvifResult.profiles || [];
  const rtspProfiles = rtspResult.profiles || [];

  const maxLen = Math.max(onvifProfiles.length, rtspProfiles.length);
  for (let i = 0; i < maxLen; i++) {
    const o = onvifProfiles[i];
    const r = rtspProfiles[i];
    if (o && r) {
      const diffs: string[] = [];
      if (normalizeCodec(o.codec) !== normalizeCodec(r.codec)) diffs.push(`codec: onvif=${o.codec} vs rtsp=${r.codec}`);
      if ((o.resolutions?.[0]?.width || 0) !== (r.resolutions?.[0]?.width || 0)) diffs.push(`width: onvif=${o.resolutions?.[0]?.width} vs rtsp=${r.resolutions?.[0]?.width}`);
      if ((o.resolutions?.[0]?.height || 0) !== (r.resolutions?.[0]?.height || 0)) diffs.push(`height: onvif=${o.resolutions?.[0]?.height} vs rtsp=${r.resolutions?.[0]?.height}`);
      if ((o.fps?.current || 0) !== (r.fps?.current || 0)) diffs.push(`fps: onvif=${o.fps?.current} vs rtsp=${r.fps?.current}`);
      if ((o.bitrate || 0) !== (r.bitrate || 0)) diffs.push(`bitrate: onvif=${o.bitrate} vs rtsp=${r.bitrate}`);
      if ((o.gop || 0) !== (r.gop || 0)) diffs.push(`gop: onvif=${o.gop} vs rtsp=${r.gop}`);
      if (diffs.length) conflicts.push({ index: i, name: o.name, type: "parameter_mismatch", differences: diffs });
    } else if (o && !r) {
      conflicts.push({ index: i, name: o.name, type: "missing_in_rtsp", differences: ["profile exists in ONVIF but not RTSP"] });
    } else if (!o && r) {
      conflicts.push({ index: i, name: r.name, type: "missing_in_onvif", differences: ["profile exists in RTSP but not ONVIF"] });
    }
  }
  return conflicts;
}

export function normalizeProbeProfiles(result: CameraProbeResult): StreamProfile[] {
  const profiles: StreamProfile[] = [];
  const src = result.profiles || [];

  if (src.length > 0) {
    src.forEach((p, i) => {
      const w = p.resolutions?.[0]?.width || 0;
      const h = p.resolutions?.[0]?.height || 0;
      profiles.push({
        id: p.id || `profile_${i}`,
        name: p.name || (i === 0 ? "Main" : "Sub"),
        type: p.type || classifyProfileType(i, p.name),
        codec: p.codec || "H.264",
        resolutions: p.resolutions?.length ? p.resolutions : (w && h ? [{ width: w, height: h, label: buildResolutionLabel(w, h) }] : []),
        fps: p.fps || { current: p.fps?.current || 0, min: p.fps?.min, max: p.fps?.max },
        bitrate: p.bitrate,
        gop: p.gop,
        source: p.source || result.sourceLabel || "manual",
        profile_token: p.profile_token,
      });
    });
  } else {
    if (result.main) {
      const w = result.main.width || 0;
      const h = result.main.height || 0;
      profiles.push({
        id: "profile_0",
        name: "Main",
        type: "main",
        codec: result.main.codec || "H.264",
        resolutions: w && h ? [{ width: w, height: h, label: buildResolutionLabel(w, h) }] : [],
        fps: { current: result.main.fps || 0, min: result.main.fps, max: result.main.fps },
        bitrate: result.main.bitrate,
        gop: result.main.gop,
        source: result.sourceLabel || "manual",
      });
    }
    if (result.sub) {
      const w = result.sub.width || 0;
      const h = result.sub.height || 0;
      profiles.push({
        id: "profile_1",
        name: "Sub",
        type: "sub",
        codec: result.sub.codec || "H.264",
        resolutions: w && h ? [{ width: w, height: h, label: buildResolutionLabel(w, h) }] : [],
        fps: { current: result.sub.fps || 0, min: result.sub.fps, max: result.sub.fps },
        bitrate: result.sub.bitrate,
        gop: result.sub.gop,
        source: result.sourceLabel || "manual",
      });
    }
  }

  return profiles;
}

export function recommendAiStreamProfile(profiles: StreamProfile[]): string | null {
  if (!profiles || profiles.length === 0) return null;

  const isCif = (w: number, h: number) => (w === 352 && h === 288) || (w === 352 && h === 240);

  let candidates = profiles.filter((p) => {
    const res = p.resolutions?.[0];
    if (!res) return false;
    return !isCif(res.width, res.height);
  });

  if (candidates.length === 0) {
    candidates = profiles;
  }

  const mainProfile = candidates.find((p) => p.type === "main");
  const subProfile = candidates.find((p) => p.type === "sub");
  if (mainProfile && subProfile) {
    const mainRes = mainProfile.resolutions?.[0];
    if (mainRes && mainRes.width >= 3840) {
      return subProfile.id;
    }
  }

  let best = candidates[0];
  let bestDist = Infinity;
  for (const p of candidates) {
    const res = p.resolutions?.[0];
    if (!res) continue;
    const dist = Math.abs(res.width - 1920) + Math.abs(res.height - 1080);
    if (dist < bestDist) {
      bestDist = dist;
      best = p;
    }
  }

  const sameDist = candidates.filter((p) => {
    const res = p.resolutions?.[0];
    if (!res) return false;
    const dist = Math.abs(res.width - 1920) + Math.abs(res.height - 1080);
    return dist === bestDist;
  });

  if (sameDist.length > 1) {
    const h264 = sameDist.find((p) => normalizeCodec(p.codec) === "H.264");
    if (h264) return h264.id;
  }

  return best.id;
}

export async function inspectCamera(ip: string, port = 554, username?: string, password?: string): Promise<CameraProbeResult> {
  const result: CameraProbeResult = {
    reachable: false,
    errors: [],
  };

  const portOpen = await checkPort(ip, port, 1500);
  if (!portOpen) {
    result.errors?.push(`Port ${port} closed`);
    result.data_confidence = "unknown";
    result.last_verified_at = new Date().toISOString();
    return result;
  }
  result.reachable = true;

  const sourceBase = `${username ? `${encodeURIComponent(username)}:${encodeURIComponent(password)}@` : ""}${ip}:${port}`;
  const rtspBase = `rtsp://${sourceBase}`;

  const rtspCandidates = [
    "/Streaming/Channels/101",
    "/Streaming/Channels/102",
    "/stream/101",
    "/stream/102",
    "/live.sdp",
  ];

  const onvifResult = await onvifProbe(ip, 80, username, password);
  result.onvif_profiles = onvifResult.profiles || [];

  let rtspProfiles: StreamProfile[] = [];
  for (const path of rtspCandidates) {
    const profile = await probeRtspChannel(rtspBase, path, username, password);
    if (profile) {
      rtspProfiles.push(profile);
      if (!result.source) {
        result.source = `${rtspBase}${path}`;
      }
    }
  }

  if (rtspProfiles.length > 0) {
    result.rtsp_profiles = rtspProfiles;
    result.profiles = rtspProfiles;
    result.transport = "tcp";
    result.sourceLabel = "rtsp";
  }

  if (onvifResult.profiles?.length) {
    Object.assign(result, onvifResult);
    if (!result.source) {
      result.source = `${rtspBase}/Streaming/Channels/101?tcp_transport=tcp`;
    }
    if (!result.sourceLabel || result.sourceLabel === "rtsp") {
      result.sourceLabel = "onvif";
    }
    if (!result.profiles?.length) {
      result.profiles = onvifResult.profiles;
    }
  }

  if (!result.source && !result.profiles?.length) {
    result.errors?.push("No RTSP stream detected");
  }

  if (onvifResult.profiles?.length && rtspProfiles.length) {
    result.conflicts = compareProbeResults(onvifResult, {
      profiles: rtspProfiles,
      sourceLabel: "rtsp",
    } as Partial<CameraProbeResult>);
    if (result.conflicts.length) {
      result.data_confidence = "conflict";
    } else if (onvifResult.vendor && rtspProfiles.length) {
      result.data_confidence = "real";
    } else if (rtspProfiles.length) {
      result.data_confidence = "probed";
    }
  } else if (onvifResult.profiles?.length) {
    result.data_confidence = "probed";
  } else if (rtspProfiles.length) {
    result.data_confidence = "probed";
  } else {
    result.data_confidence = "unknown";
  }

  result.last_verified_at = new Date().toISOString();
  return result;
}

export async function autoFillCamera(input: { ip?: string; port?: number; username?: string; password?: string; model?: string }): Promise<CameraProbeResult> {
  const result: CameraProbeResult = { reachable: false, errors: [] };

  const probePromise = input.ip
    ? inspectCamera(input.ip, input.port || 554, input.username, input.password)
    : Promise.resolve({ reachable: false, profiles: [], sourceLabel: undefined, data_confidence: "unknown" } as Partial<CameraProbeResult>);

  const probe = await probePromise;

  if (probe.profiles?.length) {
    Object.assign(result, probe);
  } else if (probe.main) {
    Object.assign(result, probe);
  } else if (probe.vendor) {
    result.vendor = probe.vendor;
    result.model = probe.model;
    result.firmware = probe.firmware;
    result.serial_number = probe.serial_number;
    result.mac_address = probe.mac_address;
    result.onvif = probe.onvif;
    result.sourceLabel = probe.sourceLabel || "onvif";
    result.data_confidence = probe.data_confidence || "unknown";
  }

  const template = input.model ? matchTemplate(input.model) : null;
  if (template) {
    if (!result.vendor) result.vendor = template.vendor;
    if (!result.model) result.model = template.model;
    if (!result.firmware) result.firmware = template.firmware;
    if (!result.serial_number) result.serial_number = template.serial_number;
    if (!result.mac_address) result.mac_address = template.mac_address;

    if (!result.profiles?.length) {
      const templateProfiles: StreamProfile[] = [
        {
          id: "template_main",
          name: "Main",
          type: "main",
          codec: template.main.codec,
          resolutions: [{ width: template.main.width, height: template.main.height, label: buildResolutionLabel(template.main.width, template.main.height) }],
          fps: { current: template.main.fps, min: template.main.fps, max: template.main.fps },
          bitrate: template.main.bitrate,
          gop: template.main.gop,
          source: "template",
        },
        {
          id: "template_sub",
          name: "Sub",
          type: "sub",
          codec: template.sub.codec,
          resolutions: [{ width: template.sub.width, height: template.sub.height, label: buildResolutionLabel(template.sub.width, template.sub.height) }],
          fps: { current: template.sub.fps, min: template.sub.fps, max: template.sub.fps },
          bitrate: template.sub.bitrate,
          gop: template.sub.gop,
          source: "template",
        },
      ];
      result.profiles = templateProfiles;
      result.main = template.main;
      result.sub = template.sub;
    }

    if (!result.sourceLabel) {
      result.sourceLabel = result.profiles?.some((p) => p.source === "onvif" || p.source === "rtsp") ? result.sourceLabel : "template";
    }

    if (!result.data_confidence || result.data_confidence === "unknown") {
      result.data_confidence = result.profiles?.some((p) => p.source === "onvif" || p.source === "rtsp") ? result.data_confidence : "template";
    }
  }

  if (!result.sourceLabel) {
    result.sourceLabel = result.profiles?.length ? result.profiles[0].source : "manual";
  }

  result.last_verified_at = new Date().toISOString();
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
