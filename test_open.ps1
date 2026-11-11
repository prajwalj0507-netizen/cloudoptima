$filePath = "C:\Users\91914\.gemini\antigravity\scratch\cloudoptima\CloudOptima_Project_Presentation.pptx"
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open($filePath, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    Write-Output "PowerPoint opened successfully!"
    $pres.Close()
    $ppt.Quit()
} catch {
    Write-Output "PowerPoint Error: $($_.Exception.Message)"
}
