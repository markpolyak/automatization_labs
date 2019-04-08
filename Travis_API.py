import json
import requests

class TravisException(Exception):

    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return super().__str__()

class TravisClient:
    def __init__(self, github_token):
        self.github_token = github_token
        self.private_base_uri = 'https://api.travis-ci.com'
        self.public_base_uri = 'https://api.travis-ci.org'
        # получение закрытоко токена травис
        _response = requests.post(self.private_base_uri + '/auth/github', params={"github_token": self.github_token})
        if not _response.ok:
            print('Travis authentication error private')
            raise TravisException('Travis authentication error')
        _content = _response.json()
        self.access_token_private = _content['access_token']
        print(_content)
        print(' TravisAPI access_token ', self.access_token_private, ' private')

        # получение открытого токена травис
        _response = requests.post(self.public_base_uri + '/auth/github', params={"github_token": self.github_token})
        if not _response.ok:
            print('Travis authentication error')
            raise TravisException('Travis authentication error public')
        _content = _response.json()
        self.access_token_public = _content['access_token']
        print(_content)
        print(' TravisAPI access_token ', self.access_token_public, ' public')

    def _get_full_url(self, url_path, private=True):
        if private==True:
            _base_url=self.private_base_uri
        else:
            _base_url=self.public_base_uri
        return _base_url+'/'+url_path

    def _get_request_headers(self, private=True):
        if private==True:
            _token=self.access_token_private
        else:
            _token=self.access_token_public
        return {
            "Travis-API-Version": "3",
            "User-Agent": "API Explorer",
            "Authorization": "token "+_token,
        }

    def request_travisAPI(self, url_path, private=True):
        _url = self._get_full_url(url_path, private)
        _mi_headers = self._get_request_headers(private)
        _request = requests.get(_url, headers=_mi_headers)
        _response_json = _request.text
        _response = json.loads(_response_json)
        return _response

    def get_number_variant(self, build_id='',num_lab=0, private=True):
        print(build_id,'-------------------------------build-----------')
        _response = self.request_travisAPI('build/'+build_id, private)
        try:
            _job_id = _response['jobs'][0]['id']
        except:
            _job_id=-1
            
        if _job_id==-1:
            return -1

        print(_job_id,'-------------------------------job-----------')
        _response = self.request_travisAPI('job/'+str(_job_id)+'/log', private)
        try:
            _job_logs = _response['content']
        except:
            _job_logs=-1

        if _job_id==-1:
            return -1
        

        if num_lab==1: # Для 1 лабораторной
            _start=_job_logs.find('The script is run on Linux machine')
            if _start>0:
                _a=_job_logs[_start:].replace('\n','').split('\r')
                _beg_line=_job_logs.find('Solution for task ')
                if _beg_line>0:
                    _b=_job_logs[_beg_line:].replace(' ','\r').split('\r')
                    _number_variant=int(_b[3])
                else:
                    return -1
            else:
                return -1 # если всё плохо

        elif num_lab == 2: # Для 2 лабораторной
            _start=_job_logs.find('Task')
            if _start>0:
                _a=_job_logs[_start:].replace(' ','\r').split('\r')
                _beg_line=_job_logs.find('Task')
                _number_variant=int(_a[1].replace(':',''))
            else:
                return -1 # если всё плохо
        else:
            return -1
        return _number_variant


# один раз в начале главной программы
# travis_client = TravisClient(github_token='7547080a56d95762954b919f6005ba125f1b2a61')

# # каждый раз при проверке номера варианта если check_runs вернул successfull берём оттуда build_id и признак привайт
# a=travis_client.get_number_variant(build_id='106992106', num_lab=2, private=True)
# print('НОМЕР ВАРИАНТА ', a)
