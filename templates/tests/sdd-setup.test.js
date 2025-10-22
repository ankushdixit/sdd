const { existsSync } = require('fs');
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
});
