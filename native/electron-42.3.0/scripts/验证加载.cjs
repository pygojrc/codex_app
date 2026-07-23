// 由项目内 Electron 实际加载四个 native module，避免只检查 ELF 外观。
const assert = require("node:assert");

const Database = require("better-sqlite3");
const pty = require("node-pty");
const serial = require("@serialport/bindings-cpp");
const hid = require("node-hid");

const database = new Database(":memory:");
assert.strictEqual(database.prepare("select 42 as value").get().value, 42);
database.close();
assert.strictEqual(typeof pty.spawn, "function");
assert.ok(serial.autoDetect);
assert.strictEqual(typeof hid.devices, "function");
assert.ok(Array.isArray(hid.devices()));

console.log("native modules loaded", {
  electron: process.versions.electron,
  modules: process.versions.modules,
  arch: process.arch,
});
