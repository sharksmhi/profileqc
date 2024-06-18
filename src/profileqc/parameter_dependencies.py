import pathlib
import json

CONFIG_PATH = pathlib.Path(__file__).parent / 'etc' / 'parameter_dependencies.json'


class ParameterDependencies:
    def __init__(self):
        self._config: dict = {}
        self._load_config()

    def _load_config(self) -> None:
        with open(CONFIG_PATH) as fid:
            self._config = json.load(fid)

    def get_dependent_parameters(self, par: str) -> list[str]:
        return self._config.get(par, [])


if __name__ == '__main__':
    pd = ParameterDependencies()

