"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import HistoryPanel, {
  type HistoryRecord,
  saveHistoryRecord,
} from "./HistoryPanel";
import ImageUploader from "./ImageUploader";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const POLL_INTERVAL_MS = 2500;

type AdvancedResult = {
  variant_id: string;
  title: string;
  prompt_used: string;
  negative_prompt_used: string;
  image_url: string;
  error: string | null;
  status?: "pending" | "done" | "error";
};

type AdviceBlocks = {
  person?: string;
  garment?: string;
  styling?: string;
  quality?: string;
};

type StyleDNA = {
  style_keywords?: string[];
  color_palette?: string[];
  occasions?: string[];
  vibe?: string;
  avoid_scenes?: string[];
  pose_suggestions?: string[];
};

type ModeOption = {
  id: "basic" | "lookbook" | "pose" | "multi";
  label: string;
  desc: string;
  href: string;
};

const MODE_OPTIONS: ModeOption[] = [
  { id: "basic", label: "标准试衣", desc: "单张稳定换衣", href: "/basic" },
  { id: "lookbook", label: "Lookbook", desc: "多场景风格展示", href: "/lookbook" },
  { id: "pose", label: "Pose Lab", desc: "根据服装推荐动作", href: "/pose" },
  { id: "multi", label: "Multi-Fit", desc: "多物件同时上身", href: "/multi" },
];

function useTypewriter(text: string, speed = 18) {
  const [value, setValue] = useState("");

  useEffect(() => {
    setValue("");
    if (!text) {
      return;
    }
    let idx = 0;
    const timer = window.setInterval(() => {
      idx += 1;
      setValue(text.slice(0, idx));
      if (idx >= text.length) {
        window.clearInterval(timer);
      }
    }, speed);
    return () => window.clearInterval(timer);
  }, [text, speed]);

  return value;
}

/**
 * 将图片 URL fetch 后，用 Canvas 压缩为 base64 data URL。
 * 历史记录用此方式持久化图片，避免服务端文件过期后 404。
 */
async function compressImageUrl(url: string, maxWidth = 600, quality = 0.75): Promise<string> {
  if (!url) return "";
  try {
    const res = await fetch(url);
    if (!res.ok) return "";
    const blob = await res.blob();
    return await new Promise<string>((resolve) => {
      const img = new Image();
      const objUrl = URL.createObjectURL(blob);
      img.onload = () => {
        const scale = Math.min(1, maxWidth / img.width);
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);
        canvas.getContext("2d")!.drawImage(img, 0, 0, canvas.width, canvas.height);
        URL.revokeObjectURL(objUrl);
        resolve(canvas.toDataURL("image/jpeg", quality));
      };
      img.onerror = () => { URL.revokeObjectURL(objUrl); resolve(""); };
      img.src = objUrl;
    });
  } catch {
    return "";
  }
}

function mapResults(rawResults: any[]): AdvancedResult[] {
  return rawResults.map((item) => {
    const rawUrl = item.image_url ?? "";
    const finalUrl = rawUrl
      ? rawUrl.startsWith("http") || rawUrl.startsWith("data:")
        ? rawUrl
        : `${API_BASE}${rawUrl}`
      : "";
    return {
      variant_id: item.variant_id ?? "",
      title: item.title ?? "",
      prompt_used: item.prompt_used ?? "",
      negative_prompt_used: item.negative_prompt_used ?? "",
      image_url: finalUrl,
      error: item.error ?? null,
      status: item.status ?? (finalUrl ? "done" : "pending"),
    };
  });
}

export default function ModePage({
  defaultMode,
}: {
  defaultMode: ModeOption["id"];
}) {
  const [personFile, setPersonFile] = useState<File | null>(null);
  const [garmentFile, setGarmentFile] = useState<File | null>(null);
  const [advice, setAdvice] = useState<AdviceBlocks | string | null>(null);
  const [tryonUrl, setTryonUrl] = useState<string | null>(null);
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [results, setResults] = useState<AdvancedResult[]>([]);
  const [variantCount, setVariantCount] = useState(4);
  const [userPrompt, setUserPrompt] = useState("");
  const [showPlan, setShowPlan] = useState(false);
  const [activeResult, setActiveResult] = useState<AdvancedResult | null>(null);
  const [meta, setMeta] = useState<{
    qwen_ms?: number;
    nano_ms?: number;
    device?: string;
  } | null>(null);
  const [totalMs, setTotalMs] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [restoredRecord, setRestoredRecord] = useState<HistoryRecord | null>(null);

  const pollTimerRef = useRef<number | null>(null);
  const jobStartRef = useRef<number | null>(null);

  const useAdvanced = defaultMode !== "basic";
  const mode = defaultMode === "basic" ? "lookbook" : defaultMode;

  const basicAdviceText = typeof advice === "string" ? advice : "";
  const typedAdvice = useTypewriter(basicAdviceText, 16);
  const canSubmit = useMemo(
    () => Boolean(personFile && garmentFile) && !loading,
    [personFile, garmentFile, loading]
  );

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, []);

  // 历史记录恢复：将存档的 results/advice 还原到当前 UI
  useEffect(() => {
    if (!restoredRecord) return;
    if (restoredRecord.results && Array.isArray(restoredRecord.results)) {
      setResults(mapResults(restoredRecord.results as any[]));
    }
    if (restoredRecord.advice !== undefined && restoredRecord.advice !== null) {
      setAdvice(restoredRecord.advice as AdviceBlocks | string);
    }
    setActiveResult(null);
    setShowHistory(false);
  }, [restoredRecord]);

  useEffect(() => {
    if (!jobId) {
      return;
    }
    let cancelled = false;

    const pollJob = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/api/process-advanced/jobs/${jobId}`
        );
        if (!response.ok) {
          throw new Error("Job status fetch failed");
        }
        const data = await response.json();
        if (cancelled) {
          return;
        }
        setAdvice(data.advice ?? "");
        setPlan(data.plan ?? null);
        setResults(mapResults(data.results ?? []));
        setMeta(data.meta ?? null);
        if (data.status === "completed" || data.status === "error") {
          if (pollTimerRef.current) {
            window.clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
          setLoading(false);
          if (jobStartRef.current !== null) {
            setTotalMs(Math.round(performance.now() - jobStartRef.current));
          }
          if (data.status === "error") {
            setError(data.error ?? "任务失败");
          }
          // 保存历史记录（将图片压缩为 base64，避免服务端文件过期后 404）
          if (data.status === "completed") {
            const rawResults: any[] = data.results ?? [];
            const adviceObj = data.advice;
            const adviceSummary =
              adviceObj && typeof adviceObj === "object"
                ? (adviceObj as Record<string, string>).person ?? ""
                : String(adviceObj ?? "");

            // 并行压缩所有图片，不阻塞当前 UI
            Promise.all(
              rawResults.map(async (r: any) => {
                const rawUrl = r.image_url ?? "";
                const fullUrl = rawUrl
                  ? rawUrl.startsWith("http") ? rawUrl : `${API_BASE}${rawUrl}`
                  : "";
                const dataUrl = await compressImageUrl(fullUrl, 600, 0.75);
                return { ...r, image_url: dataUrl };
              })
            ).then((persistedResults) => {
              const firstDataUrl = persistedResults[0]?.image_url ?? "";
              saveHistoryRecord({
                timestamp: Date.now(),
                mode: data.meta?.mode ?? defaultMode,
                garmentThumb: firstDataUrl,
                firstImageUrl: firstDataUrl,
                adviceSummary,
                results: persistedResults,
                advice: data.advice ?? null,
              });
            }).catch(() => {
              // 图片压缩失败时静默跳过，不影响主流程
            });
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "轮询失败");
          setLoading(false);
        }
      }
    };

    pollJob();
    pollTimerRef.current = window.setInterval(pollJob, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      if (pollTimerRef.current) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [jobId]);

  const handleSubmit = async () => {
    if (!personFile || !garmentFile || loading) {
      return;
    }
    setError(null);
    setAdvice(null);
    setTryonUrl(null);
    setPlan(null);
    setResults([]);
    setMeta(null);
    setTotalMs(null);
    setActiveResult(null);
    setJobId(null);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("person_image", personFile);
      formData.append("garment_image", garmentFile);
      if (useAdvanced) {
        formData.append("k_variants", String(variantCount));
        formData.append("mode", mode);
        if (userPrompt.trim()) {
          formData.append("user_prompt", userPrompt.trim());
        }
      }

      const startTime = performance.now();
      if (useAdvanced) {
        jobStartRef.current = startTime;
        const response = await fetch(`${API_BASE}/api/process-advanced-async`, {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          throw new Error("API request failed");
        }
        const data = await response.json();
        if (!data.job_id) {
          throw new Error("Missing job id");
        }
        setJobId(data.job_id ?? null);
        setAdvice(data.advice ?? "");
        setPlan(data.plan ?? null);
        setMeta(data.meta ?? null);
        setResults(mapResults(data.results ?? []));
        return;
      }

      const response = await fetch(`${API_BASE}/api/process`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error("API request failed");
      }
      const data = await response.json();
      const endTime = performance.now();
      setMeta(data.meta ?? null);
      setTotalMs(Math.round(endTime - startTime));
      setAdvice(data.advice ?? "");

      if (data.tryon_image_data_url) {
        setTryonUrl(data.tryon_image_data_url);
      } else if (data.tryon_image_url) {
        const url = data.tryon_image_url as string;
        setTryonUrl(url.startsWith("http") ? url : `${API_BASE}${url}`);
      } else {
        setTryonUrl(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误");
      setLoading(false);
    } finally {
      if (!useAdvanced) {
        setLoading(false);
      }
    }
  };

  const renderInsight = () => {
    const styleDNA = plan?.style_dna as StyleDNA | undefined;
    const adviceBlocks = advice && typeof advice === "object" ? advice as AdviceBlocks : null;

    // Basic 模式：纯文字打字机展示
    if (!useAdvanced || typeof advice === "string") {
      return (
        <>
          <p className="typewriter mt-4 min-h-[100px] font-mono text-base text-[var(--acid-green)]">
            {typedAdvice}
          </p>
          {showPlan && plan && (
            <pre className="mt-4 max-h-[320px] overflow-auto whitespace-pre-wrap text-xs text-white/70">
              {JSON.stringify(plan, null, 2)}
            </pre>
          )}
        </>
      );
    }

    // Advanced 模式：结构化分块卡片
    const ADVICE_LABELS: Record<string, string> = {
      person: "👤 人物特征",
      garment: "👕 衣物分析",
      styling: "✨ 搭配建议",
      quality: "📸 品质约束",
    };

    return (
      <div className="mt-4 flex flex-col gap-4">
        {/* 风格DNA专属卡片 */}
        {styleDNA && styleDNA.vibe && (
          <div className="rounded-2xl border border-[var(--neon-cyan)]/30 bg-[var(--neon-cyan)]/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
              🧬 风格 DNA
            </p>
            <p className="mt-2 text-sm text-white/90">{styleDNA.vibe}</p>
            {styleDNA.style_keywords && styleDNA.style_keywords.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {styleDNA.style_keywords.map((kw) => (
                  <span
                    key={kw}
                    className="rounded-full border border-[var(--neon-cyan)]/40 px-2 py-0.5 text-[11px] text-[var(--neon-cyan)]/80"
                  >
                    #{kw}
                  </span>
                ))}
              </div>
            )}
            {styleDNA.occasions && styleDNA.occasions.length > 0 && (
              <p className="mt-2 text-[11px] text-white/50">
                适合：{styleDNA.occasions.join(" / ")}
              </p>
            )}
          </div>
        )}

        {/* 动态 advice 块 */}
        {adviceBlocks && (
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(adviceBlocks).map(([key, value]) => {
              if (!value) return null;
              return (
                <div
                  key={key}
                  className="rounded-2xl border border-white/10 bg-white/5 p-4"
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-[var(--acid-green)]">
                    {ADVICE_LABELS[key] ?? key}
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-white/80">{value}</p>
                </div>
              );
            })}
          </div>
        )}

        {showPlan && plan && (
          <pre className="mt-2 max-h-[320px] overflow-auto whitespace-pre-wrap text-xs text-white/70">
            {JSON.stringify(plan, null, 2)}
          </pre>
        )}
      </div>
    );
  };

  const renderResults = () => {
    if (useAdvanced) {
      if (!results.length) {
        const placeholders = Array.from({ length: variantCount }, (_, idx) => idx);
        return (
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            {placeholders.map((idx) => (
              <div
                key={`loading-${idx}`}
                className="holo-border neon-frame flex h-72 items-center justify-center rounded-3xl bg-black/40 p-4"
              >
                <div className="flex flex-col items-center gap-3 text-white/60">
                  <span className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-[var(--acid-green)]" />
                  <span className="text-xs">生成中...</span>
                </div>
              </div>
            ))}
          </div>
        );
      }
      return (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {results.map((item) => {
            const hasImage = Boolean(item.image_url);
            return (
              <div key={item.variant_id} className="relative group">
                {/* 删除按钮 */}
                <button
                  type="button"
                  onClick={() =>
                    setResults((prev) => prev.filter((r) => r.variant_id !== item.variant_id))
                  }
                  className="absolute right-2 top-2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-black/70 text-white/50 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-red-500/80 hover:text-white"
                  title="删除此卡片"
                >
                  ✕
                </button>
                <button
                  type="button"
                  disabled={!hasImage}
                  onClick={() => hasImage && setActiveResult(item)}
                  className={[
                    "holo-border neon-frame w-full text-left overflow-hidden rounded-3xl bg-black/40 p-4 transition-transform duration-300",
                    hasImage ? "hover:-translate-y-1" : "cursor-not-allowed opacity-80",
                  ].join(" ")}
                >
                  {hasImage ? (
                    <img
                      src={item.image_url}
                      alt={item.title}
                      className="h-60 w-full rounded-2xl object-contain md:h-72"
                    />
                  ) : (
                    <div className="flex h-60 items-center justify-center rounded-2xl border border-white/10 md:h-72">
                      <div className="flex flex-col items-center gap-3 text-white/60">
                        <span className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-[var(--acid-green)]" />
                        <span className="text-xs">生成中...</span>
                      </div>
                    </div>
                  )}
                  <div className="mt-4">
                    <p className="text-sm font-semibold text-white">{item.title}</p>
                    {item.error && (
                      <p className="mt-1 text-xs text-red-400">{item.error}</p>
                    )}
                    <p className="mt-2 max-h-12 overflow-hidden text-[11px] text-white/50">
                      {item.prompt_used}
                    </p>
                    <span className="mt-3 inline-flex rounded-full border border-white/20 px-3 py-1 text-[11px] text-white/60">
                      点击查看详情
                    </span>
                  </div>
                </button>
              </div>
            );
          })}
        </div>
      );
    }
    return (
      <div className="flex items-center justify-center">
        {tryonUrl ? (
          <button
            type="button"
            onClick={() =>
              setActiveResult({
                variant_id: "v1",
                title: "Try-on",
                prompt_used: "",
                negative_prompt_used: "",
                image_url: tryonUrl,
                error: null,
              })
            }
          >
            <img
              src={tryonUrl}
              alt="Try-on result"
              className="h-[520px] w-full rounded-2xl object-contain md:h-[640px]"
            />
          </button>
        ) : (
          <div className="flex h-[520px] items-center justify-center text-white/50 md:h-[640px]">
            <div className="flex flex-col items-center gap-4">
              <span className="h-12 w-12 animate-spin rounded-full border-2 border-white/20 border-t-[var(--acid-green)]" />
              <span className="text-sm">试衣图生成中...</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-black px-6 py-16 text-white">
      <div className="pointer-events-none absolute inset-0">
        <motion.div
          className="absolute left-[-10%] top-[-15%] h-72 w-72 rounded-full bg-neonPurple/30 blur-[120px]"
          animate={{ x: [0, 40, 0], y: [0, 30, -10] }}
          transition={{ duration: 12, repeat: Infinity, repeatType: "mirror" }}
        />
        <motion.div
          className="absolute right-[-5%] top-[10%] h-80 w-80 rounded-full bg-[var(--neon-cyan)]/30 blur-[140px]"
          animate={{ x: [0, -30, 10], y: [0, -20, 20] }}
          transition={{ duration: 10, repeat: Infinity, repeatType: "mirror" }}
        />
        <motion.div
          className="absolute bottom-[-10%] left-[20%] h-96 w-96 rounded-full bg-[var(--acid-green)]/20 blur-[150px]"
          animate={{ x: [0, 20, -15], y: [0, 10, -25] }}
          transition={{ duration: 14, repeat: Infinity, repeatType: "mirror" }}
        />
      </div>

      <div className="relative mx-auto flex max-w-6xl flex-col gap-12">
        <header className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-white/60">
            StreetShow
          </p>
          <h1 className="text-4xl font-semibold md:text-5xl">
            IGNITE YOUR FUTURE FIT
          </h1>
          <p className="max-w-3xl text-base text-white/70">
            上传人物图与衣物图，生成时尚建议与试衣效果图。
          </p>
        </header>

        <div className="grid gap-8 xl:grid-cols-[280px_1fr]">
          <aside className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Modes</p>
            <div className="mt-4 space-y-3">
              {MODE_OPTIONS.map((option) => (
                <Link
                  key={option.id}
                  href={option.href}
                  className={[
                    "block w-full rounded-2xl border px-4 py-3 text-left transition",
                    defaultMode === option.id
                      ? "border-[var(--acid-green)] bg-white/10"
                      : "border-white/10 bg-black/40 hover:border-white/30",
                  ].join(" ")}
                >
                  <p className="text-sm font-semibold text-white">{option.label}</p>
                  <p className="mt-1 text-xs text-white/60">{option.desc}</p>
                </Link>
              ))}
            </div>

            {useAdvanced && (
              <div className="mt-6 space-y-4 text-xs text-white/70">
                <label className="flex items-center justify-between gap-2">
                  Variants
                  <input
                    type="number"
                    min={1}
                    max={8}
                    value={variantCount}
                    onChange={(event) =>
                      setVariantCount(Number(event.target.value || 1))
                    }
                    className="w-16 rounded-md border border-white/20 bg-black/60 px-2 py-1 text-white"
                  />
                </label>
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-white/40">
                    用户偏好
                  </p>
                  <textarea
                    value={userPrompt}
                    onChange={(event) => setUserPrompt(event.target.value)}
                    placeholder="更街头 / 更高级 / 夜景霓虹..."
                    rows={3}
                    className="w-full rounded-md border border-white/20 bg-black/60 px-3 py-2 text-white placeholder:text-white/40"
                  />
                </div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={showPlan}
                    onChange={(event) => setShowPlan(event.target.checked)}
                  />
                  显示计划 JSON
                </label>
              </div>
            )}

            {/* 历史记录按钮 */}
            <button
              type="button"
              onClick={() => setShowHistory(true)}
              className="mt-4 w-full rounded-2xl border border-white/10 bg-black/40 px-4 py-2.5 text-left text-xs text-white/60 transition hover:border-white/30 hover:text-white/80"
            >
              <span className="flex items-center gap-2">
                <span>🕒</span>
                <span>历史记录</span>
              </span>
            </button>
          </aside>

          <div className="flex flex-col gap-10">
            <section className="grid gap-6 md:grid-cols-2">
              <ImageUploader
                label="Subject (你)"
                hint="上传人物图"
                onFile={setPersonFile}
              />
              <ImageUploader
                label="Garment (衣物)"
                hint="上传衣物图"
                onFile={setGarmentFile}
              />
            </section>

            <section className="flex flex-wrap items-center gap-4">
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!canSubmit}
                className={[
                  "relative overflow-hidden rounded-full border border-white/30 px-10 py-4 text-lg font-semibold tracking-[0.2em]",
                  "transition-all duration-300",
                  canSubmit
                    ? "glow-button bg-white/10 hover:bg-white/20"
                    : "cursor-not-allowed bg-white/5 text-white/40",
                ].join(" ")}
              >
                <span className="relative z-10">
                  {loading ? "IGNITING..." : "IGNITE STYLE"}
                </span>
                {loading && (
                  <span className="loading-bar absolute inset-0" aria-hidden="true" />
                )}
              </button>
              {error && (
                <div className="flex items-center gap-3 rounded-full border border-red-400/40 bg-red-500/10 px-4 py-2 text-xs text-red-200">
                  <span>{error}</span>
                  <button
                    type="button"
                    onClick={() => setError(null)}
                    className="rounded-full border border-red-400/40 px-2 py-1 text-[11px]"
                  >
                    取消
                  </button>
                </div>
              )}
            </section>

            <AnimatePresence>
              {(advice !== null || tryonUrl || results.length > 0 || plan) && (
                <motion.section
                  className="flex flex-col gap-8"
                  initial={{ opacity: 0, y: 40 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 40 }}
                  transition={{ duration: 0.6 }}
                >
                  <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                    <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                      Qwen Insight
                    </p>
                    {renderInsight()}
                    {(meta || totalMs !== null) && (
                      <p className="mt-4 text-xs text-white/50">
                        {meta?.qwen_ms !== undefined && `Qwen ${meta.qwen_ms}ms`}
                        {meta?.nano_ms !== undefined && ` · Nano ${meta.nano_ms}ms`}
                        {totalMs !== null && ` · Total ${totalMs}ms`}
                        {meta?.device && ` · ${meta.device}`}
                      </p>
                    )}
                  </div>

                  <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                    <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                      {useAdvanced ? "Lookbook Results" : "Try-on Result"}
                    </p>
                    <div className="mt-4">{renderResults()}</div>
                  </div>
                </motion.section>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {activeResult && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 px-6 py-10"
          onClick={() => setActiveResult(null)}
        >
          <div
            className="max-h-[90vh] w-full max-w-4xl overflow-auto rounded-3xl border border-white/20 bg-black/90 p-6"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                  {activeResult.title}
                </p>
                <p className="mt-1 text-sm text-white/80">
                  {activeResult.variant_id}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setActiveResult(null)}
                className="rounded-full border border-white/20 px-3 py-1 text-xs text-white/70"
              >
                关闭
              </button>
            </div>
            <img
              src={activeResult.image_url}
              alt={activeResult.title}
              className="mt-6 w-full rounded-2xl object-contain"
            />
            {activeResult.prompt_used && (
              <div className="mt-6">
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                  Prompt
                </p>
                <p className="mt-2 text-sm text-white/80">
                  {activeResult.prompt_used}
                </p>
              </div>
            )}
            {activeResult.negative_prompt_used && (
              <div className="mt-4">
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                  Negative
                </p>
                <p className="mt-2 text-sm text-white/70">
                  {activeResult.negative_prompt_used}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      <HistoryPanel
        open={showHistory}
        onClose={() => setShowHistory(false)}
        onRestore={(rec) => setRestoredRecord(rec)}
      />
    </main>
  );
}
