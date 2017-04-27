import logging
import oo_client.errors as errors


class IntegrationTester(object):
    def __init__(self, oo_client, test_filter):
        self.oo = oo_client
        self.int_test_path = test_filter
        self.log = logging.getLogger(self.__class__.__name__)

    def filter_flows(self, flows, path_filter):
        ret = [flow for flow in flows if path_filter in flow]
        return ret

    def run_tests(self, content_pack, timeout=300):
        flows = self.oo.get_all_flows_in_cp(content_pack)
        test_flows = self.filter_flows(flows.values(), self.int_test_path)
        if not test_flows:
            raise errors.NoFlowsFound(self.int_test_path)
        self.log.info("Found the following test flows, running sequentially")
        for flow in test_flows:
            self.log.info(flow)
        return self.oo.run_flows(test_flows, timeout=timeout)
