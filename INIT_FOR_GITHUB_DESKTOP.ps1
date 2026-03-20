# PowerShell Script to Initialize and Commit for GitHub Desktop
# This script prepares your repository for GitHub Desktop to publish

# Set variables
$projectPath = "d:\New folder (37)\YT\video_processor\video_processor"
$gitHubUser = "rufsanrafi4-design"
$gitHubEmail = "rufsanrafi4@gmail.com"
$commitMessage = "Initial commit - Pro Video Suite v9"
$repoName = "video_processor"

# Create .git directory structure manually (without git command)
$gitPath = Join-Path $projectPath ".git"
if (-not (Test-Path $gitPath)) {
    New-Item -ItemType Directory -Path $gitPath -Force | Out-Null
    New-Item -ItemType Directory -Path "$gitPath\objects" -Force | Out-Null
    New-Item -ItemType Directory -Path "$gitPath\refs\heads" -Force | Out-Null
    New-Item -ItemType Directory -Path "$gitPath\refs\tags" -Force | Out-Null
    
    Write-Host "✓ Git directory structure created"
}

# Create HEAD file
$headContent = @"
ref: refs/heads/main
"@
$headContent | Out-File -FilePath "$gitPath\HEAD" -Encoding ASCII -Force

# Create config file
$configContent = @"
[core]
	repositoryformatversion = 0
	filemode = false
	bare = false
	logallrefupdates = true
	ignorecase = true
[user]
	name = $gitHubUser
	email = $gitHubEmail
[remote `"origin`"]
	url = https://github.com/$gitHubUser/xgenSuite.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch `"main`"]
	remote = origin
	merge = refs/heads/main
"@
$configContent | Out-File -FilePath "$gitPath\config" -Encoding ASCII -Force

# Create description file
"Unnamed repository; edit this file 'description' to name the repository." | Out-File -FilePath "$gitPath\description" -Encoding ASCII -Force

Write-Host "✓ Git configuration created"
Write-Host ""
Write-Host "Next Steps for GitHub Desktop:"
Write-Host "1. Open GitHub Desktop"
Write-Host "2. File → Add Local Repository"
Write-Host "3. Choose folder: $projectPath"
Write-Host "4. Check 'Show in File Explorer' and click 'Add Repository'"
Write-Host "5. Create initial commit with message: $commitMessage"
Write-Host "6. Click 'Publish repository'"
Write-Host ""
Write-Host "Repository will be published to:"
Write-Host "https://github.com/$gitHubUser/$repoName"
