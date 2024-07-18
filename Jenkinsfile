pipeline {
    agent { label 'docker' }

    environment {
        GITLAB_TOKEN = credentials('export-exchange-gitlab-token')
        SCANNER_HOME = tool name: 'SonarQube Scanner 3', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
    }
    parameters {
        booleanParam(name: 'CREATE_DUMP', defaultValue: false, description: 'Create a dump regardless of timers')
        booleanParam(name: 'EXCHANGE_DUMP', defaultValue: false, description: 'Export the dump regardless of timers or branches')
    }
    options {
        gitLabConnection('gitlab')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    triggers {
        gitlab(triggerOnPush: true, triggerOnMergeRequest: true, branchFilterType: 'All', secretToken: env.GITLAB_TOKEN)
        cron(env.EXCHANGE_CRON)
    }

    post {
        failure {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'failed'
        }
        aborted {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'canceled'
        }
        always {
            publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: true, reportDir: 'mypy-report/', reportFiles: 'index.html', reportName: 'Typing', reportTitles: ''])
            junit allowEmptyResults: true, testResults: 'mypy-report/junit.xml'
            archiveArtifacts 'openapi.json,schema/**/*.json'
        }
    }

    stages {
        stage('Start') {
            when {
                not {
                    triggeredBy 'TimerTrigger'
                }
            }
            steps {
                updateGitlabCommitStatus name: env.JOB_NAME, state: 'running'
            }
        }
        stage('Build') {
            steps {
                sh 'docker build -t $DOCKER_REGISTRY/gros-export-exchange .'
            }
        }
        stage('Push') {
            when { branch 'master' }
            steps {
                sh 'docker push $DOCKER_REGISTRY/gros-export-exchange:latest'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withPythonEnv('System-CPython-3') {
                    pysh 'python -m pip install -r analysis-requirements.txt'
                    pysh 'mypy exchange --html-report mypy-report --cobertura-xml-report mypy-report --junit-xml mypy-report/junit.xml --no-incremental --show-traceback || true'
                    pysh 'python -m pylint exchange --exit-zero --reports=n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" -d duplicate-code > pylint-report.txt'
                }
                withSonarQubeEnv('SonarQube') {
                    sh '${SCANNER_HOME}/bin/sonar-scanner -Dsonar.projectKey=export-exchange:$BRANCH_NAME -Dsonar.projectName="Export exchange $BRANCH_NAME"'
                }
            }
        }
        stage('Dump') {
            when {
                anyOf {
                    environment name: 'CREATE_DUMP', value: 'true'
                    allOf {
                        branch 'master'
                        triggeredBy 'TimerTrigger'
                        environment name: 'EXCHANGE_ENABLE', value: '1'
                    }
                }
            }
            steps {
                copyArtifacts fingerprintArtifacts: true, projectName: 'build-monetdb-dumper/master', selector: lastSuccessful()
                dir('export') {
                    git url: env.MONETDB_IMPORT_GIT, credentialsId: 'gitlab-clone-auth', branch: 'master', changelog: false, poll: false
                    dir('dump') {
                        withPythonEnv('System-CPython-3') {
                            withCredentials([file(credentialsId: 'monetdb-import-settings', variable: 'VALIDATE_SETTINGS')]) {
                                pysh 'python -m pip install -r ../Scripts/requirements.txt'
                                pysh script: 'cp $VALIDATE_SETTINGS settings.cfg && python ../Scripts/validate_schema.py --log WARNING --export --path ../Scripts/create-tables.sql', returnStatus: true
                                sh 'rm -f settings.cfg'
                            }
                        }
                        withCredentials([file(credentialsId: 'monetdb-auth', variable: 'DOTMONETDBFILE')]) {
                            sh '../Scripts/dump_tables.sh -h $MONETDB_EXPORT_DB -p ../../dist/databasedumper.jar -d databasedumper.encrypted=true -s project_salt -o .'
                        }
                    }
                    sh 'tar czf dump.tar.gz dump/'
                    sh 'rm -rf dump/'
                }
            }
        }
        stage('Upload') {
            when {
                anyOf {
                    environment name: 'EXCHANGE_DUMP', value: 'true'
                    allOf {
                        branch 'master'
                        triggeredBy 'TimerTrigger'
                        environment name: 'EXCHANGE_ENABLE', value: '1'
                    }
                }
            }
            agent {
                docker {
                    image "${env.DOCKER_REGISTRY}/gros-export-exchange"
                    args '-v $HOME/.gnupg:/home/agent/.gnupg'
                    reuseNode true
                }
            }
            steps {
                withCredentials([file(credentialsId: 'exchange-config', variable: 'GATHERER_SETTINGS_FILE')]) {
                    sh 'gros-export-exchange --files export/dump.tar.gz'
                }
            }
        }
        stage('Status') {
            when {
                not {
                    triggeredBy 'TimerTrigger'
                }
            }
            steps {
                updateGitlabCommitStatus name: env.JOB_NAME, state: 'success'
            }
        }
    }
}
