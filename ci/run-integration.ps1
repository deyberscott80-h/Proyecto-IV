# Ejecutar desde la raíz del repositorio. Solo Windows (PowerShell 5.1+).
# Inicia servicios aislados y los detiene incluso si una prueba falla.
$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$reports = Join-Path $root 'reports'
New-Item -ItemType Directory -Path $reports -Force | Out-Null
$env:REVIEWS_DB_PATH = Join-Path $reports 'ci-reviews.sqlite3'

if (Test-Path $env:REVIEWS_DB_PATH) {
    Remove-Item $env:REVIEWS_DB_PATH -Force
}

$backend = $null
$frontend = $null

function Wait-ForHttp([string] $Url, [int] $Attempts = 45) {
    for ($i = 0; $i -lt $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) { return }
        }
        catch { Start-Sleep -Seconds 1 }
    }
    throw "No respondió la aplicación: $Url. Revise los logs en reports/."
}

try {
    $backend = Start-Process -FilePath 'python' `
        -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000') `
        -WorkingDirectory (Join-Path $root 'backend') `
        -RedirectStandardOutput (Join-Path $reports 'backend.out.log') `
        -RedirectStandardError (Join-Path $reports 'backend.err.log') `
        -PassThru

    Wait-ForHttp 'http://127.0.0.1:8000/api/reviews/stats'

    $frontend = Start-Process -FilePath 'node' `
        -ArgumentList @('node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '5173', '--strictPort') `
        -WorkingDirectory (Join-Path $root 'frontend') `
        -RedirectStandardOutput (Join-Path $reports 'frontend.out.log') `
        -RedirectStandardError (Join-Path $reports 'frontend.err.log') `
        -PassThru

    Wait-ForHttp 'http://127.0.0.1:5173/'

    $env:REVIEWS_URL = 'http://127.0.0.1:5173'
    python -m pytest tests/selenium -v --junitxml=reports/selenium.xml
    if ($LASTEXITCODE -ne 0) { throw 'Selenium falló; no se publicará en main.' }

    if (-not $env:JMETER_HOME) {
        throw 'Configure JMETER_HOME en Windows y reinicie Jenkins.'
    }
    $jmeter = Join-Path $env:JMETER_HOME 'bin/jmeter.bat'
    if (-not (Test-Path $jmeter)) { throw "No se encontró $jmeter" }

    $jmx = Join-Path $root 'performance/reviews_public.jmx'
    if (-not (Test-Path $jmx)) { throw 'Falta performance/reviews_public.jmx' }
    $jtl = Join-Path $reports 'performance.jtl'
    $html = Join-Path $reports 'jmeter-html'
    if (Test-Path $jtl) { Remove-Item $jtl -Force }
    if (Test-Path $html) { Remove-Item $html -Recurse -Force }

    & $jmeter -n -t $jmx -l $jtl -e -o $html `
        -Jhost=127.0.0.1 -Jport=8000 -Jusers=5 -Jloops=10
    if ($LASTEXITCODE -ne 0) { throw 'JMeter terminó con error.' }

    python ci/check-performance.py $jtl
    if ($LASTEXITCODE -ne 0) { throw 'JMeter reportó solicitudes fallidas.' }

    Write-Host 'OK: Selenium y JMeter aprobaron.'
}
finally {
    if ($frontend -and -not $frontend.HasExited) {
        Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    }
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
}
