# Environment check script for VietStore RAG
Write-Host "=== VietStore RAG Environment Check ===" -ForegroundColor Cyan

$checks = @()

# Check Node.js
$nodeVersion = node --version 2>$null
$checks += [PSCustomObject]@{Name="Node.js"; Status=if($nodeVersion){"OK ($nodeVersion)"}else{"MISSING"}; Pass=if($nodeVersion){$true}else{$false}}

# Check Python
$pythonVersion = python --version 2>$null
$checks += [PSCustomObject]@{Name="Python"; Status=if($pythonVersion){"OK ($pythonVersion)"}else{"MISSING"}; Pass=if($pythonVersion){$true}else{$false}}

# Check Docker
$dockerVersion = docker --version 2>$null
$checks += [PSCustomObject]@{Name="Docker"; Status=if($dockerVersion){"OK"}else{"MISSING"}; Pass=if($dockerVersion){$true}else{$false}}

# Check Docker services
$pgRunning = docker ps --format "{{.Names}}" | Select-String "postgres"
$redisRunning = docker ps --format "{{.Names}}" | Select-String "redis"
$checks += [PSCustomObject]@{Name="PostgreSQL"; Status=if($pgRunning){"Running"}else{"Not running"}; Pass=if($pgRunning){$true}else{$false}}
$checks += [PSCustomObject]@{Name="Redis"; Status=if($redisRunning){"Running"}else{"Not running"}; Pass=if($redisRunning){$true}else{$false}}

# Display results
Write-Host ""
$checks | ForEach-Object {
    $color = if($_.Pass){"Green"}else{"Red"}
    $icon = if($_.Pass){"✅"}else{"❌"}
    Write-Host "$icon $($_.Name): $($_.Status)" -ForegroundColor $color
}

$passed = ($checks | Where-Object { $_.Pass }).Count
$total = $checks.Count
Write-Host "\n📊 $passed/$total checks passed" -ForegroundColor $(if($passed -eq $total){"Green"}else{"Yellow"})
