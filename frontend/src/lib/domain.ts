/**
 * Domain configuration client for the frontend.
 *
 * Fetches the active domain config from the backend and provides
 * typed access to labels, categories, and branding so the entire UI
 * adapts to whichever business domain is configured (plumbing, HVAC,
 * electrical, etc.).
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface JobCategory {
  id: string;
  label: string;
  icon: string;
}

export interface PriorityLevel {
  id: string;
  label: string;
  color: string;
}

export interface JobStatus {
  id: string;
  label: string;
  color: string;
}

export interface DomainConfig {
  business_type: string;
  app_name: string;
  tagline: string;
  labels: Record<string, string>;
  job_categories: JobCategory[];
  priority_levels: PriorityLevel[];
  job_statuses: JobStatus[];
  part_categories: string[];
  domain_context: string;
  diagnostic_prompt_context: string;
  compliance_context: string;
  default_markup_pct: number;
  enabled_modules: string[];
}

// ---------------------------------------------------------------------------
// In-memory cache
// ---------------------------------------------------------------------------

let _cachedConfig: DomainConfig | null = null;
let _fetchPromise: Promise<DomainConfig> | null = null;

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Core fetch
// ---------------------------------------------------------------------------

/**
 * Fetch the domain configuration from the backend.
 * Results are cached in memory for the lifetime of the page.
 */
export async function fetchDomainConfig(): Promise<DomainConfig> {
  if (_cachedConfig) return _cachedConfig;

  // Deduplicate concurrent requests
  if (_fetchPromise) return _fetchPromise;

  _fetchPromise = (async () => {
    const res = await fetch(`${API_BASE}/api/domain`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch domain config: ${res.status}`);
    }
    const data: DomainConfig = await res.json();
    _cachedConfig = data;
    return data;
  })();

  try {
    return await _fetchPromise;
  } finally {
    _fetchPromise = null;
  }
}

/**
 * Return the cached domain config synchronously (or null if not yet fetched).
 */
export function getCachedDomainConfig(): DomainConfig | null {
  return _cachedConfig;
}

// ---------------------------------------------------------------------------
// Helper functions (work on the cached config)
// ---------------------------------------------------------------------------

/**
 * Get a domain-specific label by key.
 * Falls back to the key itself if the label is not defined.
 *
 * @example getLabel("technician") // "Plumber" for plumbing, "HVAC Technician" for HVAC
 */
export function getLabel(key: string): string {
  return _cachedConfig?.labels[key] ?? key;
}

/**
 * Get all job categories for the current domain.
 */
export function getJobCategories(): JobCategory[] {
  return _cachedConfig?.job_categories ?? [];
}

/**
 * Get all priority levels for the current domain.
 */
export function getPriorityLevels(): PriorityLevel[] {
  return _cachedConfig?.priority_levels ?? [];
}

/**
 * Get all job statuses for the current domain.
 */
export function getJobStatuses(): JobStatus[] {
  return _cachedConfig?.job_statuses ?? [];
}

/**
 * Get part categories for the current domain.
 */
export function getPartCategories(): string[] {
  return _cachedConfig?.part_categories ?? [];
}

/**
 * Get the app name for the current domain.
 */
export function getAppName(): string {
  return _cachedConfig?.app_name ?? "Service Pro AI";
}

/**
 * Check if a module is enabled in the current domain config.
 */
export function isModuleEnabled(module: string): boolean {
  return _cachedConfig?.enabled_modules.includes(module) ?? false;
}

// ---------------------------------------------------------------------------
// React hook
// ---------------------------------------------------------------------------

import { useEffect, useState } from "react";

/**
 * React hook that fetches and caches the domain configuration.
 *
 * @example
 * const { config, loading, error } = useDomainConfig();
 * if (loading) return <Skeleton />;
 * return <h1>{config.app_name}</h1>;
 */
export function useDomainConfig() {
  const [config, setConfig] = useState<DomainConfig | null>(_cachedConfig);
  const [loading, setLoading] = useState(!_cachedConfig);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (_cachedConfig) {
      setConfig(_cachedConfig);
      setLoading(false);
      return;
    }

    let cancelled = false;

    fetchDomainConfig()
      .then((data) => {
        if (!cancelled) {
          setConfig(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { config, loading, error };
}
