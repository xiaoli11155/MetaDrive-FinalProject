param(
    [Parameter(Mandatory=$true)][string]$InputPptx,
    [Parameter(Mandatory=$true)][string]$OutputPptx
)

$ErrorActionPreference = 'Stop'
$prefix = 'MetaDrive Final Project'
$inputResolved = (Resolve-Path -LiteralPath $InputPptx).Path
$outputFull = [System.IO.Path]::GetFullPath($OutputPptx)
$workspace = [System.IO.Path]::GetFullPath('D:\code\MetaDrive')
if (-not $inputResolved.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Input outside workspace' }
if (-not $outputFull.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Output outside workspace' }

function Shorten-FooterInGroup($groupItems, [ref]$changed) {
    for ($i = 1; $i -le $groupItems.Count; $i++) {
        $shape = $groupItems.Item($i)
        if ($shape.Type -eq 6) {
            Shorten-FooterInGroup $shape.GroupItems $changed
            continue
        }
        try {
            if ($shape.TextFrame2.HasText) {
                $value = $shape.TextFrame2.TextRange.Text.Trim()
                if ($value.StartsWith($prefix, [System.StringComparison]::Ordinal) -and $value -ne $prefix) {
                    $shape.TextFrame2.TextRange.Text = $prefix
                    $changed.Value++
                }
            }
        } catch { }
    }
}

$ppt = New-Object -ComObject PowerPoint.Application
$changed = 0
try {
    $deck = $ppt.Presentations.Open($inputResolved, $false, $false, $false)
    try {
        foreach ($slide in $deck.Slides) {
            for ($i = 1; $i -le $slide.Shapes.Count; $i++) {
                $shape = $slide.Shapes.Item($i)
                if ($shape.Type -eq 6) {
                    Shorten-FooterInGroup $shape.GroupItems ([ref]$changed)
                    continue
                }
                try {
                    if ($shape.TextFrame2.HasText) {
                        $value = $shape.TextFrame2.TextRange.Text.Trim()
                        if ($value.StartsWith($prefix, [System.StringComparison]::Ordinal) -and $value -ne $prefix) {
                            $shape.TextFrame2.TextRange.Text = $prefix
                            $changed++
                        }
                    }
                } catch { }
            }
        }
        $deck.SaveAs($outputFull)
    }
    finally { $deck.Close() }
}
finally {
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($ppt) | Out-Null
}

Write-Output "Changed=$changed"
Get-Item -LiteralPath $outputFull | Select-Object FullName,Length,LastWriteTime
