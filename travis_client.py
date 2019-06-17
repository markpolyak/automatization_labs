import requests


class TravisException(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return super().__str__()


class TravisClient:
    def __init__(self, github_token, private):
        self.github_token = github_token
        self.base_uri = 'https://api.travis-ci.com' if private else 'https://api.travis-ci.org'
        self.token = self._get_auth_token()
        self.request_headers = {
            "Travis-API-Version": "3",
            "User-Agent": "API Explorer",
            "Authorization": "token " + self.token,
        }

    def _get_auth_token(self):
        response = requests.post(self.base_uri + '/auth/github',
                                 params={"github_token": self.github_token})
        if not response.ok:
            raise TravisException("Travis authentication error")
        content = response.json()
        token = content['access_token']
        return token

    def _get_full_url(self, url_path):
        return self.base_uri + '/' + url_path

    def _request(self, url_path):
        url = self._get_full_url(url_path)
        request = requests.get(url, headers=self.request_headers)
        response = request.json()
        return response

    def get_build(self, build_id):
        return self._request('build/{}'.format(build_id))

    def get_job_log(self, job_id):
        return self._request('job/{}/log'.format(job_id))

    def get_first_job_log(self, build_id):
        job_log = None
        try:
            build_info = self.get_build(build_id)
            job_id = build_info['jobs'][0]['id']
            job_info = self.get_job_log(job_id)
            job_log = job_info['content']
        except Exception as e:
            print(e)
        return job_log
