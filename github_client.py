from http import HTTPStatus
from github import Github
import requests


class GithubAPI:
    """получения данных с сервиса Github."""

    def __init__(self, token=None, organization=None, repo=None):
        self.token = token
        self.git = Github(token)
        self.org = self.git.get_organization(organization)
        self.repo = self.org.get_repo(repo)
        self.request_headers = {
            "Accept": "application/vnd.github.antiope-preview+json",
            "Authorization": "token " + token,
        }

    def get_token(self):
        return self.token

    def get_repo_name(self):
        return self.repo.name

    def repo_is_private(self):
        return self.repo.private

    def get_checks_info(self, commit_sha):
        # Почему не через self.git???
        url = 'https://api.github.com/repos/' + self.org.name + '/' + self.repo.name + '/commits/' + commit_sha + '/check-runs'
        response = requests.get(url, headers=self.request_headers)

        check_runs = None
        if response.status_code == HTTPStatus.OK:
            check_runs = response.json()['check_runs']
        return check_runs

    def get_latest_commit_sha(self, branch='master'):
        """последний коммит в ветке"""
        branch = self.repo.get_branch(branch)
        latest_commit = branch.commit
        return latest_commit.sha
