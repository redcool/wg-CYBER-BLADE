import fs from 'fs';
let bundle = fs.readFileSync('src/data/data-bundle.js', 'utf8');

// Find all character "speed": N lines
const regex = /"speed":\s*(\d+)/g;
let match;
let count = 0;
while ((match = regex.exec(bundle)) !== null) {
  const oldSpeed = parseInt(match[1]);
  const newSpeed = Math.round(oldSpeed * 1.3);
  console.log(oldSpeed + ' -> ' + newSpeed);
  count++;
}
console.log('Total speed fields: ' + count);

// Now replace
let result = bundle.replace(/"speed":\s*(\d+)/g, (m, speed) => {
  return '"speed": ' + Math.round(parseInt(speed) * 1.3);
});

fs.writeFileSync('src/data/data-bundle.js', result);
console.log('Done!');
