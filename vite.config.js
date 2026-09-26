import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function ingestPlugin() {
  return {
    name: "atelier-ingest",
    configureServer(server) {
      server.middlewares.use("/api/ingest", async (req, res) => {
        try {
          const incoming = new URL(req.url, "http://localhost");
          const target = incoming.searchParams.get("url");
          if (!target) {
            res.statusCode = 400;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ error: "Missing url" }));
            return;
          }

          const parsed = new URL(target);
          let title = parsed.hostname;
          let description = "";
          let kind = "web";
          let thumbnail = "";

          if (/youtube\.com|youtu\.be/.test(parsed.hostname)) {
            kind = "youtube";
            try {
              const oembed = await fetch(
                `https://www.youtube.com/oembed?url=${encodeURIComponent(target)}&format=json`
              );
              if (oembed.ok) {
                const data = await oembed.json();
                title = data.title || title;
                description = `Video by ${data.author_name || "unknown"}`;
                thumbnail = data.thumbnail_url || "";
              }
            } catch {
              description = "YouTube reference (metadata unavailable)";
            }
          } else {
            try {
              const page = await fetch(target, {
                headers: { "User-Agent": "AtelierDesignAgent/0.1" },
                signal: AbortSignal.timeout(8000),
              });
              const html = await page.text();
              const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
              const descMatch =
                html.match(/property="og:description"\s+content="([^"]+)"/i) ||
                html.match(/name="description"\s+content="([^"]+)"/i);
              const imageMatch = html.match(/property="og:image"\s+content="([^"]+)"/i);
              if (titleMatch) title = decodeHtml(titleMatch[1]).trim();
              if (descMatch) description = decodeHtml(descMatch[1]).trim();
              if (imageMatch) thumbnail = imageMatch[1];
            } catch {
              description = "Could not fetch page body; using the URL as a visual brief.";
            }
          }

          res.setHeader("Content-Type", "application/json");
          res.end(
            JSON.stringify({
              url: target,
              title,
              description,
              kind,
              thumbnail,
              host: parsed.hostname,
            })
          );
        } catch (error) {
          res.statusCode = 500;
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ error: String(error.message || error) }));
        }
      });
    },
  };
}

function decodeHtml(value) {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

export default defineConfig({
  plugins: [react(), ingestPlugin()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
