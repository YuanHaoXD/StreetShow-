"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useLang } from "./LangProvider";

const STORAGE_KEY = "streetshow_history";
const MAX_RECORDS = 8; // 每条含 base64 图片约 300KB，8 条 ≈ 2.4MB，留足 localStorage 余量

export type HistoryRecord = {
  id: string;
  timestamp: number;
  mode: string;
  garmentThumb: string;
  firstImageUrl: string;
  adviceSummary: string;
  results?: unknown[];
  advice?: unknown;
};

export function saveHistoryRecord(record: Omit<HistoryRecord, "id">) {
  try {
    const existing: HistoryRecord[] = JSON.parse(
      localStorage.getItem(STORAGE_KEY) ?? "[]"
    );
    const newRecord: HistoryRecord = {
      ...record,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    };
    const updated = [newRecord, ...existing].slice(0, MAX_RECORDS);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // QuotaExceededError：丢掉最旧一条后重试
      const trimmed = updated.slice(0, updated.length - 1);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
      } catch {
        // 仍然失败则放弃
      }
    }
  } catch {
    // localStorage 不可用时静默忽略
  }
}

function loadHistory(): HistoryRecord[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function formatTime(ts: number): string {
  const d = new Date(ts);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

const MODE_LABEL_KEYS: Record<string, "modeLookbookLabel" | "modePoseLabel" | "modeMultiLabel" | "modeBasicLabel"> = {
  lookbook: "modeLookbookLabel",
  pose: "modePoseLabel",
  multi: "modeMultiLabel",
  basic: "modeBasicLabel",
};

type Props = {
  open: boolean;
  onClose: () => void;
  onRestore?: (record: HistoryRecord) => void;
};

export default function HistoryPanel({ open, onClose, onRestore }: Props) {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [mounted, setMounted] = useState(false);
  const { t } = useLang();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (open) {
      setRecords(loadHistory());
    }
  }, [open]);

  const clearAll = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setRecords([]);
  };

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {open && (
        <>
          {/* 背景遮罩 */}
          <motion.div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          {/* 抽屉面板 */}
          <motion.div
            className="fixed right-0 top-0 z-50 flex h-full w-full max-w-sm flex-col border-l border-white/10 bg-black/95 shadow-2xl"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 240 }}
          >
            {/* 头部 */}
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">
                  History
                </p>
                <p className="mt-0.5 text-sm font-semibold text-white">
                  {t("historyTitle")}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {records.length > 0 && (
                  <button
                    type="button"
                    onClick={clearAll}
                    className="rounded-full border border-white/20 px-3 py-1 text-[11px] text-white/50 hover:border-red-400/40 hover:text-red-400"
                  >
                    {t("historyClearAll")}
                  </button>
                )}
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-full border border-white/20 px-3 py-1 text-xs text-white/60 hover:text-white"
                >
                  {t("historyClose")}
                </button>
              </div>
            </div>

            {/* 列表 */}
            <div className="flex-1 overflow-y-auto p-4">
              {records.length === 0 ? (
                <div className="flex h-full items-center justify-center text-white/30">
                  <p className="text-sm">{t("historyEmpty")}</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {records.map((rec) => (
                    <button
                      key={rec.id}
                      type="button"
                      onClick={() => {
                        onRestore?.(rec);
                        onClose();
                      }}
                      className="flex gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 text-left transition-colors hover:border-[var(--acid-green)]/40 hover:bg-white/10"
                    >
                      {/* 衣物缩略图 */}
                      {rec.garmentThumb ? (
                        <img
                          src={rec.garmentThumb}
                          alt="garment"
                          className="h-16 w-12 flex-shrink-0 rounded-xl object-cover"
                        />
                      ) : (
                        <div className="h-16 w-12 flex-shrink-0 rounded-xl bg-white/10" />
                      )}

                      {/* 生成结果小图 */}
                      {rec.firstImageUrl ? (
                        <img
                          src={rec.firstImageUrl}
                          alt="result"
                          className="h-16 w-12 flex-shrink-0 rounded-xl object-cover"
                        />
                      ) : (
                        <div className="h-16 w-12 flex-shrink-0 rounded-xl bg-white/5" />
                      )}

                      {/* 信息 */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="rounded-full border border-[var(--acid-green)]/40 px-2 py-0.5 text-[10px] text-[var(--acid-green)]">
                            {MODE_LABEL_KEYS[rec.mode] ? t(MODE_LABEL_KEYS[rec.mode]) : rec.mode}
                          </span>
                          <span className="text-[10px] text-white/40">
                            {formatTime(rec.timestamp)}
                          </span>
                        </div>
                        {rec.adviceSummary && (
                          <p className="mt-1.5 line-clamp-2 text-[11px] leading-relaxed text-white/60">
                            {rec.adviceSummary}
                          </p>
                        )}
                        <p className="mt-1 text-[10px] text-white/30">
                          {t("historyTapView")}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
