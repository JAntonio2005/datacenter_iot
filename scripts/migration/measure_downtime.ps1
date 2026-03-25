param(
    [string]$StartTimestamp,
    [string]$EndTimestamp
)

if ([string]::IsNullOrWhiteSpace($StartTimestamp) -or [string]::IsNullOrWhiteSpace($EndTimestamp)) {
    throw "Use -StartTimestamp y -EndTimestamp en formato ISO-8601"
}

$start = [DateTimeOffset]::Parse($StartTimestamp)
$end = [DateTimeOffset]::Parse($EndTimestamp)
$seconds = [Math]::Round(($end - $start).TotalSeconds, 3)

$status = if ($seconds -le 60) { "PASS" } else { "FAIL" }

[pscustomobject]@{
    start = $start.ToString("o")
    end = $end.ToString("o")
    downtime_seconds = $seconds
    threshold_seconds = 60
    status = $status
}
