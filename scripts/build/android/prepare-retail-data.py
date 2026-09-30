#!/usr/bin/env python3
"""Validate owned Generals archives and prepare hash-checked release assets.

The output directory is intentionally gitignored. This script never publishes
the files; upload requires a separate, deliberate release step.
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit


ZH_REQUIRED = {"inizh.big", "terrainzh.big", "textureszh.big", "w3dzh.big", "windowzh.big"}
BASE_REQUIRED = {
    "ini.big", "terrain.big", "textures.big", "w3d.big", "window.big",
    "shaders.big", "audio.big", "speech.big", "maps.big", "music.big",
}
ZH_PATCH_ARCHIVES = {"patchdata.big", "patchini.big", "patchwindow.big"}


def is_zh_archive(name: str) -> bool:
    lower = name.lower()
    return lower.endswith("zh.big") or lower in ZH_PATCH_ARCHIVES


def archives_in(folder: Path, required: set[str], label: str, zero_hour: bool) -> list[Path]:
    if not folder.is_dir():
        raise ValueError(f"{label} directory does not exist: {folder}")
    archives = sorted(
        (item for item in folder.iterdir()
         if item.is_file() and item.suffix.lower() == ".big"
         and is_zh_archive(item.name) == zero_hour),
        key=lambda item: item.name.lower(),
    )
    names = [item.name.lower() for item in archives]
    if len(names) != len(set(names)):
        raise ValueError(f"{label} has duplicate archive names differing only by case")
    missing = sorted(required - set(names))
    if missing:
        raise ValueError(f"{label} is missing: {', '.join(missing)}")
    for item in archives:
        with item.open("rb") as stream:
            if stream.read(4) != b"BIGF":
                raise ValueError(f"Invalid BIGF header: {item}")
        if item.stat().st_size < 16:
            raise ValueError(f"Truncated archive: {item}")
    return archives


def sha256_and_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zh", type=Path, required=True, help="Zero Hour archive directory")
    parser.add_argument("--base", type=Path, help="Base Generals directory; defaults to --zh")
    parser.add_argument("--base-url", help="Optional HTTPS directory URL; default uses relative URLs")
    parser.add_argument("--version", default="game-data-v1", help="Immutable data version")
    parser.add_argument("--output", type=Path, help="Empty directory for manifest and optional assets")
    parser.add_argument("--copy-assets", action="store_true", help="Copy archives to --output")
    args = parser.parse_args()

    if args.base_url:
        url = urlsplit(args.base_url)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.query or url.fragment or not args.base_url.endswith("/")):
            parser.error("--base-url must be an HTTPS directory URL without credentials or query")
    if args.copy_assets and not args.output:
        parser.error("--copy-assets requires --output")
    try:
        groups = [
            ("zh", Path("."), archives_in(args.zh, ZH_REQUIRED, "Zero Hour", True)),
            ("base", Path("ZH_Generals"), archives_in(
                args.base or args.zh, BASE_REQUIRED, "Base Generals", False)),
        ]
        source_files = [item for _, _, files in groups for item in files]
        output = args.output.resolve() if args.output else None
        if output is not None:
            if output.exists() and any(output.iterdir()):
                raise ValueError(f"Output directory must be empty: {output}")
            for source in source_files:
                if output == source.parent.resolve() or output in source.resolve().parents:
                    raise ValueError("Output directory must not contain source archives")

        manifest = {"schema": 1, "version": args.version, "files": []}
        total = 0
        for prefix, subdir, files in groups:
            for source in files:
                digest, size = sha256_and_size(source)
                asset_name = f"{prefix}-{source.name}"
                relative_path = (subdir / source.name).as_posix()
                if relative_path.startswith("./"):
                    relative_path = relative_path[2:]
                manifest["files"].append({
                    "path": relative_path,
                    "url": (args.base_url or "") + quote(asset_name),
                    "size": size,
                    "sha256": digest,
                })
                total += size
                if output is not None and args.copy_assets:
                    output.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, output / asset_name)
                print(f"{relative_path}: {size:,} bytes, SHA-256 {digest}")

        if output is not None:
            output.mkdir(parents=True, exist_ok=True)
            manifest["total_bytes"] = total
            (output / "game-data-manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
        print(f"Validated {len(manifest['files'])} archives, {total:,} bytes total")
        return 0
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
