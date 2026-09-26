# Using it from your phone, and letting Instagram fetch your media

There are two different needs. Keep them separate.

| Need | Who connects | Which port | What to expose |
|---|---|---|---|
| You use the dashboard on your phone | Only you | 5057 | Privately (Tailscale). Never the open internet. |
| Instagram downloads your video when publishing | Instagram's servers | 5058 | Publicly, but this port serves nothing except short-lived media links. |

## A. Dashboard on your phone (with working microphone)

Phones only allow the microphone and "Add to Home screen" on secure (https) addresses.

**Recommended: Tailscale** (free for personal use)

1. Install Tailscale on the PC and on the phone, sign in to both with the same account.
2. On the PC, publish the app over https to your private network. The exact command depends on your Tailscale version; run `tailscale serve --help`. Typically: `tailscale serve --bg 5057`.
3. Tailscale prints an address like `https://your-pc.your-tailnet.ts.net`. Add the host part to `.env`:
   ```
   ALLOWED_HOSTS=your-pc.your-tailnet.ts.net
   SESSION_COOKIE_SECURE=1
   ```
4. Restart the app. Open the address in Chrome on the phone, sign in, then "Add to Home screen".

Keep `HOST=127.0.0.1`. Tailscale reaches the app from the same machine, so it does not need to listen on the network.

**Quick option without https:** set `HOST=0.0.0.0` and open `http://<PC address>:5057` on the same Wi-Fi. Everything works except the microphone and installing as an app. Allow the port in Windows Firewall for Private networks only. Do not do this on public Wi-Fi.

## B. Letting Instagram fetch your media (needed only for live posting)

The app runs a second tiny server on port 5058 that serves only links like `/m/<random>/<file>`. Each link expires after 30 minutes and is deleted right after publishing.

1. Start a tunnel that points at **5058, not 5057**. With Cloudflare: `cloudflared tunnel --url http://localhost:5058` prints a temporary `https://...trycloudflare.com` address (it changes each run; for a stable address use a named tunnel on your own domain).
2. Put that address in `.env`: `PUBLIC_MEDIA_BASE_URL=https://something.trycloudflare.com`
3. Restart the app. With `DRY_RUN=1`, publishing rehearses fetching the link locally so you can check it before going live.

Because a temporary address changes each time, a permanent named tunnel is better once you are posting regularly.

## Things that will confuse you

- "Bad request" on a new address: add its host name to `ALLOWED_HOSTS` (this blocks a browser attack called DNS rebinding).
- Signed out immediately over https: set `SESSION_COOKIE_SECURE=1`. Over plain http set it to `0`.
- Tokens: an Instagram access token expires; when it does, publishing fails with a clear message and you replace `IG_ACCESS_TOKEN`.
