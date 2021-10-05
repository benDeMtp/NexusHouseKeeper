import unittest
from unittest.mock import MagicMock
from nexushousekeeper.mvnrepositoryhandler import MvnRepositoryHandler


class NexusHouseKeeperTest(unittest.TestCase):
    components = [{'name': 'module1', 'version': '2.0-20201208.121756-1', 'id': '1', 'group': 'kawamind',
                   'group': 'kawamind'},
                  {'name': 'module1', 'version': '2.1.1-20201208.121756-1', 'id': '2', 'group': 'kawamind',
                   'group': 'kawamind'},
                  {'name': 'module1', 'version': '2.1.1-20201208.134457-2', 'id': '3', 'group': 'kawamind',
                   'group': 'kawamind'},
                  {'name': 'module1', 'version': '2.5', 'id': '4', 'group': 'kawamind', 'group': 'kawamind'},
                  {'name': 'module2', 'version': '2.0-20201208.121757-1', 'id': '5', 'group': 'kawamind',
                   'group': 'kawamind'},
                  {'name': 'module2', 'version': '2.4.1-20201208.134457-2', 'id': '6', 'group': 'kawamind',
                   'group': 'kawamind'},
                  {'name': 'module2', 'version': '2.6', 'id': '7', 'group': 'kawamind', 'group': 'kawamind'},
                  {'name': 'module2', 'version': '2.1.1-20201208.121756-1', 'id': '8', 'group': 'kawamind',
                   'group': 'kawamind'},
                  {'name': 'module2', 'version': 'feature-foo28-20201208.121756-1', 'id': '9', 'group': 'kawamind',
                   'group': 'kawamind'}]

    def test_regex_should_match_release_version(self):
        # Given
        nexus_house_keeper = MvnRepositoryHandler('user', 'password', 'mock://testuri', 'maven-repo')
        nexus_house_keeper._components_size = MagicMock(return_value=10)

        # When
        aggregates_components, total_size = nexus_house_keeper.aggregates_components(self.components, True)

        # Then
        self.assertEqual(90, total_size)
        print(aggregates_components)
        self.assertDictEqual({'kawamind:module1': {'2.0-SNAPSHOT [10B]', '2.1.1-SNAPSHOT [20B]', '2.5 [10B]'},
                              'kawamind:module2': {'2.0-SNAPSHOT [10B]', 'feature-foo28-SNAPSHOT [10B]',
                                                   '2.1.1-SNAPSHOT [10B]', '2.4.1-SNAPSHOT [10B]', '2.6 [10B]'}},
                             aggregates_components)

    def test_aggregates_version_should_produce_dict_with_versions_and_size(self):
        # Given
        nexus_house_keeper = MvnRepositoryHandler('user', 'password', 'mock://testuri', 'maven-repo')
        nexus_house_keeper._components_size = MagicMock(return_value=10)

        # When
        aggregates_versions, total_size = nexus_house_keeper.aggregates_versions(self.components, True)

        # Then
        self.assertEqual(90, total_size)
        print(aggregates_versions)
        self.assertDictEqual({'2.0-SNAPSHOT': 20,
                              '2.1.1-SNAPSHOT': 30,
                              '2.4.1-SNAPSHOT': 10,
                              '2.5': 10,
                              '2.6': 10,
                              'feature-foo28-SNAPSHOT': 10
                              },
                             aggregates_versions)

    def test_filter_components_by_version_pattern_must_return_version_matching_pattern(self):
        # Given
        components = [{'name': 'module1', 'version': '1.0-20201208.121756-1', 'id': '1'},
                      {'name': 'module2', 'version': '1.1-20201208.121756-1', 'id': '2'},
                      {'name': 'module2', 'version': '2.0-20201208.121756-1', 'id': '3'},
                      {'name': 'ut', 'version': '2.1-20201208.121756-1', 'id': '4'}]
        pattern_to_delete = "1.*"
        expected = [{'name': 'module1', 'version': '1.0-20201208.121756-1', 'id': '1'},
                    {'name': 'module2', 'version': '1.1-20201208.121756-1', 'id': '2'}]
        nexus_house_keeper = MvnRepositoryHandler('user', 'password', 'mock://testuri', 'maven-repo')

        # When
        result = nexus_house_keeper._filter_components_by_version_pattern(components, pattern_to_delete)
        # Then
        self.assertEqual(expected, result)

    def test_get_last_versions_must_return_3_lasts_version_by_date(self):
        """
        Doit renvoyer deux versions DIFFERENTES dans le cas ou il y a deux snapshot pour la même version, seule la dernière doit être renvoyée
        :return: les 2 dernière version différentes
        """
        # Given
        components = [{'name': 'module1', 'version': '2.0-20201208.121756-1', 'id': '1', 'group': 'kawamind',
                       'group': 'kawamind'},
                      {'name': 'module1', 'version': '2.1.1-20201208.121756-1', 'id': '2', 'group': 'kawamind',
                       'group': 'kawamind'},
                      {'name': 'module1', 'version': '2.1.1-20201208.134457-2', 'id': '3', 'group': 'kawamind',
                       'group': 'kawamind'},
                      {'name': 'module1', 'version': '2.5', 'id': '4', 'group': 'kawamind', 'group': 'kawamind'},
                      {'name': 'module2', 'version': '2.0-20201208.121757-1', 'id': '5', 'group': 'kawamind',
                       'group': 'kawamind'},
                      {'name': 'module2', 'version': '2.4.1-20201208.134457-2', 'id': '6', 'group': 'kawamind',
                       'group': 'kawamind'},
                      {'name': 'module2', 'version': '2.6', 'id': '7', 'group': 'kawamind', 'group': 'kawamind'},
                      {'name': 'module2', 'version': '2.1.1-20201208.121756-1', 'id': '8', 'group': 'kawamind',
                       'group': 'kawamind'},
                      {'name': 'module2', 'version': 'feature-foo28-20201208.121756-1', 'id': '9', 'group': 'kawamind',
                       'group': 'kawamind'}]
        # versions = ["2.0-20201208.121756-1", "2.1.1-20201208.121756-1","2.1.1-20201208.134457-2","2.5"]
        # expected = ["2.0-20201208.121756-1", "2.1.1-20201208.134457-2","2.5"]
        expected = [{'name': 'module1', 'version': '2.5', 'id': '4', 'group': 'kawamind'},
                    {'name': 'module1', 'version': '2.1.1-20201208.134457-2', 'id': '3', 'group': 'kawamind'},
                    {'name': 'module1', 'version': '2.0-20201208.121756-1', 'id': '1', 'group': 'kawamind'},
                    {'name': 'module2', 'version': '2.6', 'id': '7', 'group': 'kawamind'},
                    {'name': 'module2', 'version': '2.4.1-20201208.134457-2', 'id': '6', 'group': 'kawamind'},
                    {'name': 'module2', 'version': '2.1.1-20201208.121756-1', 'id': '8', 'group': 'kawamind'}]
        nexus_house_keeper = MvnRepositoryHandler('user', 'password', 'mock://testuri', 'maven-repo')
        # When
        result = nexus_house_keeper._get_last_versions(components, 3)
        print(result)
        # Then
        self.assertListEqual(expected, result)

    def test_get_most_recent_artefact_for_version(self):
        # Given
        components = [{'name': 'module1', 'version': '2.0-20201208.121756-1', 'id': '1', 'group': 'kawamind'},
                      {'name': 'module1', 'version': '2.1.1-20201208.121756-1', 'id': '2', 'group': 'kawamind'},
                      {'name': 'module1', 'version': '2.1.1-20201208.134457-2', 'id': '3', 'group': 'kawamind'},
                      {'name': 'module1', 'version': '2.5', 'id': '4', 'group': 'kawamind'},
                      {'name': 'module1', 'version': '2.2.1', 'id': '5', 'group': 'kawamind'},
                      {'name': 'module1', 'version': '2.1-20201208.134457-2', 'id': '6', 'group': 'kawamind'},
                      {'name': 'module2', 'version': '2.0-20201208.121756-1', 'id': '7', 'group': 'kawamind'},
                      {'name': 'module2', 'version': '2.5', 'id': '8', 'group': 'kawamind'},
                      {'name': 'module2', 'version': 'feature-foo', 'id': '9', 'group': 'kawamind'}
                      ]
        # versions = ["2.0-20201208.121756-1", "2.1.1-20201208.121756-1", "2.1.1-20201208.134457-2", "2.5","2.2.1","2.1-20201208.134457-2"]

        expected = [{'name': 'module1', 'version': '2.0-20201208.121756-1', 'id': '1', 'group': 'kawamind'},
                    {'name': 'module1', 'version': '2.1.1-20201208.134457-2', 'id': '3', 'group': 'kawamind'},
                    {'name': 'module1', 'version': '2.5', 'id': '4', 'group': 'kawamind'},
                    {'name': 'module1', 'version': '2.2.1', 'id': '5', 'group': 'kawamind'},
                    {'name': 'module2', 'version': '2.0-20201208.121756-1', 'id': '7', 'group': 'kawamind'},
                    {'name': 'module2', 'version': '2.5', 'id': '8', 'group': 'kawamind'}
                    ]

        nexus_house_keeper2 = MvnRepositoryHandler('user', 'password', 'mock://testuri', 'maven-repo')
        # When
        for comp in components:
            nexus_house_keeper2._get_most_recent_artefact_for_version(comp)
        # Then
        print(str(nexus_house_keeper2.versions_cache.items()) + "\n")
        values = list(map(lambda x: x["component"], nexus_house_keeper2.versions_cache.values()))
        print(values)
        for exp in expected:
            self.assertTrue(exp in values, str(exp) + " n'est pas présent dans " + str(values))


if __name__ == '__main__':
    unittest.main()
