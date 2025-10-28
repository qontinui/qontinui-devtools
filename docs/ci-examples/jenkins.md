# Jenkins Integration Guide

Complete guide for integrating qontinui-devtools with Jenkins CI.

## Quick Start

Create a `Jenkinsfile` in your repository root:

```groovy
pipeline {
    agent any

    environment {
        QONTINUI_OUTPUT_DIR = 'analysis-results'
    }

    stages {
        stage('Setup') {
            steps {
                echo 'Installing qontinui-devtools...'
                sh '''
                    python3 -m pip install --upgrade pip
                    pip install qontinui-devtools
                    qontinui-devtools --version
                '''
            }
        }

        stage('Analyze') {
            parallel {
                stage('Circular Dependencies') {
                    steps {
                        sh '''
                            mkdir -p ${QONTINUI_OUTPUT_DIR}
                            qontinui-devtools import-cmd check . \
                                --output ${QONTINUI_OUTPUT_DIR}/circular-deps.json \
                                --format json
                        '''
                    }
                }

                stage('God Classes') {
                    steps {
                        sh '''
                            mkdir -p ${QONTINUI_OUTPUT_DIR}
                            qontinui-devtools architecture god-classes . \
                                --min-lines 500 \
                                --output ${QONTINUI_OUTPUT_DIR}/god-classes.json \
                                --format json
                        '''
                    }
                }

                stage('Race Conditions') {
                    steps {
                        sh '''
                            mkdir -p ${QONTINUI_OUTPUT_DIR}
                            qontinui-devtools concurrency check . \
                                --output ${QONTINUI_OUTPUT_DIR}/race-conditions.json \
                                --format json
                        '''
                    }
                }
            }
        }

        stage('Quality Gates') {
            steps {
                script {
                    def status = sh(
                        script: '''
                            python3 -m qontinui_devtools.ci.quality_gates \
                                --circular-deps ${QONTINUI_OUTPUT_DIR}/circular-deps.json \
                                --god-classes ${QONTINUI_OUTPUT_DIR}/god-classes.json \
                                --race-conditions ${QONTINUI_OUTPUT_DIR}/race-conditions.json \
                                --max-circular 0 \
                                --max-god-classes 5 \
                                --max-race-critical 0
                        ''',
                        returnStatus: true
                    )

                    if (status != 0) {
                        error('Quality gates failed!')
                    }
                }
            }
        }

        stage('Generate Report') {
            steps {
                sh '''
                    qontinui-devtools analyze . \
                        --output ${QONTINUI_OUTPUT_DIR}/analysis-report.html \
                        --format html
                '''
            }
        }
    }

    post {
        always {
            // Archive artifacts
            archiveArtifacts artifacts: "${QONTINUI_OUTPUT_DIR}/**/*", allowEmptyArchive: true

            // Publish HTML report
            publishHTML([
                reportDir: "${QONTINUI_OUTPUT_DIR}",
                reportFiles: 'analysis-report.html',
                reportName: 'Code Quality Report',
                keepAll: true
            ])

            // Clean workspace
            cleanWs()
        }

        failure {
            echo 'Quality checks failed!'
            // Send notifications
            emailext(
                subject: "Code Quality Check Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: """
                    Build failed. Check the console output for details:
                    ${env.BUILD_URL}
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }

        success {
            echo 'All quality checks passed!'
        }
    }
}
```

## Advanced Configuration

### Multi-branch Pipeline

For automatic PR checks:

```groovy
pipeline {
    agent any

    stages {
        stage('Quality Check') {
            when {
                changeRequest()
            }
            steps {
                script {
                    // Run analysis
                    sh 'qontinui-devtools analyze . --output report.html'

                    // Generate PR comment
                    sh """
                        python3 -m qontinui_devtools.ci.pr_comment \
                            --circular-deps circular-deps.json \
                            --god-classes god-classes.json \
                            --pr-number ${env.CHANGE_ID} \
                            --pr-title "${env.CHANGE_TITLE}" \
                            --output pr-comment.md
                    """

                    // Post comment (requires GitHub/GitLab plugin)
                    def comment = readFile('pr-comment.md')
                    pullRequest.comment(comment)
                }
            }
        }
    }
}
```

### Scheduled Analysis

Run analysis on a schedule:

```groovy
pipeline {
    agent any

    triggers {
        cron('H 0 * * 0')  // Weekly on Sunday
    }

    stages {
        stage('Weekly Analysis') {
            steps {
                sh '''
                    qontinui-devtools analyze . \
                        --output weekly-report-$(date +%Y-%m-%d).html
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'weekly-report-*.html'
        }
    }
}
```

### With Docker

```groovy
pipeline {
    agent {
        docker {
            image 'python:3.11'
            args '-v $PWD:/workspace -w /workspace'
        }
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install qontinui-devtools'
            }
        }

        stage('Analyze') {
            steps {
                sh 'qontinui-devtools analyze . --output report.html'
            }
        }
    }
}
```

## Integration with Other Plugins

### SonarQube Integration

```groovy
stage('SonarQube & qontinui') {
    parallel {
        stage('SonarQube') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'mvn sonar:sonar'
                }
            }
        }

        stage('qontinui-devtools') {
            steps {
                sh 'qontinui-devtools analyze . --output report.html'
            }
        }
    }
}
```

### Slack Notifications

```groovy
post {
    failure {
        slackSend(
            color: 'danger',
            message: "Code quality check failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
        )
    }
}
```

## Best Practices

1. **Use parallel stages** for faster execution
2. **Cache pip packages** to speed up builds
3. **Archive artifacts** for historical tracking
4. **Set up notifications** for failures
5. **Use quality gates** to enforce standards

## Troubleshooting

### Issue: Python not found

```groovy
stage('Setup Python') {
    steps {
        sh '''
            # Install Python if not available
            apt-get update && apt-get install -y python3 python3-pip
        '''
    }
}
```

### Issue: Permissions errors

```groovy
agent {
    docker {
        image 'python:3.11'
        args '--user root'
    }
}
```

## Complete Example

See the Quick Start section for a complete, production-ready Jenkinsfile.
