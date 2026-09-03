# ============================================================
# agent_orchestrator.ps1 — tcmP 多 Profile 进程编排调度器
# ------------------------------------------------------------
# 用法:
#   # 纯并行: 3 个 agent 各干各的(互不依赖)
#   powershell -File scripts/agent_orchestrator.ps1 -Mode parallel
#
#   # 纯串行: 前一个完成才启动下一个(按数组顺序)
#   powershell -File scripts/agent_orchestrator.ps1 -Mode serial
#
#   # 依赖混合(推荐): 按每个任务 Depends 字段调度, 就绪即启动
#   powershell -File scripts/agent_orchestrator.ps1 -Mode deps
#
# 每个任务 = 一个独立 hermes profile 进程, 拥有自己的
#   profiles\<name>\memories\MEMORY.md + USER.md 私有记忆。
# agent 之间通过文件系统交换产物(prompt 中约定输入/输出目录)。
# 全部退出后按退出码汇总, 非 0 即整体失败(适合 CI 判断)。
#
# ⚠️ 本文件含中文, 必须以 UTF-8 WITH BOM 保存(PS 5.1 按 GBK 读无 BOM
#    文件会中文乱码)。若用 write_file 重写后, 执行:
#    powershell -Command "$f='scripts\agent_orchestrator.ps1'; $c=[IO.File]::ReadAllText($f); [IO.File]::WriteAllText($f,$c,(New-Object System.Text.UTF8Encoding $true))"
# ============================================================
param(
    [ValidateSet('parallel','serial','deps')]
    [string]$Mode = 'deps',
    [string]$LogDir = 'C:\Users\DELL\tcmP\logs\agents'
)

$ErrorActionPreference = 'Stop'

# ══════════════════════════════════════════════════════════════
# 一、协作参数区(改这里: 换教材/章节只需改这几行)
# ══════════════════════════════════════════════════════════════
$BookName    = 'hermes-dongfang-zhexue'          # tcmP 下教材目录名
$BookTitle   = '《东方哲学》'                      # 教材显示名
$ChapterNum  = '01'                               # 两位章节号
$ChapterTitle = '感知在地'                        # 章节标题

# 输入/输出目录(自动创建)
$InputJson   = "C:\Users\DELL\tcmP\$BookName\chapters_tree.json"
$DraftDir    = 'C:\Users\DELL\tcmP\data\drafts'
$ReviewDir   = 'C:\Users\DELL\tcmP\data\reviews'
$FinalDir    = 'C:\Users\DELL\tcmP\data\final'
foreach ($d in @($DraftDir, $ReviewDir, $FinalDir)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

# ══════════════════════════════════════════════════════════════
# 二、任务表 — tcmP 教材三角色协作管线
#    agent-a 作者执笔 → agent-b 评阅 → agent-c 终审 (严格串行链)
#    Depends: deps 模式下生效; 清空 = 无前置依赖(可并行)
# ══════════════════════════════════════════════════════════════
$Tasks = @(
    @{
        Name     = 'agent-a-author'
        Profile  = 'tcm-author'
        Prompt   = "你是教材编写者。读取章节树 $InputJson, 找到第 $ChapterNum 章「$ChapterTitle」的 intro 与 sections 内容, 编写该章完整草稿(正文1000-1500字, 含引言/小节/要点小结), 写入 $DraftDir\chapter-$ChapterNum-$ChapterTitle-v1.md。完成后只回复: 草稿路径和字数。"
        Depends  = @()
    },
    @{
        Name     = 'agent-b-reviewer'
        Profile  = 'textbook-reviewer'
        Prompt   = "你是教材评阅者。读取草稿 $DraftDir\chapter-$ChapterNum-$ChapterTitle-v1.md, 按四维评分卡评阅: 科学性40% + 系统性25% + 教学适切性20% + 可读性15%。输出评阅报告(总分+四维得分+问题清单, 问题按严重/一般分级)到 $ReviewDir\chapter-$ChapterNum-review.md。完成后只回复: 报告路径和总分。"
        Depends  = @('agent-a-author')
    },
    @{
        Name     = 'agent-c-chief-editor'
        Profile  = 'tcm-chief-editor'
        Prompt   = "你是终审主编。读取草稿 $DraftDir\chapter-$ChapterNum-$ChapterTitle-v1.md 与评阅报告 $ReviewDir\chapter-$ChapterNum-review.md。若评阅总分>=90则签署通过, 否则签发修订意见。整合草稿与评审意见产出终稿(修订处标注)到 $FinalDir\chapter-$ChapterNum-$ChapterTitle-final.md。完成后只回复: 终稿路径与终审结论(通过/修订)。"
        Depends  = @('agent-a-author','agent-b-reviewer')
    }
)

# ══════════════════════════════════════════════════════════════
# 三、调度核心(无需修改)
# ══════════════════════════════════════════════════════════════
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$State = @{}   # Name -> @{Status='pending'|'running'|'done'; ExitCode=; Proc=}
foreach ($t in $Tasks) { $State[$t.Name] = @{ Status = 'pending'; ExitCode = $null; Proc = $null; Log = ''; ErrLog = ''; OutTask = $null; ErrTask = $null } }

function Start-AgentTask($task) {
    $st = $State[$task.Name]
    $st.Status = 'running'
    $st.Log = Join-Path $LogDir ($task.Name + '.log')
    $st.ErrLog = Join-Path $LogDir ($task.Name + '.err.log')
    Write-Host "[$(Get-Date -Format HH:mm:ss)] START  $($task.Name)  (profile=$($task.Profile))"
    # 直启 hermes.exe(不经 cmd.exe), 参数经 CreateProcessW 以 UTF-16 传递,
    # 彻底规避 cmd 对 DBCS 中文第二字节的解析(跨代码页稳健)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'hermes'
    $psi.Arguments = "-p `"$($task.Profile)`" chat -q `"$($task.Prompt)`" --yolo"
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    # 异步读输出(防 4KB 缓冲区满阻塞子进程); 进程退出后收割时落盘
    $st.OutTask = $proc.StandardOutput.ReadToEndAsync()
    $st.ErrTask = $proc.StandardError.ReadToEndAsync()
    $st.Proc = $proc
    return $proc
}

function Test-DepsReady($task) {
    foreach ($d in $task.Depends) {
        if ($State[$d].Status -ne 'done') { return $false }
    }
    return $true
}

# 调度主循环: 就绪即启动(并行), 未就绪等待
$running = @()
$finished = @{}
$deadline = (Get-Date).AddMinutes(120)

while ($finished.Count -lt $Tasks.Count) {
    if ((Get-Date) -gt $deadline) { Write-Error '超时: 120 分钟未完成'; exit 2 }

    # 1) 收割已退出进程
    foreach ($r in @($running)) {
        if ($r.Proc.HasExited) {
            $st = $State[$r.Name]
            $st.ExitCode = $r.Proc.ExitCode
            $st.Status = 'done'
            $finished[$r.Name] = $true
            $running = @($running | Where-Object { $_ -ne $r })
            # 输出落盘(UTF-8 带 BOM)
            if ($null -ne $st.OutTask) {
                [IO.File]::WriteAllText($st.Log, $st.OutTask.Result, (New-Object System.Text.UTF8Encoding $true))
                [IO.File]::WriteAllText($st.ErrLog, $st.ErrTask.Result, (New-Object System.Text.UTF8Encoding $true))
            }
            Write-Host "[$(Get-Date -Format HH:mm:ss)] DONE   $($r.Name)  exit=$($st.ExitCode)  log=$($st.Log)"
        }
    }
    # 全部完成立即退出, 不空转等待
    if ($finished.Count -eq $Tasks.Count) { break }

    # 2) 按模式选择可启动任务
    $candidates = @()
    foreach ($t in $Tasks) {
        $st = $State[$t.Name]
        if ($st.Status -ne 'pending') { continue }
        if ($Mode -eq 'serial') {
            # 串行: 前序任务(数组顺序)必须全部 done
            $idx = [Array]::IndexOf($Tasks, $t)
            $prevAllDone = $true
            for ($i = 0; $i -lt $idx; $i++) {
                if ($State[$Tasks[$i].Name].Status -ne 'done') { $prevAllDone = $false; break }
            }
            if ($prevAllDone) { $candidates += $t }
        } elseif ($Mode -eq 'deps') {
            if (Test-DepsReady $t) { $candidates += $t }
        } else {
            # parallel: 全部直接启动
            $candidates += $t
        }
    }

    # 3) 启动本轮候选(互不依赖, 真正并行)
    foreach ($t in $candidates) {
        $p = Start-AgentTask $t
        $running += @{ Name = $t.Name; Proc = $p }
    }

    if ($running.Count -eq 0) { Start-Sleep -Seconds 5 }
    else { Start-Sleep -Seconds 2 }
}

# ---------- 汇总 ----------
Write-Host "`n===== 汇总 ====="
$fail = 0
foreach ($t in $Tasks) {
    $st = $State[$t.Name]
    $mark = if ($st.ExitCode -eq 0) { 'OK ' } else { 'FAIL' }
    if ($st.ExitCode -ne 0) { $fail++ }
    Write-Host "$mark  $($t.Name)  exit=$($st.ExitCode)  log=$($st.Log)"
}
if ($fail -gt 0) { exit 1 } else { Write-Host '全部任务成功'; exit 0 }
