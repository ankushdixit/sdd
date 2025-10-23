const { existsSync } = require('fs');
const { execSync } = require('child_process');
const path = require('path');

describe('SDD Project Setup', () => {
  it('should have valid package.json', () => {
    const pkg = require('../package.json');
    expect(pkg.name).toBeDefined();
    expect(pkg.version).toBeDefined();
  });

  it('should have .session directory structure', () => {
    expect(existsSync('.session/tracking')).toBe(true);
    expect(existsSync('.session/specs')).toBe(true);
    expect(existsSync('.session/briefings')).toBe(true);
    expect(existsSync('.session/history')).toBe(true);
  });

  it('should have required config files', () => {
    expect(existsSync('.eslintrc.json')).toBe(true);
    expect(existsSync('.prettierrc.json')).toBe(true);
  });

  it('should have session config', () => {
    expect(existsSync('.session/config.json')).toBe(true);
  });

  it('should have work items tracking', () => {
    expect(existsSync('.session/tracking/work_items.json')).toBe(true);
    expect(existsSync('.session/tracking/learnings.json')).toBe(true);
  });

  it('should have initial commit from sdd init', () => {
    // Check if .git directory exists
    expect(existsSync('.git')).toBe(true);

    try {
      // Get commit count
      const commitCount = parseInt(
        execSync('git rev-list --count HEAD', { encoding: 'utf-8' }).trim()
      );
      expect(commitCount).toBeGreaterThan(0);

      // Get first commit message
      const firstCommitMessage = execSync(
        'git log --reverse --format=%B -n 1',
        { encoding: 'utf-8' }
      ).trim();

      // Verify it's an SDD initialization commit
      const isSddCommit =
        firstCommitMessage.includes('Initialize project with Session-Driven Development') ||
        firstCommitMessage.includes('Session-Driven Development');

      expect(isSddCommit).toBe(true);
    } catch (error) {
      throw new Error(`Git command failed: ${error.message}`);
    }
  });
});
