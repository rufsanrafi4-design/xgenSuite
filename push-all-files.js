const simpleGit = require('simple-git');
const path = require('path');
const fs = require('fs');

const repoPath = 'd:\\New folder (37)\\YT\\video_processor\\video_processor';

async function pushAllFiles() {
  try {
    console.log('='.repeat(50));
    console.log('GitHub Push All Files Script');
    console.log('='.repeat(50));
    console.log('');
    
    const git = simpleGit(repoPath);
    
    console.log('📁 Repository Path:', repoPath);
    console.log('');
    
    // Check current status
    console.log('📊 Checking repository status...');
    const status = await git.status();
    console.log(`   Files modified: ${status.modified.length}`);
    console.log(`   Files not tracked: ${status.not_added.length}`);
    console.log('');
    
    // Configure user
    console.log('👤 Configuring Git user...');
    await git.addConfig('user.name', 'rufsanrafi4-design');
    await git.addConfig('user.email', 'rufsanrafi4@gmail.com');
    console.log('   ✓ User configured');
    console.log('');
    
    // Add all files
    console.log('📝 Staging all files...');
    await git.add('.');
    console.log('   ✓ All files staged');
    console.log('');
    
    // Commit
    console.log('💾 Creating commit...');
    const commitResult = await git.commit('Add remaining project files - Pro Video Suite v9');
    console.log('   ✓ Commit created');
    console.log('   Message: Add remaining project files - Pro Video Suite v9');
    console.log('');
    
    // Push to GitHub
    console.log('🚀 Pushing to GitHub...');
    const pushResult = await git.push(['-u', 'origin', 'main']);
    console.log('   ✓ Push completed');
    console.log('');
    
    console.log('='.repeat(50));
    console.log('✅ SUCCESS! All files pushed to GitHub');
    console.log('='.repeat(50));
    console.log('');
    console.log('View your repository at:');
    console.log('https://github.com/rufsanrafi4-design/xgenSuite');
    console.log('');
    
    console.log('📋 Summary:');
    const newStatus = await git.status();
    console.log(`   Untracked files: ${newStatus.not_added.length}`);
    console.log(`   Modified files: ${newStatus.modified.length}`);
    console.log('');
    
  } catch (error) {
    console.error('');
    console.error('❌ ERROR:', error.message);
    console.error('');
    if (error.message.includes('not a git repository')) {
      console.error('The folder is not a Git repository.');
      console.error('GitHub Desktop may have created it with a different structure.');
    }
    process.exit(1);
  }
}

pushAllFiles();
