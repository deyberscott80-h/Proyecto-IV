pipeline {
    agent {
        label 'windows-browser'
    }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    parameters {
        booleanParam(
            name: 'PROMOTE_TO_MAIN',
            defaultValue: false,
            description: 'Activar SOLO tras comprobar pruebas, permisos y respaldo de main.'
        )

        booleanParam(
    name: 'TEST_FAILURE',
    defaultValue: false,
    description: 'Simular fallo para probar el correo FAILURE'
)
        string(
            name: 'EMAIL_TO',
            defaultValue: '',
            description: 'Direcciones del equipo separadas por coma. Requiere SMTP configurado.'
        )
    }

    stages {
        stage('Verificar STG y herramientas') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'
                    python --version
                    node --version
                    npm --version
                    git --version
                    java -version
                    if (-not $env:JMETER_HOME) {
                        throw 'Configure JMETER_HOME apuntando a la carpeta de Apache JMeter.'
                    }
                    if (-not (Test-Path "$env:JMETER_HOME\\bin\\jmeter.bat")) {
                        throw 'No existe jmeter.bat en JMETER_HOME\\bin.'
                    }
                '''
            }
        }

        stage('Pruebas unitarias FastAPI') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'
                    New-Item -ItemType Directory -Force -Path reports | Out-Null
                    Push-Location backend
                    try {
                        python -m pip install -r requirements.txt
                        if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación Python.' }
                        python -m pytest tests -v --junitxml=../reports/unit.xml
                        if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas unitarias.' }
                    }
                    finally { Pop-Location }
                '''
            }
        }

        stage('Compilar React') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'
                    Push-Location frontend
                    try {
                        if (Test-Path package-lock.json) { npm ci }
                        else { npm install }
                        if ($LASTEXITCODE -ne 0) { throw 'Falló npm install/ci.' }
                        npm run build
                        if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación React.' }
                    }
                    finally { Pop-Location }
                '''
            }
        }

        stage('Selenium y JMeter') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'
                    python -m pip install -r tests/selenium/requirements.txt
                    if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación Selenium.' }
                    & .\\ci\\run-integration.ps1
                    if (-not $?) { throw 'Fallaron las pruebas de integración.' }
                '''
            }
        }


stage('Probar correo FAILURE') {
    when {
        expression { params.TEST_FAILURE == true }
    }
    steps {
        error('Fallo controlado para verificar el correo FAILURE')
    }
}


        stage('Promover STG a MAIN') {
            when {
                expression { return params.PROMOTE_TO_MAIN }
            }
            steps {
                // Requiere la credencial github-ci-push de tipo usuario + PAT.
                // Git plugin / Credentials Binding: Git Username and Password.
                withCredentials([
                    gitUsernamePassword(
                        credentialsId: 'github-ci-push',
                        gitToolName: 'Default'
                    )
                ]) {
                    bat '''
                        @echo off
                        git fetch origin main
                        if errorlevel 1 exit /b 1
                        git merge-base --is-ancestor origin/main HEAD
                        if errorlevel 1 (
                          echo ERROR: main divergio de stg; requiere revision manual.
                          exit /b 1
                        )
                        git push origin HEAD:refs/heads/main
                        if errorlevel 1 exit /b 1
                    '''
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/*.xml'
            archiveArtifacts allowEmptyArchive: true,
                artifacts: 'reports/**,frontend/dist/**'
            script {
                if (params.EMAIL_TO?.trim()) {
                    emailext(
                        to: params.EMAIL_TO,
                        subject: "[${currentBuild.currentResult}] Reseñas STG - #${env.BUILD_NUMBER}",
                        body: """Proyecto: Reseñas independientes
Resultado: ${currentBuild.currentResult}
Rama de pruebas: stg
Reporte y logs: ${env.BUILD_URL}
Promoción a main solicitada: ${params.PROMOTE_TO_MAIN}

Revisar los archivos unit.xml, selenium.xml y performance.jtl.
"""
                    )
                }
            }
        }


success {
    emailext(
        to: 'jeremiscott14@gmail.com',
        subject: "SUCCESS - Proyecto IV - Build #${env.BUILD_NUMBER}",
        mimeType: 'text/html',
        body: """
            <h2>Pipeline ejecutado correctamente</h2>
            <p>Proyecto IV - Modulo de reseñas</p>
            <p>Estado: SUCCESS</p>
            <p>Las pruebas automatizadas finalizaron correctamente.</p>
            <p>Build: ${env.BUILD_NUMBER}</p>
            <p><a href="${env.BUILD_URL}">Ver resultados en Jenkins</a></p>
        """
    )
}

failure {
    emailext(
        to: 'jeremiscott14@gmail.com',
        subject: "FAILURE - Proyecto IV - Build #${env.BUILD_NUMBER}",
        mimeType: 'text/html',
        attachLog: true,
        body: """
            <h2>Error en el Pipeline</h2>
            <p>Proyecto IV - Modulo de reseñas</p>
            <p>Estado: FAILURE</p>
            <p>Alguna etapa de las pruebas automatizadas fallo.</p>
            <p>Build: ${env.BUILD_NUMBER}</p>
            <p><a href="${env.BUILD_URL}">Revisar error en Jenkins</a></p>
        """
    )
}

    }
}
