import requests
from requests.auth import HTTPBasicAuth
import re
import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from hurry.filesize import size
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
import asyncio
import math


class MvnRepositoryHandler:
    cred = None
    nexus_url = None
    repository = None
    dryRun = None

    version_pattern = r'(\d*\.?\d*\.?\d*)'
    date_pattern = r"(\d{8}\.\d{6})"
    snapshot_finder = re.compile(version_pattern + r"-?" + date_pattern + r"?-?\d*")

    def __init__(self, user, password, nexus_url, repository, dry_run=False, parallelism=20):
        self.cred = HTTPBasicAuth(user, password)
        self.nexus_url = nexus_url
        self.repository = repository
        self.dryRun = dry_run
        self.versions_cache = {}
        self.parallelism = parallelism
        self.console = Console()

    def _get_all_components(self, token=None):
        params = {'repository': self.repository}
        if token:
            params['continuationToken'] = token
        response = requests.get(self.nexus_url + "v1/components", auth=self.cred,
                                params=params, headers={'accept': 'application/json'})
        response.raise_for_status()
        return response

    def _search_components(self, token=None, name=None, group=None, version=None):
        params = {'repository': self.repository}
        if token:
            params['continuationToken'] = token
        if name:
            params['maven.artifactId'] = name
        if group:
            params['maven.groupId'] = group
        if version:
            params['maven.baseVersion'] = version
        response = requests.get(self.nexus_url + "v1/search", auth=self.cred,
                                params=params, headers={'accept': 'application/json'})
        response.raise_for_status()
        return response

    def _get_components_as_list(self, fun, **args) -> list:
        response = fun(**args)
        components = self._fill_tmp_array_from_json(response.json())
        with self.console.status("[bold green]Gathering components metadata...") as status:
            while 'continuationToken' in response.json() and response.json()['continuationToken']:
                response = fun(token=response.json()['continuationToken'], **args)
                components += (self._fill_tmp_array_from_json(response.json()))
        return components

    def show_all_components(self, with_size=True) -> None:
        components = self._get_components_as_list(self._get_all_components)
        aggregates_components, total_size = self.aggregates_components(components, with_size)

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="dim")
        table.add_column("Versions")
        for k, v in aggregates_components.items():
            table.add_row(k, ", ".join(v))
        self.console.print(table)
        self.console.print("Total size : " + size(total_size))

    def aggregates_components(self, components: list, with_size: bool) -> tuple:
        aggregates = {} # Map as {"group:id":{"version1":size1,"version2":size2}}
        total_size = 0

        def _add_to_aggregates(key, version, comp_size=None):
            if key in aggregates:
                if version in aggregates[key]:
                    #aggregate size
                    aggregates[key][version] += comp_size
                else:
                    aggregates[key][version] = comp_size
            else:
                aggregates[key] = {}
                aggregates[key][version] = comp_size

        async def _handle_components(x, with_size):
            comp_size = None
            if with_size:
                comp_size = await loop.run_in_executor(None, self._components_size, x)
                nonlocal total_size
                total_size += comp_size
            key = x["group"] + ":" + x["name"]
            match = regex.match(x["version"])
            if match:
                # Check if snapshot
                version = match.group(1)
                if match.group(2):
                    version += "-SNAPSHOT"
                _add_to_aggregates(key, version, comp_size)
            else:
                if re.compile(r"^[0-9\.]*").match(x["version"]):
                    _add_to_aggregates(key, x["version"], comp_size)
                else:
                    print(x["version"] + " ignored")

        regex = re.compile(r"^(.*)-" + self.date_pattern + r"-?\d*")

        with Progress() as progress:
            ceil = math.ceil(len(components) / self.parallelism)
            gather_data = progress.add_task("[green]Gathering size data ....", total=ceil)

            for batch in self.batch_generator(components, self.parallelism):
                tasks = [_handle_components(x, with_size) for x in batch]
                loop = asyncio.get_event_loop()
                loop.run_until_complete(asyncio.gather(*tasks))
                progress.update(gather_data, advance=1)


        aggregate_as_string = {} # {"group:id":{"version1 [size1],"version2 [size2]"}}
        for k,v in aggregates.items():
            for k2,v2 in v.items():
                if k not in aggregate_as_string:
                    aggregate_as_string[k] = set()
                aggregate_as_string[k].add(k2+" [" + size(v2) + "]")
        return aggregate_as_string, total_size

    def _fill_tmp_array_from_json(self, json) -> list:
        components = []
        for item in json['items']:
            # print(item)
            components.append(
                {'name': item['name'], 'version': item['version'], 'id': item['id'], 'group': item['group'],
                 'assets': item['assets']})
        return components

    def _components_size(self, component: dict) -> int:
        """
        Aggregate size of all assets of a nexus component
        :param component:
        :return: the size in bytes
        """
        size = 0
        with FuturesSession() as session:

            futures = []
            for asset in component['assets']:
                futures.append(session.head(asset['downloadUrl'], auth=self.cred))
            for future in as_completed(futures):
                resp = future.result()
                size += int(resp.headers['Content-Length'])
        return size

    def delete_all_components(self) -> None:
        """
        Delette all components in the registry
        :return: None
        """
        components = self._get_components_as_list(self._get_all_components)
        self._delete_components_in_array(components)

    def _delete_component(self, id: str):
        if not self.dryRun:
            response = requests.delete(self.nexus_url + "v1/components/" + id, auth=self.cred)
            response.raise_for_status()

    def delete_all_component_by_version_pattern(self, version_pattern: str):
        self._delete_components_in_array(
            self._filter_components_by_version_pattern(self._get_components_as_list(self._get_all_components),
                                                       version_pattern))

    def _delete_components_in_array(self, components: list) -> None:
        """
        If dryrun is True, only display which component should be deleted
        :param components: component to delete
        :return: None
        """
        total_size = 0

        async def _handle_components(comp):
            comp_size = self._components_size(comp)
            nonlocal total_size
            total_size += comp_size
            if self.dryRun:
                self.console.print(
                    "deleting " + comp['name'] + ':' + comp['version'] + ' ' + size(comp_size))
            else:
                self._delete_component(comp['id'])

        with Progress() as progress:
            ceil = math.ceil(len(components) / self.parallelism)
            gather_data = progress.add_task("[green]Deleting components ....", total=ceil, visible=not self.dryRun)

            for batch in self.batch_generator(components, self.parallelism):
                tasks = [_handle_components(x) for x in batch]
                # for x in components:
                #    _handle_components(x)
                loop = asyncio.get_event_loop()
                loop.run_until_complete(asyncio.gather(*tasks))
                progress.update(gather_data, advance=1)

        self.console.print("Free memory :[bold]" + size(total_size) + "[/bold]")

    def delete_all_components_by_version(self, version):
        self._delete_components_in_array(self._get_components_as_list(self._search_components, version=version))

    def _filter_components_by_version_pattern(self, components: list, pattern: str):
        """

        :param components: componenet list to filter
        :param pattern: pattern to match
        :return: component list that matchthe pattern
        """

        patched_pattern = "^" + pattern
        comp = re.compile(patched_pattern)

        def matcher(component):
            m = comp.match(component['version'])
            if m is not None:
                return component

        return [v for v in map(matcher, components) if v is not None]

    def keep_lasts_versions(self, last_version_count: int) -> None:
        """
        Conserve les dernière versions des artefacts
        :param last_version_count:
        """

        all_artefacts = self._get_components_as_list(self._get_all_components)
        artefact_to_keep = self._get_last_versions(all_artefacts, last_version_count)
        artefact_to_delete = [item for item in all_artefacts if item not in artefact_to_keep]
        self._delete_components_in_array(artefact_to_delete)

    def _get_last_versions(self, components: list, last_version_count: int):
        for component in components:
            self._get_most_recent_artefact_for_version(component)

        version_by_component = {}

        for k, v in self.versions_cache.items():
            if k[0] not in version_by_component:
                version_by_component[k[0]] = {k[1]: v["component"]}
            else:
                version_by_component[k[0]][k[1]] = v["component"]

        print(version_by_component)
        to_return = []
        for k, v in version_by_component.items():
            to_return += map(lambda x: x[1], sorted(v.items(), reverse=True)[0:int(last_version_count)])

        return to_return

    # TODO mettre version_cache et _get_most_recent_artefact_for_version dans une autre classe
    # versions_cache = {}  # exemple : {(group:name,2.1.1):{"date":date,"version":"2.1.1-20201208.134457-2"}}

    def _get_most_recent_artefact_for_version(self, component: dict) -> None:
        """
        Utilisé pour les snapshots pour lesquels plusieurs artefacts existent pour la même version
        :param component: dict
        :return: None
        """
        dategroup = self.snapshot_finder.match(component["version"])
        short_version = dategroup.group(1)
        key = (component["group"] + ":" + component["name"], short_version)
        if dategroup.group(2):
            date = datetime.datetime.strptime(dategroup.group(2), '%Y%m%d.%H%M%S')
            if (key in self.versions_cache and date > self.versions_cache[key][
                "date"]) or key not in self.versions_cache:
                self.versions_cache[key] = {"date": date, "component": component}
        elif dategroup.group(1):
            self.versions_cache[key] = {"component": component}
        else:
            print("ignore version " + component["version"] + " pour l'artefact " + component["group"] + ":" + component[
                "name"])

    def batch_generator(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
