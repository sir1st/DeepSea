import pathlib
from github import Github
from github.GithubException import GithubException
import urllib.request
import re
import logging

class GH():
    def __init__(self, ghToken):
        self.token = ghToken
        self.github = Github(self.token)

    def getReleaseAssetInfo(self, module):
        try:
            ghRepo = self.github.get_repo(module["repo"])
        except GithubException as e:
            raise RuntimeError(f"Unable to get repo {module['repo']}: {e.data}") from e
        
        releases = ghRepo.get_releases()
        if releases.totalCount == 0:
            raise RuntimeError(f"No available release for: {module['repo']}")
        ghLatestRelease = releases[0]

        assets = list(ghLatestRelease.get_assets())
        matched_assets = []
        unmatched_patterns = []
        for pattern in module["regex"]:
            matches = [asset for asset in assets if re.search(pattern, asset.name)]
            if matches:
                matched_assets.extend(matches)
            else:
                unmatched_patterns.append(pattern)

        if unmatched_patterns:
            asset_names = ", ".join(asset.name for asset in assets) or "no assets"
            patterns = ", ".join(unmatched_patterns)
            raise RuntimeError(
                f"{module['repo']} release {ghLatestRelease.tag_name} has no assets matching "
                f"{patterns}. Available assets: {asset_names}"
            )

        return ghLatestRelease, matched_assets

    def downloadReleaseAssets(self, module):
        ghLatestRelease, matched_assets = self.getReleaseAssetInfo(module)
        for asset in matched_assets:
            logging.info(f"[{module['repo']}] Downloading: {asset.name}")
            fpath = f"./base/{module['repo']}/"
            pathlib.Path(fpath).mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(asset.browser_download_url, f"{fpath}{asset.name}")
        return ghLatestRelease
