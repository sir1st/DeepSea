import logging, json, argparse, shutil, os
from pathlib import Path
from gh import GH
from fs import FS
logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
logging.getLogger().setLevel(logging.INFO)

def loadSettings():
  scriptDir = Path(__file__).resolve().parent
  os.chdir(scriptDir)
  with open('./settings.json', 'r') as f:
    return json.load(f)

def getNeededModules(settings):
  neededModules = []
  for package in settings["packages"]:
    if package["active"]:
      for module in package["modules"]:
        if module not in settings["moduleList"]:
          raise KeyError(f"Package {package['name']} references unknown module: {module}")
        if module not in neededModules:
          neededModules.append(module)
  return neededModules

def validateSettings(settings):
  for package in settings["packages"]:
    if not package["modules"]:
      raise ValueError(f"Package {package['name']} has no modules")

  for moduleName, module in settings["moduleList"].items():
    if not module.get("repo"):
      raise ValueError(f"Module {moduleName} is missing repo")
    if not module.get("regex"):
      raise ValueError(f"Module {moduleName} is missing regex")
    for step in module.get("steps", []):
      if step["name"] not in FS.VALID_STEPS:
        raise ValueError(f"Module {moduleName} has unknown step: {step['name']}")

def validateReleaseAssets(github, settings):
  for moduleName in getNeededModules(settings):
    module = settings["moduleList"][moduleName]
    release, assets = github.getReleaseAssetInfo(module)
    assetNames = ", ".join(asset.name for asset in assets)
    logging.info(f"[{module['repo']}] {release.tag_name}: {assetNames}")

COMMON_REQUIRED_PATHS = [
  "atmosphere/config/system_settings.ini",
  "atmosphere/reboot_payload.bin",
  "bootloader/update.bin",
]

MODULE_REQUIRED_PATHS = {
  "deepseatoolbox": ["switch/DeepSea-Toolbox/DeepSeaToolbox.nro"],
  "goldleaf": ["switch/Goldleaf/Goldleaf.nro"],
  "jksv": ["switch/jksv/JKSV.nro"],
  "ldn_mitm": ["atmosphere/contents/4200000000000010/toolbox.json"],
  "nxovlloader": ["atmosphere/contents/420000000007E51A/exefs.nsp"],
  "ovlsysmodules": ["switch/.overlays/ovlSysmodules.ovl"],
  "sphaira": ["switch/sphaira/sphaira.nro"],
  "sysftpd": ["config/sys-ftpd/config.ini"],
}

def verifyPackage(package):
  requiredPaths = list(COMMON_REQUIRED_PATHS)
  for moduleName in package["modules"]:
    requiredPaths.extend(MODULE_REQUIRED_PATHS.get(moduleName, []))

  missing = [path for path in requiredPaths if not Path("./sd", path).exists()]
  if missing:
    missingPaths = ", ".join(missing)
    raise FileNotFoundError(f"Package {package['name']} is missing required paths: {missingPaths}")

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description="Team Neptune's DeepSea build script.")
  requiredNamed = parser.add_argument_group('Options required to build a release candidate')
  requiredNamed.add_argument('-gt', '--githubToken', help='Github Token')
  parser.add_argument('--dry-run', action='store_true', help='Validate settings and release assets without downloading or packaging')
  args = parser.parse_args()

  token = args.githubToken or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
  if not token:
    parser.error("A GitHub token is required via --githubToken, GITHUB_TOKEN, or GH_TOKEN")

  settings = loadSettings()
  validateSettings(settings)
  github = GH(token)

  if args.dry_run:
    validateReleaseAssets(github, settings)
    logging.info("Dry run completed successfully.")
    raise SystemExit(0)

  sdcard = FS()
  neededModules = getNeededModules(settings)

  for i in neededModules:
    module = settings["moduleList"][i]
    github.downloadReleaseAssets(module)


  for package in settings["packages"]:
    if package["active"]:
      logging.info(f"[{package['name']}] Creating package")
      sdcard.createSDEnv()

      for i in package["modules"]:
        module = settings["moduleList"][i]
        logging.info(f"[{package['name']}][{module['repo']}] Creating module env")
        sdcard.createModuleEnv(module)
        for step in module["steps"]:
          logging.info(f"[{package['name']}][{module['repo']}] Executing step: {step['name']}")
          sdcard.executeStep(module, step)
        
        logging.info(f"[{package['name']}][{module['repo']}] Moving MENV to SD")
        sdcard.finishModule()
      
      logging.info(f"[{package['name']}] All modules processed.")
      verifyPackage(package)
      logging.info(f"[{package['name']}] Creating ZIP")
      shutil.make_archive(f"deepsea-{package['name']}_v{settings['releaseVersion']}", 'zip', "./sd")
