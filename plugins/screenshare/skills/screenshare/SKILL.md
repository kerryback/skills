---
name: screenshare
description: >-
  Put a student's screen on the classroom projector. Use when an instructor
  wants to "let students share their screen", "show a student's laptop on the
  projector", "open the screen share app", "start screen sharing for class", or
  asks how students can present from their own machines. Launches a local
  WebRTC app on the classroom computer (http://127.0.0.1:8030) and publishes it
  over a Cloudflare Quick Tunnel so students join from an https link on their
  own laptops; the instructor picks who is shown. Video travels browser to
  browser, direct when the network allows and through a TURN relay when it
  doesn't.
---

# screenshare

The instructor runs this on the classroom computer, the one wired to the
projector. Students open a link on their own laptops, pick a screen, window or
tab, and wait; the instructor decides whose screen goes up. You launch it, read
its state when something goes wrong, and set up TURN if the campus network turns
out to need it.

The video never touches the server. It goes browser to browser over WebRTC —
directly when the two machines can reach each other, through a TURN relay when
campus segmentation says they can't. All the server carries is the handshake.

## 0. First run on a new machine

Do this the first time the skill is used on a machine, and any time something
doesn't work. It checks the machine and says what to fix, without starting
anything:

```
python3 "<skill-dir>/scripts/skill_launch.py" --check
```

It reports on Python, the app environment, cloudflared, the config file, and —
if TURN is configured — whether the credentials actually work, by using them.
Exit code is non-zero while anything is unresolved.

Walk the instructor through whatever it lists, one item at a time, and rerun it
until it says Ready. Don't paper over a FIX line by launching anyway; each one
becomes a failure in front of a class instead of a message in a terminal.

The only two things it cannot fix on its own are a too-old Python and admin
rights, and it says so when that is the situation.

## 1. Launch

Run the launcher in the background — it starts a long-lived local server and a
tunnel. `<skill-dir>` is the "Base directory for this skill" reported when the
skill is invoked; use that absolute path.

```
python3 "<skill-dir>/scripts/skill_launch.py"
```

On Windows, use `py -3` instead, falling back to `python`:

```
py -3 "<skill-dir>\scripts\skill_launch.py"
```

Don't use `python3` on Windows. It is usually a Microsoft Store stub that opens
the Store instead of running anything, and the failure is confusing.

The first launch builds a small Python environment in `~/.screenshare`, so it
takes a little longer. It then prints three things you need:

```
[screenshare] Students join at: https://particular-blue-fox-abc.trycloudflare.com
[screenshare] Display (classroom computer): http://127.0.0.1:8030/display?key=…
[screenshare] Room code: 4271
```

The display page opens by itself on the classroom computer. Put it on the
projector: it shows the join link and the code in type students can read from
the back row. If the port is taken, rerun with `--port 8031` and use that port
throughout.

Leave it running for the whole class. Ctrl-C stops both the server and the
tunnel.

## 2. cloudflared has to be there

Students cannot share a screen from an `http://` page. Browsers only hand out a
screen capture in a secure context, so the campus LAN address of the classroom
computer is useless to them — they need https, and the Quick Tunnel is what
provides it. No Cloudflare account, no DNS, no config: `cloudflared` dials out
and comes back with a random `trycloudflare.com` hostname, new each launch.

If the launcher reports that cloudflared is missing, there are two ways to fix
it. With admin rights on the machine:

| | |
| --- | --- |
| Windows | `winget install --id Cloudflare.cloudflared` |
| macOS | `brew install cloudflared` |
| Linux | the distro package, or the download below |

After `winget`, `cloudflared` won't be on `PATH` until a new shell starts. Open
a fresh one before relaunching rather than concluding the install failed.

Without admin rights — a locked-down classroom PC — the launcher fetches its
own copy into `~/.screenshare/bin` and runs it by absolute path. No installer,
no `PATH` change, nothing system-wide:

```
python3 "<skill-dir>/scripts/skill_launch.py" --install-cloudflared
```

That downloads a binary from Cloudflare's GitHub releases and then launches
normally. It is a download and it is the instructor's machine, so say what it
will do and get a yes before running it — don't slip it into a launch command.

Don't work around a missing cloudflared by handing out a LAN address. It will
fail in the room, in front of the class, with a browser error that looks like
the app is broken.

## 2a. What the classroom computer needs

Windows, macOS and Linux all work, and the classroom computer is the easy end:
it only receives video. Screen capture happens on the students' machines, so
nothing about the classroom OS or its browser limits what the class can do.

Two things that come up on Windows and are worth knowing before you debug the
wrong thing:

- The server binds to `127.0.0.1`, never `0.0.0.0`. Windows Firewall does not
  prompt and does not need an exception; the tunnel is how traffic gets in.
- Closing the console window stops the server and the tunnel together, the same
  as Ctrl-C.

## 3. How the class actually uses it

The instructor does not need you for any of this — it is the app's whole
interface:

1. A student opens the link, types their name and the code, and clicks
   **Share my screen**. Their browser asks what to share; nothing leaves their
   machine until they pick.
2. They appear in the sidebar of the display page marked *ready*.
3. The instructor clicks **Show** next to their name. Their screen fills the
   projector.
4. **Take down** clears it; showing someone else swaps automatically. A student
   who has been taken down keeps their capture, so putting them back up is one
   click.

The *Show the first student automatically* checkbox promotes whoever is ready
when nothing is up — useful when students are presenting in turn and the
instructor doesn't want to keep clicking.

Press `f` on the display for full screen, Escape to take down.

## 4. Before the first class: find out whether TURN is needed

Do this once per room, and do it before a class rather than during one. Campus
networks vary too much to predict: the only authoritative answer is a device on
the students' network trying to reach this room.

Add `?test=1` to the join link and open it on a phone:

```
https://<the tunnel URL>/?test=1
```

That page sends the camera instead of the screen — same signalling, same ICE,
same TURN configuration, so it proves the media path. It exists because phones
cannot capture a screen, and a phone is the easiest second device to put on the
students' network.

Put the phone on the student wifi SSID, not the staff one, and not cellular.
The pair of networks is what is being tested. Join with the code, click Send my
camera, put it up from the display, and read the result:

| what you see | what it means |
| --- | --- |
| video arrives, path says *direct* | no TURN needed in this room |
| the phone says no video could get through | TURN is required |
| video arrives, path says *TURN relay* | it is already relaying — TURN is required and working |

If it fails, that is a finding, not a fault: it means the campus keeps student
wireless and the classroom apart, which is exactly the case TURN exists for. Go
to section 6.

Test from cellular too if you like, but read it correctly — cellular proves the
app works between two unrelated networks, not that the classroom will. Only the
student wifi answers the question that matters.

## 5. When a student's video never arrives

The overlay on the display's video says how the connection was made: *direct,
same network*, *direct, through NAT*, or *TURN relay*. That line is the
diagnosis. Read the room's state for the same thing plus who is connected:

```
GET http://127.0.0.1:8030/api/state?key=<display key from the launcher output>
  -> {"code": "4271", "tunnel_url": "…", "stage": "…", "peers": [...],
      "path": {"local": "srflx", "remote": "relay", "relayed": true},
      "turn_configured": false, "ice_policy": "all"}
```

If a student joins and goes *ready* but their video never appears, and
`turn_configured` is false, the campus network is blocking the direct path
between the two machines and there is nothing left to fall back to. That is what
TURN is for. Nothing about the app changes; both browsers just get a relay they
can both reach.

Everything under `/api` and `/display` needs the display key, which the launcher
prints. The tunnel makes every route publicly reachable and cloudflared connects
from localhost, so where a request comes from proves nothing — the key is what
separates the instructor's page from the students'.

## 6. Setting up TURN

Everything lives in `~/.screenshare/config.json`, and a relaunch picks it up.
Never anywhere else: these are credentials, and they don't belong in the repo,
in a course folder, or in chat.

### Cloudflare (the managed option)

In the Cloudflare dashboard, under Realtime → TURN Keys, create a key. It gives
a key ID and an API token:

```json
{
  "code": "4271",
  "cloudflare": {"key_id": "…", "api_token": "…"}
}
```

Cloudflare does not issue a fixed password. The key is long-lived and mints
short-lived credentials from it, so the app fetches a set at startup and caches
them. Don't try to paste a username and password from the dashboard into the
`turn` block below — there aren't any to paste, and anything you did paste would
expire mid-term.

Cloudflare's reply carries the whole ICE list, including `turns:` on 443/TCP,
which is the variant that gets through networks that block UDP.

### A TURN server with fixed credentials

Your own coturn, or a provider that works that way:

```json
{
  "turn": {
    "urls": ["turn:turn.example.edu:3478?transport=udp",
             "turns:turn.example.edu:5349?transport=tcp"],
    "username": "classroom",
    "credential": "…"
  }
}
```

Include a `turns:` TCP entry as well as UDP. A network strict enough to need
TURN often blocks UDP too, and TCP/443 is the one thing that always gets out.

### The other keys

- `code` fixes the room code so it is the same all term instead of changing at
  each launch. The join link still changes — Quick Tunnel hostnames are random.
- `force_relay` refuses direct paths entirely, so a connection that works
  proves TURN worked. Turn it off before class: relaying every session when you
  don't have to costs bandwidth and adds latency. It is ignored while TURN is
  broken, since forcing a relay that isn't there would connect nothing at all.

### Check it actually worked

A wrong token fails quietly — video still connects wherever the network allows
a direct path, so it looks fine until the day it matters. Both the launcher
output and `/api/state` say plainly what happened:

```
"turn_source": "cloudflare",           TURN is live
"turn_source": "cloudflare (failing)", credentials rejected -- read turn_error
"turn_source": "none",                 nothing configured
```

Then prove the relay end to end: set `force_relay`, relaunch, and run the
`?test=1` check from section 4 on a phone using cellular. Direct paths are
refused, so video arriving means it came through TURN.

## Browsers

| | screen sharing |
| --- | --- |
| Chrome, Edge on any desktop OS | yes, including a single tab with its audio |
| Safari on macOS | yes; video only, no audio capture |
| Firefox | yes; no audio capture |
| iPhone, iPad, Android | no — mobile browsers cannot capture a screen |

Recommend Chrome or Edge and check Safari separately on the Macs in the room.
On a Mac, the first attempt may need Screen Recording permission for the
browser in System Settings → Privacy & Security; the browser prompts, but the
student has to restart it afterwards, so it is worth doing before class rather
than during.

## Notes

- The room code is what keeps a leaked link out. It is on the display page, not
  in the URL, so forwarding the link to someone outside the room doesn't get
  them in.
- Sharing is always explicit: the student picks what to send in their own
  browser's picker, and can stop at any time from the page or from the browser's
  own sharing indicator.
- One screen shows at a time. That is deliberate — it is a projector.
- The app records nothing and writes nothing to disk. When the launcher stops,
  the room is gone.
- The room might record it anyway. Lecture capture (Panopto and the like) grabs
  the classroom computer's screen, so a student's shared screen goes into the
  recording along with the rest of the class. That can be a feature — a student
  demo preserved for free — or a problem, since a student's laptop may show more
  than they meant during the moment they pick what to share. If the room records
  and the instructor hasn't raised it, say so before the first class rather than
  after. Pausing the capture, or having students share one window instead of a
  whole screen, both solve it.
