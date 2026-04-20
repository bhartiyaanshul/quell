"use client";

import { useEffect } from "react";

/**
 * Swallows runtime errors that bubble up from browser extensions
 * (MetaMask, wallet extensions, ad blockers, etc.).
 *
 * Extensions like MetaMask inject scripts into every page via
 * ``chrome-extension://.../inpage.js`` and throw when they can't reach
 * their background worker — a dev-only annoyance that shows up as a
 * Next.js "Unhandled Runtime Error" overlay even though our code is
 * fine.  We filter those out by inspecting the error source / stack.
 *
 * We only prevent-default on errors whose stack comes from an
 * extension URL, so real bugs in our own code still surface normally.
 */
export function ExtensionErrorFilter() {
  useEffect(() => {
    const EXTENSION_MARKERS = [
      "chrome-extension://",
      "moz-extension://",
      "safari-web-extension://",
    ];

    function isExtensionError(text: unknown): boolean {
      if (typeof text !== "string") return false;
      return EXTENSION_MARKERS.some((m) => text.includes(m));
    }

    const onError = (event: ErrorEvent) => {
      const src = event.filename ?? "";
      const stack =
        (event.error &&
          typeof event.error === "object" &&
          "stack" in event.error &&
          typeof (event.error as { stack: unknown }).stack === "string" &&
          (event.error as { stack: string }).stack) ||
        "";
      if (
        isExtensionError(src) ||
        isExtensionError(stack) ||
        isExtensionError(event.message)
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    };

    const onRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      const text =
        (reason && typeof reason === "object" && "stack" in reason
          ? String((reason as { stack: unknown }).stack ?? "")
          : "") +
        " " +
        String(reason?.message ?? reason ?? "");
      if (
        isExtensionError(text) ||
        text.toLowerCase().includes("metamask")
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    };

    window.addEventListener("error", onError, true);
    window.addEventListener("unhandledrejection", onRejection, true);
    return () => {
      window.removeEventListener("error", onError, true);
      window.removeEventListener("unhandledrejection", onRejection, true);
    };
  }, []);

  return null;
}
