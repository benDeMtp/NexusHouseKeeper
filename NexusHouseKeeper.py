from pyclbr import _main
import requests
from requests.auth import HTTPBasicAuth
import argparse
import re
import datetime
from rich.console import Console
from rich.table import Column, Table

#base_uri = "http://localhost:8096/service/rest/"


class NexusHouseKeeper:
    cred = None
    nexus_url = None
    repository = None
    dryRun = None

    version_pattern = "(\d*\.?\d*\.?\d*)"
    date_pattern = "(\d{8}\.\d{6})"
    snapshot_finder = re.compile(version_pattern + "-?" + date_pattern + "?-?\d*")

    def __init__(self, user, password, nexus_url, repository, dryRun=False):
        self.cred = HTTPBasicAuth(user, password)
        self.nexus_url = nexus_url
        self.repository = repository
        self.dryRun = dryRun
        self.versions_cache = {}

    def get_components(self, token=None):
        params = {'repository': self.repository}
        if token:
            params['continuationToken'] = token
        response = requests.get(self.nexus_url + "v1/components", auth=self.cred,
                                params=params, headers={'accept': 'application/json'})
        response.raise_for_status()
        return response

    def _get_components_as_list(self) -> list:
        response = self.get_components()
        components = self._fill_tmp_array_from_json(response.json())
        while 'continuationToken' in response.json() and response.json()['continuationToken']:
            response = self.get_components(response.json()['continuationToken'])
            components += (self._fill_tmp_array_from_json(response.json()))
        return components

    def show_components(self) -> None:
        components = self._get_components_as_list()
        aggregates = {}
        regex = re.compile("^(.*)-"+self.date_pattern+"-?\d*")
        for x in components:
            key = x["group"]+":"+x["name"]
            match = regex.match(x["version"])
            #Check if snapshot
            version = "[bold]"+match.group(1)+"[/bold]"
            if match.group(2):
                version+="-SNAPSHOT"
            if key in aggregates:
                aggregates[key].add(version)
            else:
                aggregates[key]=set()
                aggregates[key].add(version)

        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="dim")
        table.add_column("Versions")
        for k,v in aggregates.items():
            table.add_row(k,", ".join(v))
        console.print(table)
        console.print("[red]* Pour supprimer une version SNAPSHOT il ne faut pas suffixer par \"SNAPSHOT\"[/red]")
        console.print("[red] Exemple : python NexusHouseKeeper.py -u USER -p PASS -r my-maven-snapshots --version-match 1.1 [/red]")

    def _fill_tmp_array_from_json(self, json) -> list:
        components = []
        for item in json['items']:
            #print(item)
            components.append({'name': item['name'], 'version': item['version'], 'id': item['id'],'group':item['group']})
        return components

    def delete_all_components(self):
        """
        Supprime tous les composant présents dans le repository
        :return:
        """
        components = self._get_components_as_list()
        self._delete_components_in_array(components)

    def delete_component(self, id):
        if not self.dryRun:
            response = requests.delete(base_uri + "v1/components/" + id, auth=self.cred)
            response.raise_for_status()

    def clean(self,version_pattern=None,last_versions=None):
        if version_pattern:
            components = self._get_components_as_list()
            self._delete_components_in_array(self._filter_components_by_version_pattern(components,version_pattern))


    def _delete_components_in_array(self, components_array):
        for comp in components_array:
            if self.dryRun:
                print("deleting " + comp['name'] + ':' + comp['version'])
            else:
                self.delete_component(comp['id'])



    def _filter_components_by_version_pattern(self, versions, pattern):
        """
        Filtre les versions pour ne retourner que celles qui doivent être supprimée

        :param versions: liste de versions à filtrer
        :param pattern: pattern à matcher
        :return: liste de version a supprimer
        """

        patched_pattern = "^" + pattern
        comp = re.compile(patched_pattern)

        def matcher(component):
            m = comp.match(component['version'])
            if m is not None:
                return component

        return [v for v in map(matcher, versions) if v is not None]

    def keep_lasts_versions(self,last_version_count)->None:
        """
        Conserve les dernière versions des artefacts
        :param last_version_count:
        """

        all_artefacts = self._get_components_as_list()
        artefact_to_keep = self._get_last_versions(all_artefacts, last_version_count)
        artefact_to_delete = [item for item in all_artefacts if item not in artefact_to_keep]
        self._delete_components_in_array(artefact_to_delete)


    def _get_last_versions(self, components, last_version_count):
        for component in components:
            self._get_most_recent_artefact_for_version(component)

       #def get_key(item):
       #     return item[0][1]+"-"+item[0][0]

        version_by_component = {}

        for k,v in self.versions_cache.items():
            if k[0] not in version_by_component:
                version_by_component[k[0]] = {k[1]:v["component"]}
            else:
                version_by_component[k[0]][k[1]]=v["component"]

        print(version_by_component)
        to_return = []
        for k,v in version_by_component.items():
            to_return+=map(lambda x:x[1],sorted(v.items(), reverse=True)[0:int(last_version_count)])

        return to_return
        #return list(
            #map(lambda x: x[1]["component"], sorted(self.versions_cache.items(), reverse=True,key=get_key)[0:int(last_version_count)]))


    #TODO mettre version_cache et _get_most_recent_artefact_for_version dans une autre classe
    #versions_cache = {}  # exemple : {(group:name,2.1.1):{"date":date,"version":"2.1.1-20201208.134457-2"}}


    def _get_most_recent_artefact_for_version(self, component) -> None:
        """
        Utilisé pour les snapshots pour lequel plusieurs artefacts existe pour la même version
        :param component: dict
        :return: component: dict
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
            print("ignore version "+component["version"]+" pour l'artefact "+component["group"] + ":" + component["name"])



def main():
    parser = argparse.ArgumentParser(description="Script permetant de faire des opérations sur des composants nexus")
    parser.add_argument("-u", help="nom de l'utilisateur nexus")
    parser.add_argument("-p", help="mot de passe de l'utilisateur nexus")
    parser.add_argument("-r", help="repository")
    parser.add_argument("-s", help="affiche l'ensemble des versions pour chaque composants",action="store_true")
    parser.add_argument("--nexus-url",help="la base path de l'api nexus")
    parser.add_argument("--version-match",
                        help="supprime tous les artefacts dont le numéro de version réponds à l'expression")
    parser.add_argument("-l",
                        help="conserve uniquement les n dernière version. Ne fonctionne uniquement qu'avec les versions au format X.Y.Z")
    parser.add_argument("--dryrun",
                        help="n'execute pas réellement la requête mais affiche les composants potentiellement effacés",
                        action="store_true")
    #TODO rendre des paramètre obligatoire
    args = parser.parse_args()

    nexus = NexusHouseKeeper(args.u, args.p, args.nexus_url, args.r, args.dryrun)
    if args.version_match:
        nexus.clean(version_pattern=args.version_match)
    elif args.s:
        nexus.show_components()
    elif args.l:
        nexus.keep_lasts_versions(args.l)


if __name__ == "__main__":
    main()
