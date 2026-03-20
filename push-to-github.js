const simpleGit = require('simple-git');
const path = require('path');
const fs = require('fs');

const repoPath = 'd:\\New folder (37)\\YT\\video_processor\\video_processor';
const git = simpleGit(repoPath);

async function pushAllFiles() {
  try {
    console.log('🚀 Starting Git Push Operation...\n');

    // Check if .git exists
    const gitPath = path.join(repoPath, '.git');
    if (!fs.existsSync(gitPath)) {
      console.log('⚠️  .git folder not found. Reinitializing repository...');
      await git.init();
      console.log('✅ Repository reinitialized\n');
    }

    // Configure Git user
    console.log('Configuring Git user...');
    await git.addConfig('user.name', 'rufsanrafi4-design');
    await git.addConfig('user.email', 'rufsanrafi4@gmail.com');
    console.log('✅ Git user configured\n');

    // Add remote if it doesn't exist
    console.log('Checking remote repository...');
    const remotes = await git.getRemotes();
    const hasOrigin = remotes.some(r => r.name === 'origin');
    
    if (!hasOrigin) {
      console.log('Adding remote origin...');
      await git.addRemote('origin', 'https://github.com/rufsanrafi4-design/xgenSuite.git');
      console.log('✅ Remote origin added\n');
    } else {
      console.log('✅ Remote origin already exists\n');
    }

    // Get current status
    console.log('Checking repository status...');
    const status = await git.status();
    console.log(`Untracked files: ${status.untracked.length}`);
    console.log(`Modified files: ${status.modified.length}`);
    console.log(`Staged files: ${status.staged.length}\n`);

    // List files that will be added
    const allFiles = [...status.untracked, ...status.modified, ...status.created];
    if (allFiles.length > 0) {
      console.log('📄 Files to be committed:');
      allFiles.forEach(file => console.log(`   - ${file}`));
      console.log();
    }

    // Stage all files
    console.log('Staging all files...');
    await git.add('.');
    console.log('✅ All files staged\n');

    // Check if there's anything to commit
    const statusAfterAdd = await git.status();
    if (statusAfterAdd.staged.length === 0) {
      console.log('⚠️  No files to commit. Repository may be up to date.');
      return;
    }

    // Create commit
    console.log('Creating commit...');
    const commitMessage = 'Add remaining project files - Pro Video Suite v9';
    const commit = await git.commit(commitMessage);
    console.log(`✅ Commit created: ${commit.commit}\n`);

    // Push to GitHub
    console.log('Pushing to GitHub (this may take a moment)...');
    await git.push('origin', 'main');
    console.log('✅ Successfully pushed to GitHub!\n');

    // Final status
    console.log('🎉 OPERATION COMPLETE!\n');
    console.log('📍 Your repository is now ready at:');
    console.log('   https://github.com/rufsanrafi4-design/xgenSuite\n');
    
    const finalStatus = await git.status();
    console.log('📊 Final Status:');
    console.log(`   Untracked files: ${finalStatus.untracked.length}`);
    console.log(`   Modified files: ${finalStatus.modified.length}`);
    console.log(`   Working directory clean: ${finalStatus.isClean()}\n`);

    console.log('✨ All files have been successfully pushed to GitHub!');

  } catch (error) {
    console.error('❌ ERROR:', error.message);
    console.error('\nDebug Info:');
    console.error(error);
    process.exit(1);
  }
}

pushAllFiles();
