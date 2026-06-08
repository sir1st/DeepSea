import shutil, os, re, zipfile, glob
from pathlib import Path

class FS():
    VALID_STEPS = {
        "extract",
        "create_dir",
        "create_file",
        "replace_content",
        "delete",
        "copy",
        "move",
    }

    def __init__(self):
        shutil.rmtree("./base", ignore_errors=True)
        shutil.rmtree("./menv", ignore_errors=True)
        shutil.rmtree("./sd", ignore_errors=True)
        for elements in glob.glob(f"./*.zip"):
            os.remove(elements)

    def createSDEnv(self):
        shutil.rmtree("./sd", ignore_errors=True)
        Path("./sd").mkdir(parents=True, exist_ok=True)

    def createModuleEnv(self, module):
        shutil.rmtree("./menv", ignore_errors=True)
        Path("./menv").mkdir(parents=True, exist_ok=True)
        shutil.copytree(f"./base/{module['repo']}", f"./menv/", dirs_exist_ok=True)

    def finishModule(self):
        self.__copyToSD()
        shutil.rmtree("./menv", ignore_errors=True)

    def executeStep(self, module, step):
        if step["name"] not in self.VALID_STEPS:
            raise ValueError(f"Unknown step '{step['name']}' for {module['repo']}")

        if step["name"] == "extract":
            self.__extract(step["arguments"][0])
        elif step["name"] == "create_dir":
            self.__createDir(step["arguments"][0])
        elif step["name"] == "create_file":
            self.__createFile(step["arguments"][0], step["arguments"][1])
        elif step["name"] == "replace_content":
            self.__replaceFileContent(step["arguments"][0], step["arguments"][1], step["arguments"][2])
        elif step["name"] == "delete":
            self.__delete(step["arguments"][0])
        elif step["name"] == "copy":
            self.__copy(step["arguments"][0], step["arguments"][1])
        elif step["name"] == "move":
            self.__copy(step["arguments"][0], step["arguments"][1])
            self.__delete(step["arguments"][0])

    def __extract(self, source):
        path = f"./menv/"
        matches = []
        for filename in os.listdir(path):
            if re.search(source, filename):
                matches.append(filename)
        if not matches:
            raise FileNotFoundError(f"No file matching '{source}' in ./menv")

        target_root = Path(path).resolve()
        for filename in matches:
            assetPath = f"./menv/{filename}"
            with zipfile.ZipFile(assetPath, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    target = (target_root / member.filename).resolve()
                    if target_root not in target.parents and target != target_root:
                        raise ValueError(f"Refusing to extract unsafe path '{member.filename}'")
                zip_ref.extractall(path)
                self.__delete(filename)   

    def __delete(self, source):
        matches = glob.glob(f"./menv/{source}") or [f"./menv/{source}"]
        for element in matches:
            if not os.path.isdir(element):
                if os.path.exists(element):
                    os.remove(element)
            else:
                shutil.rmtree(element, ignore_errors=True)
    
    def __copy(self, source, dest):
        matches = glob.glob(f"./menv/{source}")
        if not matches:
            raise FileNotFoundError(f"No file or directory matching './menv/{source}'")

        dest_path = Path("./menv") / dest
        for elements in matches:
            source_path = Path(elements)
            if source_path.is_dir():
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            else:
                if dest_path.exists() and dest_path.is_dir():
                    shutil.copy(source_path, dest_path)
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(source_path, dest_path)
            break
    
    def __createDir(self, source):
        Path(f"./menv/{source}").mkdir(parents=True, exist_ok=True)
    
    def __createFile(self, source, content):
        Path(f"./menv/{source}").parent.mkdir(parents=True, exist_ok=True)
        with open(f"./menv/{source}", "w") as f:
            f.write(content)
    
    def __replaceFileContent(self, source, search, replace):
        path = f"./menv/{source}"
        with open(path, "rt") as fin:
            data = fin.read()
        if search not in data:
            raise ValueError(f"Unable to find replacement text in './menv/{source}': {search}")
        data = data.replace(search, replace)
        with open(path, "wt") as fin:
            fin.write(data)

    def __copyToSD(self):
        shutil.copytree("./menv", "./sd/", dirs_exist_ok=True)
