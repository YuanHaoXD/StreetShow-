"use client";

import { motion } from "framer-motion";
import { useRef, useState } from "react";

import HistoryPanel, { saveHistoryRecord } from "../../components/HistoryPanel";
import ImageUploader from "../../components/ImageUploader";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type StyleDNA = {
  style_keywords?: string[];
  vibe?: string;
  occasions?: string[];
};

type MultiResult = {
  image_url: string;
  prompt_used: string;
  garment_count: number;
  style_dna_list: StyleDNA[];
  error: string | null;
  meta: {
    nano_ms?: number;
    total_ms?: number;
    nanobanana_used?: boolean;
    nanobanana_error?: string | null;
  };
};

const NAV_LINKS = [
  { href: "/basic", label: "标准试衣" },
  { href: "/lookbook", label: "Lookbook" },
  { href: "/pose", label: "Pose Lab" },
  { href: "/multi", label: "Multi-Fit", active: true },
];

export default function MultiPage() {
  const [personFile, setPersonFile] = useState<File | null>(null);
  const [garmentFiles, setGarmentFiles] = useState<(File | null)[]>([null, null]);
  const [userPrompt, setUserPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MultiResult | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const totalMsRef = useRef<number | null>(null);

  const canSubmit =
    Boolean(personFile) &&
    garmentFiles.some(Boolean) &&
    !loading;

  const addGarment = () => {
    if (garmentFiles.length < 3) {
      setGarmentFiles([...garmentFiles, null]);
    }
  };

  const removeGarment = (idx: number) => {
    if (garmentFiles.length <= 1) return;
    setGarmentFiles(garmentFiles.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    if (!canSubmit || !personFile) return;
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("person_image", personFile);
      garmentFiles.forEach((f) => {
        if (f) formData.append("garment_images", f);
      });
      if (userPrompt.trim()) {
        formData.append("user_prompt", userPrompt.trim());
      }

      const startTime = performance.now();
      const response = await fetch(`${API_BASE}/api/process-multi`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const data: MultiResult = await response.json();
      totalMsRef.current = Math.round(performance.now() - startTime);

      // 规范化图片 URL
      if (data.image_url && !data.image_url.startsWith("http")) {
        data.image_url = `${API_BASE}${data.image_url}`;
      }
      setResult(data);

      // 保存历史记录
      saveHistoryRecord({
        timestamp: Date.now(),
        mode: "multi",
        garmentThumb: "",
        firstImageUrl: data.image_url ?? "",
        adviceSummary: data.style_dna_list?.[0]?.vibe ?? "多物件试衣",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-black px-6 py-16 text-white">
      {/* 背景光球 */}
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
      </div>

      <div className="relative mx-auto flex max-w-6xl flex-col gap-12">
        <header className="flex flex-col gap-4">
          <p className="text-xs uppercase tracking-[0.4em] text-white/60">StreetShow</p>
          <h1 className="text-4xl font-semibold md:text-5xl">MULTI-FIT</h1>
          <p className="max-w-2xl text-base text-white/70">
            上传人物图与多件衣物，AI 将它们同时穿到模特身上，展示完整穿搭效果。
          </p>
        </header>

        <div className="grid gap-8 xl:grid-cols-[280px_1fr]">
          {/* 侧边栏 */}
          <aside className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <p className="text-xs uppercase tracking-[0.3em] text-white/50">Modes</p>
            <div className="mt-4 space-y-3">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={[
                    "block w-full rounded-2xl border px-4 py-3 text-left transition",
                    link.active
                      ? "border-[var(--acid-green)] bg-white/10"
                      : "border-white/10 bg-black/40 hover:border-white/30",
                  ].join(" ")}
                >
                  <p className="text-sm font-semibold text-white">{link.label}</p>
                </Link>
              ))}
            </div>

            <div className="mt-6 space-y-4 text-xs text-white/70">
              <div>
                <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-white/40">
                  用户偏好
                </p>
                <textarea
                  value={userPrompt}
                  onChange={(e) => setUserPrompt(e.target.value)}
                  placeholder="街头风 / 正式场合 / 度假风..."
                  rows={3}
                  className="w-full rounded-md border border-white/20 bg-black/60 px-3 py-2 text-white placeholder:text-white/40"
                />
              </div>
            </div>

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
            {/* 人物上传 */}
            <section>
              <p className="mb-3 text-xs uppercase tracking-[0.3em] text-white/50">
                人物图
              </p>
              <div className="max-w-xs">
                <ImageUploader
                  label="Subject (你)"
                  hint="上传人物图"
                  onFile={setPersonFile}
                />
              </div>
            </section>

            {/* 衣物上传（动态增减） */}
            <section>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                  衣物图（最多 3 件）
                </p>
                {garmentFiles.length < 3 && (
                  <button
                    type="button"
                    onClick={addGarment}
                    className="rounded-full border border-white/20 px-3 py-1 text-xs text-white/60 hover:border-[var(--acid-green)]/50 hover:text-[var(--acid-green)]"
                  >
                    + 添加衣物
                  </button>
                )}
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {garmentFiles.map((_, idx) => (
                  <div key={idx} className="relative">
                    <ImageUploader
                      label={`Garment ${idx + 1}`}
                      hint={idx === 0 ? "上装 / 第一件" : idx === 1 ? "下装 / 第二件" : "叠穿 / 第三件"}
                      onFile={(f) => {
                        const updated = [...garmentFiles];
                        updated[idx] = f;
                        setGarmentFiles(updated);
                      }}
                    />
                    {garmentFiles.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeGarment(idx)}
                        className="absolute right-2 top-2 rounded-full border border-white/20 bg-black/60 px-2 py-0.5 text-[10px] text-white/50 hover:border-red-400/40 hover:text-red-400"
                      >
                        移除
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* 生成按钮 */}
            <section className="flex flex-wrap items-center gap-4">
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!canSubmit}
                className={[
                  "glow-button relative overflow-hidden rounded-full px-10 py-4 text-sm font-bold uppercase tracking-widest transition",
                  canSubmit
                    ? "cursor-pointer bg-white text-black"
                    : "cursor-not-allowed bg-white/5 text-white/40",
                ].join(" ")}
              >
                <span className="relative z-10">
                  {loading ? "GENERATING..." : "GENERATE MULTI-FIT"}
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

            {/* 结果展示 */}
            {result && (
              <motion.section
                className="flex flex-col gap-8"
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                {/* 风格DNA列表 */}
                {result.style_dna_list && result.style_dna_list.length > 0 && (
                  <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                    <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                      🧬 衣物风格 DNA
                    </p>
                    <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {result.style_dna_list.map((dna, idx) => (
                        <div
                          key={idx}
                          className="rounded-2xl border border-[var(--neon-cyan)]/20 bg-[var(--neon-cyan)]/5 p-4"
                        >
                          <p className="text-[11px] font-semibold text-[var(--neon-cyan)]">
                            衣物 {idx + 1}
                          </p>
                          {dna.vibe && (
                            <p className="mt-1.5 text-sm text-white/80">{dna.vibe}</p>
                          )}
                          {dna.style_keywords && dna.style_keywords.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              {dna.style_keywords.map((kw) => (
                                <span
                                  key={kw}
                                  className="rounded-full border border-[var(--neon-cyan)]/30 px-2 py-0.5 text-[10px] text-[var(--neon-cyan)]/70"
                                >
                                  #{kw}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    {result.meta && (
                      <p className="mt-3 text-xs text-white/30">
                        {result.meta.nano_ms !== undefined && `生成耗时 ${result.meta.nano_ms}ms`}
                        {totalMsRef.current !== null && ` · 总计 ${totalMsRef.current}ms`}
                      </p>
                    )}
                  </div>
                )}

                {/* 生成图片 */}
                <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                  <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                    Multi-Fit Result
                  </p>
                  <div className="mt-4">
                    {result.image_url ? (
                      <img
                        src={result.image_url}
                        alt="Multi-Fit result"
                        className="mx-auto max-h-[640px] rounded-2xl object-contain"
                      />
                    ) : (
                      <div className="flex h-[400px] items-center justify-center text-white/40">
                        <p className="text-sm">图片生成失败</p>
                      </div>
                    )}
                    {result.error && (
                      <p className="mt-3 text-xs text-red-400">{result.error}</p>
                    )}
                  </div>
                </div>
              </motion.section>
            )}
          </div>
        </div>
      </div>

      <HistoryPanel
        open={showHistory}
        onClose={() => setShowHistory(false)}
      />
    </main>
  );
}
