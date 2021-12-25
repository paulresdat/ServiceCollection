import unittest

from src.service_collection.servicecollection import ConfigurationContext, ServiceCollectionConst


class ConfigurationTests(unittest.TestCase):
    def test_configure_context_grabs_settings_by_file_name(self):
        ctxt = ConfigurationContext("tests/settings.json")
        js = ctxt.file_as_dict
        self.assertTrue('name' in js.keys())
        self.assertTrue('complex' in js.keys())

    def test_configure_context_merges_settings_from_target_context(self):
        ctxt = ConfigurationContext("tests/settings.json")
        js = ctxt.file_as_dict
        self.assertTrue(js['complex_object']['value1'])
        ctxt = ConfigurationContext("tests/settings.json", target_context="target1")
        js = ctxt.file_as_dict
        # value 1 is overridden to be false from true
        self.assertFalse(js['complex_object']['value1'])

    def test_configure_context_grabs_settings_from_file_merges_with_target_from_os_env_name(self):
        import os
        os.environ[ServiceCollectionConst.OS_ENV_NAME.value] = "target1"
        ctxt = ConfigurationContext("tests/settings.json")
        js = ctxt.file_as_dict
        # value 1 is overridden to be false from true
        self.assertFalse(js['complex_object']['value1'])
        os.environ[ServiceCollectionConst.OS_ENV_NAME.value] = ""

    def test_configure_context_grabs_settings_from_file_merges_with_target_from_os_env_name(self):
        import os
        os.environ["CUSTOM_ENV_NAME"] = "target1"
        ctxt = ConfigurationContext("tests/settings.json", overriden_target_context_os_env_name="CUSTOM_ENV_NAME")
        js = ctxt.file_as_dict
        self.assertFalse(js['complex_object']['value1'])
        os.environ['CUSTOM_ENV_NAME'] = ""
