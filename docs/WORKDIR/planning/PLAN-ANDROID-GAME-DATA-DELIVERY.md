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

Keep the source repository free of retail archives. The chosen delivery mode is
a first-run download from the user's VPS over HTTPS. A small manifest lists
each file's relative path, byte length, and SHA-256. Download into temporary
files and verify before making the installation active. The same manifest can
support a locally bundled build later if needed.

Install into an app-owned directory on a worker thread with visible progress,
preserve the base Generals subdirectory layout, and write
`gamedata_path.txt` only after complete validation. Keep Setup's existing
folder picker for players who already have a copy on the phone. Do not use the
GeneralsOnline community-data installer for the retail archives: it has a
different source, destination, and update contract.

## Source data and VPS audit

The supplied folder, `C:\lan`, now contains 34 `BIGF` archives totaling
2,076,166,791 bytes: Zero Hour and base Generals archives in one directory.
Public distribution of the retail data has been authorized by the user for
this project. The assets will be served from the user's VPS after a read-only
audit identifies an isolated location that cannot affect other services.
The configured `evaenergy-vps` SSH host currently fails host-key verification;
no remote audit or upload has occurred. Verify the current key through the VPS
provider before using SSH. The audit must remain read-only and identify a new
directory and web route without changing other projects or shared services.

`scripts/build/android/prepare-retail-data.py` checks the archive set and
creates a SHA-256 manifest for individually named VPS assets. Keep any output
in the gitignored `retail-game-data/` directory. Each asset can be fetched
independently on a retry; the manifest is the contract for the device-side
installer. Do not upload anything until the VPS audit is complete.

## Network validation after an installable build

GeneralsOnline multiplayer is implemented in the fork. Retail LAN uses the
legacy UDP lobby on port 8086 and remains unverified on Android. Test
Android-to-Android on one Wi-Fi network first, then Android-to-PC with matching
game data and simulation rate. Test internet play separately through
GeneralsOnline. Preserve engine logs and a replay for any desync.
