import { readFile } from 'node:fs/promises';
import { ESLint } from 'eslint';
import globals from 'globals';

const eslint = new ESLint({
  overrideConfigFile: true,
  overrideConfig: [{
    languageOptions: {
      ecmaVersion: 'latest',
      globals: { ...globals.browser, ...globals.node, doReset: 'readonly' },
    },
    rules: {
      'no-undef': 'error', 'no-unreachable': 'error', 'no-dupe-args': 'error',
      'no-dupe-keys': 'error', 'no-constant-condition': 'error',
      'valid-typeof': 'error', 'constructor-super': 'error',
    },
  }],
});
const results = [];
for (const file of ['web/bitling.html', 'web/panel.html']) {
  const html = await readFile(file, 'utf8');
  for (const [index, match] of [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].entries()) {
    results.push(...await eslint.lintText(match[1], { filePath: `${file}.${index}.js` }));
  }
}
results.push(...await eslint.lintFiles(['Tools/*.mjs', 'tests/*.mjs']));
const formatter = await eslint.loadFormatter('stylish');
process.stdout.write(formatter.format(results));
const errors = results.reduce((sum, result) => sum + result.errorCount, 0);
if (errors) process.exitCode = 1;
else console.log('JavaScript lint passed (shared pet, control panel, and verification tools).');
