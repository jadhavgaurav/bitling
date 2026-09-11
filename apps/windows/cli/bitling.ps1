# Bitling command line: tell the desktop pet what just happened. Windows port of
# apps/macos/Resources/bitling (bash). See that file's header comment for the full
# command reference; the commands and their arguments are identical here.
#
#   bitling.ps1 run <command...>              run tests; the pet reacts to pass or fail
#   bitling.ps1 deploy <target> <command...>  run a deploy; the pet shows progress, then rocket or error
#   bitling.ps1 event <kind> [key=value...]   raw event, e.g. `event test-failed count=3 name=api`
#   bitling.ps1 say <text>                    make the pet say something
#   bitling.ps1 panel                         open the control room window
#   bitling.ps1 pet <id>                      switch species, e.g. robot, dragon
#   bitling.ps1 size <n>                      resize the pet, 0.8 to 1.6
#   bitling.ps1 claude                        Claude Code hook adapter (reads hook JSON on stdin)
#   bitling.ps1 git <hook> [args...]          global git hook adapter (installed for you by the tray menu)
#
# Events travel over the bitling:// URL scheme (registered in HKEY_CURRENT_USER, no admin
# needed), so this works from any shell, script or git hook on the same PC.
param(
    [Parameter(Position = 0)]
    [string]$Command,
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Rest = @()
)

function Send-Event {
    param([string]$Kind, [hashtable]$Params = @{})
    $query = ($Params.GetEnumerator() | ForEach-Object {
        "$($_.Key)=$([uri]::EscapeDataString([string]$_.Value))"
    }) -join '&'
    $url = "bitling://$Kind" + $(if ($query) { "?$query" } else { "" })
    Start-Process $url | Out-Null
}

function Usage {
    Get-Content $PSCommandPath | Select-Object -Skip 3 -First 11 | ForEach-Object { $_ -replace '^# ?', '' }
}

switch ($Command) {
    'run' {
        if ($Rest.Count -eq 0) { Usage; exit 2 }
        $name = Split-Path -Leaf (Get-Location)
        $log = New-TemporaryFile
        & $Rest[0] $Rest[1..($Rest.Count - 1)] 2>&1 | Tee-Object -FilePath $log
        $status = $LASTEXITCODE
        $countMatch = Select-String -Path $log -Pattern '(\d+) (failed|failing)' | Select-Object -Last 1
        $count = if ($countMatch) { $countMatch.Matches[0].Groups[1].Value } else { '0' }
        Remove-Item $log -ErrorAction SilentlyContinue
        if ($status -eq 0) { Send-Event 'test-passed' @{ name = $name } }
        else { Send-Event 'test-failed' @{ name = $name; count = $count } }
        exit $status
    }
    'deploy' {
        if ($Rest.Count -lt 2) { Usage; exit 2 }
        $target = $Rest[0]
        Send-Event 'deploy-started' @{ target = $target }
        & $Rest[1] $Rest[2..($Rest.Count - 1)]
        $status = $LASTEXITCODE
        if ($status -eq 0) { Send-Event 'deploy-finished' @{ target = $target } }
        else { Send-Event 'deploy-failed' @{ target = $target } }
        exit $status
    }
    'event' {
        if ($Rest.Count -eq 0) { Usage; exit 2 }
        $kind = $Rest[0]
        $params = @{}
        foreach ($pair in $Rest[1..($Rest.Count - 1)]) {
            $idx = $pair.IndexOf('=')
            if ($idx -ge 0) { $params[$pair.Substring(0, $idx)] = $pair.Substring($idx + 1) }
        }
        Send-Event $kind $params
    }
    'say' {
        if ($Rest.Count -eq 0) { Usage; exit 2 }
        Send-Event 'say' @{ text = ($Rest -join ' ') }
    }
    'panel' { Start-Process 'bitling://panel' | Out-Null }
    'pet' {
        if ($Rest.Count -eq 0) { Usage; exit 2 }
        Send-Event 'pet' @{ id = $Rest[0] }
    }
    'size' {
        if ($Rest.Count -eq 0) { Usage; exit 2 }
        Send-Event 'size' @{ v = $Rest[0] }
    }
    'claude' {
        # Claude Code hook adapter: reads the hook JSON on stdin and forwards one event.
        $payload = [Console]::In.ReadToEnd()
        try { $data = $payload | ConvertFrom-Json } catch { exit 0 }
        $event = $data.hook_event_name
        $cwd = if ($data.cwd) { $data.cwd } else { (Get-Location).Path }
        $project = Split-Path -Leaf ($cwd.TrimEnd('\', '/'))
        if (-not $project) { $project = $cwd }
        $kind = $null
        $params = @{ name = $project }
        switch ($event) {
            'SessionStart' { $kind = 'claude-session-start' }
            'UserPromptSubmit' { $kind = 'claude-prompt'; $params.message = [string]$data.prompt }
            'PreToolUse' {
                $kind = 'claude-tool'
                $input = $data.tool_input
                $params.name = [string]$data.tool_name
                $detail = if ($input.command) { $input.command } elseif ($input.file_path) { $input.file_path } elseif ($input.pattern) { $input.pattern } else { '' }
                $params.message = [string]$detail
            }
            'Stop' { $kind = 'claude-done' }
            'Notification' { $kind = 'claude-notify'; $params.message = [string]$data.message }
            'SessionEnd' { $kind = 'claude-session-end' }
        }
        if ($kind) { Send-Event $kind $params }
        exit 0
    }
    'git' {
        # Global git hook adapter: `bitling.ps1 git <hook-name> [hook args]` inside a repository.
        if ($Rest.Count -eq 0) { exit 0 }
        $hook = $Rest[0]
        $hookArgs = if ($Rest.Count -gt 1) { $Rest[1..($Rest.Count - 1)] } else { @() }
        $top = (& git rev-parse --show-toplevel 2>$null)
        if (-not $top) { $top = (Get-Location).Path }
        $repo = Split-Path -Leaf $top
        $branch = (& git rev-parse --abbrev-ref HEAD 2>$null)
        switch ($hook) {
            'post-commit' {
                $hash = (& git rev-parse HEAD 2>$null)
                $message = (& git log -1 --format=%s 2>$null)
                $stat = (& git show --shortstat --format= HEAD 2>$null | Select-Object -Last 1)
                $files = if ($stat -match '(\d+) file') { $matches[1] } else { '0' }
                $ins = if ($stat -match '(\d+) insertion') { $matches[1] } else { '0' }
                $del = if ($stat -match '(\d+) deletion') { $matches[1] } else { '0' }
                Send-Event 'commit' @{ repo = $repo; branch = $branch; hash = $hash; message = $message; files = $files; insertions = $ins; deletions = $del }
            }
            'post-merge' { Send-Event 'merge' @{ repo = $repo; branch = $branch } }
            'post-checkout' { if ($hookArgs.Count -ge 3 -and $hookArgs[2] -eq '1') { Send-Event 'checkout' @{ repo = $repo; branch = $branch } } }
            'post-rewrite' {
                if ($hookArgs.Count -ge 1 -and $hookArgs[0] -eq 'amend') { Send-Event 'amend' @{ repo = $repo; branch = $branch } }
                else { Send-Event 'rebase-done' @{ repo = $repo; branch = $branch } }
            }
            'pre-push' { Send-Event 'push' @{ repo = $repo; branch = $branch } }
        }
        exit 0
    }
    default { Usage; exit 2 }
}
