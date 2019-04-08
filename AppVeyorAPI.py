import requests
import re


class AppVeyorException(Exception):

    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return super().__str__()


class AppVeyorAPI:

    def __init__(self, token, org_name="suai-os-2019"):
        self.headers = {"Authorization": "Bearer %s" % token, "Content-type": "application/json"}
        self.base_uri = 'https://ci.appveyor.com/api'
        self.org_name = org_name

    def set_organization(self, org_name):
        self.org_name = org_name

    def check_task(self, repo_name):

        try:
            proj = self.get_proj(repo_name)
            if proj is None:
                raise AppVeyorException('Project is not found on AppVeyor')

            last_build = proj['build']
            if last_build is None:
                raise AppVeyorException('No builds found on this project')

            job = last_build['jobs'][0]
            job_id = job['jobId']
            log_text = self.get_job_log(job_id)
            return True

        except (requests.RequestException, KeyError, ValueError):
            return False

    def get_json_object(self, entity_uri):

        uri = self.base_uri + entity_uri
        response = requests.get(uri, headers=self.headers)

        if response.status_code != 200:
            return None

        json = response.json()
        if json is not None:
            return json
        else:
            return None

    def get_log_text(self, entity_uri):

        uri = self.base_uri + entity_uri
        response = requests.get(uri, headers=self.headers)

        b = bytearray(response.content)
        log_text = b.decode("utf-8")

        return log_text

    def get_proj(self, proj_slug):

        if self.org_name is not None:
            proj_uri = '/projects/%s/%s' % (self.org_name, proj_slug)
            return self.get_json_object(proj_uri)
        else:
            return None

    def get_job_log(self, job_id):

        log_uri = '/buildjobs/%s/log' % job_id
        return self.get_log_text(log_uri)
