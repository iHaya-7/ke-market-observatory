<#
.SYNOPSIS
Run the offline Development Observatory with verified local Python dependencies.
.DESCRIPTION
Does not install packages, fetch jobs, publish, or alter captures. SourceRoot is
the supplied private Development checkout. Results is relative to SourceRoot.
Output defaults to a fresh ignored directory. Existing results are never replaced.
The historical exact-LF eligibility test convention is separate from this launcher;
no source materialization or hash normalization is performed here.
.EXAMPLE
.\scripts\run_observatory.ps1 -SourceRoot <fixture-checkout> -Results <saved-batch-json> -Serve
#>
param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$Results,
    [string]$Output,
    [string]$PythonExecutable,
    [string]$Dependencies,
    [switch]$Serve,
    [ValidateRange(1024,65535)][int]$Port=8766
)
$ErrorActionPreference='Stop'
$repositoryRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sourcePath=(Resolve-Path -LiteralPath $SourceRoot).Path
$resultsPath=if([System.IO.Path]::IsPathRooted($Results)){$Results}else{Join-Path $sourcePath $Results}
if(-not (Test-Path -LiteralPath $resultsPath -PathType Leaf)){throw ('Saved Development results not found: '+$resultsPath+'. Supply -Results for an existing saved batch; no source collection is performed.')}
if(-not $Output){$Output='learning-local/observatory-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')}
$outputPath=if([System.IO.Path]::IsPathRooted($Output)){$Output}else{Join-Path $repositoryRoot $Output}
if($Dependencies){
    $dependencyCandidates=@(if([System.IO.Path]::IsPathRooted($Dependencies)){$Dependencies}else{Join-Path $repositoryRoot $Dependencies})
}else{
    $dependencyCandidates=@()
    if($env:KE_LOCAL_DEPS){$dependencyCandidates+=if([System.IO.Path]::IsPathRooted($env:KE_LOCAL_DEPS)){$env:KE_LOCAL_DEPS}else{Join-Path $repositoryRoot $env:KE_LOCAL_DEPS}}
    $dependencyCandidates+=Join-Path $repositoryRoot 'learning-local/stage6-deps'
    $dependencyCandidates+=Join-Path $repositoryRoot 'learning-local/development-v2-deps/Lib/site-packages'
}
if(-not $PythonExecutable){
    foreach($key in @('HKCU:\Software\Python\PythonCore\3.13\InstallPath','HKLM:\Software\Python\PythonCore\3.13\InstallPath')){
        $registered=Get-ItemProperty -LiteralPath $key -ErrorAction SilentlyContinue
        if($registered.ExecutablePath){$PythonExecutable=$registered.ExecutablePath;break}
    }
    if(-not $PythonExecutable){$command=Get-Command python3.13.exe -ErrorAction SilentlyContinue; if($command){$PythonExecutable=$command.Source}}
}
if(-not $PythonExecutable){throw 'Python 3.13 is unavailable. Supply -PythonExecutable for an existing compatible installation.'}
$previousDeps=$env:KE_LOCAL_DEPS
$previousBytecode=$env:PYTHONDONTWRITEBYTECODE
$check=@'
import importlib.metadata, pathlib, sys
if sys.version_info[:2] != (3, 13):
    raise SystemExit('Python 3.13 required; supply -PythonExecutable for an existing compatible installation.')
requirements = []
for line in (pathlib.Path(sys.argv[1])/'knowledge-engineering/06-validation/requirements-local.txt').read_text().splitlines():
    if '==' in line:
        requirements.append(line.split('=='))
failures = []
for value in sys.argv[2:]:
    candidate = pathlib.Path(value).resolve()
    try:
        for name, version in requirements:
            distribution = next(importlib.metadata.distributions(path=[str(candidate)], name=name), None)
            if distribution is None or distribution.version != version:
                raise ValueError('Missing/unreadable or mismatched '+name+'=='+version)
        sys.path.insert(0, str(candidate))
        import rdflib, pyshacl
        if not all(pathlib.Path(module.__file__).resolve().is_relative_to(candidate) for module in (rdflib, pyshacl)):
            raise ValueError('RDF packages must load from the verified dependency directory')
        print(candidate)
        break
    except (OSError, ValueError, ImportError) as error:
        failures.append(str(candidate)+': '+str(error))
else:
    raise SystemExit('No readable pinned dependency set. Supply -Dependencies for an existing site-packages directory. Nothing was installed.\n'+'\n'.join(failures))
'@
try{
    $env:PYTHONDONTWRITEBYTECODE='1'
    $verifiedDependencies=& $PythonExecutable -B -X utf8 -c $check $repositoryRoot @dependencyCandidates
    if($LASTEXITCODE -ne 0){throw 'Runtime/dependency verification failed; nothing was installed.'}
    $env:KE_LOCAL_DEPS=$verifiedDependencies
    Write-Output ('Runtime: '+$PythonExecutable+' ; pinned dependencies verified in '+$verifiedDependencies)
    & $PythonExecutable -B -X utf8 -W ignore::DeprecationWarning (Join-Path $repositoryRoot 'scripts/process_experimental_workflow.py') --source-root $sourcePath --results $resultsPath --output $outputPath
    if($LASTEXITCODE -ne 0){throw 'Workflow failed; inspect the retained local output.'}
    Write-Output ('Preview: '+(Join-Path $outputPath 'preview/index.html'))
    $report=Get-Content -LiteralPath (Join-Path $outputPath 'results.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $failed=@($report.results | Where-Object execution -ne 'PASS')
    if($failed.Count){Write-Warning ($failed.Count.ToString()+' isolated failures; successful results remain available.')}
    if($Serve){
        Write-Output ('Local URL: http://127.0.0.1:'+$Port+'/')
        & $PythonExecutable -B -m http.server $Port --bind 127.0.0.1 --directory (Join-Path $outputPath 'preview')
    }
}finally{
    $env:KE_LOCAL_DEPS=$previousDeps
    $env:PYTHONDONTWRITEBYTECODE=$previousBytecode
}
