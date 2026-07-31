#!/usr/bin/env bash
# Check audio files against ElevenLabs voice-cloning targets before uploading.
#
# Usage: bash audio_check.sh <file> [file ...]
#
# Reports duration, codec, sample rate, bit depth, channels, mean/peak level,
# clipping, and a noise-floor estimate; flags anything outside spec.

set -uo pipefail

for cmd in ffprobe ffmpeg; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "error: $cmd not found on PATH." >&2
        echo "  macOS:  brew install ffmpeg" >&2
        echo "  Debian: sudo apt install ffmpeg" >&2
        exit 1
    fi
done

if [ "$#" -eq 0 ]; then
    echo "usage: bash audio_check.sh <file> [file ...]" >&2
    exit 1
fi

# ElevenLabs targets: -23..-18 dBFS RMS, true peak <= -3 dBFS, >=30 min for PVC.
RMS_MIN=-23; RMS_MAX=-18; PEAK_MAX=-3

total_duration=0
issues_total=0

fmt_hms() { printf '%d:%02d:%02d' $(( ${1%.*} / 3600 )) $(( (${1%.*} % 3600) / 60 )) $(( ${1%.*} % 60 )); }

# Compare two decimals: returns 0 if $1 < $2
lt() { awk -v a="$1" -v b="$2" 'BEGIN { exit !(a < b) }'; }

for f in "$@"; do
    echo "=============================================================="
    echo "$f"
    echo "=============================================================="

    if [ ! -f "$f" ]; then
        echo "  MISSING: no such file"
        issues_total=$((issues_total + 1))
        continue
    fi

    probe=$(ffprobe -v error -select_streams a:0 \
        -show_entries stream=codec_name,sample_rate,channels,bits_per_raw_sample,bit_rate \
        -show_entries format=duration \
        -of default=noprint_wrappers=1 "$f" 2>/dev/null)

    if [ -z "$probe" ]; then
        echo "  UNREADABLE: ffprobe found no audio stream"
        issues_total=$((issues_total + 1))
        continue
    fi

    get() { echo "$probe" | grep "^$1=" | head -1 | cut -d= -f2-; }

    # ffprobe reports "N/A" for fields a container doesn't carry; blank those out
    # so later arithmetic and comparisons never see a non-numeric value.
    num() { case "$1" in ''|*[!0-9]*) echo "" ;; *) echo "$1" ;; esac; }

    codec=$(get codec_name)
    rate=$(num "$(get sample_rate)")
    chans=$(num "$(get channels)")
    bits=$(num "$(get bits_per_raw_sample)")
    bitrate=$(num "$(get bit_rate)")
    duration=$(get duration)
    [ -z "$bits" ] && bits="?"
    case "$duration" in ''|*[!0-9.]*) duration=0 ;; esac

    total_duration=$(awk -v a="$total_duration" -v b="$duration" 'BEGIN { printf "%.2f", a + b }')

    # volumedetect gives mean_volume and max_volume in dBFS.
    vol=$(ffmpeg -hide_banner -nostats -i "$f" -map 0:a:0 -af volumedetect -f null - 2>&1)
    mean=$(echo "$vol" | grep -o 'mean_volume: -\?[0-9.]*' | head -1 | awk '{print $2}')
    peak=$(echo "$vol" | grep -o 'max_volume: -\?[0-9.]*' | head -1 | awk '{print $2}')
    [ -z "$mean" ] && mean="?"
    [ -z "$peak" ] && peak="?"

    # Noise floor: the quietest short window in the first 30s, which is the level
    # during a pause between phrases. Meaningful only if the audio contains a pause.
    floor=$(ffmpeg -hide_banner -nostats -t 30 -i "$f" -map 0:a:0 \
        -af astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level \
        -f null - 2>&1 | grep -o '=-\?[0-9.]*' | tr -d '=' | sort -n | head -1)
    if [ -n "$floor" ]; then
        floor=$(awk -v x="$floor" 'BEGIN { printf "%.1f", x }')
    else
        floor="?"
    fi

    echo "  duration     $(fmt_hms "$duration")  (${duration%.*}s)"
    echo "  codec        $codec${bitrate:+ @ $((bitrate / 1000)) kbps}"
    echo "  sample rate  $rate Hz"
    echo "  bit depth    $bits"
    echo "  channels     $chans"
    echo "  mean (RMS)   $mean dBFS"
    echo "  true peak    $peak dBFS"
    echo "  noise floor  $floor dBFS (quietest window in first 30s)"
    echo ""

    issues=0
    note() { echo "  ! $1"; issues=$((issues + 1)); }

    if [ "$peak" != "?" ]; then
        if ! lt "$peak" "0.0"; then
            note "CLIPPED (peak $peak dBFS). Re-record. Normalizing cannot undo this."
        elif ! lt "$peak" "$PEAK_MAX"; then
            note "Peak $peak dBFS exceeds the -3 dBFS target. Reduce input gain and re-record."
        fi
    fi

    if [ "$mean" != "?" ]; then
        if lt "$mean" "$RMS_MIN"; then
            note "Quiet: RMS $mean dBFS, target $RMS_MIN..$RMS_MAX. Check mic distance before adding gain."
        elif ! lt "$mean" "$RMS_MAX"; then
            note "Hot: RMS $mean dBFS, target $RMS_MIN..$RMS_MAX."
        fi
    fi

    if [ -n "$rate" ] && [ "$rate" -le 16000 ] 2>/dev/null; then
        note "Sample rate ${rate} Hz is bandwidth-limited. The clone will sound muffled and this cannot be fixed later — set the recorder to 48 kHz and record again."
    elif [ -n "$rate" ] && [ "$rate" -lt 44100 ] 2>/dev/null; then
        note "Sample rate ${rate} Hz is below the recommended 44.1/48 kHz."
    fi

    case "$codec" in
        opus|amr_nb|amr_wb|gsm)
            note "Codec '$codec' is speech-optimized and lossy — this is not a clean recording chain. Note that Opus always reports a 48 kHz container rate regardless of true bandwidth, so the sample rate above does not clear it. Record to WAV instead." ;;
        aac|mp3)
            if [ -n "$bitrate" ] && [ "$bitrate" -lt 192000 ] 2>/dev/null; then
                note "Lossy $codec at $((bitrate / 1000)) kbps, below the 192 kbps ElevenLabs recommends. Typical of phone voice-memo apps. Record to WAV instead."
            fi ;;
    esac

    if [ "$floor" != "?" ] && [ "$mean" != "?" ]; then
        snr=$(awk -v m="$mean" -v f="$floor" 'BEGIN { printf "%.1f", m - f }')
        if lt "$snr" "10"; then
            # Floor never drops far below the mean, so no pause was found to measure
            # in. Continuous tone, heavy compression, or speech with no gaps.
            echo "  - Noise floor not measurable (no pause in the first 30s). Judge it by ear."
        elif lt "$snr" "35"; then
            note "Noise floor is high (only ${snr} dB below speech). Identify the source before re-recording, or the retake will match."
        fi
    fi

    if [ "$chans" -gt 1 ] 2>/dev/null; then
        echo "  - Multi-channel ($chans). Mono is preferred; downmix unless the channels differ meaningfully."
    fi

    [ "$issues" -eq 0 ] && echo "  OK — nothing outside spec."
    issues_total=$((issues_total + issues))
    echo ""
done

echo "=============================================================="
echo "TOTAL: $(fmt_hms "$total_duration") across $# file(s)"
if lt "$total_duration" "1800"; then
    echo "  ! Under the 30-minute minimum for professional cloning."
    echo "    Record more, or use instant cloning (1-3 minutes)."
    issues_total=$((issues_total + 1))
elif lt "$total_duration" "7200"; then
    echo "  Above the 30-minute minimum. ElevenLabs considers 2-3 hours optimal,"
    echo "  but consistent quality matters more than quantity."
else
    echo "  Well above the minimum."
fi

echo ""
if [ "$issues_total" -eq 0 ]; then
    echo "No issues flagged. Listen to a few minutes before uploading anyway."
else
    echo "$issues_total issue(s) flagged above. Resolve before spending a cloning slot."
fi
