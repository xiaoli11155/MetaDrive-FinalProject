param(
    [Parameter(Mandatory=$true)][string]$InputPptx,
    [Parameter(Mandatory=$true)][string]$OutputPptx
)

$ErrorActionPreference = 'Stop'
$inputResolved = (Resolve-Path -LiteralPath $InputPptx).Path
$outputFull = [System.IO.Path]::GetFullPath($OutputPptx)
$workspace = [System.IO.Path]::GetFullPath('D:\code\MetaDrive')
if (-not $inputResolved.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Input outside workspace' }
if (-not $outputFull.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Output outside workspace' }

$success = (Resolve-Path -LiteralPath 'D:\code\MetaDrive\videos\high_density_diagnostics\success_seed_1023.mp4').Path
$collision = (Resolve-Path -LiteralPath 'D:\code\MetaDrive\videos\high_density_diagnostics\collision_seed_1000.mp4').Path
$departure = (Resolve-Path -LiteralPath 'D:\code\MetaDrive\videos\high_density_diagnostics\out_of_road_seed_1046.mp4').Path

$ppt = New-Object -ComObject PowerPoint.Application
try {
    $deck = $ppt.Presentations.Open($inputResolved, $false, $false, $false)
    try {
        # SVG canvas coordinates are converted to PowerPoint points at 0.75 pt/px.
        [void]$deck.Slides.Item(2).Shapes.AddMediaObject2($success, $false, $true, 48, 94.5, 615, 375)
        [void]$deck.Slides.Item(13).Shapes.AddMediaObject2($success, $false, $true, 48, 94.5, 543, 352.5)
        [void]$deck.Slides.Item(13).Shapes.AddMediaObject2($collision, $false, $true, 615, 94.5, 297, 163.5)
        [void]$deck.Slides.Item(13).Shapes.AddMediaObject2($departure, $false, $true, 615, 283.5, 297, 163.5)
        $deck.SaveAs($outputFull)
    }
    finally { $deck.Close() }
}
finally {
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($ppt) | Out-Null
}

Get-Item -LiteralPath $outputFull | Select-Object FullName,Length,LastWriteTime
