# Script para verificar hashes MD5 desde archivos md5sum*

# Función para calcular el hash MD5 de un archivo
function Get-FileMD5 {
    param([string]$FilePath)
    try {
        $md5 = [System.Security.Cryptography.MD5]::Create()
        $stream = [System.IO.File]::OpenRead($FilePath)
        $hash = $md5.ComputeHash($stream)
        $stream.Close()
        return [System.BitConverter]::ToString($hash).Replace("-", "").ToLower()
    }
    catch {
        Write-Warning "Error calculando hash de $FilePath : $_"
        return $null
    }
}

# Buscar todos los archivos que empiezan con "md5sum"
$md5sumFiles = Get-ChildItem -Path . -Recurse -Filter "md5sum*.txt" -File -ErrorAction SilentlyContinue

if ($md5sumFiles.Count -eq 0) {
    Write-Host "No se encontraron archivos que empiecen con 'md5sum'" -ForegroundColor Yellow
    exit
}

Write-Host "Encontrados $($md5sumFiles.Count) archivo(s) md5sum" -ForegroundColor Cyan
Write-Host ""

foreach ($md5File in $md5sumFiles) {
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "Procesando: $($md5File.FullName)" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    
    $baseDirectory = $md5File.Directory.FullName
    $lines = Get-Content $md5File.FullName
    
    $total = 0
    $correctos = 0
    $incorrectos = 0
    $noEncontrados = 0
    
    foreach ($line in $lines) {
        # Ignorar líneas vacías o comentarios
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }
        
        # Formato esperado: hash  archivo (dos espacios)
        if ($line -match '^([a-fA-F0-9]{32})\s\s(.+)$') {
            $expectedHash = $matches[1].ToLower()
            $fileName = $matches[2].Trim()
            $total++
            
            # Construir ruta completa del archivo
            $filePath = Join-Path $baseDirectory $fileName
            
            if (Test-Path $filePath) {
                $actualHash = Get-FileMD5 -FilePath $filePath
                
                if ($actualHash -eq $expectedHash) {
                    Write-Host "[OK] $fileName" -ForegroundColor Green
                    $correctos++
                }
                else {
                    Write-Host "[FAIL] $fileName" -ForegroundColor Red
                    Write-Host "  Esperado: $expectedHash" -ForegroundColor Red
                    Write-Host "  Actual  : $actualHash" -ForegroundColor Red
                    $incorrectos++
                }
            }
            else {
                Write-Host "[NOT FOUND] $fileName" -ForegroundColor Yellow
                $noEncontrados++
            }
        }
    }
    
    Write-Host ""
    Write-Host "Resumen para $($md5File.Name):" -ForegroundColor Cyan
    Write-Host "  Total      : $total" -ForegroundColor White
    Write-Host "  Correctos  : $correctos" -ForegroundColor Green
    Write-Host "  Incorrectos: $incorrectos" -ForegroundColor Red
    Write-Host "  No encontr.: $noEncontrados" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Verificación completada." -ForegroundColor Cyan
