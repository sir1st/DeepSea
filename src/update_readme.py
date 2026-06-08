import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "src" / "settings.json"
README = ROOT / "README.md"
BEGIN = "<!-- BEGIN MODULE TABLE -->"
END = "<!-- END MODULE TABLE -->"

MODULE_METADATA = {
    "aioupdater": ("AIO-switch-updater", "https://github.com/HamletDuFromage/aio-switch-updater"),
    "atmosphere": ("Atmosphere", "https://github.com/Atmosphere-NX/Atmosphere"),
    "deepseaassets": ("DeepSea Assets", "https://github.com/Team-Neptune/DeepSea-Assets"),
    "deepseacleaner": ("DeepSea Cleaner", "https://github.com/Team-Neptune/DeepSea-Cleaner"),
    "deepseacpr": ("DeepSea CPR", "https://github.com/Team-Neptune/CommonProblemResolver"),
    "deepseatoolbox": ("DeepSea Toolbox", "https://github.com/Team-Neptune/DeepSea-Toolbox"),
    "edizon": ("EdiZon-SE", "https://github.com/tomvita/EdiZon-SE"),
    "edizon-ovl": ("EdiZon-Overlay", "https://github.com/proferabg/EdiZon-Overlay"),
    "emuiibo": ("Emuiibo", "https://github.com/XorTroll/emuiibo"),
    "goldleaf": ("Goldleaf", "https://github.com/XorTroll/Goldleaf"),
    "hbappstore": ("Homebrew App Store", "https://github.com/fortheusers/hb-appstore"),
    "hekate": ("Hekate", "https://github.com/CTCaer/hekate"),
    "jksv": ("JKSV", "https://github.com/J-D-K/JKSV"),
    "ldn_mitm": ("ldn_mitm", "https://github.com/spacemeowx2/ldn_mitm"),
    "missioncontrol": ("MissionControl", "https://github.com/ndeadly/MissionControl"),
    "nxovlloader": ("nx-ovlloader", "https://github.com/WerWolv/nx-ovlloader"),
    "nxshell": ("NX-Shell", "https://github.com/joel16/NX-Shell"),
    "ovlsysmodules": ("ovlSysmodules", "https://github.com/WerWolv/ovl-sysmodules"),
    "sphaira": ("Sphaira", "https://github.com/ITotalJustice/sphaira"),
    "statusmonitoroverlay": ("Status Monitor Overlay", "https://github.com/masagrator/Status-Monitor-Overlay"),
    "sysclk": ("sys-clk", "https://github.com/retronx-team/sys-clk"),
    "syscon": ("sys-con", "https://github.com/cathery/sys-con"),
    "sysftpd": ("sys-ftpd", "https://github.com/cathery/sys-ftpd"),
    "tegraexplorer": ("TegraExplorer", "https://github.com/suchmememanyskill/TegraExplorer"),
    "teslamenu": ("Tesla-Menu", "https://github.com/WerWolv/Tesla-Menu"),
}

TABLE_PACKAGES = ["advanced", "normal", "minimal"]


def ordered_modules(settings):
    seen = []
    for package_name in TABLE_PACKAGES:
        package = next(p for p in settings["packages"] if p["name"] == package_name)
        for module in package["modules"]:
            if module not in seen:
                seen.append(module)
    return seen


def render_table(settings):
    packages = {package["name"]: set(package["modules"]) for package in settings["packages"]}
    lines = [
        BEGIN,
        "| Software | Advanced Package | Normal Package | Minimal Package |",
        "| -------- | :--------------: | :------------: | :-------------: |",
    ]
    for module in ordered_modules(settings):
        label, url = MODULE_METADATA[module]
        cells = ["yes" if module in packages[name] else "" for name in TABLE_PACKAGES]
        checks = ["✅" if cell else "" for cell in cells]
        lines.append(f"| [{label}]({url}) | {checks[0]} | {checks[1]} | {checks[2]} |")
    lines.append(END)
    return "\n".join(lines)


def main():
    settings = json.loads(SETTINGS.read_text())
    missing = set(settings["moduleList"]) - set(MODULE_METADATA)
    if missing:
        raise SystemExit(f"Missing README metadata for modules: {', '.join(sorted(missing))}")

    readme = README.read_text()
    if BEGIN not in readme or END not in readme:
        raise SystemExit("README module table markers are missing")

    before = readme.split(BEGIN, 1)[0]
    after = readme.split(END, 1)[1]
    README.write_text(before + render_table(settings) + after)


if __name__ == "__main__":
    main()
