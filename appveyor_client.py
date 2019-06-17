import re
import requests
from http import HTTPStatus
from dateutil import parser


class AppVeyorException(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return super().__str__()


class AppVeyorClient:
    _BASE_URI = 'https://ci.appveyor.com/api'

    @staticmethod
    def _get_headers(api_token):
        return {
            "Authorization": "Bearer %s" % api_token,
            "Content-type": "application/json",
        }

    @staticmethod
    def _get_variant_name_from_job_log(log_text):
        pattern = 'Task ([0-9]+):'
        match = re.search(pattern, log_text, re.IGNORECASE)
        variant_name = int(match.group(1)) if match is not None else None
        return variant_name

    def __init__(self, api_token, org_name, project_name):
        self._organization = org_name
        self._project = project_name
        self._request_headers = AppVeyorClient._get_headers(api_token)

    def get_latest_build_info(self):
        project = self._get_project_info(self._project)

        latest_build = project.get('build', None)
        if latest_build is None:
            raise AppVeyorException(
                "No builds found for project '%s'" % self._project)

        jobs = latest_build['jobs']
        latest_job = jobs[0]
        return self._extract_job_info(latest_job)

    def _extract_job_info(self, job_data):
        job_status = job_data['status']
        job_succeeded = (job_status == 'success')
        job_finished_date1 = parser.parse(job_data['finished'])
        job_finished_date = job_finished_date1.replace(microsecond=0).isoformat()
        variant_name = None

        if job_succeeded:
            job_id = job_data['jobId']
            log_text = self._get_job_log(job_id)
            variant_name = AppVeyorClient._get_variant_name_from_job_log(log_text)

        return variant_name, job_succeeded, job_finished_date

    def _get(self, entity_uri):
        url = '%s/%s' % (AppVeyorClient._BASE_URI, entity_uri)
        response = requests.get(url, headers=self._request_headers)

        if response.status_code != HTTPStatus.OK:
            raise AppVeyorException("Network request failed")

        return response

    def _get_json(self, entity_uri):
        response = self._get(entity_uri)
        return response.json()

    def _get_text(self, entity_uri):
        response = self._get(entity_uri)
        return response.text

    def _get_project_info(self, project_name):
        entity_uri = 'projects/%s/%s' % (self._organization, project_name)
        return self._get_json(entity_uri)

    def _get_job_log(self, job_id):
        entity_uri = 'buildjobs/%s/log' % job_id
        return self._get_text(entity_uri)
