import unittest
from src.service_collection.servicecollection import ConfigurationContext, ServiceCollectionConst


class ConfigurationTests(unittest.TestCase):
    def test_configure_context_grabs_settings_by_file_name(self):
        ctxt = ConfigurationContext("tests/settings.json")
        self.assertTrue('name' in ctxt.keys())
        self.assertTrue('complex' in ctxt.keys())

    def test_configure_context_merges_settings_from_target_context(self):
        ctxt = ConfigurationContext("tests/settings.json")
        section = ctxt.get_section("complex_object:value1")
        self.assertTrue(section.settings)
        ctxt = ConfigurationContext("tests/settings.json", target_context="target1")
        section = ctxt.get_section("complex_object:value1")
        # value 1 is overridden to be false from true
        self.assertFalse(section.settings)

    def test_configure_context_grabs_settings_from_file_merges_with_target_from_os_env_name(self):
        import os
        os.environ[ServiceCollectionConst.OS_ENV_NAME.value] = "target1"
        ctxt = ConfigurationContext("tests/settings.json")
        section = ctxt.get_section("complex_object:value1")
        # value 1 is overridden to be false from true
        self.assertFalse(section.settings)
        os.environ[ServiceCollectionConst.OS_ENV_NAME.value] = ""

    def test_configure_context_grabs_settings_from_file_merges_with_target_from_os_env_name2(self):
        import os
        os.environ["CUSTOM_ENV_NAME"] = "target1"
        ctxt = ConfigurationContext("tests/settings.json", target_context_os_env_name="CUSTOM_ENV_NAME")
        section = ctxt.get_section("complex_object:value1")
        self.assertFalse(section.settings)
        os.environ['CUSTOM_ENV_NAME'] = ""

    def test_configuration_context_can_be_translated_to_an_exploded_dictionary(self):
        ctxt = ConfigurationContext("tests/settings.json")
        dict_val = {**ctxt}
        self.assertEqual("one", dict_val['complex_object']['complex1']['term1'])
