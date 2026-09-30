# Android game data delivery

## Current behavior

The Android APK contains the engine, launcher, fonts, runtime settings, and an
optional Vulkan driver. It does not contain the retail game archives. Setup
asks the player to select a folder containing `INIZH.big` or `INI.big`, writes
`gamedata_path.txt`, and the native engine uses that folder on launch.

The presence check alone is not proof of a playable installation. Setup also
checks archive headers and expects the base Generals assets, notably
`Terrain.big`, `Textures.big`, and `W3D.big`. An expansion-only copy can reach
the launcher but miss artwork. GeneralsOnline has a separate, existing
download for its community patch and maps; that download is not a source for
the retail archives.

## Delivery design

Keep the source repository free of retail archives. Two delivery modes can
share one device-side installer:

1. **Locally bundled data:** During a personal build, stage an authorized
   complete game-data directory outside Git. The packaging step includes it in
   the APK if its total size fits the selected Android distribution format.
2. **First-run download:** Publish the same data through an authorized HTTPS
   endpoint outside the source repository. A small manifest lists each file's
   relative path, byte length, and SHA-256. Download into temporary files and
   verify before making the installation active.

For either mode, install into an app-owned directory on a worker thread with
visible progress, preserve the base Generals subdirectory layout, and write
`gamedata_path.txt` only after complete validation. Keep Setup's existing
folder picker for players who already have a copy on the phone. Do not use the
GeneralsOnline community-data installer for the retail archives: it has a
different source, destination, and update contract.

## Information needed before implementation

- The local path to the authorized game-data directory or its download URL.
- Whether the authorization covers public distribution of the original game
  data, or only private/personal builds.
- Total size and the actual directory layout, including base Generals files.

## Network validation after an installable build

GeneralsOnline multiplayer is implemented in the fork. Retail LAN uses the
legacy UDP lobby on port 8086 and remains unverified on Android. Test
Android-to-Android on one Wi-Fi network first, then Android-to-PC with matching
game data and simulation rate. Test internet play separately through
GeneralsOnline. Preserve engine logs and a replay for any desync.
