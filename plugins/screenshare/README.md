# screenshare

Let students put their own screen on the classroom projector.

Ask Claude to start it and the classroom computer shows a join link and a code
in type readable from the back row. Students open the link on their laptops,
pick a screen, window or tab, and appear in a queue. You click Show, and their
screen fills the projector.

The video goes browser to browser. It never passes through the server, and
nothing is written to disk — when you stop the app, the room is gone.

The app records nothing, but the room may. Lecture capture like Panopto records
the classroom computer's screen, so a shared student screen lands in the lecture
recording along with everything else. Sometimes that's a bonus and sometimes
it's a surprise for the student — worth settling before the first class. Having
students share a single window rather than a whole screen is the easy fix.

## Install

From the `kerryback-skills` marketplace:

```
/plugin marketplace add kerryback/skills
/plugin install screenshare@kerryback-skills
```

Then ask Claude Code to start screen sharing, or invoke the skill directly with
`/screenshare:screenshare`.

## Requirements

Windows, macOS or Linux on the classroom computer, Python 3.11+, and
`cloudflared`.

`cloudflared` isn't optional. Browsers only hand out a screen capture over
https, so the classroom computer's address on the campus LAN is no use to
students. A Cloudflare Quick Tunnel gives the app a real https hostname — no
Cloudflare account, no DNS, no configuration, and a new random hostname each
launch.

With admin rights:

| | |
| --- | --- |
| Windows | `winget install --id Cloudflare.cloudflared` |
| macOS | `brew install cloudflared` |
| Linux | your distro package |

Without them, on a locked-down classroom PC, ask Claude to launch with
`--install-cloudflared`. It downloads a copy into `~/.screenshare/bin` and runs
it from there — no installer, no `PATH` change, nothing system-wide.

The classroom computer is the easy end: it only receives video. Screen capture
happens on the students' machines, so the classroom OS and browser don't limit
what the class can do. The server binds to `127.0.0.1`, so Windows Firewall
never prompts and needs no exception.

## First run

Ask Claude to check the setup, or run it yourself:

```
python3 <skill-dir>/scripts/skill_launch.py --check
```

It reports on Python, the app environment, cloudflared, your config file, and
whether your TURN credentials actually work — by using them, not by checking
they exist. Everything it flags comes with what to run next. Claude will walk
you through it.

## Using it

Claude runs the launcher. The display page opens on the classroom computer; put
it on the projector. It shows the join link, the room code, and a QR of the
link, and it becomes the video as soon as you show someone.

| | |
| --- | --- |
| a student joins | name plus the code from the screen |
| they click Share my screen | their browser asks what to send; nothing leaves their machine until they pick |
| they land in the queue | marked *ready* in the sidebar |
| you click Show | their screen fills the projector |
| you click Take down, or show someone else | the first student keeps their capture, so putting them back is one click |

`f` toggles full screen, Escape takes the current student down. The *Show the
first student automatically* checkbox promotes whoever is waiting when nothing
is up — useful when students present in turn.

The code is what keeps a forwarded link from getting a stranger in. It is on the
screen, not in the URL.

## Finding out whether you need TURN

Do this once per room, before a class rather than during one. Open the join link
on a phone with `?test=1` on the end:

```
https://<the tunnel URL>/?test=1
```

That sends the phone's camera instead of a screen — same connection path, same
settings — so it answers the question without needing a second laptop. Phones
can't capture a screen, which is the whole reason this mode exists.

Put the phone on the student wifi, join, and put it up. If the video arrives,
this room needs no TURN. If it doesn't, the campus keeps student wireless and
the classroom apart, and TURN is what bridges them.

## When the video doesn't arrive

The overlay on the video says how the connection was made: *direct, same
network*, *direct, through NAT*, or *TURN relay*.

WebRTC tries to send the video straight from the student's laptop to the
classroom computer. On a network where those two machines can reach each other,
that is what happens. Campus networks often segment wireless clients from wired
ones specifically so they can't — and then there is no direct path to find. The
fallback is a TURN server, which relays the video through the public internet.

Nothing about the app changes; both browsers just get a relay they can both
reach. Put the credentials in `~/.screenshare/config.json` — not in a course
folder, and not in the repo.

With Cloudflare, create a key under Realtime → TURN Keys and use its ID and API
token:

```json
{
  "code": "4271",
  "cloudflare": {"key_id": "…", "api_token": "…"}
}
```

Cloudflare issues short-lived credentials rather than a fixed password, so the
app mints a fresh set at each launch. There is no username and password to paste
— and anything you did paste would expire partway through the term.

For a TURN server that does have fixed credentials, your own coturn or similar:

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

Two other keys are useful. `code` fixes the room code so it stays the same all
term, though the join link still changes each launch. `force_relay` refuses
direct paths, so a connection that works proves the relay works — test with it
on from a phone on cellular, then turn it off.

A wrong token fails quietly, since video still connects wherever a direct path
exists. Ask Claude to check `http://127.0.0.1:8030/api/state?key=…`: it reports
`turn_source` as `cloudflare`, `cloudflare (failing)` with the reason, or
`none`, along with how the current student's video is actually travelling.

## Browsers

| | screen sharing |
| --- | --- |
| Chrome, Edge | yes, including a single tab with its audio |
| Safari on macOS | yes; video only |
| Firefox | yes; video only |
| iPhone, iPad, Android | no — mobile browsers cannot capture a screen |

Tell students Chrome or Edge. On a Mac, the first attempt may need Screen
Recording permission for the browser in System Settings → Privacy & Security,
which requires restarting the browser — worth doing before class rather than
during.

## Where things are kept

| what | where |
| --- | --- |
| TURN credentials, fixed room code | `~/.screenshare/config.json` |
| Python environment | `~/.screenshare/venv`, built once on first launch |

Nothing else. There is no database and no recording.
