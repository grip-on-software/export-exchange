pipeline {
    agent { label 'docker' }

    environment {
        MONETDB_IMPORT_GIT=credentials('monetdb-import-git')
        MONETDB_EXPORT_DB=credentials('monetdb-export-db')
        SCANNER_HOME = tool name: 'SonarQube Scanner 3', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
    }
    options {
        gitLabConnection('gitlab')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    triggers {
        gitlab(triggerOnPush: true, triggerOnMergeRequest: true, branchFilterType: 'All')
        cron(env.EXCHANGE_CRON)
    }

    post {
        failure {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'failed'
        }
        aborted {
            updateGitlabCommitStatus name: env.JOB_NAME, state: 'canceled'
        }
    }

    stages {
        stage('Start') {
            when {
                expression {
                    currentBuild.rawBuild.getCause(hudson.triggers.TimerTrigger$TimerTriggerCause) == null
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
                withSonarQubeEnv('SonarQube') {
                    withPythonEnv('System-CPython-3') {
                        pysh 'python -m pip install pylint'
                        pysh 'sed -i "1s|.*|#!/usr/bin/env python|" `which pylint`'
                        pysh '${SCANNER_HOME}/bin/sonar-scanner -Dsonar.branch=$BRANCH_NAME -Dsonar.python.pylint=`which pylint`'
                    }
                }
            }
        }
        stage('Dump') {
            when {
                expression {
                    currentBuild.rawBuild.getCause(hudson.triggers.TimerTrigger$TimerTriggerCause) != null
                }
            }
            steps {
                copyArtifacts fingerprintArtifacts: true, projectName: 'build-monetdb-dumper/master', selector: lastSuccessful()
                dir('export') {
                    git url: env.MONETDB_IMPORT_GIT, credentialsId: 'gitlab-clone-auth', branch: 'master', changelog: false, poll: false
                    dir('dump') {
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
                allOf {
                    branch 'master'
                    expression {
                        currentBuild.rawBuild.getCause(hudson.triggers.TimerTrigger$TimerTriggerCause) != null
                    }
                    environment name: 'EXCHANGE_ENABLE', value: '1'
                }
            }
            agent {
                docker {
                    image '$DOCKER_REGISTRY/gros-export-exchange'
                    args '-v $HOME/.gnupg:/home/agent/.gnupg'
                    reuseNode true
                }
            }
            steps {
                withCredentials([file(credentialsId: 'exchange-config', variable: 'GATHERER_SETTINGS_FILE')]) {
                    sh 'python exchange/upload.py --files export/dump.tar.gz'
                }
            }
        }
        stage('Status') {
            when {
                expression {
                    currentBuild.rawBuild.getCause(hudson.triggers.TimerTrigger$TimerTriggerCause) == null
                }
            }
            steps {
                updateGitlabCommitStatus name: env.JOB_NAME, state: 'success'
            }
        }
    }
}
