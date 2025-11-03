# HWP → PDF 변환 PowerShell 스크립트
# 한컴오피스 COM 자동화 사용

param(
    [Parameter(Mandatory=$true)]
    [string]$InputPath,

    [Parameter(Mandatory=$true)]
    [string]$OutputPath
)

# 절대 경로로 변환
$InputPath = Resolve-Path $InputPath
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)

Write-Host "[CONVERT] $($InputPath.Path) -> $OutputPath"

try {
    # 한글 COM 객체 생성
    $hwp = New-Object -ComObject "HWPFrame.HwpObject"
    $hwp.XHwpWindows.Item(0).Visible = $false  # 창 숨김

    # HWP 파일 열기 (Open 메소드: filename, format, readonly)
    $result = $hwp.Open($InputPath.Path, "", "")
    if (-not $result) {
        throw "Failed to open HWP file"
    }
    Write-Host "  [OPENED] HWP file loaded"

    # 출력 디렉토리 생성
    $outDir = Split-Path -Parent $OutputPath
    if (-not (Test-Path $outDir)) {
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    }

    # PDF로 저장 (SaveAs 메소드: filename, format)
    # Format: "PDF"
    $result = $hwp.SaveAs($OutputPath, "PDF")
    if (-not $result) {
        throw "Failed to save as PDF"
    }
    Write-Host "  [SAVED] PDF created"

    # 닫기
    $hwp.Clear(1)  # 문서 닫기
    $hwp.Quit()

    # COM 객체 해제
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($hwp) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()

    Write-Host "  [SUCCESS] Conversion completed"
    exit 0

} catch {
    Write-Host "  [ERROR] $($_.Exception.Message)"

    # 정리
    if ($hwp) {
        try {
            $hwp.Quit()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($hwp) | Out-Null
        } catch {}
    }

    exit 1
}
