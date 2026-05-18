# First Recording

This is the fastest path to a first clone that still sounds like you.

## Use this setup

- Record in `Voice Memos` or `QuickTime Player`
- Use wired earbuds or your laptop mic if that is all you have
- Pick the quietest soft-furnished room you can
- Speak a little slower and calmer than normal conversation

## Aim for one strong take

For the first run, do this:

- `10` to `20` seconds
- one take
- natural pacing
- no background music
- no keyboard clicks

## Read this, naturally

Use the script in:

- [`data/voice_refs/jean_reference_script.txt`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/data/voice_refs/jean_reference_script.txt)

Do not perform it like an announcer. The best reference clip sounds like your normal speaking voice on a very good day.

## Save the raw file

Examples:

- `data/voice_refs/jean_raw_take_01.m4a`
- `data/voice_refs/jean_raw_take_01.wav`

## Prep it for cloning

```bash
.venv/bin/avatar-clone prep-audio \
  --input data/voice_refs/jean_raw_take_01.m4a \
  --output data/voice_refs/jean_ref_take_01.wav
```

That command:

- trims dead air at the start and end
- converts to mono
- normalizes loudness
- writes a clean `wav`

## Save the transcript beside it

Create:

- `data/voice_refs/jean_ref_take_01.txt`

And paste the exact words you actually said, including any small mistakes or restarts if they made it into the final clip.

## Best first test pair

For your first end-to-end run, use:

- portrait: [`data/portraits/jean_headshot_1024.png`](/Users/jmoncayopursuit.org/Desktop/Personal_Avatar/data/portraits/jean_headshot_1024.png)
- audio: `data/voice_refs/jean_ref_take_01.wav`

## If the first clone sounds off

- Too robotic: rerecord with warmer pacing and fewer clipped consonants
- Too generic: use a slightly longer reference clip, around `15` to `20` seconds
- Too breathy or noisy: move farther from walls and turn off fans
