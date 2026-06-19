import { useEffect, useState } from 'react';

interface WebVitals {
  cls: number;
  lcp: number;
  fid: number;
  fcp: number;
  ttfb: number;
}

export const useWebVitals = () => {
  const [vitals, setVitals] = useState<WebVitals>({
    cls: 0,
    lcp: 0,
    fid: 0,
    fcp: 0,
    ttfb: 0,
  });

  useEffect(() => {
    // CLS - Cumulative Layout Shift
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
        }
      }
      setVitals((prev) => ({ ...prev, cls: clsValue }));
    });
    clsObserver.observe({ entryTypes: ['layout-shift'] });

    // LCP - Largest Contentful Paint
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      setVitals((prev) => ({ ...prev, lcp: lastEntry.startTime }));
    });
    lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

    // FID - First Input Delay
    const fidObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const delay = (entry as any).processingStart - entry.startTime;
        setVitals((prev) => ({ ...prev, fid: delay }));
      }
    });
    fidObserver.observe({ entryTypes: ['first-input'] });

    // FCP & TTFB from navigation timing
    window.addEventListener('load', () => {
      const timing = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (timing) {
        setVitals((prev) => ({
          ...prev,
          fcp: timing.domContentLoadedEventStart,
          ttfb: timing.responseStart,
        }));
      }
    });

    return () => {
      clsObserver.disconnect();
      lcpObserver.disconnect();
      fidObserver.disconnect();
    };
  }, []);

  return vitals;
};
