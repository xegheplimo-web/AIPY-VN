import * as Sentry from "@sentry/react";

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || "development",
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    // Tracing
    tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || "0.1"),
    // Session Replay
    replaysSessionSampleRate: parseFloat(import.meta.env.VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE || "0.1"),
    replaysOnErrorSampleRate: 1.0,
    // Filter sensitive data
    beforeSend(event, hint) {
      // Filter out sensitive data
      if (event.request) {
        if (event.request.headers) {
          const sensitiveHeaders = ["authorization", "cookie", "x-api-key"];
          event.request.headers = Object.fromEntries(
            Object.entries(event.request.headers).filter(([key]) => 
              !sensitiveHeaders.includes(key.toLowerCase())
            )
          );
        }
      }
      return event;
    },
  });
}

export default Sentry;
