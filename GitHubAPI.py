from Travis_API import TravisClient
from Travis_API import TravisException
from AppVeyorAPI_2 import AppVeyorAPI
from AppVeyorAPI_2 import AppVeyorException
from github import Github
from github import GithubException
import requests
import json

# класс для получения данных о выполненных лабораторных работах с сервиса Github
class GithubAPI: # (конструктор класса)

    def __init__(self, git_token, appveyor_token, organization="suai-os-2019"): # инициальзация

        try:
            self.git = Github(git_token)
            self.name_organization=organization #  дополнительное свойства класса githubapi
            self.org = self.git.get_organization(organization)
        except GithubException as e:
            #print("GitHub authorization error: " + str(e)) # отладка
            raise ValueError

        self.requestHeaders = {
            "Accept": "application/vnd.github.antiope-preview+json",
            "Authorization": "token " + git_token}  # !!!! SELF.

        try: # токены доступа к TravisAPI для закрытых и открытых репозиториев
            #self.public_travis = TravisAPI.git_auth(git_token, private=False) # инициализация публичного TravisAPI
            #self.public_travis.set_organization(organization)
            #self.private_travis = TravisAPI.git_auth(git_token, private=True) # инициализация приватного TravisAPI
            #self.private_travis.set_organization(organization)
            self.travis_client = TravisClient(github_token=git_token)
        except TravisException as e:
            #print(str(e)) # отладка
            raise ValueError
        #print('self.private_travis',self.private_travis)
        try:
            self.appveyor = AppVeyorAPI(api_token=appveyor_token, org_name=org_name_appv) # инициализация AppVeyorAPI
        except AppVeyorException as e:
            raise ValueError
        
    def set_organization(self, organization):  # установить новую организацию
        self.name_organization=organization
        self.org = self.git.get_organization(organization)

    def successful_commit_date(self, organization, num_lab, repo_name): # проверка выполнения лабораторной

        self.set_organization(organization=organization)
        try:  # Получить репозиторий из GitHub для получения SHA старым путём
            _repo = self.org.get_repo(repo_name)
        except GithubException:
            print("Repository not found on github") # отладка
            return None

        if _repo is None:
            print('not repo') # отладка
            return None

        _commits = _repo.get_commits() # получим список, но будем работать только с последним из списка коммитов репозитория _commits[0]
        if _commits is None:
            print('commits is None') # отладка
            return None

        # Получить репозиторий из GitHub
        #_repo.private
        _url='https://api.github.com/repos/'+self.name_organization+'/'+repo_name+'/commits/'+_commits[0].get_combined_status().sha+'/check-runs'
        _date_completed='' # дата выполнения, найдём максимальную дату (если несколько элементов)
        if (num_lab==1) or (num_lab==2): 
            try:
                _check_runs = requests.get(_url, headers=self.requestHeaders) #
            except GithubException:
                print("Check-runs not found on github") # !!!
                return None

            _check_runs=_check_runs.json() # парсим текст в словать с помощью библиотеки json
            # print(_check_runs) 
            #print(_check_runs['total_count']) # вернулось total_count элементов столько раз и цикл выполнить, так как в check_runs вернётся столько же элементов списка, в каждом элементе словарь
            
            for _check_run in _check_runs['check_runs']:
                #print(_check_run['conclusion']) # статус выполнения
                #print(_check_run['status']) # статус завершения
                _external_id=_check_run['external_id'] # id
                print(_external_id)
                if _check_run['conclusion'] == "success" and _check_run['status'] == "completed":  #!!!
                    _date_completed=max(_check_run['completed_at'],_date_completed)
                else:
                    return None       
                _numvar=self.travis_client.get_number_variant(build_id=_external_id, num_lab=num_lab, private=_repo.private)
        elif num_lab==3:
            _,_status,_=self.appveyor.get_latest_build_info(project_name=repo_name)
            if _status==True:
                _numvar,_,_date_completed=self.appveyor.get_latest_build_info(project_name=repo_name)
        else:
            print('error num_lab')
        """
        # проверки варианта задания
        print(repo_name) # отладка
        try:    # lunix
            print('lunix') # отладка
            if not travis.check_task(repo_name):
                return " Task num is incorrect (travis)" # при завершении отладки цифру 7 убираем
        except TravisException:
           try:    # windows
               print('windows') # отладка. при завершении отладки цифру 7 убираем
               if not self.appveyor.check_task(repo_name):
                    return "7 Task num is incorrect (appveyor)"
           except AppVeyorException:
               return "7 Build not found"
        """
        return _date_completed, _numvar

#--------------------- MAIN ------------------------
org_name_appv='markpolyak'
# github_api = GithubAPI('dd250f60bc8656ae90a79a18d49241056194bf17', 'v2.7w5hnu6pmhkm1rpfesuq', 'suai-os-2019')
# successful_commit_date = github_api.successful_commit_date('suai-os-2019', 3, 'os-task3-julianskay')
# print('FINAL: ',successful_commit_date)
