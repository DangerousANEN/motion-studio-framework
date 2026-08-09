// remotion/src/lib/safeArea.ts
var REFERENCE_HEIGHT = 1920;
var REFERENCE_WIDTH = 1080;
var PROFILES = {
  platform: { top: 280, bottom: 380, left: 80, right: 80 },
  loose: { top: 140, bottom: 180, left: 60, right: 60 },
  none: { top: 0, bottom: 0, left: 0, right: 0 }
};
function getSafeArea(width, height, mode = "platform", custom) {
  let insets;
  if (mode === "custom") {
    insets = {
      top: custom?.top ?? 0,
      bottom: custom?.bottom ?? 0,
      left: custom?.left ?? 0,
      right: custom?.right ?? 0
    };
  } else {
    const ref = PROFILES[mode];
    const vScale = height / REFERENCE_HEIGHT;
    const hScale = width / REFERENCE_WIDTH;
    insets = {
      top: Math.round(ref.top * vScale),
      bottom: Math.round(ref.bottom * vScale),
      left: Math.round(ref.left * hScale),
      right: Math.round(ref.right * hScale)
    };
  }
  const usableWidth = Math.max(0, width - insets.left - insets.right);
  const usableHeight = Math.max(0, height - insets.top - insets.bottom);
  return {
    ...insets,
    width: usableWidth,
    height: usableHeight,
    centerX: insets.left + usableWidth / 2,
    centerY: insets.top + usableHeight / 2
  };
}
function safeAreaPadding(width, height, mode = "platform", custom) {
  const safe = getSafeArea(width, height, mode, custom);
  return {
    paddingTop: safe.top,
    paddingBottom: safe.bottom,
    paddingLeft: safe.left,
    paddingRight: safe.right
  };
}
function safeAreaBox(width, height, mode = "platform", custom) {
  const safe = getSafeArea(width, height, mode, custom);
  return {
    position: "absolute",
    top: safe.top,
    left: safe.left,
    width: safe.width,
    height: safe.height
  };
}
function violatesSafeArea(box, canvasWidth, canvasHeight, mode = "platform") {
  const safe = getSafeArea(canvasWidth, canvasHeight, mode);
  const reasons = [];
  if (box.top < safe.top) {
    reasons.push(`top ${box.top} is above safe top ${safe.top}`);
  }
  if (box.top + box.height > canvasHeight - safe.bottom) {
    reasons.push(
      `bottom ${box.top + box.height} is below safe bottom ${canvasHeight - safe.bottom}`
    );
  }
  if (box.left < safe.left) {
    reasons.push(`left ${box.left} is outside safe left ${safe.left}`);
  }
  if (box.left + box.width > canvasWidth - safe.right) {
    reasons.push(
      `right ${box.left + box.width} is outside safe right ${canvasWidth - safe.right}`
    );
  }
  return { violates: reasons.length > 0, reasons };
}

// audit/safearea_probe.ts
var failures = 0;
var checks = 0;
function ok(cond, label, detail = "") {
  checks++;
  if (!cond) {
    failures++;
    console.log(`  FAIL  ${label} ${detail}`);
  }
}
console.log("=== 1080x1920 profiles ===");
for (const mode of ["platform", "loose", "none"]) {
  const s = getSafeArea(1080, 1920, mode);
  console.log(
    `  ${mode.padEnd(9)} top=${String(s.top).padStart(3)} bottom=${String(s.bottom).padStart(3)} sides=${s.left}/${s.right}  box=${s.width}x${s.height}  center=(${s.centerX},${s.centerY})`
  );
  ok(s.width === 1080 - s.left - s.right, `${mode}: width math`, `${s.width}`);
  ok(s.height === 1920 - s.top - s.bottom, `${mode}: height math`, `${s.height}`);
  ok(s.width >= 0 && s.height >= 0, `${mode}: non-negative box`);
}
{
  const p = getSafeArea(1080, 1920, "platform");
  ok(p.top === 280, "platform top is 280", String(p.top));
  ok(p.bottom === 380, "platform bottom is 380", String(p.bottom));
  ok(p.left === 80 && p.right === 80, "platform sides are 80");
  ok(
    p.bottom > p.top,
    "bottom inset exceeds top inset (asymmetric)",
    `top=${p.top} bottom=${p.bottom}`
  );
  const none = getSafeArea(1080, 1920, "none");
  ok(none.width === 1080 && none.height === 1920, "none is full bleed");
}
console.log("\n=== regression: the bug that motivated this ===");
{
  const caption = { top: 1800, left: 80, width: 920, height: 100 };
  const v = violatesSafeArea(caption, 1080, 1920, "platform");
  ok(v.violates, "caption at y=1800 is rejected by platform profile");
  console.log(`  y=1800 caption -> violates=${v.violates}`);
  for (const r of v.reasons) console.log(`      ${r}`);
  const safe = getSafeArea(1080, 1920, "platform");
  const good = { top: safe.top + 50, left: safe.left, width: safe.width, height: 100 };
  const v2 = violatesSafeArea(good, 1080, 1920, "platform");
  ok(!v2.violates, "caption inside the safe box passes", v2.reasons.join("; "));
  console.log(`  y=${good.top} caption -> violates=${v2.violates}`);
  const oldStyle = getSafeArea(1080, 1920, "custom", {
    top: 120,
    bottom: 120,
    left: 120,
    right: 120
  });
  ok(
    oldStyle.bottom < safe.bottom,
    "legacy 120 margin is weaker than platform bottom",
    `legacy=${oldStyle.bottom} platform=${safe.bottom}`
  );
  console.log(`  legacy bottom=${oldStyle.bottom} vs platform bottom=${safe.bottom}`);
}
console.log("\n=== scaling to other canvases ===");
for (const [w, h, label] of [
  [1080, 1920, "vertical 1080p"],
  [720, 1280, "vertical 720p"],
  [1920, 1080, "landscape"],
  [1080, 1080, "square"]
]) {
  const s = getSafeArea(w, h, "platform");
  console.log(
    `  ${label.padEnd(16)} ${w}x${h} -> top=${String(s.top).padStart(3)} bottom=${String(s.bottom).padStart(3)} sides=${s.left}/${s.right} box=${s.width}x${s.height}`
  );
  ok(
    s.width > 0 && s.height > 0,
    `${label}: usable box is positive`,
    `${s.width}x${s.height}`
  );
  ok(s.width <= w && s.height <= h, `${label}: box fits canvas`);
}
{
  const s = getSafeArea(720, 1280, "platform");
  ok(s.top === Math.round(280 * (1280 / 1920)), "720p top scales proportionally", String(s.top));
  ok(s.bottom === Math.round(380 * (1280 / 1920)), "720p bottom scales proportionally", String(s.bottom));
  ok(s.left === Math.round(80 * (720 / 1080)), "720p sides scale on width", String(s.left));
}
console.log("\n=== degenerate inputs ===");
{
  const s = getSafeArea(1080, 1920, "custom", {
    top: 1200,
    bottom: 1200,
    left: 700,
    right: 700
  });
  ok(s.width === 0, "over-wide insets clamp width to 0", String(s.width));
  ok(s.height === 0, "over-tall insets clamp height to 0", String(s.height));
  ok(
    Number.isFinite(s.centerX) && Number.isFinite(s.centerY),
    "centers stay finite on a degenerate box",
    `${s.centerX},${s.centerY}`
  );
  console.log(`  oversized insets -> box=${s.width}x${s.height} center=(${s.centerX},${s.centerY})`);
  const tiny = getSafeArea(100, 100, "platform");
  ok(
    tiny.width >= 0 && tiny.height >= 0,
    "tiny canvas stays non-negative",
    `${tiny.width}x${tiny.height}`
  );
  console.log(`  100x100 platform -> box=${tiny.width}x${tiny.height}`);
  const partial = getSafeArea(1080, 1920, "custom", { top: 100 });
  ok(
    partial.top === 100 && partial.bottom === 0 && partial.left === 0,
    "partial custom insets default to 0",
    `${partial.top}/${partial.bottom}/${partial.left}`
  );
}
console.log("\n=== css helpers ===");
{
  const pad = safeAreaPadding(1080, 1920, "platform");
  ok(
    pad.paddingTop === 280 && pad.paddingBottom === 380,
    "padding helper matches profile",
    `${pad.paddingTop}/${pad.paddingBottom}`
  );
  ok(pad.paddingLeft === 80 && pad.paddingRight === 80, "padding sides match profile");
  console.log(`  padding -> ${pad.paddingTop}/${pad.paddingRight}/${pad.paddingBottom}/${pad.paddingLeft}`);
  const box = safeAreaBox(1080, 1920, "platform");
  ok(box.position === "absolute", "box helper is absolutely positioned");
  ok(box.top === 280 && box.left === 80, "box helper origin matches insets");
  ok(
    box.width === 920 && box.height === 1260,
    "box helper size matches usable area",
    `${box.width}x${box.height}`
  );
  console.log(`  box -> top=${box.top} left=${box.left} ${box.width}x${box.height}`);
}
console.log("\n=== violation reporting ===");
{
  const safe = getSafeArea(1080, 1920, "platform");
  const cases = [
    ["fully inside", { top: safe.top, left: safe.left, width: safe.width, height: 200 }, false],
    ["above top", { top: 100, left: safe.left, width: safe.width, height: 200 }, true],
    ["below bottom", { top: 1600, left: safe.left, width: safe.width, height: 300 }, true],
    ["past left", { top: safe.top, left: 10, width: 400, height: 200 }, true],
    ["past right", { top: safe.top, left: 800, width: 400, height: 200 }, true],
    ["full bleed", { top: 0, left: 0, width: 1080, height: 1920 }, true]
  ];
  for (const [label, box, shouldViolate] of cases) {
    const v = violatesSafeArea(box, 1080, 1920, "platform");
    ok(
      v.violates === shouldViolate,
      `violation: ${label}`,
      `expected ${shouldViolate}, got ${v.violates} (${v.reasons.join("; ")})`
    );
    console.log(`  ${label.padEnd(14)} violates=${String(v.violates).padEnd(5)} ${v.reasons.length} reason(s)`);
  }
  const fullBleed = violatesSafeArea(
    { top: 0, left: 0, width: 1080, height: 1920 },
    1080,
    1920,
    "none"
  );
  ok(
    !fullBleed.violates,
    "full bleed is legal under none profile",
    fullBleed.reasons.join("; ")
  );
}
console.log(`
${"=".repeat(52)}`);
console.log(`checks: ${checks}   failures: ${failures}`);
console.log(failures === 0 ? "SAFE AREA: ALL CHECKS PASS" : "SAFE AREA: FAILURES PRESENT");
process.exit(failures === 0 ? 0 : 1);
