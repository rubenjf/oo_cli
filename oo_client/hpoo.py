import requests
import json
import os.path
import oo_client.utils as utils
import oo_client.errors as errors
import logging
from uuid import UUID


class OORestCaller(object):
    def __init__(self, central_url, user, password, version="v1", ssl=True):
        # pylint: disable=fixme, line-too-long
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.session.verify = ssl
        self.session.headers.update({'accept': 'application/json',
                                     'content-type': 'application/json'})
        self.central = central_url
        self.url = "{0}/oo/rest/{1}".format(central_url, version)
        self.log = logging.getLogger(self.__class__.__name__)

    def get(self, url_path, **kwargs):
        req = self.session.get("{0}/{1}".format(self.url, url_path),
                               params=kwargs)
        if req.status_code not in range(200, 205):
            raise errors.HTTPNon200(req.status_code, req.text)
        try:
            csrf = req.headers['X-CSRF-TOKEN']
            self.session.headers.update({'X-CSRF-TOKEN': csrf})
        except KeyError:
            # OO 10 added CSRF at some point version so not a problem
            # if we don't get a token
            pass
        if req.text:
            return json.loads(req.text)

    def put(self, url_path, data):
        req = self.session.put("{0}/{1}".format(self.url, url_path), data)
        if req.status_code not in range(200, 205):
            self.log.error(req.status_code)
            self.log.error(req.text)
            raise errors.HTTPNon200(req.status_code, req.text)
        if req.text:
            return json.loads(req.text)

    def post(self, url_path, data=None, files=None):
        if isinstance(data, dict):
            data = json.dumps(data)
        if files:
            self.session.headers.pop('content-type')
            req = self.session.post("{0}/{1}".format(self.url, url_path),
                                    files=files)
            self.session.headers.update({'content-type': 'application/json'})
        else:
            req = self.session.post("{0}/{1}".format(self.url, url_path), data)
        if req.status_code not in range(200, 205):
            self.log.error(req.status_code)
            self.log.error(req.text)
            raise errors.HTTPNon200(req.status_code, req.text)
        if req.text:
            return json.loads(req.text)


class OOClient(object):
    def __init__(self, central_url, user, password, version="v1", ssl=True):
        self.rest = OORestCaller(central_url, user, password, version=version,
                                 ssl=ssl)
        self.log = logging.getLogger(self.__class__.__name__)
        self.deploy_id = None
        # Checks OO is up and forces the CSRF token
        self.rest.get('version')
        # We have to get twice for valid CSRF because OO?
        self.rest.get('version')

    def get_new_deployment(self):
        return self.rest.post('deployments', None)['deploymentProcessId']

    def deploy_content_packs(self, path_list, timeout=3600):
        """
        Deploy a list of content packs
        return True if they all succeed, otherwise False
        """
        if not self.deploy_id:
            self.deploy_id = self.get_new_deployment()
            self.log.info("Got new deployment ID: {0}".format(self.deploy_id))
        for file_path in path_list:
            self.log.info("Starting uploads...")
            with open(file_path, 'rb') as cp:
                filename = os.path.basename(file_path)
                ret = self.rest.post("deployments/"
                                     "{0}/files".format(self.deploy_id),
                                     files={'file': (filename, cp)})
                self.log.info("Uploaded {0}".format(filename))
                self.log.debug(ret)
        ret = self.rest.put('deployments/{0}'.format(self.deploy_id), None)
        self.log.info("Deployment started, waiting up"
                      " to {0}s to complete".format(timeout))
        results = self.wait_for_deployment_to_complete(self.deploy_id,
                                                       timeout, 5)
        self.log.debug(results)
        all_res = []
        for cp, res in results['contentPackResponses'].items():
            api_response = res['responses'][0]['responseCategory']
            api_message = res['responses'][0]['message']
            if api_response != 'Success':
                self.log.error('{0}: {1}'.format(api_response, api_message))
                self.log.error("Failed to deploy {0}".format(cp))
                all_res.append(False)
            else:
                self.log.info("Deployed {0} successfully".format(cp))
                all_res.append(True)
        self.log.debug(all_res)
        if not all_res:
            return False
        return all(all_res)

    def deploy_content_pack(self, file_url_path):
        cp_name = os.path.splitext(os.path.basename(file_url_path))[0]
        with open(file_url_path) as cp:
            ret = self.rest.put("content-packs/{0}".format(cp_name), cp)
            cp_response = ret['contentPackResponses']
            api_responses = cp_response['{0}.jar'.format(cp_name)]['responses']
            api_response = api_responses[0]['responseCategory']
            api_message = api_responses[0]['message']
            if api_response != 'Success':
                self.log.error('{0}: {1}'.format(api_response, api_message))
                return False
            return True

    def is_deployment_complete(self, deploy_id):
        deployment = self.rest.get('deployments/{0}'.format(deploy_id))
        if deployment['status'] in ['FINISHED', 'FAILED']:
            return deployment['deploymentResultVO']
        else:
            return False

    def wait_for_deployment_to_complete(self, deploy_id, timeout, interval):
        func = utils.timeout(timeout, interval)(self.is_deployment_complete)
        return func(deploy_id)

    def run_flow_async(self, flow, run_name=None, inputs={}):
        if utils.validate_uuid4(flow):
            # this makes sure the UUID is formated how OO likes it
            uuid = str(UUID(flow))
        else:
            uuid = self.get_flow_uuid_from_path(flow)
        self.log.debug(uuid)
        payload = {'uuid': uuid,
                   'runName': run_name,
                   'inputs': inputs}
        self.log.info('Running flow: {0}'.format(flow))
        return self.rest.post('executions', data=payload)

    def run_flow(self, flow, run_name=None, inputs={}, timeout=300):
        '''
        Returns "RESOLVED", "ERROR", "DIAGNOSED", "NO_ACTION_TAKEN"
        or None if there is no result type.
        '''
        execution = self.run_flow_async(flow, run_name=run_name, inputs=inputs)
        run_id = execution['executionId']
        self.wait_for_run_to_complete(run_id, timeout, 5)
        self.log.info("Flow {0} FINISHED: {1}, link"
                      " {2}/oo/#/runtimeWorkspace/runs/"
                      "{3}".format(flow,
                                   self.get_run_result_type(run_id),
                                   self.rest.central, run_id))
        if self.get_run_status(run_id) == 'COMPLETED':
            return self.get_run_result_type(run_id)
        else:
            return None

    def run_flows(self, flows, timeout=300):
        ret = []
        for flow in flows:
            ret.append(self.run_flow(flow, timeout=timeout))
        if all([False if flow == 'ERROR' else True for flow in ret]):
            return True
        else:
            return False

    def is_run_complete(self, run_id):
        status = self.get_run_status(run_id)
        if status in ['COMPLETED', 'SYSTEM_FAILURE', 'CANCELED']:
            return True
        else:
            return False

    def wait_for_run_to_complete(self, run_id, timeout, interval):
        return utils.timeout(timeout, interval)(self.is_run_complete)(run_id)

    def get_flow_uuid_from_path(self, flow_path):
        folder_name = os.path.dirname(flow_path)
        flow_name = os.path.splitext(os.path.basename(flow_path))[0]
        flows = self.rest.get('flows/tree/level', path=folder_name)
        flow = [x['id'] for x in flows if x['name'] == flow_name]
        if len(flow) != 1:
            raise errors.NotFound('Flow not found with path'
                                  ' {0}'.format(flow_path))
        return flow[0]

    def get_run_status(self, run_id):
        return self.get_run_summary(run_id)['status']

    def get_run_result_type(self, run_id):
        return self.get_run_summary(run_id)['resultStatusType']

    def get_run_summary(self, run_id):
        summary = self.rest.get('executions/{0}/summary'.format(run_id))
        if len(summary) != 1:
            raise errors.NotFound('No run summary found for run id:'
                                  ' {0}'.format(run_id))
        return summary[0]

    def get_content_pack_id(self, name):
        cps = self.rest.get('content-packs')
        ret = [cp['id'] for cp in cps if cp['name'] == name]
        if len(ret) != 1:
            raise errors.NotFound('No content pack found with name'
                                  ' {0}'.format(name))
        return ret[0]

    def get_content_pack_from_flow(self, flow_path):
        uuid = self.get_flow_uuid_from_path(flow_path)
        return self.rest.get('flows/{0}'.format(uuid))['cpName']

    def get_all_flows_in_cp(self, cp_name):
        # pylint: disable=fixme, line-too-long
        cp_id = self.get_content_pack_id(cp_name)
        tree = self.rest.get('content-packs/{0}/content-tree'.format(cp_id))
        flows = {flow['id']: flow['path'] for flow in tree if flow['type'] == 'FLOW'}
        return flows

    # Add ability to operate configuration items
    def get_name_value_pair(self, output):
        name = output['name']
        val = output['value']
        ret = {'name': name, 'value': val}
        return ret

    def get_a_configuration_item(self, type, path):
        """
        Supported types: domain-terms, group-aliases, selection-lists,
        system-accounts, system-properties
        """
        ret = self.rest.get('config-items/{0}/{1}'.format(type, path))
        name_value = self.get_name_value_pair(ret)
        print json.dumps(name_value, indent=4)
        return name_value

    def set_a_configuration_item(self, type, path, data):
        # path includes name of the configuration item
        # data should be value
        if type == 'system-accounts':
            user_pass = data.partition(':')
            username = user_pass[0]
            password = user_pass[2]
            dct = {'username': username, 'password': password}
            data = json.dumps(dct)
        jdata = json.dumps(data)
        print jdata
        ret = self.rest.put('config-items/{0}/{1}'.format(type, path), jdata)
        res = self.get_name_value_pair(ret)
        print json.dumps(res, indent=4)
        return res

    def get_configuration_items_by_type(self, type):
        ret = self.rest.get('config-items/{0}'.format(type))
        name_val = [{'name': d['name'], 'value': d['value']} for d in ret]
        print json.dumps(name_val, indent=4)
        return name_val

    def get_all_configuration_items(self):
        ret = self.rest.get('config-items')
        print ret
        triple = [{'type': d['type'], 'name': d['name'], 'value': d['value']} for d in ret]
        print json.dumps(triple, indent=4)
        return triple
