#!/usr/bin/env python3
"""Manta AirLab | Fabio Giuliodori | duilio.cc

# ______  _     _  ___  _       ___  ______      ____  ____
# |     \ |     |   |   |        |   |     |    |     |
# |_____/ |_____| __|__ |_____ __|__ |_____| .  |____ |____

Release helper for Manta Airfoil Tools.
Builds and cleans packaged Windows release artifacts for the project.

Usage:
  python release_tool/release_tool.py
  python release_tool/release_tool.py build
  python release_tool/release_tool.py build-exe
  python release_tool/release_tool.py build-installer
  python release_tool/release_tool.py clean
"""

from __future__ import annotations

import argparse
import io
import os
import stat
import shutil
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path) -> None:
    print(f"[run] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd), check=True)


def portable_exe_name(app_version: str) -> str:
    return f"Manta_Airfoil_Tools_portable_{app_version}.exe"


def _load_wizard_source_image(root: Path):
    try:
        from PIL import Image
    except Exception:
        return None

    for svg_path in (
        root / "images" / "logo_airfoil_tools.svg",
        root / "images" / "logo_manta_air_lab.svg",
    ):
        if svg_path.exists():
            try:
                import cairosvg

                png_bytes = cairosvg.svg2png(url=str(svg_path))
                if not isinstance(png_bytes, (bytes, bytearray)):
                    continue
                img = Image.open(io.BytesIO(bytes(png_bytes)))
                img.load()
                return img
            except Exception:
                pass

    for fallback in (
        root / "images" / "logo_airfoil_tools.png",
        root / "images" / "manta.jpg",
    ):
        if fallback.exists():
            try:
                img = Image.open(fallback)
                img.load()
                return img
            except Exception:
                continue
    return None


def _save_bmp_fit(img, target_size: tuple[int, int], out_path: Path) -> None:
    from PIL import Image

    width, height = target_size
    canvas = Image.new("RGB", (width, height), (245, 246, 248))
    src = img.convert("RGBA")
    src.thumbnail((max(width - 12, 1), max(height - 12, 1)), Image.Resampling.LANCZOS)
    pos = ((width - src.width) // 2, (height - src.height) // 2)
    canvas.paste(src, pos, src.split()[-1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="BMP")


def prepare_inno_graphics(root: Path) -> tuple[Path | None, Path | None]:
    img = _load_wizard_source_image(root)
    if img is None:
        return None, None

    assets_dir = root / "release_tool" / "dist" / "_inno_assets"
    large = assets_dir / "wizard_large.bmp"
    small = assets_dir / "wizard_small.bmp"
    _save_bmp_fit(img, (164, 314), large)
    _save_bmp_fit(img, (55, 55), small)
    return large, small


def _rmtree_onerror(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def remove_if_exists(path: Path, *, strict: bool = False) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path, onerror=_rmtree_onerror)
            print(f"Removed directory: {path}")
        elif path.is_file():
            path.unlink()
            print(f"Removed file: {path}")
    except Exception as exc:
        msg = f"Warning: unable to remove {path} ({exc})"
        if strict:
            raise RuntimeError(msg) from exc
        print(msg)


def cleanup_transient_artifacts(root: Path, *, strict: bool = False) -> None:
    for target in (
        root / "build",
        root / "release_tool" / "dist",
        root / "__pycache__",
        root / "release_tool" / "__pycache__",
    ):
        remove_if_exists(target, strict=strict)


def find_iscc(custom_path: str | None) -> Path:
    if custom_path:
        candidate = Path(custom_path).expanduser().resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"ISCC not found at: {candidate}")

    env_candidate = os.environ.get("INNO_ISCC_PATH", "").strip()
    if env_candidate:
        candidate = Path(env_candidate).expanduser().resolve()
        if candidate.exists():
            return candidate

    for candidate in (
        shutil.which("ISCC.exe"),
        shutil.which("iscc"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ):
        if candidate and Path(candidate).exists():
            return Path(candidate).resolve()

    raise FileNotFoundError(
        "Inno Setup compiler (ISCC.exe) not found. Install Inno Setup 6 or pass --iscc-path."
    )


def do_build_exe(root: Path, app_version: str) -> Path:
    req_file = root / "release_tool" / "requirements-build.txt"
    spec_file = root / "release_tool" / "manta-airfoil-tools.spec"

    if not req_file.exists():
        raise FileNotFoundError(f"Missing requirements file: {req_file}")
    if not spec_file.exists():
        raise FileNotFoundError(f"Missing PyInstaller spec file: {spec_file}")

    run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], cwd=root)
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_file)], cwd=root)

    base_out_file = root / "dist" / "Manta_Airfoil_Tools_portable.exe"
    out_file = root / "dist" / portable_exe_name(app_version)
    if base_out_file.exists():
        if out_file.exists():
            out_file.unlink()
        base_out_file.replace(out_file)
    if out_file.exists():
        print(f"Executable completed: {out_file}")
    else:
        print("Executable build completed. Check dist/ for generated artifacts.")
    return out_file


def do_build_installer(root: Path, app_version: str, iscc_path: str | None) -> Path:
    iss_file = root / "release_tool" / "manta-airlab-installer.iss"
    exe_file = root / "dist" / portable_exe_name(app_version)
    if not iss_file.exists():
        raise FileNotFoundError(f"Missing Inno Setup script file: {iss_file}")
    if not exe_file.exists():
        raise FileNotFoundError(f"Missing executable for installer: {exe_file}. Run build-exe first.")

    iscc = find_iscc(iscc_path)
    icon_path = root / "images" / "ico.ico"
    wizard_large, wizard_small = prepare_inno_graphics(root)
    define_args = [
        f"/DAppVersion={app_version}",
        f"/DAppExePath={exe_file}",
        f"/DAppExeName={exe_file.name}",
    ]
    if icon_path.exists():
        define_args.append(f"/DAppSetupIconPath={icon_path}")
    if wizard_large is not None and wizard_large.exists():
        define_args.append(f"/DAppWizardImageBmpPath={wizard_large}")
    if wizard_small is not None and wizard_small.exists():
        define_args.append(f"/DAppWizardSmallImageBmpPath={wizard_small}")
    run(
        [
            str(iscc),
            f"/O{root / 'dist'}",
            *define_args,
            str(iss_file),
        ],
        cwd=root,
    )

    setup_file = root / "dist" / f"Manta_Airfoil_Tools_setup_{app_version}.exe"
    if setup_file.exists():
        print(f"Installer completed: {setup_file}")
    else:
        print("Installer build finished. Check dist/ for generated setup executable.")
    return setup_file


def do_build(root: Path, app_version: str, iscc_path: str | None) -> None:
    try:
        do_build_exe(root, app_version=app_version)
        do_build_installer(root, app_version=app_version, iscc_path=iscc_path)
    finally:
        cleanup_transient_artifacts(root)


def do_clean(root: Path) -> None:
    targets = [
        root / "build",
        root / "dist",
        root / "manta-airfoil-tools.spec",
        root / "__pycache__",
        root / "release_tool" / "__pycache__",
        root / "release_tool" / "dist",
    ]

    for target in targets:
        remove_if_exists(target, strict=False)

    print("Clean completed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and clean Manta Airfoil Tools release artifacts",
        epilog="Manta Airfoil Tools | Manta Airlab | Fabio Giuliodori | Duilio.cc",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="build",
        choices=["build", "build-exe", "build-installer", "clean"],
        help="Action to execute (default: build)",
    )
    parser.add_argument(
        "--app-version",
        default="1.0.0",
        help="Installer version string for Inno Setup (default: 1.0.0)",
    )
    parser.add_argument(
        "--iscc-path",
        default=None,
        help="Optional explicit path to ISCC.exe",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    if args.command == "build":
        do_build(root, app_version=args.app_version, iscc_path=args.iscc_path)
    elif args.command == "build-exe":
        try:
            do_build_exe(root, app_version=args.app_version)
        finally:
            cleanup_transient_artifacts(root)
    elif args.command == "build-installer":
        try:
            do_build_installer(root, app_version=args.app_version, iscc_path=args.iscc_path)
        finally:
            cleanup_transient_artifacts(root)
    elif args.command == "clean":
        do_clean(root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
