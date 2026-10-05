# inFAMOUS (PS3) decompilation

Rebuilding inFAMOUS (Sucker Punch, 2009, PS3, `BCUS-98119`) as source code that
compiles back to the same machine code as the retail game, then running it
natively on PC.

The game was built with GCC 4.1.1, not Sony's own compiler. That is what makes a
matching decompilation possible: the original compiler can be pinned and rerun,
so a rewritten function either produces the same bytes or it doesn't.

**Live status and devlog:** <https://bucketcomps.github.io/infamous/>
**Wiki:** <https://github.com/bucketcomps/infamous/wiki>

## How it works

- **Functions are proven one at a time.** A function counts only when its C
  recompiles to the exact retail bytes, or when it matches the original's
  behaviour across thousands of test inputs and a do-nothing stub fails the
  same test. Every proof is re-checked by a second, independent reviewer before
  it counts. Where something isn't known, the records say so.
- **A runtime that boots the real game.** Our own PPU/SPU runtime runs the
  game's code, including Sony's SPURS job system and the game's own SPU
  programs. It currently boots into the intro movie, decoded by the game's own
  video code. It is slow for now; it exists to find and prove behaviour, not to
  play on.
- **A clean-room renderer.** The game's RSX graphics commands are translated to
  Vulkan. It has drawn the Sony and Sucker Punch splash screens from the game's
  own draw calls.
- **Real hardware where it matters.** Some Cell instructions only promise an
  approximate answer. We measured what a real PS3 returns (844,920 results from
  a retail CECHL01) and model those exact bits.

## What's in this repo

Right now: the public devlog site and wiki. No code yet.

The plan is to release a recompiled build here first, then replace it piece by
piece with decompiled source as each part is proven and tested. More people
testing on more machines is how the bugs get found.

## Got a PS3? Help out

If you have a PS3 on HEN or CFW, one run of our
[hardware probe](https://github.com/bucketcomps/ps3-hwprobe) records exactly
what your console's Cell CPU returns for instructions that emulators still guess
at. It takes about 20 minutes and writes one file.

- [Download the probe (`cell-hwprobe.gnpdrm.pkg`, v1)](https://github.com/bucketcomps/ps3-hwprobe/releases/latest)
- [How to run it](https://github.com/bucketcomps/ps3-hwprobe#run-it)
- [Send your results](https://github.com/bucketcomps/ps3-hwprobe/issues/new?template=submit-results.yml)

Every model helps: fat, slim and super slim.

## Related public tools

- [xpp-tool](https://github.com/deucebucket/infamous-xpp-textures): extract,
  edit and repack the game's textures and models (`.xpp` packages).
- [rpcs3-repro](https://github.com/deucebucket/rpcs3-repro): an RPCS3 fork that
  only changes behaviour where real PS3 hardware was measured to differ.

## What you need

Your own legally obtained copy of the game. Nothing here contains game code,
assets, keys or firmware, and nothing ever will.

---

inFAMOUS is a trademark of Sony Interactive Entertainment. This is an
independent fan project by DeuceBucket, not affiliated with Sony or Sucker Punch.
