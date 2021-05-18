import argparse
from .mvnrepositoryhandler import MvnRepositoryHandler


def main():
    parser = argparse.ArgumentParser(description="Script permetant de faire des opérations sur des composants nexus")
    parser.add_argument("-u", help="nom de l'utilisateur nexus", required=True)
    parser.add_argument("-p", help="mot de passe de l'utilisateur nexus", required=True)
    parser.add_argument("-r", help="repository", required=True)
    parser.add_argument("-s", help="affiche l'ensemble des versions pour chaque composants", action="store_true")
    parser.add_argument("--nexus-url", help="la base path de l'api nexus", required=True)
    parser.add_argument("--version-match",
                        help="supprime tous les artefacts dont le numéro de version réponds à l'expression")
    parser.add_argument("--version",
                        help="delete all components with this exact version")
    parser.add_argument("-l",
                        help="conserve uniquement les n dernière version. Ne fonctionne uniquement qu'avec les "
                             "versions au format X.Y.Z")
    parser.add_argument("--dryrun",
                        help="n'execute pas réellement la requête mais affiche les composants potentiellement effacés",
                        action="store_true")
    parser.add_argument("--parallel",
                        help="number of parallel tasks (default 20)", default=20)
    parser.add_argument("--no-size",
                        help="don't grab size of each object", action="store_false", default=True)
    # TODO make some parameters mandatory
    args = parser.parse_args()

    nexus = MvnRepositoryHandler(args.u, args.p, args.nexus_url, args.r, args.dryrun, int(args.parallel))
    if args.version_match:
        nexus.delete_all_component_by_version_pattern(version_pattern=args.version_match)
    elif args.s:
        nexus.show_all_components(args.no_size)
    elif args.l:
        nexus.keep_lasts_versions(args.l)
    elif args.version:
        nexus.delete_all_components_by_version(args.version)


if __name__ == "__main__":
    main()
