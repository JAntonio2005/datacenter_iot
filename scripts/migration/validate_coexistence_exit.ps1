param(
    [int]$WindowMinutes = 30,
    [int]$ConsecutiveWindows = 2,
    [int]$CriticalMappingErrors = 0,
    [bool]$SC002Passed = $false,
    [bool]$SC003Passed = $false
)

$pass = $SC002Passed -and $SC003Passed -and ($CriticalMappingErrors -le 0)
$requiredEvidence = "$ConsecutiveWindows windows of $WindowMinutes minutes with zero critical mapping errors"

[pscustomobject]@{
    sc002_passed = $SC002Passed
    sc003_passed = $SC003Passed
    critical_mapping_errors = $CriticalMappingErrors
    required_windows = $ConsecutiveWindows
    window_minutes = $WindowMinutes
    evidence_rule = $requiredEvidence
    status = if ($pass) { "PASS" } else { "FAIL" }
}
