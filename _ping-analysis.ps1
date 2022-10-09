$stats = Get-Content ./Ping.txt

$n = $stats.Length
$t0 = $stats[0].Substring(0, 19)
$t1 = $stats[$n - 1].Substring(0, 19)
$dt = New-TimeSpan -Start $t0 -End $t1
Write-Host "ip =" $stats[0].Substring(33, 13)
Write-Host "n =" $n
Write-Host "t0 =" $t0
Write-Host "t1 =" $t1
Write-Host "dt =" $dt

$total = 0
$stats | % { $ms = $_.Substring(62, 4) -replace '[ms ]',''; $total += $ms }
$avg = $total / $n
Write-Host "avg =" $avg