
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
            description: 'Promover STG a MAIN solo si todas las pruebas pasan.'
        )

        booleanParam(
            name: 'TEST_FAILURE',
            defaultValue: false,
            description: 'Simular un fallo para verificar el correo FAILURE.'
        )

        string(
            name: 'EMAIL_TO',
            defaultValue: '',
            description: 'Correos adicionales separados por coma.'
        )
    }

    stages {

        stage('Verificar STG y herramientas') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'

                    Write-Host 'Verificando herramientas...'

                    python --version
                    node --version
                    npm --version
                    git --version
                    java -version

                    if (-not $env:JMETER_HOME) {
                        throw 'Configure JMETER_HOME para Apache JMeter.'
                    }

                    $jmeter = Join-Path $env:JMETER_HOME 'bin/jmeter.bat'

                    if (-not (Test-Path $jmeter)) {
                        throw 'No se encontro jmeter.bat en JMETER_HOME.'
                    }

                    Write-Host 'OK: Herramientas verificadas.'
                '''
            }
        }

        stage('Pruebas unitarias FastAPI') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'

                    New-Item -ItemType Directory -Force -Path reports |
                        Out-Null

                    Push-Location backend

                    try {
                        python -m pip install -r requirements.txt

                        if ($LASTEXITCODE -ne 0) {
                            throw 'Fallo la instalacion de dependencias Python.'
                        }

                        python -m pytest tests -v --junitxml=../reports/unit.xml

                        if ($LASTEXITCODE -ne 0) {
                            throw 'Fallaron las pruebas unitarias.'
                        }

                        Write-Host 'OK: Pruebas unitarias aprobadas.'
                    }
                    finally {
                        Pop-Location
                    }
                '''
            }
        }

        stage('Compilar React') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'

                    Push-Location frontend

                    try {
                        if (Test-Path package-lock.json) {
                            npm ci
                        }
                        else {
                            npm install
                        }

                        if ($LASTEXITCODE -ne 0) {
                            throw 'Fallo la instalacion de dependencias React.'
                        }

                        npm run build

                        if ($LASTEXITCODE -ne 0) {
                            throw 'Fallo la compilacion React.'
                        }

                        Write-Host 'OK: React compilado correctamente.'
                    }
                    finally {
                        Pop-Location
                    }
                '''
            }
        }

        stage('Selenium y JMeter') {
            steps {
                powershell '''
                    $ErrorActionPreference = 'Stop'

                    python -m pip install -r tests/selenium/requirements.txt

                    if ($LASTEXITCODE -ne 0) {
                        throw 'Fallo la instalacion de Selenium.'
                    }

                    & .\\ci\\run-integration.ps1

                    if (-not $?) {
                        throw 'Fallaron las pruebas de integracion.'
                    }

                    Write-Host 'OK: Selenium y JMeter completados.'
                '''
            }
        }

        stage('Probar correo FAILURE') {
            when {
                expression {
                    return params.TEST_FAILURE == true
                }
            }

            steps {
                error('Fallo controlado para verificar el correo FAILURE')
            }
        }

        stage('Promover STG a MAIN') {
            when {
                expression {
                    return params.PROMOTE_TO_MAIN == true
                }
            }

            steps {
                timeout(time: 3, unit: 'MINUTES') {

                    withCredentials([
                        gitUsernamePassword(
                            credentialsId: 'github-ci-push',
                            gitToolName: 'Default'
                        )
                    ]) {

                        bat '''
                            @echo off

                            REM Evitar solicitudes interactivas de Git
                            set GIT_TERMINAL_PROMPT=0
                            set GCM_INTERACTIVE=never

                            echo ==========================================
                            echo PROMOCION AUTOMATICA STG A MAIN
                            echo ==========================================

                            echo.
                            echo PASO 1: Verificando credenciales Git...

                            if not defined GIT_ASKPASS (
                                echo ERROR: Jenkins no proporciono GIT_ASKPASS.
                                exit /b 1
                            )

                            echo OK: Autenticacion de Jenkins disponible.

                            echo.
                            echo PASO 2: Consultando rama MAIN...

                            git -c credential.helper= fetch origin main

                            if errorlevel 1 (
                                echo ERROR: No fue posible consultar MAIN.
                                exit /b 1
                            )

                            echo.
                            echo PASO 3: Verificando historial de ramas...

                            git merge-base --is-ancestor origin/main HEAD

                            if errorlevel 1 (
                                echo ERROR: MAIN tiene cambios que requieren revision.
                                echo Promocion cancelada para proteger el repositorio.
                                exit /b 1
                            )

                            echo OK: MAIN puede avanzar a STG.

                            echo.
                            echo PASO 4: Enviando cambios a MAIN...

                            git -c credential.helper= push origin HEAD:refs/heads/main

                            if errorlevel 1 (
                                echo ERROR: No fue posible actualizar MAIN.
                                echo Revise permisos o proteccion de ramas.
                                exit /b 1
                            )

                            echo.
                            echo ==========================================
                            echo PROMOCION COMPLETADA CORRECTAMENTE
                            echo ==========================================
                        '''
                    }
                }
            }
        }
    }

    post {

        always {
            junit(
                allowEmptyResults: true,
                testResults: 'reports/*.xml'
            )

            archiveArtifacts(
                allowEmptyArchive: true,
                artifacts: 'reports/**,frontend/dist/**'
            )

            script {
                if (params.EMAIL_TO?.trim()) {
                    emailext(
                        to: params.EMAIL_TO,
                        subject: "[${currentBuild.currentResult}] Resenas STG - #${env.BUILD_NUMBER}",
                        body: """
Proyecto: Resenas independientes

Resultado: ${currentBuild.currentResult}
Rama de pruebas: stg
Numero de ejecucion: ${env.BUILD_NUMBER}

Promocion solicitada:
${params.PROMOTE_TO_MAIN}

Resultados y registros:
${env.BUILD_URL}

Reportes:
- unit.xml
- selenium.xml
- performance.jtl
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

                    <p><strong>Proyecto IV - Modulo de resenas</strong></p>

                    <p>Estado: SUCCESS</p>

                    <p>Las pruebas automatizadas finalizaron correctamente.</p>

                    <p>Build: ${env.BUILD_NUMBER}</p>

                    <p>Promocion a MAIN solicitada:
                    ${params.PROMOTE_TO_MAIN}</p>

                    <p>
                        <a href="${env.BUILD_URL}">
                            Ver resultados en Jenkins
                        </a>
                    </p>
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

                    <p><strong>Proyecto IV - Modulo de resenas</strong></p>

                    <p>Estado: FAILURE</p>

                    <p>Alguna etapa de las pruebas automatizadas fallo.</p>

                    <p>Build: ${env.BUILD_NUMBER}</p>

                    <p>Revise el registro adjunto.</p>

                    <p>
                        <a href="${env.BUILD_URL}">
                            Revisar error en Jenkins
                        </a>
                    </p>
                """
            )
        }
    }
}
