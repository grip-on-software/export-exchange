pipeline {
    agent { label 'docker' }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    triggers {
        cron(env.EXCHANGE_CRON)
    }

    stages {
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
        stage('Upload') {
            agent {
                docker {
                    image '$DOCKER_REGISTRY/gros-export-exchange'
                    args '-v $HOME/.gnupg:/home/agent/.gnupg'
                    reuseNode true
                }
            }
            steps {
                sh 'echo Test > message.txt'
                withCredentials([file(credentialsId: 'exchange-config', variable: 'GATHERER_SETTINGS_FILE')]) {
                    sh 'python upload.py --files message.txt'
                }
            }
        }
    }
}
