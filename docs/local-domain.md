# Local beanagile.org

Open the apps at **https://toolkit.beanagile.org** and **https://comms.beanagile.org** on your own machine, with a real padlock, while the public internet only ever sees the cat video at beanagile.org.

How it fits together:

- The two app names point at `127.0.0.1`, so they only ever reach the machine you're sitting at.
- Caddy, a small web server, answers on those names with HTTPS and passes requests to the apps on ports 8801 and 8802.
- The apps still listen only on `127.0.0.1`, and they refuse any request addressed to a name they don't know (this blocks a trick called DNS rebinding).
- beanagile.org and www.beanagile.org point at a public static host serving `site/` (the cat video), with no link to anything else.

## 1. Point the names at this machine

Pick one.

**DNS records (no admin password, works on any machine you install the apps on).** At your registrar, add two A records:

| Name | Type | Value |
| --- | --- | --- |
| toolkit | A | 127.0.0.1 |
| comms | A | 127.0.0.1 |

**Or the hosts file (this machine only).** Add these lines to `/etc/hosts` (needs your admin password):

```text
127.0.0.1  toolkit.beanagile.org
127.0.0.1  comms.beanagile.org
```

`beanagileorg domain` prints these lines and the Caddy config below.

## 2. Install Caddy and trust its certificates

```bash
brew install caddy
```

```bash
caddy trust
```

`caddy trust` adds Caddy's local certificate authority to your keychain (it asks for your password), so browsers show the padlock for the local names. Nothing is requested from a public certificate authority.

## 3. Save the config and start Caddy

```bash
beanagileorg domain --caddyfile > ~/.beanagileorg/Caddyfile
```

```bash
caddy run --config ~/.beanagileorg/Caddyfile
```

To keep it running in the background instead, use `caddy start --config ~/.beanagileorg/Caddyfile` (and `caddy stop` to end it).

## 4. Use the new addresses

- Toolkit: https://toolkit.beanagile.org
- Comms studio: https://comms.beanagile.org
- In the Comms studio's Connections screen, the toolkit address can stay `http://127.0.0.1:8801`; both work.

Sign in again once at each new address, since sign-in is tied to the address you use.

## Other names

To reach an app under another name (for example through Tailscale later), list it in `BEANAGILEORG_ALLOWED_HOSTS` before starting the app:

```bash
export BEANAGILEORG_ALLOWED_HOSTS="[placeholder-machine-name].[placeholder-tailnet].ts.net"
```

## The public site

`site/index.html` is the whole public site: the cat video and nothing else. Put the video file next to it as `site/[placeholder video file name].mp4`, update the file name in `index.html`, and publish the folder on any static host (GitHub Pages, Cloudflare Pages, Netlify). Point beanagile.org and www at that host. Never add records for the app names there other than the `127.0.0.1` ones above.
