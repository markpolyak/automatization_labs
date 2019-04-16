import re
import requests
from http import HTTPStatus
from dateutil import parser


class AppVeyorException(Exception):

    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return super().__str__()


class AppVeyorAPI:
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

    def __init__(self, api_token, org_name='markpolyak'):
        self._organization = org_name
        self._request_headers = AppVeyorAPI._get_headers(api_token)

    def get_latest_build_info(self, project_name):
        project = self._get_project_info(project_name)

        latest_build = project.get('build', None)
        if latest_build is None:
            raise AppVeyorException(
                "No builds found for project '%s'" % project_name)

        jobs = latest_build['jobs']
        latest_job = jobs[0]
        return self._extract_job_info(latest_job)

    def _extract_job_info(self, job_data):
        job_status = job_data['status']
        job_succeeded = (job_status == 'success')
        job_finished_date1 = parser.parse(job_data['finished'])
        job_finished_date=job_finished_date1.replace(microsecond=0).isoformat()
        variant_name = None

        if job_succeeded:
            job_id = job_data['jobId']
            log_text = self._get_job_log(job_id)
            variant_name = AppVeyorAPI._get_variant_name_from_job_log(log_text)

        return variant_name, job_succeeded, job_finished_date
    def _get(self, entity_uri):
        url = '%s/%s' % (AppVeyorAPI._BASE_URI, entity_uri)
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


# hui = AppVeyorAPI('v2.7w5hnu6pmhkm1rpfesuq', 'markpolyak')
# succeeded, finished_date, variant_name = hui.get_latest_build_info('os-task3-Julianskay')#succeeded, finished_date, 
# print(succeeded, finished_date, variant_name) #