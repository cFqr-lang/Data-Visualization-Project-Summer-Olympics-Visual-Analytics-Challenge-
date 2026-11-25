<#
.SYNOPSIS
    一键跑通任务一 / 任务二 / 任务三，产出全部可视化效果（任务四暂不纳入）。

.DESCRIPTION
    执行顺序（存在硬依赖）：
      任务一 pipeline 7 步 → 任务二指标与 10 图 JSON → 任务二导出 PNG/SVG + 离线单文件 → 任务三 3 个专题 + 10 图渲染

    全部产物：
      task1-data/output/                         审计表、清洗表、校验报告、说明书
      task2-visual/site/public/data/figures/     10 幅图 JSON
      shared/metrics/metrics_master.csv          全队共享指标
      task2-visual/exports/png|svg/              10 组 PNG@4x + SVG
      task2-visual/offline/olympics-story.offline.html   单文件故事站（双击即开）
      task3-insights/data/                       三个专题的 JSON 底表
      task3-insights/exports/                    10 组 PNG@4x + SVG

.PARAMETER SkipTask1
    跳过任务一（已跑过、只想看图表时可加）。

.PARAMETER SkipExports
    跳过 PNG/SVG 导出（只出 JSON 与站点，省时间）。

.PARAMETER Open
    跑完自动在浏览器打开离线故事站。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1 -Open

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1 -SkipTask1 -SkipExports
#>
[CmdletBinding()]
param(
    [switch]$SkipTask1,
    [switch]$SkipTask2,
    [switch]$SkipTask3,
    [switch]$SkipExports,
    [switch]$Open,
    [string]$Python = 'py',
    [string]$PyVersion = '-3.12'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$watch = [System.Diagnostics.Stopwatch]::StartNew()
$failed = $null

function Write-Head([string]$text) {
    Write-Host ""
    Write-Host ("=" * 62) -ForegroundColor DarkGray
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host ("=" * 62) -ForegroundColor DarkGray
}

function Write-Sub([string]$text) {
    Write-Host "  · $text" -ForegroundColor DarkGray
}

function Assert-LastExit([string]$what) {
    if ($LASTEXITCODE -ne 0) {
        throw "$what 失败（exit $LASTEXITCODE）"
    }
}

# ---------------- 0. 前置检查 ----------------
Write-Head "0/4 环境检查"

$rawCsv = Join-Path $Root 'data\raw\olympics_dataset.csv'
if (-not (Test-Path $rawCsv)) {
    Write-Host "!! 缺少原始数据：$rawCsv" -ForegroundColor Red
    Write-Host "   请先把赛题 CSV 放到 data/raw/olympics_dataset.csv" -ForegroundColor Yellow
    exit 1
}
Write-Sub "原始数据 OK（$([math]::Round((Get-Item $rawCsv).Length / 1MB, 2)) MB）"

if (-not $SkipTask1) {
    & $Python $PyVersion -c "import pandas, numpy, matplotlib, docx" 2>$null
    Assert-LastExit "Python 依赖检查（pandas / matplotlib / python-docx）"
    Write-Sub "Python 依赖 OK（$Python $PyVersion）"
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "!! 未找到 node，任务二/三需要 Node.js" -ForegroundColor Red
    exit 1
}
Write-Sub "Node OK（$(& node --version)）"

# ---------------- 1. 任务一 ----------------
if (-not $SkipTask1) {
    Write-Head "1/4 任务一：数据体检与口径"
    $pipeline = Join-Path $Root 'task1-data\pipeline'
    $steps = @(
        '01_audit.py', '01b_extra.py', '02_clean.py', '03_figures.py',
        '04_validate.py', '05_build_spec.py', '06_build_answer.py'
    )
    foreach ($s in $steps) {
        Write-Sub $s
        & $Python $PyVersion (Join-Path $pipeline $s)
        Assert-LastExit "任务一 $s"
    }
} else {
    Write-Head "1/4 任务一：已跳过"
}

# ---------------- 2. 任务二 ----------------
if (-not $SkipTask2) {
    Write-Head "2/4 任务二：百年全景 10 图与故事站"

    Write-Sub "生成图表 JSON 与共享指标"
    # 必须在 task2-visual 目录运行：build.py 使用相对导入（from . import common）
    Push-Location (Join-Path $Root 'task2-visual')
    try {
        & $Python $PyVersion -m pipeline.build
        Assert-LastExit "任务二 pipeline.build"
    } finally {
        Pop-Location
    }

    $site = Join-Path $Root 'task2-visual\site'
    Push-Location $site
    try {
        if (-not (Test-Path 'node_modules')) {
            Write-Sub "安装站点依赖（首次较慢）"
            & npm install --no-audit --no-fund
            Assert-LastExit "npm install"
        }

        if (-not $SkipExports) {
            Write-Sub "启动 dev server（端口 5273）"
            $dev = Start-Process -FilePath 'cmd.exe' `
                -ArgumentList '/c', 'npm run dev' `
                -WorkingDirectory $site -PassThru -WindowStyle Hidden

            $ready = $false
            for ($i = 0; $i -lt 40; $i++) {
                Start-Sleep -Milliseconds 500
                try {
                    $null = Invoke-WebRequest -Uri 'http://localhost:5273/' -UseBasicParsing -TimeoutSec 2
                    $ready = $true
                    break
                } catch { }
            }
            if (-not $ready) { throw 'dev server 未在 20 秒内就绪' }

            Write-Sub "导出 10 组 PNG@4x + SVG"
            $env:EXPORT_BASE_URL = 'http://localhost:5273'
            & npm run export:figures
            $exportExit = $LASTEXITCODE

            # 关闭 dev server（按端口找进程，避免子进程残留）
            try {
                Get-NetTCPConnection -LocalPort 5273 -State Listen -ErrorAction Stop |
                    Select-Object -ExpandProperty OwningProcess -Unique |
                    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
            } catch { }
            Stop-Process -Id $dev.Id -Force -ErrorAction SilentlyContinue

            if ($exportExit -ne 0) { throw "图资产导出失败（exit $exportExit）" }
        }

        Write-Sub "构建站点并生成离线单文件"
        & npm run build:offline
        Assert-LastExit "npm run build:offline"
    } finally {
        Pop-Location
    }
} else {
    Write-Head "2/4 任务二：已跳过"
}

# ---------------- 3. 任务三 ----------------
if (-not $SkipTask3) {
    Write-Head "3/4 任务三：专题深挖（东道主 / 地缘 / 通胀）"
    $t3 = Join-Path $Root 'task3-insights\pipeline'
    foreach ($s in @('host_effect.py', 'geopolitics.py', 'inflation.py')) {
        Write-Sub $s
        & $Python $PyVersion (Join-Path $t3 $s)
        Assert-LastExit "任务三 $s"
    }

    $t3site = Join-Path $Root 'task3-insights\site'
    Push-Location $t3site
    try {
        if (-not (Test-Path 'node_modules')) {
            Write-Sub "安装渲染依赖（首次较慢）"
            & npm install --no-audit --no-fund
            Assert-LastExit "npm install（task3）"
        }
        Write-Sub "渲染 10 组 SVG + PNG@4x"
        & node --max-old-space-size=4096 render.mjs
        Assert-LastExit "任务三 render.mjs"
    } finally {
        Pop-Location
    }
} else {
    Write-Head "3/4 任务三：已跳过"
}

# ---------------- 4. 汇总 ----------------
Write-Head "4/4 完成，产物清单"

$artifacts = @(
    @{ Name = '离线故事站（双击即开）'; Path = 'task2-visual\offline\olympics-story.offline.html' },
    @{ Name = '站点构建产物'; Path = 'task2-visual\site\dist\index.html' },
    @{ Name = '任务二图资产'; Path = 'task2-visual\exports\png' },
    @{ Name = '任务三图资产'; Path = 'task3-insights\exports' },
    @{ Name = '共享指标'; Path = 'shared\metrics\metrics_master.csv' },
    @{ Name = '任务一产物'; Path = 'task1-data\output' }
)
foreach ($a in $artifacts) {
    $full = Join-Path $Root $a.Path
    if (Test-Path $full) {
        Write-Host ("  [OK] " + $a.Name.PadRight(20) + " -> " + $a.Path) -ForegroundColor Green
    } else {
        Write-Host ("  [--] " + $a.Name.PadRight(20) + " -> " + $a.Path + "（未生成）") -ForegroundColor Yellow
    }
}

$watch.Stop()
Write-Host ""
Write-Host ("总耗时 " + [math]::Round($watch.Elapsed.TotalSeconds, 1) + " 秒") -ForegroundColor Cyan

if ($Open) {
    $offline = Join-Path $Root 'task2-visual\offline\olympics-story.offline.html'
    if (Test-Path $offline) {
        Start-Process $offline
        Write-Host "已在浏览器打开离线故事站" -ForegroundColor Cyan
    }
}
