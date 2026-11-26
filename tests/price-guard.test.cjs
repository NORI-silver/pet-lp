// 料金の基本・上乗せの判定（tools/cardpolicy.py）の両方向の固定データ。本物の基本料金を隠さず、上乗せだけの値を基本にしない。
const { spawnSync } = require("child_process");
const path = require("path");
const r = spawnSync("python3", [path.join(__dirname, "..", "tools", "price_guard_fixtures.py")], { encoding: "utf8" });
process.stdout.write(r.stdout || "");
if (r.status !== 0) { process.stderr.write(r.stderr || ""); console.error("FAIL: price guard fixtures"); process.exit(1); }
